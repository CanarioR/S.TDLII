"""
Compilador Principal
===================
Punto de entrada principal del compilador que coordina todos los módulos.
"""

import sys
from lexer import analyze_tokens, LexicalError
from parser import Parser
from semantic_analyzer import SemanticAnalyzer
from utils import cargar_gramatica_lr, save_ast_dot, generate_png_from_dot


def main():
    """Función principal del compilador"""
    # Verificar si hay input desde stdin
    if not sys.stdin.isatty():
        # Hay input desde stdin (por ejemplo, desde la GUI)
        code_input = sys.stdin.read().strip()
    else:
        # No hay input desde stdin, usar ejemplo por defecto
        code_input = """int a;
int suma(int a, int b){
    return a+b;
}

int main(){
    float a;
    int b;
    int c;
    c = a+b;
    c = suma(8,9);
}"""
    
    try:
        # === ANÁLISIS LÉXICO ===
        print("=== ANÁLISIS LÉXICO ===")
        tokens = analyze_tokens(code_input)
        print("Tokens encontrados:")
        for token in tokens:
            print(f"  {token.tipo}('{token.lexema}') línea {token.linea}")
        
        # === ANÁLISIS SINTÁCTICO ===
        print("\n=== ANÁLISIS SINTÁCTICO ===")
        # Cargar la gramática LR
        grammar_data = cargar_gramatica_lr('compilador.lr')
        
        # Crear y ejecutar el parser
        parser = Parser(grammar_data)
        ast_root = parser.parse(tokens)
        
        if parser.tiene_errores():
            print("Errores sintácticos encontrados:")
            for error in parser.obtener_errores():
                print(f"  - {error}")
            return
        
        if ast_root is None:
            print("Error: No se pudo construir el AST")
            return
            
        print(f"AST construido exitosamente con raíz: {ast_root.name}")
        
        # === ANÁLISIS SEMÁNTICO ===
        print("\n=== ANÁLISIS SEMÁNTICO ===")
        semantic_analyzer = SemanticAnalyzer()
        semantic_analyzer.analyze(ast_root)
        
        # === GENERACIÓN DE ARCHIVOS ===
        print("\n=== GENERACIÓN DE ARCHIVOS ===")
        try:
            save_ast_dot(ast_root, 'ast.dot')
            generate_png_from_dot('ast.dot', 'ast.png')
        except Exception as e:
            print(f'Error al generar archivos gráficos del AST: {e}')
        
        # === RESUMEN FINAL ===
        print("\n=== RESUMEN FINAL ===")
        print("Análisis léxico: Completado")
        print("Análisis sintáctico: Completado")
        print(f"Análisis semántico: {len(semantic_analyzer.get_errors())} errores, {len(semantic_analyzer.get_warnings())} advertencias")
        
        if not semantic_analyzer.has_errors():
            print("Compilación exitosa - Código semánticamente correcto")
        else:
            print("X Compilación fallida - Errores semánticos encontrados")
            
    except LexicalError as le:
        print(f"\nX Error léxico en línea {le.line}, columna {le.column}: {le}")
        try:
            lines = code_input.splitlines()
            if le.line is not None and 1 <= le.line <= len(lines):
                line_text = lines[le.line - 1]
                print('> ' + line_text)
                col = le.column or 1
                caret = '  ' + (' ' * (col - 1)) + '^'
                print(caret)
        except Exception:
            pass
            
    except Exception as e:
        print(f"\nX Error inesperado: {e}")


if __name__ == "__main__":
    main()