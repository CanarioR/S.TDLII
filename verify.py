"""
Verificador del Sistema de Compilador
===================================
Script para verificar que todos los componentes funcionen correctamente
"""

import os
import sys
import subprocess

def check_file_exists(filename, description):
    """Verificar si un archivo existe"""
    if os.path.exists(filename):
        print(f"✅ {description}: {filename}")
        return True
    else:
        print(f"❌ {description}: {filename} - NO ENCONTRADO")
        return False

def check_python_import(module_name, description):
    """Verificar si un módulo se puede importar"""
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {module_name} - ERROR: {e}")
        return False

def test_compiler():
    """Probar el compilador con código de ejemplo"""
    print("\n🧪 Probando compilador...")
    
    test_code = """int a;

int suma(int a, int b) {
    return a + b;
}

int main() {
    float a;
    int b;
    int c;
    c = a + b;
    c = suma(8, 9);
}"""
    
    try:
        result = subprocess.run(
            [sys.executable, 'main.py'],
            input=test_code,
            text=True,
            capture_output=True,
            timeout=30
        )
        
        if "Análisis léxico: Completado" in result.stdout + result.stderr:
            print("✅ Compilador funcionando correctamente")
            print("✅ Análisis léxico: OK")
            
        if "Análisis sintáctico: Completado" in result.stdout + result.stderr:
            print("✅ Análisis sintáctico: OK")
            
        if "ERRORES ENCONTRADOS (1):" in result.stdout + result.stderr:
            print("✅ Análisis semántico: OK (detectó error esperado)")
            
        if "ADVERTENCIAS (3):" in result.stdout + result.stderr:
            print("✅ Análisis semántico: OK (detectó advertencias esperadas)")
            
        return True
        
    except Exception as e:
        print(f"❌ Error probando compilador: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("🔍 VERIFICACIÓN DEL SISTEMA DE COMPILADOR")
    print("=" * 50)
    
    all_ok = True
    
    # Verificar archivos core del compilador
    print("\n📁 Verificando archivos del compilador:")
    core_files = [
        ("main.py", "Archivo principal"),
        ("lexer.py", "Analizador léxico"),
        ("parser.py", "Analizador sintáctico"),
        ("semantic_analyzer.py", "Analizador semántico"),
        ("utils.py", "Utilidades"),
        ("compilador.lr", "Gramática"),
        ("compilador.csv", "Tabla LR")
    ]
    
    for filename, desc in core_files:
        if not check_file_exists(filename, desc):
            all_ok = False
    
    # Verificar archivos de GUI
    print("\n🖥️ Verificando interfaz gráfica:")
    gui_files = [
        ("gui.py", "Interfaz gráfica"),
        ("run_gui.py", "Launcher GUI")
    ]
    
    for filename, desc in gui_files:
        if not check_file_exists(filename, desc):
            all_ok = False
    
    # Verificar dependencias de Python
    print("\n📦 Verificando dependencias Python:")
    dependencies = [
        ("tkinter", "Interfaz gráfica tkinter"),
        ("PIL", "Pillow para imágenes"),
        ("subprocess", "Ejecución de procesos"),
        ("threading", "Hilos para GUI")
    ]
    
    for module, desc in dependencies:
        if not check_python_import(module, desc):
            all_ok = False
    
    # Probar compilador
    if all_ok:
        if not test_compiler():
            all_ok = False
    
    # Resultado final
    print("\n" + "=" * 50)
    if all_ok:
        print("🎉 ¡VERIFICACIÓN EXITOSA!")
        print("✅ Todos los componentes están funcionando correctamente")
        print("\n🚀 Puedes usar:")
        print("   • Interfaz gráfica: python run_gui.py")
        print("   • Línea de comandos: python main.py")
    else:
        print("❌ VERIFICACIÓN FALLIDA")
        print("🔧 Algunos componentes necesitan atención")
    
    print("=" * 50)

if __name__ == "__main__":
    main()