def cargar_gramatica_lr(ruta):
    """Lee el archivo de gramática LR y retorna los vectores y la tabla LR en un diccionario."""
    import os
    import csv
    with open(ruta, 'r', encoding='utf-8') as f:
        lineas = [line.strip() for line in f if line.strip()]

    # Leer cantidad de reglas
    n_reglas = int(lineas[0])
    idRegla = []
    lonRegla = []
    nombreRegla = []
    # Leer los 3 vectores de reglas
    for i in range(1, n_reglas + 1):
        partes = lineas[i].split('\t')
        idRegla.append(int(partes[0]))
        lonRegla.append(int(partes[1]))
        nombreRegla.append(partes[2])

    # Leer dimensiones de la tabla LR
    idx_dim = n_reglas + 1
    filas, columnas = map(int, lineas[idx_dim].split('\t'))

    # Leer la tabla LR
    tabla_lr = []
    for i in range(idx_dim + 1, idx_dim + 1 + filas):
        fila = list(map(int, lineas[i].split('\t')))
        tabla_lr.append(fila)

    # Leer nombres de columna directamente del archivo CSV asociado
    columnas_csv = []
    csv_path = os.path.splitext(ruta)[0] + '.csv'
    if os.path.exists(csv_path):
        with open(csv_path, encoding='utf-8') as fcsv:
            reader = csv.reader(fcsv)
            columnas_csv = next(reader)[1:]
    else:
        columnas_csv = [str(i) for i in range(columnas)]

    # Mapeo de nombre de columna a índice
    token_a_columna = {nombre: idx for idx, nombre in enumerate(columnas_csv)}
    # Separar terminales y no terminales 
    num_term = 0
    for i, nombre in enumerate(columnas_csv):
        if nombre == 'programa':
            num_term = i
            break
    nonterminal_a_columna = {nombre: idx for idx, nombre in enumerate(columnas_csv[num_term:], start=num_term)}

    print("[DEBUG] Mapeo de columnas de terminales:")
    for t, col in list(token_a_columna.items())[:num_term]:
        print(f"  {t}: columna {col}")
    print("[DEBUG] Mapeo de columnas de no terminales (GOTO):")
    for nt, col in nonterminal_a_columna.items():
        print(f"  {nt}: columna {col}")
    print(f"[DEBUG] Número de terminales: {num_term}")
    print(f"[DEBUG] Número de no terminales: {len(columnas_csv) - num_term}")
    print(f"[DEBUG] Total columnas en tabla LR: {columnas}")

    return {
        'idRegla': idRegla,
        'lonRegla': lonRegla,
        'nombreRegla': nombreRegla,
        'filas': filas,
        'columnas': columnas,
        'tabla_lr': tabla_lr,
        'nonterminal_a_columna': nonterminal_a_columna,
        'token_a_columna': token_a_columna,
        'columnas_csv': columnas_csv,
        'num_term': num_term
    }

# Operadores y símbolos
SIMBOLOS = {
    "+": ("OpSuma", 5), "-": ("OpSuma", 5),
    "*": ("OpMul", 6), "/": ("OpMul", 6),
    "=": ("OpAsignacion", 18),
    "<": ("OpRelac", 7), ">": ("OpRelac", 7),
    "<=": ("OpRelac", 7), ">=": ("OpRelac", 7),
    "!=": ("OpIgualdad", 11), "==": ("OpIgualdad", 11),
    "&&": ("OpAnd", 9), "||": ("OpOr", 8),
    "!": ("OpNot", 10),
    ";": ("PuntoYComa", 12), ",": ("Coma", 13),
    "(": ("ParentesisIzq", 14), ")": ("ParentesisDer", 15),
    "{": ("LlaveIzq", 16), "}": ("LlaveDer", 17),
    "$": ("Fin", 23),
}

# Palabras reservadas (nombre, tipo)
PALABRAS_RESERVADAS = {
    'int': ('Tipo', 3),
    'float': ('Tipo', 3),
    'if': ('If', 19),
    'else': ('Else', 21),
    'while': ('While', 20),
    'return': ('Return', 22),
}


class Token:
    def __init__(self, nombre, tipo, lexema, pos):
        self.nombre = nombre
        self.tipo = tipo
        self.lexema = lexema
        self.pos = pos


class LexicalError(Exception):
    """Excepción para errores léxicos con información de posición (línea, columna)."""
    def __init__(self, message, pos=None, line=None, column=None):
        super().__init__(message)
        self.pos = pos
        self.line = line
        self.column = column


def obtener_line_col(texto, pos):
    """Devuelve (line, column) 1-based para la posición absoluta pos en texto."""
    if pos is None:
        return (None, None)
    line = texto.count('\n', 0, pos) + 1
    last_n = texto.rfind('\n', 0, pos)
    col = pos - last_n
    return (line, col)

def es_letra(c): return c.isalpha()
def es_digito(c): return c.isdigit()
def es_espacio(c): return c in " \t\r\n"

