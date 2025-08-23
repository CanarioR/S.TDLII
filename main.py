from dataclasses import dataclass

@dataclass
class Token:
    nombre: str  
    tipo: int     
    lexema: str   
    pos: int      

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

        # --- Número: entero o real ---
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
        for t in analizar(ejemplo):
            print(t)
    except Exception as e:
        print("Error:", e)
