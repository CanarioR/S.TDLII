"""
Launcher para la Interfaz Gráfica del Compilador
==============================================
Archivo de inicio simple para lanzar la GUI
"""

import sys
import os

# Agregar el directorio actual al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui import main
    
    if __name__ == "__main__":
        print("🚀 Iniciando Interfaz Gráfica del Compilador...")
        main()
        
except ImportError as e:
    print("❌ Error: Falta una dependencia necesaria.")
    print("📦 Por favor instala Pillow: pip install Pillow")
    print(f"🔍 Error específico: {e}")
    input("Presiona Enter para salir...")
except Exception as e:
    print(f"❌ Error al iniciar la aplicación: {e}")
    input("Presiona Enter para salir...")