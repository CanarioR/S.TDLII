"""
Analizador Sintáctico (Parser)
==============================
Módulo que contiene el parser LR y la representación del AST.
"""

from lexer import Token, LexicalError


class Node:
    """Nodo del Árbol de Sintaxis Abstracta (AST)"""
    
    TERMINAL = 1
    NO_TERMINAL = 2
    
    def __init__(self, name, state, token=None):
        self.name = name
        self.state = state
        self.token = token
        self.children = []
    
    def add_child(self, child):
        """Agrega un hijo al nodo"""
        if child is not None:
            self.children.append(child)
    
    def __str__(self):
        return f"Node({self.name}, {self.state})"
    
    def __repr__(self):
        return self.__str__()


class Parser:
    """Parser LR para el analizador sintáctico"""
    
    def __init__(self, grammar_data):
        """
        Inicializa el parser con los datos de la gramática LR.
        
        Args:
            grammar_data (dict): Datos de la gramática LR cargada
        """
        self.grammar = grammar_data
        self.tabla_lr = grammar_data['tabla_lr']
        self.token_a_columna = grammar_data['token_a_columna']
        self.nonterminal_a_columna = grammar_data['nonterminal_a_columna']
        self.idRegla = grammar_data['idRegla']
        self.lonRegla = grammar_data['lonRegla']
        self.nombreRegla = grammar_data['nombreRegla']
        self.num_terminales = grammar_data['num_terminales']
        
        # Pila para el parsing
        self.pila_estados = [0]
        self.pila_nodos = []
        
        # Variables de estado
        self.errores = []
        self.raiz_ast = None
        
    def parse(self, tokens):
        """
        Realiza el análisis sintáctico usando el algoritmo LR.
        
        Args:
            tokens (list): Lista de tokens del analizador léxico
            
        Returns:
            Node: Nodo raíz del AST si el parsing es exitoso, None en caso contrario
        """
        print("\n=== INICIO DEL PARSING LR ===")
        
        # Reiniciar estado
        self.errores = []
        self.pila_estados = [0]
        self.pila_nodos = []
        
        # Mapeo de equivalencias como en el original
        equivalencias = {
            'Identificador': 'identificador',
            'Entero': 'entero',
            'Real': 'real',
            'Cadena': 'cadena',
            'Tipo': 'tipo',
            'OpSuma': 'opSuma',
            'OpMul': 'opMul',
            'OpRelac': 'opRelac',
            'OpOr': 'opOr',
            'OpAnd': 'opAnd',
            'OpNot': 'opNot',
            'OpIgualdad': 'opIgualdad',
            'PuntoYComa': ';',
            'Coma': ',',
            'ParentesisIzq': '(',
            'ParentesisDer': ')',
            'LlaveIzq': '{',
            'LlaveDer': '}',
            'OpAsignacion': '=',
            'If': 'if',
            'While': 'while',
            'Return': 'return',
            'Else': 'else',
            'Fin': '$',
        }
        
        # Agregar token especial de fin de archivo
        tokens_con_eof = tokens + [Token("$", "$", len(tokens) + 1)]
        
        i = 0  # Índice del token actual
        
        while i < len(tokens_con_eof):
            token_actual = tokens_con_eof[i]
            estado_actual = self.pila_estados[-1]
            
            print(f"\nPaso {i + 1}:")
            print(f"  Token actual: {token_actual.tipo} ('{token_actual.lexema}')")
            print(f"  Estado actual: {estado_actual}")
            print(f"  Pila estados: {self.pila_estados}")
            
            # Obtener columna del token en la tabla LR usando equivalencias
            nombre_token = equivalencias.get(token_actual.tipo, token_actual.tipo)
            columna = self.token_a_columna.get(nombre_token)
            if columna is None:
                self._registrar_error(f"Token '{token_actual.tipo}' no tiene columna asignada en la tabla LR (buscado como '{nombre_token}')")
                return None
            
            # Obtener acción de la tabla LR
            try:
                accion = self.tabla_lr[estado_actual][columna]
                print(f"  Acción LR[{estado_actual}][{columna}]: {accion}")
            except IndexError:
                self._registrar_error(f"Estado o columna fuera de rango: estado={estado_actual}, columna={columna}")
                return None
            
            if accion > 0:  # SHIFT
                self._shift(accion, token_actual)
                i += 1  # Avanzar al siguiente token solo en SHIFT
                
            elif accion < 0:  # REDUCE
                # Lógica de candidatos múltiples como en el original
                candidatos = []
                for offset in (1, 2):
                    idx_cand = -accion - offset
                    if 0 <= idx_cand < len(self.lonRegla):
                        lon_cand = self.lonRegla[idx_cand]
                        nt_cand = self.nombreRegla[idx_cand]
                        
                        # Simular pop para verificar si el candidato es válido
                        temp_states = self.pila_estados.copy()
                        for _ in range(lon_cand):
                            if temp_states:
                                temp_states.pop()
                        if not temp_states:
                            continue
                            
                        estado_goto_cand = temp_states[-1]
                        col_goto_cand = self.nonterminal_a_columna.get(nt_cand)
                        if col_goto_cand is None:
                            continue
                        
                        try:
                            goto_cand = self.tabla_lr[estado_goto_cand][col_goto_cand]
                            if goto_cand >= 0:  # Solo considerar GOTOs válidos
                                accion_despues = self.tabla_lr[goto_cand][columna] if goto_cand < len(self.tabla_lr) else None
                                candidatos.append((idx_cand, lon_cand, estado_goto_cand, goto_cand, accion_despues, offset))
                        except Exception:
                            continue

                print(f"[LR][REDUCE] Candidatos válidos: {candidatos}")

                # Seleccionar el mejor candidato basándose en la gramática
                elegido = None
                
                if candidatos:
                    # Filtrar candidatos con GOTO válido (no 0)
                    candidatos_validos = [c for c in candidatos if c[3] != 0]
                    
                    if candidatos_validos:
                        # Preferir reglas más largas entre los válidos
                        elegido = max(candidatos_validos, key=lambda x: (x[1], -x[0]))
                    else:
                        # Si no hay válidos, tomar el primero
                        elegido = candidatos[0]

                if elegido is None:
                    # Fallback: usar el cálculo directo
                    num_regla = max(0, min(-accion - 1, len(self.lonRegla) - 1))
                    lon = self.lonRegla[num_regla]
                else:
                    num_regla, lon, estado_goto_sim, goto_sim, accion_despues, used_offset = elegido

                print(f"[LR][REDUCE] Regla elegida: R{num_regla+1} - {self.nombreRegla[num_regla]} con longitud {lon}")

                if not self._reduce_original(num_regla, lon):
                    return None
                
                # Si fue aceptación (regla 0), ya tenemos el AST
                if num_regla == 0:
                    return self.raiz_ast
                # No incrementar i - el mismo token se procesa con el nuevo estado
                    
            elif accion == 0:  # ERROR
                self._registrar_error(f"Error sintáctico en token '{token_actual.lexema}' (línea {token_actual.linea})")
                return None
                
            else:  # ACCEPT (debería ser una condición especial)
                print("  ACEPTADO!")
                break
        
        # Verificar si el parsing fue exitoso
        if len(self.pila_nodos) == 1:
            self.raiz_ast = self.pila_nodos[0]
            print(f"\nParsing exitoso. AST creado con raíz: {self.raiz_ast.name}")
            return self.raiz_ast
        else:
            self._registrar_error("Error: La pila no contiene exactamente un nodo al final del parsing")
            return None
    
    def _obtener_columna_token(self, tipo_token):
        """Obtiene la columna de un token en la tabla LR"""
        if tipo_token in self.token_a_columna:
            return self.token_a_columna[tipo_token]
        return -1
    
    def _obtener_columna_nonterminal(self, nombre_nt):
        """Obtiene la columna de un no terminal en la tabla LR"""
        if nombre_nt in self.nonterminal_a_columna:
            return self.nonterminal_a_columna[nombre_nt]
        return -1
    
    def _shift(self, nuevo_estado, token):
        """Realiza una operación SHIFT"""
        print(f"    SHIFT: Estado {nuevo_estado}")
        
        # Crear nodo terminal
        nodo_terminal = Node(token.tipo, Node.TERMINAL, token)
        
        # Agregar a las pilas
        self.pila_estados.append(nuevo_estado)
        self.pila_nodos.append(nodo_terminal)
    
    def _reduce_original(self, num_regla, lon):
        """Realiza una operación REDUCE usando la lógica original"""
        print(f"    REDUCE: Regla {num_regla} ({self.nombreRegla[num_regla]}) - Longitud {lon}")
        
        hijos = []
        for _ in range(lon):
            if self.pila_estados:
                self.pila_estados.pop()
            if self.pila_nodos:
                hijos.insert(0, self.pila_nodos.pop())

        # Si la regla elegida es la regla 0 se interpreta como aceptación
        if num_regla == 0:
            print("[LR] R1: programa -> Definiciones (Regla de aceptación)")
            nt = self.nombreRegla[num_regla]
            nodo_final = Node(nt, Node.NO_TERMINAL)
            for hijo in hijos:
                nodo_final.add_child(hijo)
            print(f"[LR] AST raíz creado: {nodo_final.name} con {len(hijos)} hijos")
            self.raiz_ast = nodo_final
            return True  # Indicar que la parsing ha terminado exitosamente

        nt = self.nombreRegla[num_regla]
        nodo = Node(nt, Node.NO_TERMINAL)
        for hijo in hijos:
            nodo.add_child(hijo)
        
        print(f"[LR] Nodo creado: {nt} con {len(hijos)} hijos")
        if hijos:
            for i, hijo in enumerate(hijos):
                print(f"  hijo[{i}]: {hijo.name}")
        
        # R8: ListaVar ::= , identificador ListaVar - el orden correcto es Coma, Identificador, ListaVar
        if num_regla == 7 and len(hijos) == 3:  # R8 
            # Reordenar: debe ser Coma, Identificador, ListaVar
            nodo = Node(nt, Node.NO_TERMINAL)
            nodo.add_child(hijos[1])  # Coma
            nodo.add_child(hijos[0])  # Identificador
            nodo.add_child(hijos[2])  # ListaVar
            print(f"[LR] Nodo R8 reordenado: {nt} - Coma, Identificador, ListaVar")
        
        # Para producciones recursivas como "Definiciones -> Definicion Definiciones"
        elif (len(hijos) >= 2 and hijos[1].name == nt and 
              nt in ['Definiciones', 'DefLocales', 'Sentencias', 'ListaVar', 'ListaParam']):
            # Combinar: tomar hijos del segundo nodo y agregar el primero
            nodo = Node(nt, Node.NO_TERMINAL)
            nodo.add_child(hijos[0])
            for hijo in hijos[1].children:
                nodo.add_child(hijo)
            print(f"[LR] Nodo recursivo combinado: {nt} ahora tiene {len(nodo.children)} hijos")
        
        if not self.pila_estados:
            self._registrar_error("Error: Pila de estados vacía durante GOTO")
            return False
        
        estado_goto = self.pila_estados[-1]
        col_goto = self.nonterminal_a_columna.get(nt)
        if col_goto is None:
            self._registrar_error(f"No terminal '{nt}' no tiene columna GOTO asignada en la tabla LR")
            return False
        
        goto = self.tabla_lr[estado_goto][col_goto]
        print(f"[LR] GOTO: Estado: {estado_goto}, NoTerminal: {nt}, Columna: {col_goto}, Goto: {goto}")
        
        if goto == 0:
            print(f"[LR] ERROR: GOTO devuelve 0 - revisar tabla LR")
            print(f"[LR] Estado actual: {estado_goto}, No terminal: {nt}")
            return False
            
        self.pila_estados.append(goto)
        self.pila_nodos.append(nodo)
        return True

    def _reduce(self, regla_idx):
        """Realiza una operación REDUCE"""
        if regla_idx >= len(self.idRegla):
            self._registrar_error(f"Índice de regla fuera de rango: {regla_idx}")
            return False
        
        longitud = self.lonRegla[regla_idx]
        nombre_produccion = self.nombreRegla[regla_idx]
        
        print(f"    REDUCE: Regla {regla_idx} ({nombre_produccion}) - Longitud {longitud}")
        
        # Verificar que tenemos suficientes elementos en las pilas para producciones no-epsilon
        if longitud > 0 and (longitud > len(self.pila_estados) or longitud > len(self.pila_nodos)):
            self._registrar_error(f"Error: No hay suficientes elementos en la pila para REDUCE (necesita {longitud})")
            return False
        
        # Crear nodo no terminal
        nodo_nt = Node(nombre_produccion, Node.NO_TERMINAL)
        
        # Sacar elementos de las pilas y agregarlos como hijos
        hijos = []
        for _ in range(longitud):
            if self.pila_estados:
                self.pila_estados.pop()
            if self.pila_nodos:
                hijos.append(self.pila_nodos.pop())
        
        # Los hijos están en orden inverso, voltearlos
        hijos.reverse()
        for hijo in hijos:
            nodo_nt.add_child(hijo)
        
        # Verificar si es la regla de aceptación (regla 0)
        if regla_idx == 0:
            print(f"    ACEPTACIÓN: {nombre_produccion}")
            self.pila_nodos.append(nodo_nt)
            return True
        
        # Agregar el nuevo nodo a la pila
        self.pila_nodos.append(nodo_nt)
        
        # GOTO: Encontrar el siguiente estado
        if not self.pila_estados:
            self._registrar_error("Error: Pila de estados vacía durante GOTO")
            return False
        
        estado_actual = self.pila_estados[-1]
        columna_goto = self._obtener_columna_nonterminal(nombre_produccion)
        
        print(f"    [DEBUG GOTO] Estado actual: {estado_actual}, Columna: {columna_goto}")
        
        if columna_goto == -1:
            self._registrar_error(f"No terminal no encontrado en tabla GOTO: {nombre_produccion}")
            return False
        
        try:
            nuevo_estado = self.tabla_lr[estado_actual][columna_goto]
            print(f"    [DEBUG GOTO] tabla_lr[{estado_actual}][{columna_goto}] = {nuevo_estado}")
            print(f"    GOTO: Estado {nuevo_estado}")
            
            # En algunos casos, GOTO puede ser 0 sin ser error
            # Continuamos con el parsing
            self.pila_estados.append(nuevo_estado)
            return True
            
        except IndexError:
            self._registrar_error(f"Error en GOTO: índices fuera de rango")
            return False
    
    def _registrar_error(self, mensaje):
        """Registra un error de parsing"""
        self.errores.append(mensaje)
        print(f"[ERROR] {mensaje}")
    
    def obtener_errores(self):
        """Retorna la lista de errores encontrados durante el parsing"""
        return self.errores
    
    def tiene_errores(self):
        """Verifica si hubo errores durante el parsing"""
        return len(self.errores) > 0