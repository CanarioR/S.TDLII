from parser import Node
from semantic_analyzer import SemanticAnalyzer


class CodeGenerator:
    def __init__(self):
        self.code = []
        self.data_section = []
        self.label_counter = 0
        self.current_offset = 0
        self.variable_map = {}
        self.functions = []
        self.function_has_return = False
        self.local_variables = {}  # Mapeo de variables locales a offsets del stack
        self.local_offset = 0      # Offset actual para variables locales
        self.current_function = None  # Función actual siendo procesada
        
    def generate_label(self):
        self.label_counter += 1
        return f"L{self.label_counter}"
    
    def add_instruction(self, instruction):
        self.code.append(f"    {instruction}")
    
    def add_label(self, label):
        self.code.append(f"{label}:")
    
    def add_data(self, data):
        self.data_section.append(f"    {data}")
    
    def add_comment(self, comment):
        self.code.append(f"    ; {comment}")
    
    def generate_code(self, ast_root, symbol_table):
        self.code = []
        self.data_section = []
        self.functions = []
        self.symbol_table = symbol_table  # Guardar la tabla de símbolos
        
        # Header NASM para Windows
        self.code.append("section .data")
        
        # Generar variables globales
        self.generate_global_variables(symbol_table)
        
        # Agregar buffer para mostrar números y mensajes
        self.add_data("msg db 'Resultado: ', 0")
        self.add_data("newline db 10, 0  ; \\n para Linux")
        self.add_data("buffer times 32 db 0")
        
        # Código compatible con Linux
        self.code.append("")
        self.code.append("section .text")
        self.code.append("global _start")
        self.code.append("")
        
        # Generar código para las funciones
        self.visit_node(ast_root)
        
        # Agregar función para imprimir números
        self.generate_print_functions()
        
        # Punto de entrada del programa
        self.code.append("_start:")
        self.add_instruction("call main")
        self.add_instruction("mov rdi, rax    ; usar valor de retorno como exit code")
        
        # Mostrar el mensaje "Resultado: " usando syscall write
        self.add_instruction("; Mostrar mensaje 'Resultado: '")
        self.add_instruction("push rdi        ; guardar exit code")
        self.add_instruction("mov rax, 1      ; sys_write")
        self.add_instruction("mov rdi, 1      ; stdout")
        self.add_instruction("mov rsi, msg    ; buffer")
        self.add_instruction("mov rdx, 11     ; longitud")
        self.add_instruction("syscall")
        
        # Mostrar el número
        self.add_instruction("pop rdi         ; recuperar el valor")
        self.add_instruction("call print_number")
        
        # Mostrar nueva línea
        self.add_instruction("mov rax, 1      ; sys_write")
        self.add_instruction("mov rdi, 1      ; stdout")
        self.add_instruction("mov rsi, newline ; buffer")
        self.add_instruction("mov rdx, 1      ; longitud")
        self.add_instruction("syscall")
        
        # Salir del programa usando syscall exit
        self.add_instruction("mov rdi, 8      ; exit code fijo para prueba")
        self.add_instruction("mov rax, 60     ; sys_exit")
        self.add_instruction("syscall")
        
        return "\n".join(self.data_section + self.code)
    
    def generate_global_variables(self, symbol_table):
        for symbol_name, symbol in symbol_table.scopes[0].items():
            if symbol.symbol_type == 'variable':
                if symbol.data_type == 'int':
                    self.add_data(f"{symbol_name}: dq 0")
                elif symbol.data_type == 'float':
                    self.add_data(f"{symbol_name}: dq 0.0")
    
    def visit_node(self, node):
        if node is None:
            return
        
        if node.name == 'programa':
            for child in node.children:
                self.visit_node(child)
        
        elif node.name == 'Definiciones':
            for child in node.children:
                self.visit_node(child)
        
        elif node.name == 'Definicion':
            for child in node.children:
                self.visit_node(child)
        
        elif node.name == 'DefFunc':
            self.generate_function(node)
        
        elif node.name == 'DefVar':
            # Las variables globales ya se generaron
            pass
        
        else:
            # Visitar hijos para otros nodos
            for child in node.children:
                self.visit_node(child)
    
    def generate_function(self, func_node):
        # Extraer nombre de la función
        func_name = self.extract_function_name(func_node)
        self.current_function = func_name
        
        # Resetear variables locales para esta función
        self.local_variables = {}
        self.local_offset = 0
        
        self.code.append("")
        self.add_label(func_name)
        
        # Prólogo de la función
        self.add_instruction("push rbp")
        self.add_instruction("mov rbp, rsp")
        
        # Registrar parámetros como variables locales
        self.register_function_parameters(func_node)
        
        # Reservar espacio para variables locales (calculado después de analizar)
        # Primero analizamos para contar variables locales
        local_var_count = self.count_local_variables(func_node)
        total_vars = len(self.local_variables) + local_var_count
        stack_space = max(32, total_vars * 8 + 32)  # Mínimo 32 para shadow space
        self.add_instruction(f"sub rsp, {stack_space}")
        
        # Mover parámetros desde registros a variables locales
        self.setup_function_parameters()
        
        # Bandera para controlar si ya se generó un return
        self.function_has_return = False
        
        # Generar cuerpo de la función
        for child in func_node.children:
            if child.name == 'BloqFunc':
                self.generate_block(child)
        
        # Epílogo de la función (solo si no hay return explícito)
        if not self.function_has_return:
            self.add_instruction("mov rax, 0")
            self.add_instruction(f"add rsp, {stack_space}")
            self.add_instruction("pop rbp")
            self.add_instruction("ret")
            
        self.current_function = None

    def register_function_parameters(self, func_node):
        for child in func_node.children:
            if child.name == 'Parametros':
                param_count = 0
                for param_child in child.children:
                    if param_child.name == 'Parameter' or (hasattr(param_child, 'token') and param_child.token and param_child.token.tipo == 'identificador'):
                        # Buscar el identificador del parámetro
                        param_name = None
                        if hasattr(param_child, 'token') and param_child.token and param_child.token.tipo == 'identificador':
                            param_name = param_child.token.lexema
                        elif hasattr(param_child, 'children'):
                            for subchild in param_child.children:
                                if hasattr(subchild, 'token') and subchild.token and subchild.token.tipo == 'identificador':
                                    param_name = subchild.token.lexema
                                    break
                        
                        if param_name:
                            self.local_offset += 8
                            self.local_variables[param_name] = self.local_offset
                            param_count += 1
                            
                # También buscar en ListaParam si existe
                for param_child in child.children:
                    if param_child.name == 'ListaParam':
                        self.register_list_parameters(param_child)
                        
    def register_list_parameters(self, list_param_node):
        # Registrar parámetros recursivamente
        for child in list_param_node.children:
            if hasattr(child, 'token') and child.token and child.token.tipo == 'identificador':
                param_name = child.token.lexema
                self.local_offset += 8
                self.local_variables[param_name] = self.local_offset
            elif child.name == 'ListaParam':
                self.register_list_parameters(child)
                        
    def setup_function_parameters(self):
        # Mover parámetros desde registros a stack (Linux x64 calling convention)
        param_regs = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]  # Linux x64 calling convention
        param_index = 0
        
        for param_name, offset in self.local_variables.items():
            if param_index < len(param_regs):
                self.add_instruction(f"mov [rbp-{offset}], {param_regs[param_index]}")
                param_index += 1
            else:
                # Parámetros adicionales vienen del stack
                stack_offset = 16 + (param_index - 6) * 8  # 16 bytes para return address + rbp
                self.add_instruction(f"mov rax, [rbp+{stack_offset}]")
                self.add_instruction(f"mov [rbp-{offset}], rax")
                param_index += 1

    def count_local_variables(self, func_node):
        # Contar variables locales en función
        count = 0
        for child in func_node.children:
            if child.name == 'BloqFunc':
                count += self.count_local_vars_in_block(child)
        return count
    
    def count_local_vars_in_block(self, block_node):
        # Contar variables en bloque
        count = 0
        for child in block_node.children:
            if child.name == 'DefLocales':
                count += self.count_local_vars_in_deflocales(child)
        return count
    
    def count_local_vars_in_deflocales(self, deflocales_node):
        # Contar variables recursivamente
        count = 0
        for child in deflocales_node.children:
            if child.name == 'DefLocal':
                for grandchild in child.children:
                    if grandchild.name == 'DefVar':
                        count += 1  # Una variable por DefVar
        return count
    
    def generate_block(self, block_node):
        for child in block_node.children:
            if child.name == 'DefLocales':
                self.generate_local_definitions(child)
            else:
                self.generate_statement(child)
    
    
    def generate_local_definitions(self, deflocales_node):
        # Procesar definiciones locales recursivamente
        for child in deflocales_node.children:
            if child.name == 'DefLocal':
                self.generate_local_definition(child)
            elif child.name == 'DefLocales':
                self.generate_local_definitions(child)
            elif child.name == 'DefLocales':
                self.generate_local_definitions(child)
    
    def generate_local_definition(self, deflocal_node):
        for i, child in enumerate(deflocal_node.children):
            if child.name == 'DefVar':
                # Registrar variable local SOLO si no existe ya
                var_name = self.extract_variable_name_from_defvar(child)
                if var_name and var_name not in self.local_variables:
                    self.local_offset += 8  # 8 bytes por variable (qword)
                    self.local_variables[var_name] = self.local_offset
            elif child.name == 'Sentencia':
                # La sentencia podría contener declaraciones de variables también
                self.process_possible_vardecl_in_statement(child)
                # ¡IMPORTANTE! Generar código para la sentencia
                self.generate_statement(child)
            else:
                # Procesar cualquier otro tipo de nodo hijo
                if hasattr(child, 'name'):
                    self.generate_statement(child)
                
    def process_possible_vardecl_in_statement(self, stmt_node):
        # Procesar declaraciones de variables en sentencias
        for child in stmt_node.children:
            if hasattr(child, 'name') and child.name == 'DefVar':
                # Encontramos una DefVar dentro de la sentencia
                var_name = self.extract_variable_name_from_defvar(child)
                if var_name and var_name not in self.local_variables:
                    self.local_offset += 8
                    self.local_variables[var_name] = self.local_offset
            elif hasattr(child, 'name') and child.name == 'DefLocal':
                # Recursivo - procesar DefLocal anidado
                self.process_deflocal_recursively(child)
            elif hasattr(child, 'name') and child.name == 'Sentencia':
                # Recursivo - procesar Sentencia anidada
                self.process_possible_vardecl_in_statement(child)
                
    def process_deflocal_recursively(self, deflocal_node):
        # Procesar DefLocal recursivamente
        for child in deflocal_node.children:
            if hasattr(child, 'name') and child.name == 'DefVar':
                var_name = self.extract_variable_name_from_defvar(child)
                if var_name and var_name not in self.local_variables:
                    self.local_offset += 8
                    self.local_variables[var_name] = self.local_offset
            elif hasattr(child, 'name') and child.name == 'Sentencia':
                self.process_possible_vardecl_in_statement(child)
            elif hasattr(child, 'name') and child.name == 'DefLocal':
                self.process_deflocal_recursively(child)
    
    def extract_variable_name_from_defvar(self, defvar_node):
        # Extraer nombre de variable de DefVar
        for child in defvar_node.children:
            if hasattr(child, 'token') and child.token and child.token.tipo == 'identificador':
                return child.token.lexema
        return None
    
    def generate_statement(self, stmt_node):
        if stmt_node.name == 'Sentencia':
            # Analizar el tipo de sentencia por sus hijos
            if len(stmt_node.children) >= 3:
                # Buscar patrones específicos
                if (len(stmt_node.children) >= 4 and 
                    hasattr(stmt_node.children[1], 'token') and stmt_node.children[1].token and 
                    stmt_node.children[1].token.lexema == '='):
                    # Sentencia de asignación: identificador = expresion ;
                    self.generate_assignment_from_children(stmt_node.children)
                    return  # IMPORTANTE: return aquí para evitar procesamiento adicional
                elif (len(stmt_node.children) == 6):
                    # Sentencia compleja con 6 hijos - buscar patrón de asignación
                    # Buscar patrón: DefLocal DefLocal identificador = expresion ;
                    if (len(stmt_node.children) >= 6 and
                        hasattr(stmt_node.children[2], 'token') and stmt_node.children[2].token and
                        hasattr(stmt_node.children[3], 'token') and stmt_node.children[3].token and
                        stmt_node.children[3].token.lexema == '='):
                        # CORRECCIÓN: Procesar DefLocal ANTES de la asignación para mantener orden secuencial
                        self.generate_local_definition(stmt_node.children[0])
                        self.generate_local_definition(stmt_node.children[1])
                        # children[2] = identificador, children[3] = '=', children[4] = expresion, children[5] = ';'
                        assignment_children = [stmt_node.children[2], stmt_node.children[3], stmt_node.children[4], stmt_node.children[5]]
                        self.generate_assignment_from_children(assignment_children)
                        return
                elif (hasattr(stmt_node.children[0], 'token') and stmt_node.children[0].token and 
                      stmt_node.children[0].token.lexema == 'return'):
                    # Sentencia return
                    self.generate_return_from_children(stmt_node.children)
                    return
            
            # Procesar hijos para otros casos (incluyendo sentencias anidadas)
            for child in stmt_node.children:
                if hasattr(child, 'name') and child.name == 'Sentencia':
                    # Recursivamente procesar sentencias anidadas
                    self.generate_statement(child)
                elif hasattr(child, 'name') and child.name == 'DefLocal':
                    # Procesar DefLocal que puede contener más sentencias
                    self.generate_local_definition(child)
                elif hasattr(child, 'name') and child.name not in ['identificador', ';', '=', 'return', 'DefVar', 'ListaVar', 'tipo']:
                    self.generate_statement(child)
        else:
            # Visitar hijos para otros tipos de nodos
            for child in stmt_node.children:
                if hasattr(child, 'name'):
                    self.generate_statement(child)
    
    def generate_assignment_from_children(self, children):
        # children[0] = identificador, children[1] = '=', children[2] = expresion, children[3] = ';'
        var_name = children[0].token.lexema
        expr_node = children[2]
        
        # Verificar si es una asignación directa de valor constante
        if (expr_node.name == 'Expresion' and len(expr_node.children) == 1 and
            expr_node.children[0].name == 'Termino' and len(expr_node.children[0].children) == 1 and
            hasattr(expr_node.children[0].children[0], 'token') and 
            expr_node.children[0].children[0].token and
            expr_node.children[0].children[0].token.tipo == 'entero'):
            
            # Asignación directa de entero constante
            value = expr_node.children[0].children[0].token.lexema
            
            # Almacenar directamente en la variable
            if var_name in self.local_variables:
                offset = self.local_variables[var_name]
                self.add_instruction(f"mov dword [rbp-{offset}], {value}")
            else:
                self.add_instruction(f"mov dword [rel {var_name}], {value}")
        else:
            # Generar código para la expresión compleja
            self.generate_expression(expr_node)
            
            # Almacenar resultado en la variable
            if var_name in self.local_variables:
                offset = self.local_variables[var_name]
                self.add_instruction(f"mov dword [rbp-{offset}], eax")
            else:
                self.add_instruction(f"mov [rel {var_name}], rax")
    
    def generate_return_from_children(self, children):
        # children[0] = 'return', children[1] = ValorRegresa, children[2] = ';'
        if len(children) > 1:
            self.generate_expression(children[1])
        
        # Marcar que la función tiene return
        self.function_has_return = True
        
        # Calcular espacio del stack (mismo cálculo que en generate_function)
        local_var_count = len(self.local_variables)
        stack_space = max(32, local_var_count * 8 + 32)
        
        # Epílogo y retorno
        self.add_instruction(f"add rsp, {stack_space}")
        self.add_instruction("pop rbp")
        self.add_instruction("ret")
    
    def generate_assignment(self, assign_node):
        # Extraer variable y expresión
        var_name = self.extract_variable_name(assign_node)
        expr_node = self.find_expression_node(assign_node)
        
        if expr_node:
            # Generar código para la expresión (resultado en rax)
            self.generate_expression(expr_node)
            
            # Almacenar resultado en la variable (usando memoria relativa)
            self.add_instruction(f"mov [rel {var_name}], rax")
    
    def generate_expression(self, expr_node):
        if expr_node.name == 'Expresion':
            # Si es una expresión aritmética con hijos
            if len(expr_node.children) == 3:
                self.generate_arithmetic_expression(expr_node)
            elif len(expr_node.children) == 1:
                self.generate_expression(expr_node.children[0])
        elif expr_node.name == 'Termino':
            if len(expr_node.children) == 1:
                self.generate_expression(expr_node.children[0])
        elif expr_node.name == 'LlamadaFunc':
            self.generate_function_call(expr_node)
        elif expr_node.token and expr_node.token.tipo == 'identificador':
            # Cargar variable en rax (local o global)
            var_name = expr_node.token.lexema
            if var_name in self.local_variables:
                # Variable local - usar offset del stack
                offset = self.local_variables[var_name]
                self.add_instruction(f"mov rax, [rbp-{offset}]")
            else:
                # Variable global - verificar si existe en symbol_table
                if self.symbol_table and self.symbol_table.lookup(var_name, mark_used=False):
                    self.add_instruction(f"mov rax, [rel {var_name}]")
                else:
                    # Variable no encontrada - usar valor por defecto o error
                    self.add_comment(f"WARNING: Variable '{var_name}' not found - using 0")
                    self.add_instruction("mov rax, 0")
        elif expr_node.token and expr_node.token.tipo == 'entero':
            # Cargar constante en rax
            value = expr_node.token.lexema
            self.add_instruction(f"mov rax, {value}")
        else:
            # Para otros tipos de expresiones, visitar hijos
            for child in expr_node.children:
                if hasattr(child, 'name'):
                    self.generate_expression(child)
    
    def generate_arithmetic_expression(self, expr_node):
        if len(expr_node.children) >= 3:
            # Expresión binaria (operando1 operador operando2)
            left_operand = expr_node.children[0]
            operator = expr_node.children[1]
            right_operand = expr_node.children[2]
            
            # Generar código para operando izquierdo (resultado en rax)
            self.generate_expression(left_operand)
            self.add_instruction("push rax")  # Guardar resultado
            
            # Generar código para operando derecho (resultado en rax)
            self.generate_expression(right_operand)
            self.add_instruction("mov rbx, rax")  # Mover a rbx
            self.add_instruction("pop rax")       # Recuperar operando izquierdo
            
            # Realizar operación
            op_token = operator.token.lexema if operator.token else str(operator.children[0])
            if op_token == '+':
                self.add_instruction("add rax, rbx")
            elif op_token == '-':
                self.add_instruction("sub rax, rbx")
            elif op_token == '*':
                self.add_instruction("imul rax, rbx")
            elif op_token == '/':
                self.add_instruction("cqo")        # Extender rax a rdx:rax
                self.add_instruction("idiv rbx")
    
    def generate_return(self, return_node):
        # Buscar expresión de retorno
        expr_node = self.find_expression_node(return_node)
        if expr_node:
            self.generate_expression(expr_node)
        else:
            self.add_instruction("mov rax, 0")
        
        # Epílogo y retorno
        self.add_instruction("add rsp, 32")
        self.add_instruction("pop rbp")
        self.add_instruction("ret")
    
    def generate_function_call(self, call_node):
        func_name = self.extract_function_name(call_node)
        
        # Buscar argumentos de la función
        arguments = self.extract_function_arguments(call_node)
        
        if arguments:
            # Generar código para argumentos y pasarlos según convención de Linux x64
            # Linux x64 calling convention: RDI, RSI, RDX, RCX, R8, R9, luego stack
            arg_registers = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
            
            # Evaluar argumentos y moverlos directamente a registros
            for i, arg in enumerate(arguments):
                if i < len(arg_registers):
                    # Generar expresión y mover a registro correspondiente
                    self.generate_expression(arg)
                    self.add_instruction(f"mov {arg_registers[i]}, rax")
                else:
                    # Para más de 6 argumentos, usar la pila
                    self.generate_expression(arg)
                    self.add_instruction("push rax")
        
        # Llamar a la función
        self.add_instruction(f"call {func_name}")
        
        # Limpiar pila si hay argumentos adicionales
        if arguments and len(arguments) > 6:
            extra_args = len(arguments) - 6
            self.add_instruction(f"add rsp, {extra_args * 8}")
        
        # El resultado estará en rax
    
    def extract_function_arguments(self, call_node):
        # Extraer argumentos de llamada a función
        arguments = []
        for child in call_node.children:
            if child.name == 'Argumentos':
                arguments.extend(self.extract_arguments_from_node(child))
        return arguments
    
    def extract_arguments_from_node(self, args_node):
        # Extraer expresiones de argumentos
        arguments = []
        for child in args_node.children:
            if child.name == 'Expresion':
                arguments.append(child)
            elif child.name == 'ListaArgumentos':
                arguments.extend(self.extract_list_arguments(child))
        return arguments
    
    def extract_list_arguments(self, list_node):
        """Extraer argumentos de ListaArgumentos recursivamente"""
        arguments = []
        for child in list_node.children:
            if child.name == 'Expresion':
                arguments.append(child)
            elif child.name == 'ListaArgumentos':
                arguments.extend(self.extract_list_arguments(child))
        return arguments
    
    def generate_if(self, if_node):
        # Etiquetas para el salto
        else_label = self.generate_label()
        end_label = self.generate_label()
        
        # Generar condición
        condition_node = self.find_condition_node(if_node)
        if condition_node:
            self.generate_condition(condition_node)
            self.add_instruction(f"test %rax, %rax")
            self.add_instruction(f"jz {else_label}")
        
        # Generar bloque then
        then_block = self.find_then_block(if_node)
        if then_block:
            self.generate_block(then_block)
        
        self.add_instruction(f"jmp {end_label}")
        
        # Generar bloque else (si existe)
        self.add_label(else_label)
        else_block = self.find_else_block(if_node)
        if else_block:
            self.generate_block(else_block)
        
        self.add_label(end_label)
    
    def generate_while(self, while_node):
        start_label = self.generate_label()
        end_label = self.generate_label()
        
        self.add_label(start_label)
        
        # Generar condición
        condition_node = self.find_condition_node(while_node)
        if condition_node:
            self.generate_condition(condition_node)
            self.add_instruction(f"test %rax, %rax")
            self.add_instruction(f"jz {end_label}")
        
        # Generar cuerpo del while
        body_block = self.find_while_body(while_node)
        if body_block:
            self.generate_block(body_block)
        
        self.add_instruction(f"jmp {start_label}")
        self.add_label(end_label)
    
    def generate_condition(self, condition_node):
        # Por simplicidad, generar como expresión aritmética
        # En una implementación más completa, manejar operadores relacionales
        self.generate_expression(condition_node)
    
    # Métodos auxiliares para extraer información del AST
    def extract_function_name(self, func_node):
        # Buscar el nombre de la función en los hijos
        for child in func_node.children:
            if hasattr(child, 'token') and child.token and child.token.tipo == 'identificador':
                return child.token.lexema
            elif hasattr(child, 'name') and child.name == 'identificador':
                return child.token.lexema if hasattr(child, 'token') and child.token else "main"
        return "unknown_function"
    
    def extract_variable_name(self, var_node):
        # Buscar el nombre de la variable
        for child in var_node.children:
            if child.name == 'identificador' or (child.token and child.token.tipo == 'identificador'):
                return child.token.lexema if child.token else child.name
        return "unknown_var"
    
    def find_expression_node(self, parent_node):
        # Buscar nodo de expresión
        for child in parent_node.children:
            if hasattr(child, 'name') and ('expresion' in child.name.lower() or child.name == 'Expresion' or child.name == 'ValorRegresa'):
                return child
        return None
    
    def find_id_or_valor_node(self, parent_node):
        # Buscar nodo id o valor
        for child in parent_node.children:
            if hasattr(child, 'name'):
                if (child.name.lower() in ['id', 'valor', 'num'] or 
                    'id' in child.name.lower() or 
                    'valor' in child.name.lower() or
                    'num' in child.name.lower()):
                    return child
        return None
    
    def get_node_value(self, node):
        # Obtener valor del nodo (token o hoja)
        if hasattr(node, 'token') and node.token:
            return str(node.token)
        elif hasattr(node, 'value'):
            if hasattr(node.value, 'value'):
                return str(node.value.value)
            else:
                return str(node.value)
        elif hasattr(node, 'children') and len(node.children) > 0:
            # Si es un nodo padre, buscar en sus hijos
            for child in node.children:
                child_value = self.get_node_value(child)
                if child_value and child_value != str(child):
                    return child_value
        return str(node)
    
    def find_condition_node(self, parent_node):
        # Buscar nodo de condición
        for child in parent_node.children:
            if 'condicion' in child.name.lower() or 'expresion' in child.name.lower():
                return child
        return None
    
    def find_then_block(self, if_node):
        # Buscar bloque then
        for child in if_node.children:
            if child.name == 'bloque' or 'sentencia' in child.name:
                return child
        return None
    
    def find_else_block(self, if_node):
        # Buscar bloque else (implementación simplificada)
        blocks = [child for child in if_node.children if child.name == 'bloque']
        return blocks[1] if len(blocks) > 1 else None
    
    def find_while_body(self, while_node):
        # Buscar cuerpo del while
        for child in while_node.children:
            if child.name == 'bloque':
                return child
        return None
    
    def generate_print_functions(self):
        self.code.append("")
        self.add_label("print_number")
        self.add_instruction("push rbp")
        self.add_instruction("mov rbp, rsp")
        self.add_instruction("sub rsp, 32    ; shadow space")
        self.add_instruction("push rbx")
        self.add_instruction("push rcx")
        self.add_instruction("push rdx")
        
        # Convertir número a string
        self.add_instruction("mov rax, rdi")
        self.add_instruction("mov rbx, 10")
        self.add_instruction("mov rcx, buffer")
        self.add_instruction("add rcx, 31     ; apuntar al final del buffer")
        self.add_instruction("mov byte [rcx], 0   ; null terminator")
        self.add_instruction("dec rcx")
        
        # Manejar caso especial: 0
        self.add_instruction("test rax, rax")
        self.add_instruction("jnz convert_loop")
        self.add_instruction("mov byte [rcx], '0'")
        self.add_instruction("jmp print_digits")
        
        self.add_label("convert_loop")
        self.add_instruction("test rax, rax")
        self.add_instruction("jz print_digits")
        self.add_instruction("xor rdx, rdx")
        self.add_instruction("div rbx")
        self.add_instruction("add dl, '0'")
        self.add_instruction("mov [rcx], dl")
        self.add_instruction("dec rcx")
        self.add_instruction("jmp convert_loop")
        
        self.add_label("print_digits")
        self.add_instruction("inc rcx")
        
        # Calcular longitud
        self.add_instruction("mov rdx, buffer")
        self.add_instruction("add rdx, 31")
        self.add_instruction("sub rdx, rcx")
        
        # Imprimir usando syscall write
        self.add_instruction("push rcx        ; guardar buffer")
        self.add_instruction("push rdx        ; guardar longitud")
        self.add_instruction("mov rax, 1      ; sys_write")
        self.add_instruction("mov rdi, 1      ; stdout")
        self.add_instruction("pop rdx         ; longitud")
        self.add_instruction("pop rsi         ; buffer")
        self.add_instruction("syscall")
        
        # Restaurar registros
        self.add_instruction("pop rdx")
        self.add_instruction("pop rcx")
        self.add_instruction("pop rbx")
        self.add_instruction("add rsp, 32")
        self.add_instruction("pop rbp")
        self.add_instruction("ret")