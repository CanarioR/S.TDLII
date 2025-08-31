from dataclasses import dataclass

@dataclass
class Token:
    nombre: str
    tipo: int
    lexema: str
    pos: int
    estado: str = "TERMINAL"   

# Palabras reservadas
PALABRAS_RESERVADAS = {
    "if": ("If", 19),
    "while": ("While", 20),
    "return": ("Return", 21),
    "else": ("Else", 22),
    "int": ("Tipo", 4),
    "float": ("Tipo", 4),
    "void": ("Tipo", 4),
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

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

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
    int x = 10;
    float y = 3.14;
    if (x < y && y != 0) {
        return x + y;
    } else {
        x = x * 2;
    }
    $"""
    try:
        toks = analizar(ejemplo)
        print("Tokens:")
        for t in toks:
            print(t)
        print("\nÁrbol sintáctico:")
        p = Parser(toks)
        tree = p.parse_program()
        print(tree)
    except Exception as e:
        print("Error:", e)