def analizar(texto):
    tokens = []
    i, n = 0, len(texto)

    # Normalizar Unicode para convertir variantes (p.ej. paréntesis/llaves fullwidth) a formas canónicas
    try:
        import unicodedata
        texto = unicodedata.normalize('NFKC', texto)
    except Exception:
        pass

    while i < n:
        if es_espacio(texto[i]):
            i += 1
            continue

        inicio = i
        c = texto[i]

        # Aceptar explícitamente el marcador de fin '$' si aparece en la entrada
        if c == '$':
            tokens.append(Token('Fin', 23, '$', inicio))
            i += 1
            continue

        if es_letra(c):
            while i < n and (es_letra(texto[i]) or es_digito(texto[i])):
                i += 1
            lexema = texto[inicio:i]
            if lexema in PALABRAS_RESERVADAS:
                nombre, tipo = PALABRAS_RESERVADAS[lexema]
            else:
                nombre, tipo = "Identificador", 0
            tokens.append(Token(nombre, tipo, lexema, inicio))
            continue

        if es_digito(c):
            # consumir la parte entera
            while i < n and es_digito(texto[i]):
                i += 1
            # si hay un punto y a continuación dígitos, es real
            if i < n and texto[i] == '.':
                i += 1
                if i >= n or not es_digito(texto[i]):
                    line, col = obtener_line_col(texto, inicio)
                    snippet = texto[inicio:inicio+10].split('\n')[0]
                    raise LexicalError(f"Real mal formado en posición {inicio} (línea {line}, columna {col}): '{snippet}...'", pos=inicio, line=line, column=col)
                # consumir la fracción
                while i < n and es_digito(texto[i]):
                    i += 1
                lexema = texto[inicio:i]
                tokens.append(Token("Real", 2, lexema, inicio))
            else:
                lexema = texto[inicio:i]
                tokens.append(Token("Entero", 1, lexema, inicio))
            continue

        if i+1 < n:
            doble = texto[i:i+2]
            if doble in SIMBOLOS:
                nombre, tipo = SIMBOLOS[doble]
                tokens.append(Token(nombre, tipo, doble, inicio))
                i += 2
                continue

        if c in SIMBOLOS:
            nombre, tipo = SIMBOLOS[c]
            tokens.append(Token(nombre, tipo, c, inicio))
            i += 1
            continue
        # Si no correspondió a nada, es un carácter no reconocido
        line, col = obtener_line_col(texto, inicio)
        fragment = texto[inicio:inicio+40].split('\n')[0]
        cp = ord(c)
        raise LexicalError(f"Carácter no reconocido '{c}' (U+{cp:04X}) en posición {inicio} (línea {line}, columna {col}): '{fragment}...'", pos=inicio, line=line, column=col)

    return tokens


TERMINAL = "TERMINAL"
NO_TERMINAL = "NO_TERMINAL"
ESTADO = "ESTADO"

class Node:
    def __init__(self, name, state=NO_TERMINAL, token=None, children=None):
        self.name = name
        self.state = state
        self.token = token
        self.children = children or []
    def __repr__(self, level=0):
        pad = "  " * level
        if self.state == TERMINAL:
            return f"{pad}{self.state}: {self.name}({self.token.lexema})"
        
        # Para no terminales, mostrar el nombre y el número de hijos
        s = f"{pad}{self.state}: {self.name}"
        if self.children:
            s += f" [{len(self.children)} hijos]"
        
        for c in self.children:
            if isinstance(c, Node):
                s += "\n" + c.__repr__(level+1)
            else:
                s += f"\n{pad}  {c}"
        return s


def ast_to_dot(root):
    """Genera el contenido DOT (Graphviz) para el árbol raíz `root`."""
    import html
    lines = ["digraph AST {", "  node [shape=box, fontname=\"Arial\"];", "  rankdir=TB;"]
    counter = {"n": 0}

    def node_id():
        i = counter["n"]
        counter["n"] += 1
        return f"n{i}"

    def visit(node):
        nid = node_id()
        label = node.name
        if node.state == TERMINAL and node.token is not None:
            label = f"{label}\\n{html.escape(str(node.token.lexema))}"
        # escape double quotes
        label = label.replace('"', '\\"')
        lines.append(f'  {nid} [label="{label}"];')
        for c in node.children:
            if isinstance(c, Node):
                cid = visit(c)
                lines.append(f'  {nid} -> {cid};')
            else:
                cid = node_id()
                lab = str(c).replace('"', '\\"')
                lines.append(f'  {cid} [label="{lab}"];')
                lines.append(f'  {nid} -> {cid};')
        return nid

    visit(root)
    lines.append('}')
    return "\n".join(lines)


def save_ast_dot(root, path_dot):
    dot = ast_to_dot(root)
    with open(path_dot, 'w', encoding='utf-8') as f:
        f.write(dot)
    print(f"AST DOT guardado en: {path_dot}")


def generate_png_from_dot(path_dot, path_png):
    import shutil, subprocess
    if shutil.which('dot') is None:
        print("Graphviz 'dot' no encontrado en PATH; no se generará PNG. Puedes instalar graphviz o generar la imagen manualmente con: dot -Tpng ast.dot -o ast.png")
        return False
    try:
        subprocess.run(['dot', '-Tpng', path_dot, '-o', path_png], check=True)
        print(f"AST PNG generado en: {path_png}")
        return True
    except Exception as e:
        print("Error al generar PNG con dot:", e)
        return False

