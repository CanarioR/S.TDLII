from parser import Node


class SemanticError(Exception):
    def __init__(self, message, node=None):
        self.message = message
        self.node = node
        super().__init__(self.message)
    
    def __str__(self):
        return self.message


class Symbol:
    def __init__(self, name, symbol_type, data_type=None, initialized=False, params=None, return_type=None):
        self.name = name
        self.symbol_type = symbol_type
        self.data_type = data_type
        self.initialized = initialized
        self.used = False
        self.params = params or []
        self.return_type = return_type
        self.defined_at = None
    
    def __str__(self):
        if self.symbol_type == 'function':
            param_str = ', '.join([f"{p}:{t}" for p, t in self.params])
            return f"Function({self.name}({param_str}) -> {self.return_type})"
        else:
            init_str = " [init]" if self.initialized else " [uninit]"
            return f"{self.symbol_type.capitalize()}({self.name}:{self.data_type}{init_str})"


class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.scope_names = ['global']
        self.current_function = None
    
    def enter_scope(self, scope_name):
        # Entra a un nuevo ámbito
        self.scopes.append({})
        self.scope_names.append(scope_name)
        print(f"[SEMANTIC] Entrando a scope: {scope_name}")
    
    def exit_scope(self):
        # Sale del ámbito actual
        if len(self.scopes) > 1:
            exiting_scope = self.scope_names.pop()
            exited_symbols = self.scopes.pop()
            print(f"[SEMANTIC] Saliendo de scope: {exiting_scope}")
        else:
            print("[SEMANTIC] Advertencia: Intentando salir del ámbito global")
    
    def current_scope(self):
        """Retorna el nombre del ámbito actual"""
        return self.scope_names[-1] if self.scope_names else 'unknown'
    
    def define(self, symbol):
        """Define un símbolo en el ámbito actual"""
        current_scope_dict = self.scopes[-1]
        
        # Verificar si ya existe en el ámbito actual
        if symbol.name in current_scope_dict:
            existing = current_scope_dict[symbol.name]
            raise SemanticError(f"El símbolo '{symbol.name}' ya está definido en el ámbito '{self.current_scope()}'")
        
        # Agregar el símbolo
        current_scope_dict[symbol.name] = symbol
        print(f"[SEMANTIC] Definido: {symbol} en scope '{self.current_scope()}'")
    
    def lookup(self, name, mark_used=True):
        """Busca un símbolo en todos los ámbitos"""
        for i in range(len(self.scopes) - 1, -1, -1):
            if name in self.scopes[i]:
                symbol = self.scopes[i][name]
                if mark_used:
                    symbol.used = True
                return symbol
        
        return None
    
    def get_all_symbols(self):
        """Retorna todos los símbolos con sus ámbitos"""
        all_symbols = []
        for i, scope_dict in enumerate(self.scopes):
            scope_name = self.scope_names[i]
            for symbol in scope_dict.values():
                all_symbols.append((scope_name, symbol))
        return all_symbols


