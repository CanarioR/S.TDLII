from dataclasses import dataclass

@dataclass
class Token:
    tipo: str
    lexema: str
    pos: int

def es_letra(c: str) -> bool:
    return c.isalpha()

def es_digito(c: str) -> bool:
    return c.isdigit()

def es_espacio(c: str) -> bool:
    return c in " \t\r\n"

def automata(texto: str) -> list[Token]:
    tokens = []
    i, n = 0, len(texto)

    while i < n:
        if es_espacio(texto[i]):
            i += 1
            continue

        inicio = i
        estado = "q0"

        while i < n:
            c = texto[i]

            if estado == "q0":
                if es_letra(c):
                    estado = "qID"
                    i += 1
                elif es_digito(c):
                    estado = "qINT"
                    i += 1
                else:
                    raise ValueError(f"Carácter inválido '{c}' en posición {i}")

            elif estado == "qID":
                if es_letra(c) or es_digito(c):
                    i += 1
                else:
                    break  # fin de IDENT

            elif estado == "qINT":
                if es_digito(c):
                    i += 1
                elif c == '.':
                    estado = "qDOT"
                    i += 1
                else:
                    raise ValueError(f"entero sin decimales en posición {inicio}")

            elif estado == "qDOT":
                if es_digito(c):
                    estado = "qREAL"
                    i += 1
                else:
                    raise ValueError(f"Se esperaba dígito después del punto en posición {i}")

            elif estado == "qREAL":
                if es_digito(c):
                    i += 1
                else:
                    break  # fin de REAL
            else:
                raise ValueError("Estado inválido en el autómata")

        # Estado final -> token válido
        lexema = texto[inicio:i]
        if estado == "qID":
            tokens.append(Token("IDENT", lexema, inicio))
        elif estado == "qREAL":
            tokens.append(Token("REAL", lexema, inicio))
        else:
            raise ValueError(f"Token no válido '{lexema}' en posición {inicio}")

    return tokens


if __name__ == "__main__":
    pruebas = [
        "x var1 prueba2",
        "pi 3.14 0.5",
        "a12b 12.34 valor",
        "12.5", 
        ".5"     # error
        "12."  #error
    ]
    for cad in pruebas:
        print(f"\nEntrada: {cad}")
        try:
            for t in automata(cad):
                print("  ", t)
        except Exception as e:
            print("  Error:", e)