class Parser:
    def parse_lr(self):
        """
        Analizador sintáctico LR usando la tabla LR y los vectores de reglas.
        Retorna el árbol sintáctico o lanza una excepción en caso de error.
        """
        if not self.gramatica_lr:
            raise Exception("No se ha cargado la gramática LR")

        # Usa el mapeo de token a columna generado en cargar_gramatica_lr
        token_a_columna = self.gramatica_lr['token_a_columna']
        columnas_csv = self.gramatica_lr['columnas_csv']
        num_term = self.gramatica_lr['num_term']
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

        pila_estados = [0]
        pila_simbolos = []
        idx_token = 0
        tokens = self.tokens + [Token("Fin", 23, "$", -1)]

        reducciones_sin_consumir = 0

        while True:
            estado = pila_estados[-1]
            actual = tokens[idx_token]
            # Buscar columna correspondiente al token actual
            nombre_token = equivalencias.get(actual.nombre, actual.nombre)
            col = token_a_columna.get(nombre_token)
            if col is None:
                raise SyntaxError(f"Token '{actual.nombre}' no tiene columna asignada en la tabla LR (buscado como '{nombre_token}')")
            accion = self.tabla_lr[estado][col]
            # Debug print
            print(f"[LR] Estado: {estado}, Token: {actual.nombre}('{actual.lexema}') pos {actual.pos}, Columna: {col}, Acción: {accion}")

            if accion > 0:
                # Desplazamiento (shift)
                pila_estados.append(accion)
                pila_simbolos.append(Node(actual.nombre, TERMINAL, token=actual))
                idx_token += 1
                reducciones_sin_consumir = 0
            elif accion < 0:
                # Aceptar: algunas tablas codifican 'accept' como -1, otras como -(n_reglas+1)
                if accion == -1:
                    print(f"[LR] ACEPTAR (-1): pila_simbolos tiene {len(pila_simbolos)} elementos")
                    # Buscar el símbolo inicial 'programa' en la pila
                    for i, simbolo in enumerate(pila_simbolos):
                        if simbolo.name == 'programa':
                            print(f"[LR] Encontrado 'programa' en posición {i}: {simbolo}")
                            return simbolo
                    # Si no encontramos 'programa', retornar el último elemento
                    if pila_simbolos:
                        print(f"[LR] Retornando último símbolo: {pila_simbolos[-1].name}")
                        return pila_simbolos[-1]
                    else:
                        print("[LR] ADVERTENCIA: pila_simbolos vacía en aceptación")
                        return None

                # Intentar mapear reducción a índice de regla
                candidatos = []
                for offset in (1, 2):
                    idx_cand = -accion - offset
                    if 0 <= idx_cand < len(self.lonRegla):
                        lon_cand = self.lonRegla[idx_cand]
                        nt_cand = self.nombreRegla[idx_cand]
                        
                        # Simular pop para verificar si el candidato es válido
                        temp_states = pila_estados.copy()
                        for _ in range(lon_cand):
                            if temp_states:
                                temp_states.pop()
                        if not temp_states:
                            continue
                            
                        estado_goto_cand = temp_states[-1]
                        col_goto_cand = self.gramatica_lr['nonterminal_a_columna'].get(nt_cand)
                        if col_goto_cand is None:
                            continue
                        
                        try:
                            goto_cand = self.tabla_lr[estado_goto_cand][col_goto_cand]
                            if goto_cand >= 0:  # Solo considerar GOTOs válidos
                                accion_despues = self.tabla_lr[goto_cand][col] if goto_cand < len(self.tabla_lr) else None
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

                hijos = []
                for _ in range(lon):
                    pila_estados.pop()
                    hijos.insert(0, pila_simbolos.pop())

                # Si la regla elegida es la regla 0 se interpreta como aceptación (R1: programa -> Definiciones)
                if num_regla == 0:
                    print("[LR] R1: programa -> Definiciones (Regla de aceptación)")
                    nt = self.nombreRegla[num_regla]
                    nodo_final = Node(nt, NO_TERMINAL, children=hijos)
                    print(f"[LR] AST raíz creado: {nodo_final.name} con {len(hijos)} hijos")
                    return nodo_final

                nt = self.nombreRegla[num_regla]
                nodo = Node(nt, NO_TERMINAL, children=hijos)
                print(f"[LR] Nodo creado: {nt} con {len(hijos)} hijos")
                if hijos:
                    for i, hijo in enumerate(hijos):
                        print(f"  hijo[{i}]: {hijo.name} ({hijo.state})")
                
                # R8: ListaVar ::= , identificador ListaVar - el orden correcto es Coma, Identificador, ListaVar
                if num_regla == 7 and len(hijos) == 3:  # R8 
                    # Reordenar: debe ser Coma, Identificador, ListaVar
                    nodo = Node(nt, NO_TERMINAL, children=[hijos[1], hijos[0], hijos[2]])  # Coma, Identificador, ListaVar
                    print(f"[LR] Nodo R8 reordenado: {nt} - Coma, Identificador, ListaVar")
                
                # Para producciones recursivas como "Definiciones -> Definicion Definiciones"
                elif (len(hijos) >= 2 and hijos[1].name == nt and 
                      nt in ['Definiciones', 'DefLocales', 'Sentencias', 'ListaVar', 'ListaParam']):
                    # Combinar: tomar hijos del segundo nodo y agregar el primero
                    nodo = Node(nt, NO_TERMINAL, children=[hijos[0]] + hijos[1].children)
                    print(f"[LR] Nodo recursivo combinado: {nt} ahora tiene {len(nodo.children)} hijos")
                
                estado_goto = pila_estados[-1]
                nonterminal_a_columna = self.gramatica_lr['nonterminal_a_columna']
                col_goto = nonterminal_a_columna.get(nt)
                if col_goto is None:
                    raise SyntaxError(f"No terminal '{nt}' no tiene columna GOTO asignada en la tabla LR")
                goto = self.tabla_lr[estado_goto][col_goto]
                print(f"[LR] GOTO: Estado: {estado_goto}, NoTerminal: {nt}, Columna: {col_goto}, Goto: {goto}")
                
                if goto == 0:
                    print(f"[LR] ERROR: GOTO devuelve 0 - revisar tabla LR")
                    print(f"[LR] Estado actual: {estado_goto}, No terminal: {nt}")
                    return None
                    
                pila_estados.append(goto)
                pila_simbolos.append(nodo)

                reducciones_sin_consumir += 1
                if reducciones_sin_consumir > 200:
                    raise RuntimeError(f"Posible ciclo de reducciones sin consumir token: estado={estado}, token={actual.nombre}('{actual.lexema}') pos {actual.pos}, accion_inicial={accion}, candidatos={candidatos}")
            else:
                raise SyntaxError(f"Error de sintaxis en token {actual.nombre}('{actual.lexema}') pos {actual.pos}")
    def __init__(self, tokens, gramatica_lr=None):
        self.tokens = tokens
        self.pos = 0
        # gramática_lr debe ser un diccionario como el retornado por cargar_gramatica_lr
        self.gramatica_lr = gramatica_lr
        if gramatica_lr:
            self.idRegla = gramatica_lr['idRegla']
            self.lonRegla = gramatica_lr['lonRegla']
            self.nombreRegla = gramatica_lr['nombreRegla']
            self.tabla_lr = gramatica_lr['tabla_lr']
            self.filas = gramatica_lr['filas']
            self.columnas = gramatica_lr['columnas']
    
    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token("Fin", 23, "$", self.pos)

    def eat(self, nombre=None):
        t = self.current()
        if nombre and t.nombre != nombre:
            raise SyntaxError(f"Se esperaba {nombre} en pos {t.pos}, encontrado {t.nombre}('{t.lexema}')")
        self.pos += 1
        node = Node(t.nombre, TERMINAL, token=t)
        return node

    def parse_program(self):
        root = Node("Program", NO_TERMINAL)
        root.children.append(Node("ENTER_PROGRAM_STATE", ESTADO))
        while self.current().nombre != "Fin":
            root.children.append(self.parse_statement())
        root.children.append(self.eat("Fin"))
        return root

    def parse_statement(self):
        t = self.current()
        # declaración: Tipo Identificador ';'  o Tipo Identificador '=' expr ';'
        if t.nombre == "Tipo":
            n = Node("Declaration", NO_TERMINAL)
            n.children.append(self.eat("Tipo"))
            n.children.append(self.eat("Identificador"))
            if self.current().nombre == "OpAsignacion":
                n.children.append(self.eat("OpAsignacion"))
                n.children.append(self.parse_expression())
            n.children.append(self.eat("PuntoYComa"))
            return n
        # if
        if t.nombre == "If":
            n = Node("If", NO_TERMINAL)
            n.children.append(self.eat("If"))
            n.children.append(self.eat("ParentesisIzq"))
            n.children.append(self.parse_expression())
            n.children.append(self.eat("ParentesisDer"))
            n.children.append(self.parse_block())
            if self.current().nombre == "Else":
                n.children.append(self.eat("Else"))
                n.children.append(self.parse_block())
            return n
        # while
        if t.nombre == "While":
            n = Node("While", NO_TERMINAL)
            n.children.append(self.eat("While"))
            n.children.append(self.eat("ParentesisIzq"))
            n.children.append(self.parse_expression())
            n.children.append(self.eat("ParentesisDer"))
            n.children.append(self.parse_block())
            return n
        # return
        if t.nombre == "Return":
            n = Node("Return", NO_TERMINAL)
            n.children.append(self.eat("Return"))
            n.children.append(self.parse_expression())
            n.children.append(self.eat("PuntoYComa"))
            return n
        # bloque o asignación / llamada
        if t.nombre == "LlaveIzq":
            return self.parse_block()
        # asignación: Identificador '=' expr ';'
        if t.nombre == "Identificador":
            n = Node("Assignment", NO_TERMINAL)
            n.children.append(self.eat("Identificador"))
            if self.current().nombre == "OpAsignacion":
                n.children.append(self.eat("OpAsignacion"))
                n.children.append(self.parse_expression())
                n.children.append(self.eat("PuntoYComa"))
                return n

            n2 = Node("ExprStmt", NO_TERMINAL)
            n2.children.append(n.children[0])
            while self.current().nombre != "PuntoYComa":
                n2.children.append(self.eat(self.current().nombre))
            n2.children.append(self.eat("PuntoYComa"))
            return n2

        raise SyntaxError(f"Sentencia no reconocida empieza en token {t.nombre}('{t.lexema}') pos {t.pos}")

    def parse_block(self):
        n = Node("Block", NO_TERMINAL)
        n.children.append(self.eat("LlaveIzq"))
        while self.current().nombre != "LlaveDer":
            n.children.append(self.parse_statement())
        n.children.append(self.eat("LlaveDer"))
        return n

    # Expresiones con precedencia
    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        node = self.parse_and()
        while self.current().nombre == "OpOr":
            op = self.eat("OpOr")
            right = self.parse_and()
            node = Node("OrExpr", NO_TERMINAL, children=[node, op, right])
        return node

    def parse_and(self):
        node = self.parse_equality()
        while self.current().nombre == "OpAnd":
            op = self.eat("OpAnd")
            right = self.parse_equality()
            node = Node("AndExpr", NO_TERMINAL, children=[node, op, right])
        return node

    def parse_equality(self):
        node = self.parse_relational()
        while self.current().nombre == "OpIgualdad":
            op = self.eat("OpIgualdad")
            right = self.parse_relational()
            node = Node("EqExpr", NO_TERMINAL, children=[node, op, right])
        return node

    def parse_relational(self):
        node = self.parse_add()
        while self.current().nombre == "OpRelac":
            op = self.eat("OpRelac")
            right = self.parse_add()
            node = Node("RelExpr", NO_TERMINAL, children=[node, op, right])
        return node

    def parse_add(self):
        node = self.parse_mul()
        while self.current().nombre == "OpSuma":
            op = self.eat("OpSuma")
            right = self.parse_mul()
            node = Node("AddExpr", NO_TERMINAL, children=[node, op, right])
        return node

    def parse_mul(self):
        node = self.parse_unary()
        while self.current().nombre == "OpMul":
            op = self.eat("OpMul")
            right = self.parse_unary()
            node = Node("MulExpr", NO_TERMINAL, children=[node, op, right])
        return node

    def parse_unary(self):
        if self.current().nombre == "OpNot":
            op = self.eat("OpNot")
            operand = self.parse_unary()
            return Node("NotExpr", NO_TERMINAL, children=[op, operand])
        return self.parse_primary()

    def parse_primary(self):
        t = self.current()
        if t.nombre in ("Entero", "Real", "Identificador"):
            return self.eat(t.nombre)
        if t.nombre == "ParentesisIzq":
            self.eat("ParentesisIzq")
            e = self.parse_expression()
            self.eat("ParentesisDer")
            return e
        raise SyntaxError(f"Expresión primaria mal formada en {t.pos}: {t.nombre}")