class SemanticAnalyzer:
    """Analizador semántico que recorre el AST"""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.warnings = []
        self.current_function_return_type = None
        self.has_return = False
    
    def error(self, message, node=None):
        """Registra un error semántico"""
        self.errors.append(message)
        print(f"[SEMANTIC ERROR] {message}")
    
    def warning(self, message, node=None):
        """Registra una advertencia semántica"""
        self.warnings.append((message, node))
        print(f"[SEMANTIC WARNING] {message}")
    
    def analyze(self, ast_root):
        """Punto de entrada principal para el análisis semántico"""
        print("\\n========== ANÁLISIS SEMÁNTICO ==========\\n")
        print("[SEMANTIC] Analizando programa principal")
        
        try:
            # Primer pasada: recolectar declaraciones de funciones y variables globales
            self.collect_declarations(ast_root)
            
            # Segunda pasada: análisis semántico completo
            self.visit(ast_root)
            
            # Verificaciones finales
            self.final_checks()
            
            # Imprimir tabla de símbolos
            self.print_symbol_table()
            
            # Imprimir resultados
            self.print_results()
            
            return self.errors, [w[0] for w in self.warnings]
        except Exception as e:
            self.error(f"Error interno del analizador semántico: {e}")
            return self.errors, [w[0] for w in self.warnings]
    
    def collect_declarations(self, node):
        """Primer pasada: recolecta declaraciones de funciones y variables globales"""
        if node.name == 'Definiciones':
            for child in node.children:
                if isinstance(child, Node):
                    self.collect_declarations(child)
        elif node.name == 'Definicion':
            for child in node.children:
                if isinstance(child, Node):
                    if child.name == 'DefVar':
                        self.collect_global_var(child)
                    elif child.name == 'DefFunc':
                        self.collect_function(child)
        elif node.name == 'programa':
            for child in node.children:
                if isinstance(child, Node):
                    self.collect_declarations(child)
    
    def collect_global_var(self, node):
        """Recolecta variables globales"""
        if len(node.children) >= 2:
            type_node = node.children[0]
            name_node = node.children[1]
            
            if (type_node.state == Node.TERMINAL and 
                name_node.state == Node.TERMINAL):
                var_type = type_node.token.lexema
                var_name = name_node.token.lexema
                
                var_symbol = Symbol(
                    name=var_name,
                    symbol_type='variable',
                    data_type=var_type,
                    initialized=False
                )
                var_symbol.defined_at = node
                
                try:
                    self.symbol_table.define(var_symbol)
                except SemanticError as e:
                    self.error(str(e), node)
    
    def collect_function(self, node):
        """Recolecta declaraciones de funciones"""
        if len(node.children) >= 6:
            return_type_node = node.children[0]
            name_node = node.children[1]
            params_node = node.children[3]
            
            if (return_type_node.state == Node.TERMINAL and 
                name_node.state == Node.TERMINAL):
                func_name = name_node.token.lexema
                return_type = return_type_node.token.lexema
                
                # Extraer parámetros
                params = self.extract_parameters(params_node)
                
                func_symbol = Symbol(
                    name=func_name,
                    symbol_type='function',
                    return_type=return_type,
                    params=params
                )
                func_symbol.defined_at = node
                
                try:
                    self.symbol_table.define(func_symbol)
                except SemanticError as e:
                    self.error(str(e), node)
    
    def visit(self, node):
        """Método de dispatch para visitar nodos según su tipo"""
        if node is None:
            return None
            
        method_name = f"visit_{node.name}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node):
        """Visita genérica que recorre todos los hijos"""
        for child in node.children:
            if isinstance(child, Node):
                self.visit(child)
    
    def visit_DefFunc(self, node):
        """Visita una definición de función."""
        if len(node.children) < 6:
            return
        
        name_node = node.children[1]
        params_node = node.children[3]
        body_node = node.children[5]
        
        if name_node.state != Node.TERMINAL:
            return
        
        func_name = name_node.token.lexema
        
        # La función ya debería estar declarada
        func_symbol = self.symbol_table.lookup(func_name, mark_used=False)
        if not func_symbol:
            self.error(f"Función '{func_name}' no declarada correctamente", node)
            return
        
        # Entrar al scope de la función
        self.symbol_table.enter_scope(f"function_{func_name}")
        self.symbol_table.current_function = func_symbol
        self.current_function_return_type = func_symbol.return_type
        self.has_return = False
        
        # Agregar parámetros al scope de la función
        for param_name, param_type in func_symbol.params:
            param_symbol = Symbol(
                name=param_name,
                symbol_type='parameter',
                data_type=param_type,
                initialized=True
            )
            try:
                self.symbol_table.define(param_symbol)
            except SemanticError as e:
                self.error(str(e), node)
        
        # Analizar el cuerpo de la función
        self.visit(body_node)
        
        # Verificar que funciones no-void tengan return
        if func_symbol.return_type != 'void' and not self.has_return:
            self.warning(f"Función '{func_name}' con tipo de retorno '{func_symbol.return_type}' no tiene declaración return", node)
        
        # Salir del scope de la función
        self.symbol_table.exit_scope()
        self.symbol_table.current_function = None
        self.current_function_return_type = None
        self.has_return = False
    
    def visit_BloqFunc(self, node):
        """Visita el bloque de una función."""
        for child in node.children:
            if isinstance(child, Node) and child.name == 'DefLocales':
                self.visit(child)
    
    def visit_DefLocales(self, node):
        """Visita las definiciones locales."""
        for child in node.children:
            if isinstance(child, Node):
                self.visit(child)
    
    def visit_DefLocal(self, node):
        """Visita una definición local (variable o sentencia)."""
        for child in node.children:
            if isinstance(child, Node):
                self.visit(child)
    
    def visit_DefVar(self, node):
        """Visita una definición de variable local"""
        if len(node.children) >= 2:
            type_node = node.children[0]
            name_node = node.children[1]
            
            if (type_node.state == Node.TERMINAL and 
                name_node.state == Node.TERMINAL):
                var_type = type_node.token.lexema
                var_name = name_node.token.lexema
                
                # Solo definir variables locales (no globales ya definidas)
                if self.symbol_table.current_scope() != 'global':
                    var_symbol = Symbol(
                        name=var_name,
                        symbol_type='variable',
                        data_type=var_type,
                        initialized=False
                    )
                    var_symbol.defined_at = node
                    
                    try:
                        self.symbol_table.define(var_symbol)
                    except SemanticError as e:
                        self.error(str(e), node)
    
    def visit_Sentencia(self, node):
        """Visita una sentencia."""
        if len(node.children) == 0:
            return
        
        # Primero, visitar todos los hijos DefLocal que podrían contener declaraciones
        for child in node.children:
            if isinstance(child, Node) and child.name == 'DefLocal':
                self.visit(child)
        
        # Identificar tipo de sentencia basado en la estructura
        has_return = False
        has_assignment = False
        assignment_var = None
        assignment_op_pos = None
        
        # Analizar estructura completa - buscar patrón Identificador OpAsignacion
        for i, child in enumerate(node.children):
            if child.state == Node.TERMINAL:
                if child.name == 'return' or (hasattr(child, 'token') and child.token.lexema == 'return'):
                    has_return = True
                elif (child.name == '=' or child.name == 'OpAsignacion' or 
                      (hasattr(child, 'token') and child.token.lexema == '=')):
                    has_assignment = True
                    assignment_op_pos = i
                    # Buscar el identificador antes del =
                    for j in range(i-1, -1, -1):
                        prev_child = node.children[j]
                        if (prev_child.state == Node.TERMINAL and 
                            (prev_child.name == 'identificador' or 
                             prev_child.name == 'Identificador')):
                            assignment_var = prev_child.token.lexema
                            break
        
        if has_return:
            self.visit_return_statement(node)
        elif has_assignment and assignment_var:
            # Sentencia de asignación directa
            self.visit_assignment_in_sentencia(node, assignment_var, assignment_op_pos)
        else:
            # Visitar otros hijos que no sean DefLocal (ya visitados)
            for child in node.children:
                if isinstance(child, Node) and child.name != 'DefLocal':
                    self.visit(child)
    
    def visit_assignment_in_sentencia(self, node, var_name, op_pos):
        """Procesa una asignación dentro de una sentencia compleja"""
        
        # Buscar la expresión después del operador de asignación
        expr_node = None
        for i in range(op_pos + 1, len(node.children)):
            if isinstance(node.children[i], Node) and node.children[i].name == 'Expresion':
                expr_node = node.children[i]
                break
        
        if not expr_node:
            return
        
        # Verificar que la variable esté declarada
        var_symbol = self.symbol_table.lookup(var_name, mark_used=False)
        if not var_symbol:
            self.error(f"Variable '{var_name}' no declarada", node)
            return
        
        if var_symbol.symbol_type not in ['variable', 'parameter']:
            self.error(f"'{var_name}' no es una variable", node)
            return
        
        # Analizar la expresión del lado derecho
        expr_type = self.visit(expr_node)
        
        # Marcar variable como inicializada
        var_symbol.initialized = True
        var_symbol.used = True
        
        if expr_type and not self.are_types_compatible(var_symbol.data_type, expr_type):
            self.error(f"Asignación de tipo incompatible: '{var_name}' es '{var_symbol.data_type}' pero se asigna '{expr_type}'", node)
    
    def visit_return_statement(self, node):
        """Visita una sentencia return."""
        self.has_return = True
        
        if self.current_function_return_type is None:
            self.error("Sentencia 'return' fuera de una función", node)
            return
        
        # Buscar expresión de retorno
        for child in node.children:
            if isinstance(child, Node) and child.name in ['Expresion', 'ValorRegresa']:
                expr_type = self.visit(child)
                if expr_type and self.current_function_return_type != 'void':
                    if not self.are_types_compatible(self.current_function_return_type, expr_type):
                        self.error(f"Tipo de retorno incompatible: esperado '{self.current_function_return_type}', encontrado '{expr_type}'", node)
                break
    
    def visit_assignment_statement(self, node):
        """Visita una sentencia de asignación."""
        var_name = None
        expr_node = None
        
        for i, child in enumerate(node.children):
            if child.state == Node.TERMINAL and child.name == 'Identificador' and var_name is None:
                if (i + 1 < len(node.children) and 
                    node.children[i + 1].state == Node.TERMINAL and 
                    node.children[i + 1].name == 'OpAsignacion'):
                    var_name = child.token.lexema
            elif isinstance(child, Node) and child.name == 'Expresion' and expr_node is None:
                expr_node = child
        
        if not var_name or not expr_node:
            return
        
        # Verificar que la variable esté declarada
        var_symbol = self.symbol_table.lookup(var_name, mark_used=False)
        if not var_symbol:
            self.error(f"Variable '{var_name}' no declarada", node)
            return
        
        if var_symbol.symbol_type not in ['variable', 'parameter']:
            self.error(f"'{var_name}' no es una variable", node)
            return
        
        # Analizar la expresión del lado derecho
        expr_type = self.visit(expr_node)
        
        # Marcar variable como inicializada
        var_symbol.initialized = True
        var_symbol.used = True
        
        if expr_type and not self.are_types_compatible(var_symbol.data_type, expr_type):
            self.error(f"Asignación de tipo incompatible: '{var_name}' es '{var_symbol.data_type}' pero se asigna '{expr_type}'", node)
    
    def visit_ValorRegresa(self, node):
        """Visita el valor de retorno."""
        if len(node.children) > 0:
            return self.visit(node.children[0])
        return None
    
    def visit_Expresion(self, node):
        """Visita una expresión y retorna su tipo."""
        if len(node.children) == 1:
            return self.visit(node.children[0])
        elif len(node.children) == 3:
            left_type = self.visit(node.children[0])
            operator = node.children[1]
            right_type = self.visit(node.children[2])
            return self.check_binary_operation(left_type, operator, right_type, node)
        return None
    
    def visit_Termino(self, node):
        """Visita un término y retorna su tipo."""
        if len(node.children) == 1:
            child = node.children[0]
            
            if child.state == Node.TERMINAL:
                if child.name == 'entero' or child.name == 'Entero':
                    return 'int'
                elif child.name == 'real' or child.name == 'Real':
                    return 'float'
                elif child.name == 'identificador' or child.name == 'Identificador':
                    var_name = child.token.lexema
                    var_symbol = self.symbol_table.lookup(var_name)
                    if not var_symbol:
                        self.error(f"Variable '{var_name}' no declarada", node)
                        return None
                    
                    if var_symbol.symbol_type not in ['variable', 'parameter']:
                        self.error(f"'{var_name}' no es una variable", node)
                        return None
                    
                    if not var_symbol.initialized:
                        self.warning(f"Variable '{var_name}' usada antes de ser inicializada", node)
                    
                    return var_symbol.data_type
            elif isinstance(child, Node):
                return self.visit(child)
        
        return None
    
    def visit_LlamadaFunc(self, node):
        """Visita una llamada a función y retorna su tipo."""
        if len(node.children) < 3:
            return None
        
        func_name_node = node.children[0]
        
        if func_name_node.state != Node.TERMINAL:
            return None
        
        func_name = func_name_node.token.lexema
        func_symbol = self.symbol_table.lookup(func_name, mark_used=True)
        
        if not func_symbol:
            self.error(f"Función '{func_name}' no declarada", node)
            return None
        
        if func_symbol.symbol_type != 'function':
            self.error(f"'{func_name}' no es una función", node)
            return None
        
        # Validar tipos de argumentos
        # Estructura esperada: LlamadaFunc -> identificador ( Argumentos )
        if len(node.children) >= 4:
            argumentos_node = node.children[2]  # Nodo Argumentos
            if argumentos_node and argumentos_node.name == 'Argumentos':
                arg_types = self.extract_argument_types(argumentos_node)
                expected_param_types = [param_type for _, param_type in func_symbol.params]
                
                # Verificar número de argumentos
                if len(arg_types) != len(expected_param_types):
                    self.error(f"Función '{func_name}' espera {len(expected_param_types)} argumentos, pero se pasaron {len(arg_types)}", node)
                    return func_symbol.return_type
                
                # Verificar tipos de argumentos
                for i, (arg_type, expected_type) in enumerate(zip(arg_types, expected_param_types)):
                    if arg_type and expected_type and arg_type != expected_type:
                        # Verificar conversiones implícitas válidas
                        if not self.is_compatible_type(arg_type, expected_type):
                            self.error(f"Función '{func_name}': argumento {i+1} es de tipo '{arg_type}' pero se esperaba '{expected_type}'", node)
        
        return func_symbol.return_type
    
    def extract_argument_types(self, argumentos_node):
        """Extrae los tipos de los argumentos de una llamada a función."""
        arg_types = []
        
        if not argumentos_node or len(argumentos_node.children) == 0:
            return arg_types
        
        # Estructura: Argumentos -> Expresion ListaArgumentos
        if len(argumentos_node.children) >= 1:
            # Primer argumento
            first_expr = argumentos_node.children[0]
            first_type = self.visit_Expresion(first_expr)
            if first_type:
                arg_types.append(first_type)
            
            # Argumentos adicionales en ListaArgumentos
            if len(argumentos_node.children) >= 2:
                lista_args = argumentos_node.children[1]
                arg_types.extend(self.extract_lista_argumentos_types(lista_args))
        
        return arg_types
    
    def extract_lista_argumentos_types(self, lista_node):
        """Extrae tipos de ListaArgumentos recursivamente."""
        arg_types = []
        
        if not lista_node or len(lista_node.children) == 0:
            return arg_types
        
        # Estructura: ListaArgumentos -> , Expresion ListaArgumentos
        if len(lista_node.children) >= 2:
            # Segundo argumento (después de la coma)
            expr_node = lista_node.children[1]
            expr_type = self.visit_Expresion(expr_node)
            if expr_type:
                arg_types.append(expr_type)
            
            # Continuar con el resto de argumentos
            if len(lista_node.children) >= 3:
                remaining_args = lista_node.children[2]
                arg_types.extend(self.extract_lista_argumentos_types(remaining_args))
        
        return arg_types
    
    def is_compatible_type(self, from_type, to_type):
        """Verifica si los tipos son compatibles (conversiones implícitas válidas)."""
        # En un lenguaje estricto, no permitimos conversiones implícitas de float a int
        # Solo permitimos int a float si se desea
        if from_type == to_type:
            return True
        
        # Comentado: permitir int a float (si se desea flexibilidad)
        # if from_type == 'int' and to_type == 'float':
        #     return True
        
        # No permitir otras conversiones automáticas
        return False
    
    def extract_parameters(self, params_node):
        """Extrae los parámetros de un nodo Parametros."""
        params = []
        if params_node and len(params_node.children) > 0:
            params.extend(self.extract_param_list(params_node))
        return params
    
    def extract_param_list(self, node):
        """Extrae parámetros de forma recursiva."""
        params = []
        
        if node.name == 'Parametros' and len(node.children) >= 2:
            type_node = node.children[0]
            name_node = node.children[1]
            
            if type_node.state == Node.TERMINAL and name_node.state == Node.TERMINAL:
                param_type = type_node.token.lexema
                param_name = name_node.token.lexema
                params.append((param_name, param_type))
            
            if len(node.children) > 2:
                list_param_node = node.children[2]
                params.extend(self.extract_list_param(list_param_node))
        
        return params
    
    def extract_list_param(self, node):
        """Extrae parámetros de ListaParam recursivamente."""
        params = []
        
        if node.name == 'ListaParam' and len(node.children) >= 3:
            type_node = node.children[1]
            name_node = node.children[2]
            
            if type_node.state == Node.TERMINAL and name_node.state == Node.TERMINAL:
                param_type = type_node.token.lexema
                param_name = name_node.token.lexema
                params.append((param_name, param_type))
            
            if len(node.children) > 3:
                next_list_param = node.children[3]
                params.extend(self.extract_list_param(next_list_param))
        
        return params
    
    def check_binary_operation(self, left_type, operator_node, right_type, node):
        """Verifica una operación binaria y retorna el tipo resultado."""
        if not left_type or not right_type:
            return None
        
        if operator_node.state != Node.TERMINAL:
            return None
        
        op = operator_node.token.lexema
        
        if op in ['+', '-', '*', '/']:
            if left_type in ['int', 'float'] and right_type in ['int', 'float']:
                if left_type == 'float' or right_type == 'float':
                    return 'float'
                return 'int'
            else:
                self.error(f"Operación aritmética '{op}' no válida entre '{left_type}' y '{right_type}'", node)
                return None
        elif op in ['<', '>', '<=', '>=', '==', '!=']:
            if left_type in ['int', 'float'] and right_type in ['int', 'float']:
                return 'int'
            else:
                self.error(f"Comparación '{op}' no válida entre '{left_type}' y '{right_type}'", node)
                return None
        elif op in ['&&', '||']:
            return 'int'
        
        return None
    
    def are_types_compatible(self, expected, actual):
        """Verifica si dos tipos son compatibles para asignación."""
        if expected == actual:
            return True
        if expected == 'float' and actual == 'int':
            return True
        return False
    
    def final_checks(self):
        """Verificaciones finales después del análisis."""
        all_symbols = self.symbol_table.get_all_symbols()
        for scope_name, symbol in all_symbols:
            if symbol.symbol_type == 'function' and not symbol.used and symbol.name != 'main':
                self.warning(f"Función '{symbol.name}' declarada pero no usada")
    
    def print_symbol_table(self):
        """Imprime la tabla de símbolos para debugging."""
        print("\\n========== TABLA DE SÍMBOLOS ==========\\n")
        all_symbols = self.symbol_table.get_all_symbols()
        current_scope = None
        
        for scope_name, symbol in all_symbols:
            if scope_name != current_scope:
                print(f"Scope: {scope_name}")
                current_scope = scope_name
            
            used_str = " [USED]" if symbol.used else ""
            print(f"  {symbol}{used_str}")
        
        print("\\n" + "="*40)
    
    def print_results(self):
        """Imprime los resultados del análisis semántico."""
        print("\\n========== RESULTADOS ANÁLISIS SEMÁNTICO ==========\\n")
        
        if not self.errors and not self.warnings:
            print("Análisis semántico completado sin errores ni advertencias")
        else:
            if self.errors:
                print(f"ERRORES ENCONTRADOS ({len(self.errors)}):")
                for i, error in enumerate(self.errors, 1):
                    print(f"  {i}. {error}")
                print()
            
            if self.warnings:
                print(f"ADVERTENCIAS ({len(self.warnings)}):")
                for i, (warning, node) in enumerate(self.warnings, 1):
                    print(f"  {i}. {warning}")
                print()
        
        print(f"ESTADÍSTICAS:")
        all_symbols = self.symbol_table.get_all_symbols()
        functions = [s for _, s in all_symbols if s.symbol_type == 'function']
        variables = [s for _, s in all_symbols if s.symbol_type in ['variable', 'parameter']]
        
        print(f"  - Funciones declaradas: {len(functions)}")
        print(f"  - Variables declaradas: {len(variables)}")
        print(f"  - Errores semánticos: {len(self.errors)}")
        print(f"  - Advertencias: {len(self.warnings)}")
        
        print("\\n" + "="*50)
    
    def has_errors(self):
        return len(self.errors) > 0
    
    def get_errors(self):
        return self.errors
    
    def get_warnings(self):
        return [w[0] for w in self.warnings]