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
    # Separar terminales y no terminales (buscamos 'programa' como primer no terminal)
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

def es_letra(c): return c.isalpha()
def es_digito(c): return c.isdigit()
def es_espacio(c): return c in " \t\r\n"

def analizar(texto):
    tokens = []
    i, n = 0, len(texto)

    while i < n:
        if es_espacio(texto[i]):
            i += 1
            continue

        inicio = i
        c = texto[i]

        # --- Identificador o palabra reservada ---
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

        # --- entero o real ---
        if es_digito(c):
            while i < n and es_digito(texto[i]):
                i += 1
            if i < n and texto[i] == '.':
                i += 1
                if i >= n or not es_digito(texto[i]):
                    raise ValueError(f"Real mal formado en posición {inicio}")
                while i < n and es_digito(texto[i]):
                    i += 1
                lexema = texto[inicio:i]
                tokens.append(Token("Real", 2, lexema, inicio))
            else:
                lexema = texto[inicio:i]
                tokens.append(Token("Entero", 1, lexema, inicio))
            continue

        # --- Operadores de dos caracteres ---
        if i+1 < n:
            doble = texto[i:i+2]
            if doble in SIMBOLOS:
                nombre, tipo = SIMBOLOS[doble]
                tokens.append(Token(nombre, tipo, doble, inicio))
                i += 2
                continue

        # --- Operadores y símbolos de un carácter ---
        if c in SIMBOLOS:
            nombre, tipo = SIMBOLOS[c]
            tokens.append(Token(nombre, tipo, c, inicio))
            i += 1
            continue

        raise ValueError(f"Carácter no reconocido '{c}' en posición {i}")

    return tokens

# --- Analizador sintáctico  ---
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
        s = f"{pad}{self.state}: {self.name}"
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
        # Diccionario de equivalencias de nombres de token a columna CSV
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
        historial_reducciones = {}

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
                # Aceptar codificado como -(n_reglas+1)
                if accion == -(len(self.idRegla) + 1):
                    return pila_simbolos[0] if pila_simbolos else None

                # Intentar mapear reducción a índice de regla. Usamos dos offsets comunes
                candidatos = []
                for offset in (1, 2):
                    idx_cand = -accion - offset
                    if 0 <= idx_cand < len(self.lonRegla):
                        lon_cand = self.lonRegla[idx_cand]
                        # Simular pop
                        temp_states = pila_estados.copy()
                        for _ in range(lon_cand):
                            if temp_states:
                                temp_states.pop()
                        if not temp_states:
                            continue
                        estado_goto_cand = temp_states[-1]
                        nt_cand = self.nombreRegla[idx_cand]
                        col_goto_cand = self.gramatica_lr['nonterminal_a_columna'].get(nt_cand)
                        if col_goto_cand is None:
                            continue
                        goto_cand = self.tabla_lr[estado_goto_cand][col_goto_cand]
                        try:
                            accion_despues = self.tabla_lr[goto_cand][col]
                        except Exception:
                            accion_despues = None
                        candidatos.append((idx_cand, lon_cand, estado_goto_cand, goto_cand, accion_despues, offset))

                print(f"[LR][REDUCE] Candidatos simulados: {candidatos}")

                elegido = None
                usado = historial_reducciones.get((estado, col), set())
                # Preferir candidatos que llevan a shift
                for cand in candidatos:
                    if cand[0] in usado:
                        continue
                    if cand[4] is not None and cand[4] > 0:
                        elegido = cand
                        break
                # Si no hay shifts, preferir alguna reducción no usada
                if elegido is None:
                    for cand in candidatos:
                        if cand[0] in usado:
                            continue
                        if cand[4] is not None and cand[4] < 0:
                            elegido = cand
                            break
                # Preferir regla vacía si existe
                if elegido is None:
                    for cand in candidatos:
                        if cand[0] in usado:
                            continue
                        if cand[1] == 0:
                            elegido = cand
                            break

                if elegido is None:
                    # fallback determinista: probar offset 2 luego 1
                    if 0 <= -accion - 2 < len(self.lonRegla):
                        num_regla = -accion - 2
                    else:
                        num_regla = -accion - 1
                    lon = self.lonRegla[num_regla]
                else:
                    num_regla, lon, estado_goto_sim, goto_sim, accion_despues, used_offset = elegido

                historial_reducciones.setdefault((estado, col), set()).add(num_regla)
                print(f"[LR][REDUCE] Elegido: regla_index={num_regla}, lon={lon}")

                hijos = []
                for _ in range(lon):
                    pila_estados.pop()
                    hijos.insert(0, pila_simbolos.pop())

                nt = self.nombreRegla[num_regla]
                nodo = Node(nt, NO_TERMINAL, children=hijos)
                estado_goto = pila_estados[-1]
                nonterminal_a_columna = self.gramatica_lr['nonterminal_a_columna']
                col_goto = nonterminal_a_columna.get(nt)
                if col_goto is None:
                    raise SyntaxError(f"No terminal '{nt}' no tiene columna GOTO asignada en la tabla LR")
                goto = self.tabla_lr[estado_goto][col_goto]
                print(f"[LR] GOTO: Estado: {estado_goto}, NoTerminal: {nt}, Columna: {col_goto}, Goto: {goto}")
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

# --- Prueba ---
if __name__ == "__main__":
    ejemplo = """
    int main(){
    int y;
}"""
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
    # Guardar AST en formato DOT y opcionalmente generar PNG (si graphviz dot está instalado)
    try:
        save_ast_dot(tree_lr, 'ast.dot')
        generate_png_from_dot('ast.dot', 'ast.png')
    except Exception as e:
        print('No se pudo generar AST gráfico:', e)
    print("\nGramática LR cargada:")
    print(f"Cantidad de reglas: {len(gramatica['idRegla'])}")
    print(f"Dimensiones tabla LR: {gramatica['filas']} x {gramatica['columnas']}")
except Exception as e:
    print("Error:", e)