# ============== ANALIZADOR SEMÁNTICO ==============

class SemanticError(Exception):
    """Excepción para errores semánticos."""
    def __init__(self, message, node=None, line=None, column=None):
        super().__init__(message)
        self.node = node
        self.line = line
        self.column = column


class Symbol:
    """Representa un símbolo en la tabla de símbolos."""
    def __init__(self, name, symbol_type, data_type=None, scope=None, params=None, return_type=None, initialized=False):
        self.name = name
        self.symbol_type = symbol_type  # 'variable', 'function', 'parameter'
        self.data_type = data_type      # 'int', 'float', 'void'
        self.scope = scope              # nombre del scope donde está definido
        self.params = params or []      # para funciones: lista de parámetros [(nombre, tipo), ...]
        self.return_type = return_type  # para funciones: tipo de retorno
        self.initialized = initialized  # para variables: si ha sido inicializada
        self.used = False              # si el símbolo ha sido usado
        self.defined_at = None         # referencia al nodo donde se definió
    
    def __repr__(self):
        if self.symbol_type == 'function':
            params_str = ', '.join([f"{p[0]}:{p[1]}" for p in self.params])
            return f"Function({self.name}({params_str}) -> {self.return_type})"
        else:
            init_str = " [init]" if self.initialized else " [uninit]"
            return f"{self.symbol_type.title()}({self.name}:{self.data_type}{init_str})"


