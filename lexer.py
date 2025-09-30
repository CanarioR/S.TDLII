"""
Analizador Léxico - Compilador
===============================
Módulo que contiene la implementación del analizador léxico
incluyendo tokens, errores léxicos y funciones de análisis.
"""

import re

class Token:
    """Representa un token reconocido por el analizador léxico."""
    def __init__(self, tipo, lexema, linea, columna=0):
        self.tipo = tipo
        self.lexema = lexema
        self.linea = linea
        self.columna = columna
        self.posicion = linea  # Para compatibilidad

    def __repr__(self):
        return f"{self.tipo}('{self.lexema}') línea {self.linea}"


class LexicalError(Exception):
    """Excepción para errores léxicos."""
    pass


def analyze_tokens(input_text):
    """
    Analiza el texto de entrada y retorna una lista de tokens.
    
    Args:
        input_text (str): Texto a analizar
        
    Returns:
        list: Lista de objetos Token
        
    Raises:
        LexicalError: Si encuentra un carácter no reconocido
    """
    # Patrones de tokens
    token_patterns = [
        ('tipo', r'\b(int|float|void)\b'),
        ('if', r'\bif\b'),
        ('while', r'\bwhile\b'),
        ('else', r'\belse\b'),
        ('return', r'\breturn\b'),
        ('identificador', r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
        ('real', r'\d+\.\d+'),
        ('entero', r'\d+'),
        ('cadena', r'"[^"]*"'),
        ('opIgualdad', r'(==|!=)'),
        ('opRelac', r'(<=|>=|<|>)'),
        ('=', r'='),
        ('opOr', r'\|\|'),
        ('opAnd', r'&&'),
        ('opNot', r'!'),
        ('opSuma', r'[+\-]'),
        ('opMul', r'[*/]'),
        ('(', r'\('),
        (')', r'\)'),
        ('{', r'\{'),
        ('}', r'\}'),
        (',', r','),
        (';', r';'),
        ('Espacio', r'\s+'),
        ('Comentario', r'//.*'),
    ]

    tokens = []
    posicion = 0
    linea = 1
    columna = 1

    while posicion < len(input_text):
        coincidencia = None
        
        for tipo_token, patron in token_patterns:
            regex = re.compile(patron)
            coincidencia = regex.match(input_text, posicion)
            if coincidencia:
                lexema = coincidencia.group(0)
                
                # Ignorar espacios y comentarios
                if tipo_token not in ['Espacio', 'Comentario']:
                    token = Token(tipo_token, lexema, linea, columna)
                    tokens.append(token)
                
                # Actualizar posición
                posicion = coincidencia.end()
                
                # Actualizar línea y columna para mejor reporte de errores
                if '\n' in lexema:
                    linea += lexema.count('\n')
                    columna = 1
                else:
                    columna += len(lexema)
                break
        
        if not coincidencia:
            raise LexicalError(f"Carácter no reconocido '{input_text[posicion]}' en línea {linea}, columna {columna}", linea, columna)
    
    return tokens


def print_tokens(tokens):
    """
    Imprime la lista de tokens de forma legible.
    
    Args:
        tokens (list): Lista de objetos Token
    """
    print("Tokens:")
    for token in tokens:
        if token.tipo != 'Fin':
            print(token)