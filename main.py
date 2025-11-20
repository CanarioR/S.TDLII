import sys
import argparse
from lexer import analyze_tokens, LexicalError
from parser import Parser
from semantic_analyzer import SemanticAnalyzer
from code_generator import CodeGenerator
from utils import cargar_gramatica_lr, save_ast_dot, generate_png_from_dot


def main():
    parser = argparse.ArgumentParser(description='Compilador C simplificado')
    parser.add_argument('archivo', nargs='?', help='Archivo de código fuente .c')
    parser.add_argument('--force-asm', action='store_true', 
                        help='Generar ASM aún con errores semánticos')
    args = parser.parse_args()
    
    if args.archivo:
        try:
            with open(args.archivo, 'r', encoding='utf-8') as f:
                code_input = f.read()
        except FileNotFoundError:
            print(f"Error: No se pudo encontrar el archivo '{args.archivo}'")
            sys.exit(1)
        except Exception as e:
            print(f"Error al leer el archivo: {e}")
            sys.exit(1)
    elif not sys.stdin.isatty():
        code_input = sys.stdin.read().strip()
    else:
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
        
        print("\n=== ANÁLISIS SINTÁCTICO ===")
        grammar_data = cargar_gramatica_lr('compilador.lr')
        
        parser = Parser(grammar_data)
        ast_root = parser.parse(tokens)
        
        # Verificar errores sintácticos
        syntax_errors = parser.obtener_errores() if parser.tiene_errores() else []
        
        if syntax_errors:
            print("Errores sintácticos encontrados:")
            for error in syntax_errors:
                print(f"  - {error}")
            
            print("\n=== RESUMEN FINAL ===")
            print("Análisis léxico: Completado")
            print(f"Análisis sintáctico: FALLIDO ({len(syntax_errors)} errores)")
            print("Análisis semántico: No ejecutado")
            print("X COMPILACIÓN FALLIDA - Errores sintácticos encontrados")
            sys.exit(1)
        
        if ast_root is None:
            print("Error: No se pudo construir el AST")
            print("\n=== RESUMEN FINAL ===")
            print("Análisis léxico: Completado")
            print("Análisis sintáctico: FALLIDO (AST no construido)")
            print("Análisis semántico: No ejecutado")
            print("X COMPILACIÓN FALLIDA - No se pudo construir el AST")
            sys.exit(1)
            
        print(f"AST construido exitosamente con raíz: {ast_root.name}")
        
        print("\n=== ANÁLISIS SEMÁNTICO ===")
        semantic_analyzer = SemanticAnalyzer()
        semantic_analyzer.analyze(ast_root)
        
        print("\n=== GENERACIÓN DE ARCHIVOS ===")
        try:
            save_ast_dot(ast_root, 'ast.dot')
            generate_png_from_dot('ast.dot', 'ast.png')
        except Exception as e:
            print(f'Error al generar archivos gráficos del AST: {e}')
        
        # Variables para el resumen
        semantic_errors = semantic_analyzer.get_errors()
        semantic_warnings = semantic_analyzer.get_warnings()
        has_semantic_errors = semantic_analyzer.has_errors()
        
        # Generar código ensamblador si no hay errores semánticos O si se fuerza
        if not has_semantic_errors or args.force_asm:
            print("\n=== GENERACIÓN DE CÓDIGO ASM ===")
            try:
                code_generator = CodeGenerator()
                asm_code = code_generator.generate_code(ast_root, semantic_analyzer.symbol_table)
                
                # Guardar código ensamblador en archivo
                with open('output.s', 'w', encoding='utf-8') as f:
                    f.write(asm_code)
                
                print("Código ensamblador generado en: output.s")
                print("Primeras líneas del código ASM:")
                lines = asm_code.split('\n')
                for i, line in enumerate(lines[:15]):
                    print(f"  {line}")
                if len(lines) > 15:
                    print(f"  ... ({len(lines) - 15} líneas más)")
                
            except Exception as e:
                print(f'Error al generar código ensamblador: {e}')
                import traceback
                traceback.print_exc()
        
        print("\n=== RESUMEN FINAL ===")
        print("Análisis léxico: Completado")
        print("Análisis sintáctico: Completado")
        print(f"Análisis semántico: {len(semantic_errors)} errores, {len(semantic_warnings)} advertencias")
        
        if not has_semantic_errors:
            print("✓ COMPILACIÓN EXITOSA - Código semánticamente correcto")
            print("Código ensamblador generado exitosamente")
        elif args.force_asm:
            print("⚠ COMPILACIÓN CON ADVERTENCIAS - Código ASM generado forzadamente")
        else:
            print("X COMPILACIÓN FALLIDA - Errores semánticos encontrados")
            sys.exit(1)
            
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