class SymbolTable:
    """Tabla de símbolos con soporte para múltiples scopes."""
    def __init__(self):
        self.scopes = [{}]  # Lista de diccionarios, cada uno representa un scope
        self.scope_names = ['global']  # Nombres de los scopes
        self.current_function = None   # Función actual para validar returns
    
    def enter_scope(self, scope_name):
        """Entra a un nuevo scope."""
        self.scopes.append({})
        self.scope_names.append(scope_name)
        print(f"[SEMANTIC] Entrando a scope: {scope_name}")
    
    def exit_scope(self):
        """Sale del scope actual."""
        if len(self.scopes) > 1:
            exited_scope = self.scopes.pop()
            scope_name = self.scope_names.pop()
            print(f"[SEMANTIC] Saliendo de scope: {scope_name}")
            # Verificar símbolos no usados
            for symbol in exited_scope.values():
                if not symbol.used and symbol.symbol_type == 'variable':
                    print(f"[SEMANTIC] Advertencia: Variable '{symbol.name}' declarada pero no usada en scope '{scope_name}'")
            return exited_scope
        return {}
    
    def define(self, symbol):
        """Define un símbolo en el scope actual."""
        current_scope = self.scopes[-1]
        if symbol.name in current_scope:
            raise SemanticError(f"Símbolo '{symbol.name}' ya está definido en el scope actual '{self.scope_names[-1]}'")
        symbol.scope = self.scope_names[-1]
        current_scope[symbol.name] = symbol
        print(f"[SEMANTIC] Definido: {symbol} en scope '{symbol.scope}'")
    
    def lookup(self, name, mark_used=True):
        """Busca un símbolo en todos los scopes (del más interno al más externo)."""
        for i in range(len(self.scopes) - 1, -1, -1):
            if name in self.scopes[i]:
                symbol = self.scopes[i][name]
                if mark_used:
                    symbol.used = True
                return symbol
        return None
    
    def get_current_scope_name(self):
        return self.scope_names[-1]
    
    def is_global_scope(self):
        return len(self.scopes) == 1
    
    def get_all_symbols(self):
        """Retorna todos los símbolos de todos los scopes."""
        all_symbols = []
        for i, scope in enumerate(self.scopes):
            scope_name = self.scope_names[i]
            for symbol in scope.values():
                all_symbols.append((scope_name, symbol))
        return all_symbols


class SemanticAnalyzer:
    """Analizador semántico que recorre el AST y verifica la semántica."""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.warnings = []
        self.current_function_return_type = None
        self.has_return = False
    
    def error(self, message, node=None):
        """Registra un error semántico."""
        error = SemanticError(message, node)
        self.errors.append(error)
        print(f"[SEMANTIC ERROR] {message}")
    
    def warning(self, message, node=None):
        """Registra una advertencia semántica."""
        self.warnings.append((message, node))
        print(f"[SEMANTIC WARNING] {message}")
    
    def analyze(self, ast_root):
        """Punto de entrada principal para el análisis semántico."""
        print("\n========== ANÁLISIS SEMÁNTICO ==========\n")
        try:
            self.visit(ast_root)
            self.final_checks()
            return self.errors, self.warnings
        except Exception as e:
            self.error(f"Error interno del analizador semántico: {e}")
            return self.errors, self.warnings
    
    def visit(self, node):
        """Método de dispatch para visitar nodos según su tipo."""
        if node is None:
            return None
            
        method_name = f"visit_{node.name}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node):
        """Visita genérica que recorre todos los hijos."""
        for child in node.children:
            if isinstance(child, Node):
                self.visit(child)
    
    def visit_programa(self, node):
        """Visita el nodo raíz del programa."""
        print("[SEMANTIC] Analizando programa principal")
        
        # Primera pasada: declarar todas las funciones para permitir llamadas forward
        self.declare_functions(node)
        
        # Segunda pasada: analizar completamente
        for child in node.children:
            if isinstance(child, Node):
                self.visit(child)
        
        # Verificar que existe la función main
        main_func = self.symbol_table.lookup('main', mark_used=False)
        if not main_func or main_func.symbol_type != 'function':
            self.error("No se encontró la función 'main' requerida")
        elif main_func.return_type != 'int':
            self.error("La función 'main' debe retornar 'int'")
        elif len(main_func.params) != 0:
            self.error("La función 'main' no debe tener parámetros")
    
    def declare_functions(self, node):
        """Primera pasada: declara todas las funciones para permitir llamadas forward."""
        for child in node.children:
            if isinstance(child, Node) and child.name == 'Definiciones':
                self.declare_functions_in_definitions(child)
    
    def declare_functions_in_definitions(self, node):
        """Recorre las definiciones y declara las funciones."""
        for child in node.children:
            if isinstance(child, Node):
                if child.name == 'Definicion':
                    self.declare_functions_in_definition(child)
                elif child.name == 'Definiciones':
                    self.declare_functions_in_definitions(child)
    
    def declare_functions_in_definition(self, node):
        """Declara una función si encuentra DefFunc."""
        for child in node.children:
            if isinstance(child, Node) and child.name == 'DefFunc':
                self.declare_function(child)
    
    def declare_function(self, node):
        """Declara una función en la tabla de símbolos."""
        if len(node.children) < 6:
            return
        
        return_type_node = node.children[0]  # Tipo
        name_node = node.children[1]         # Identificador
        params_node = node.children[3]       # Parametros
        
        if (return_type_node.state != TERMINAL or name_node.state != TERMINAL):
            return
        
        func_name = name_node.token.lexema
        return_type = return_type_node.token.lexema
        
        # Extraer parámetros
        params = self.extract_parameters(params_node)
        
        # Crear símbolo de función
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
    
    def visit_Definiciones(self, node):
        """Visita las definiciones del programa."""
        for child in node.children:
            if isinstance(child, Node):
                self.visit(child)
    
    def visit_Definicion(self, node):
        """Visita una definición (variable o función)."""
        for child in node.children:
            if isinstance(child, Node):
                self.visit(child)
    
    def visit_DefVar(self, node):
        """Visita una definición de variable."""
        if len(node.children) < 4:
            return
        
        type_node = node.children[0]      # Tipo
        name_node = node.children[1]      # Identificador
        
        if type_node.state != TERMINAL or name_node.state != TERMINAL:
            return
        
        var_type = type_node.token.lexema
        var_name = name_node.token.lexema
        
        # Verificar tipo válido
        if var_type not in ['int', 'float']:
            self.error(f"Tipo de dato '{var_type}' no reconocido", node)
            return
        
        # Crear símbolo de variable
        var_symbol = Symbol(
            name=var_name,
            symbol_type='variable',
            data_type=var_type,
            initialized=False  # Las declaraciones no inicializan automáticamente
        )
        var_symbol.defined_at = node
        
        try:
            self.symbol_table.define(var_symbol)
        except SemanticError as e:
            self.error(str(e), node)
    
    def visit_DefFunc(self, node):
        """Visita una definición de función."""
        if len(node.children) < 6:
            return
        
        return_type_node = node.children[0]  # Tipo
        name_node = node.children[1]         # Identificador
        params_node = node.children[3]       # Parametros
        body_node = node.children[5]         # BloqFunc
        
        if (return_type_node.state != TERMINAL or name_node.state != TERMINAL):
            return
        
        func_name = name_node.token.lexema
        return_type = return_type_node.token.lexema
        
        # La función ya debería estar declarada, solo la marcamos como usada
        func_symbol = self.symbol_table.lookup(func_name, mark_used=False)
        if not func_symbol:
            self.error(f"Función '{func_name}' no declarada correctamente", node)
            return
        
        # Entrar al scope de la función
        self.symbol_table.enter_scope(f"function_{func_name}")
        self.symbol_table.current_function = func_symbol
        self.current_function_return_type = return_type
        self.has_return = False
        
        # Agregar parámetros al scope de la función
        params = self.extract_parameters(params_node)
        for param_name, param_type in params:
            param_symbol = Symbol(
                name=param_name,
                symbol_type='parameter',
                data_type=param_type,
                initialized=True  # Los parámetros vienen inicializados
            )
            try:
                self.symbol_table.define(param_symbol)
            except SemanticError as e:
                self.error(str(e), node)
        
        # Analizar el cuerpo de la función
        self.visit(body_node)
        
        # Verificar que funciones no-void tengan return
        if return_type != 'void' and not self.has_return:
            self.warning(f"Función '{func_name}' con tipo de retorno '{return_type}' no tiene declaración return", node)
        
        # Salir del scope de la función
        self.symbol_table.exit_scope()
        self.symbol_table.current_function = None
        self.current_function_return_type = None
        self.has_return = False
    
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
            # Parametros -> Tipo Identificador ListaParam
            type_node = node.children[0]
            name_node = node.children[1]
            
            if type_node.state == TERMINAL and name_node.state == TERMINAL:
                param_type = type_node.token.lexema
                param_name = name_node.token.lexema
                params.append((param_name, param_type))
            
            # Procesar ListaParam si existe
            if len(node.children) > 2:
                list_param_node = node.children[2]
                params.extend(self.extract_list_param(list_param_node))
        
        return params
    
    def extract_list_param(self, node):
        """Extrae parámetros de ListaParam recursivamente."""
        params = []
        
        if node.name == 'ListaParam' and len(node.children) >= 3:
            # ListaParam -> Coma Tipo Identificador ListaParam
            type_node = node.children[1]
            name_node = node.children[2]
            
            if type_node.state == TERMINAL and name_node.state == TERMINAL:
                param_type = type_node.token.lexema
                param_name = name_node.token.lexema
                params.append((param_name, param_type))
            
            # Procesar el siguiente ListaParam
            if len(node.children) > 3:
                next_list_param = node.children[3]
                params.extend(self.extract_list_param(next_list_param))
        
        return params
    
    def visit_BloqFunc(self, node):
        """Visita el bloque de una función."""
        # BloqFunc -> { DefLocales }
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
        # DefLocal puede contener DefVar (declaración) o Sentencia
        # Procesar todos los hijos normalmente
        for child in node.children:
            if isinstance(child, Node):
                self.visit(child)
    
    def visit_Sentencia(self, node):
        """Visita una sentencia."""
        if len(node.children) == 0:
            return
        
        # Primero, visitar todos los hijos DefLocal que podrían contener sentencias anidadas
        for child in node.children:
            if isinstance(child, Node) and child.name == 'DefLocal':
                self.visit(child)
        
        # Identificar tipo de sentencia analizando la estructura
        has_return = False
        has_assignment = False
        
        # Buscar patrones en los hijos directos (no recursivo)
        for child in node.children:
            if child.state == TERMINAL:
                if child.name == 'Return':
                    has_return = True
                elif child.name == 'OpAsignacion':
                    has_assignment = True
        
        if has_return:
            self.visit_return_statement(node)
        elif has_assignment:
            # Sentencia de asignación directa
            self.visit_assignment_statement(node)
        else:
            # Visitar otros hijos que no sean DefLocal (ya visitados)
            for child in node.children:
                if isinstance(child, Node) and child.name != 'DefLocal':
                    self.visit(child)
                if isinstance(child, Node):
                    self.visit(child)
    
    def visit_return_statement(self, node):
        """Visita una sentencia return."""
        self.has_return = True
        
        if self.current_function_return_type is None:
            self.error("Sentencia 'return' fuera de una función", node)
            return
        
        # Return Expresion ;
        if len(node.children) >= 2:
            expr_node = None
            for child in node.children:
                if isinstance(child, Node) and child.name in ['Expresion', 'ValorRegresa']:
                    expr_node = child
                    break
            
            if expr_node:
                expr_type = self.visit(expr_node)
                if expr_type and self.current_function_return_type != 'void':
                    if not self.are_types_compatible(expr_type, self.current_function_return_type):
                        self.error(f"Tipo de retorno incompatible: esperado '{self.current_function_return_type}', encontrado '{expr_type}'", node)
            elif self.current_function_return_type != 'void':
                self.error(f"Función debe retornar un valor de tipo '{self.current_function_return_type}'", node)
    
    def visit_assignment_statement(self, node):
        """Visita una sentencia de asignación."""
        # Buscar Identificador, OpAsignacion y Expresion en hijos directos
        var_name = None
        expr_node = None
        
        for i, child in enumerate(node.children):
            if child.state == TERMINAL and child.name == 'Identificador' and var_name is None:
                # Verificar que haya un OpAsignacion después
                if i + 1 < len(node.children) and node.children[i + 1].state == TERMINAL and node.children[i + 1].name == 'OpAsignacion':
                    var_name = child.token.lexema
            elif isinstance(child, Node) and child.name == 'Expresion' and expr_node is None:
                expr_node = child
        
        if not var_name or not expr_node:
            return
        
        # Verificar que la variable esté declarada
        var_symbol = self.symbol_table.lookup(var_name)
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
        
        if expr_type and not self.are_types_compatible(var_symbol.data_type, expr_type):
            self.error(f"Asignación de tipo incompatible: '{var_name}' es '{var_symbol.data_type}' pero se asigna '{expr_type}'", node)
        # Marcar la variable como inicializada
        var_symbol.initialized = True
    
    def visit_ValorRegresa(self, node):
        """Visita el valor de retorno."""
        if len(node.children) > 0:
            return self.visit(node.children[0])
        return None
    
    def visit_Expresion(self, node):
        """Visita una expresión y retorna su tipo."""
        if len(node.children) == 1:
            # Expresion -> Termino
            return self.visit(node.children[0])
        elif len(node.children) == 3:
            # Expresion -> Expresion OpBinario Expresion
            left_type = self.visit(node.children[0])
            operator = node.children[1]
            right_type = self.visit(node.children[2])
            
            return self.check_binary_operation(left_type, operator, right_type, node)
        
        return None
    
    def visit_Termino(self, node):
        """Visita un término y retorna su tipo."""
        if len(node.children) == 1:
            child = node.children[0]
            if child.state == TERMINAL:
                if child.name == 'Entero':
                    return 'int'
                elif child.name == 'Real':
                    return 'float'
                elif child.name == 'Identificador':
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
        args_node = node.children[2] if len(node.children) > 2 else None
        
        if func_name_node.state != TERMINAL or func_name_node.name != 'Identificador':
            return None
        
        func_name = func_name_node.token.lexema
        func_symbol = self.symbol_table.lookup(func_name)
        
        if not func_symbol:
            self.error(f"Función '{func_name}' no declarada", node)
            return None
        
        if func_symbol.symbol_type != 'function':
            self.error(f"'{func_name}' no es una función", node)
            return None
        
        # Extraer argumentos
        actual_args = self.extract_arguments(args_node) if args_node else []
        expected_params = func_symbol.params
        
        # Verificar número de argumentos
        if len(actual_args) != len(expected_params):
            self.error(f"Función '{func_name}' espera {len(expected_params)} argumentos, pero recibió {len(actual_args)}", node)
            return func_symbol.return_type
        
        # Verificar tipos de argumentos
        for i, (arg_type, (param_name, param_type)) in enumerate(zip(actual_args, expected_params)):
            if not self.are_types_compatible(param_type, arg_type):
                self.error(f"Argumento {i+1} de función '{func_name}': esperado '{param_type}', encontrado '{arg_type}'", node)
        
        # Marcar función como usada
        func_symbol.used = True
        
        return func_symbol.return_type
    
    def extract_arguments(self, args_node):
        """Extrae los tipos de los argumentos de una llamada a función."""
        args = []
        if args_node and args_node.name == 'Argumentos':
            args.extend(self.extract_arg_list(args_node))
        return args
    
    def extract_arg_list(self, node):
        """Extrae argumentos de forma recursiva."""
        args = []
        
        if node.name == 'Argumentos' and len(node.children) >= 1:
            # Argumentos -> Expresion ListaArgumentos
            expr_node = node.children[0]
            expr_type = self.visit(expr_node)
            if expr_type:
                args.append(expr_type)
            
            # Procesar ListaArgumentos si existe
            if len(node.children) > 1:
                list_args_node = node.children[1]
                args.extend(self.extract_list_arguments(list_args_node))
        
        return args
    
    def extract_list_arguments(self, node):
        """Extrae argumentos de ListaArgumentos recursivamente."""
        args = []
        
        if node.name == 'ListaArgumentos' and len(node.children) >= 2:
            # ListaArgumentos -> Coma Expresion ListaArgumentos
            expr_node = node.children[1]
            expr_type = self.visit(expr_node)
            if expr_type:
                args.append(expr_type)
            
            # Procesar el siguiente ListaArgumentos
            if len(node.children) > 2:
                next_list_args = node.children[2]
                args.extend(self.extract_list_arguments(next_list_args))
        
        return args
    
    def check_binary_operation(self, left_type, operator_node, right_type, node):
        """Verifica una operación binaria y retorna el tipo resultado."""
        if not left_type or not right_type:
            return None
        
        if operator_node.state != TERMINAL:
            return None
        
        op = operator_node.token.lexema
        
        # Operaciones aritméticas
        if op in ['+', '-', '*', '/']:
            if left_type in ['int', 'float'] and right_type in ['int', 'float']:
                # int + int = int, int + float = float, float + float = float
                if left_type == 'float' or right_type == 'float':
                    return 'float'
                return 'int'
            else:
                self.error(f"Operación aritmética '{op}' no válida entre '{left_type}' y '{right_type}'", node)
                return None
        
        # Operaciones de comparación
        elif op in ['<', '>', '<=', '>=', '==', '!=']:
            if left_type in ['int', 'float'] and right_type in ['int', 'float']:
                return 'int'  # Las comparaciones retornan int (0 o 1)
            else:
                self.error(f"Comparación '{op}' no válida entre '{left_type}' y '{right_type}'", node)
                return None
        
        # Operaciones lógicas
        elif op in ['&&', '||']:
            return 'int'  # Las operaciones lógicas retornan int
        
        return None
    
    def are_types_compatible(self, expected, actual):
        """Verifica si dos tipos son compatibles para asignación."""
        if expected == actual:
            return True
        
        # int puede ser promovido a float
        if expected == 'float' and actual == 'int':
            return True
        
        return False
    
    def final_checks(self):
        """Verificaciones finales después del análisis."""
        # Verificar funciones declaradas pero no usadas
        all_symbols = self.symbol_table.get_all_symbols()
        for scope_name, symbol in all_symbols:
            if symbol.symbol_type == 'function' and not symbol.used and symbol.name != 'main':
                self.warning(f"Función '{symbol.name}' declarada pero no usada")
    
    def print_symbol_table(self):
        """Imprime la tabla de símbolos para debugging."""
        print("\n========== TABLA DE SÍMBOLOS ==========\n")
        all_symbols = self.symbol_table.get_all_symbols()
        current_scope = None
        
        for scope_name, symbol in all_symbols:
            if scope_name != current_scope:
                print(f"Scope: {scope_name}")
                current_scope = scope_name
            
            used_str = " [USED]" if symbol.used else ""
            print(f"  {symbol}{used_str}")
        
        print("\n" + "="*40)
    
    def print_results(self):
        """Imprime los resultados del análisis semántico."""
        print("\n========== RESULTADOS ANÁLISIS SEMÁNTICO ==========\n")
        
        if not self.errors and not self.warnings:
            print("✅ Análisis semántico completado sin errores ni advertencias")
        else:
            if self.errors:
                print(f"❌ ERRORES ENCONTRADOS ({len(self.errors)}):")
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
        
        print("\n" + "="*50)

if __name__ == "__main__":
    ejemplo = """
    int a;
    int suma(int a, int b){
        return a+b;
    }

    int main(){
        float a;
        int b;
        int c;
        c = a+b;
        c = suma(8,9);
    }
    """
    try:
        toks = analizar(ejemplo)
        print("Tokens:")
        for t in toks:
            print(f"{t.nombre}('{t.lexema}') pos {t.pos}")
        print("\nÁrbol sintáctico:")
        # Cargar la gramática LR
        gramatica = cargar_gramatica_lr('compilador.lr')
        p = Parser(toks, gramatica_lr=gramatica)
        # Analizar usando el parser LR
        tree_lr = p.parse_lr()
        print("\nÁrbol sintáctico (LR):")
        print(tree_lr)
        
        # ===== ANÁLISIS SEMÁNTICO =====
        semantic_analyzer = SemanticAnalyzer()
        errors, warnings = semantic_analyzer.analyze(tree_lr)
        
        # Mostrar tabla de símbolos
        semantic_analyzer.print_symbol_table()
        
        # Mostrar resultados del análisis semántico
        semantic_analyzer.print_results()
        
        # Guardar AST en formato DOT y opcionalmente generar PNG 
        try:
            save_ast_dot(tree_lr, 'ast.dot')
            generate_png_from_dot('ast.dot', 'ast.png')
        except Exception as e:
            print('No se pudo generar AST gráfico:', e)
        print("\nGramática LR cargada:")
        print(f"Cantidad de reglas: {len(gramatica['idRegla'])}")
        print(f"Dimensiones tabla LR: {gramatica['filas']} x {gramatica['columnas']}")
    except LexicalError as le:
        print(f"Error léxico en línea {le.line}, columna {le.column}: {le}")
        try:
            lines = ejemplo.splitlines()
            if le.line is not None and 1 <= le.line <= len(lines):
                line_text = lines[le.line - 1]
                print('> ' + line_text)
                col = le.column or 1
                caret = '  ' + (' ' * (col - 1)) + '^'
                print(caret)
                #depuración
                codes = [f"{i+1}:{repr(ch)}(U+{ord(ch):04X})" for i, ch in enumerate(line_text)]
                print('Códigos en la línea:', ' '.join(codes))
        except Exception:
            pass
    except Exception as e:
        print("Error:", e)
