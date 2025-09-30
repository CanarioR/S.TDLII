@echo off
REM Launcher para Windows - Interfaz Gráfica del Compilador
REM ========================================================

echo 🚀 Iniciando Interfaz Gráfica del Compilador...
echo.

REM Verificar si Python está disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python no está instalado o no está en el PATH
    echo 📥 Por favor instala Python desde: https://python.org
    pause
    exit /b 1
)

REM Verificar si Pillow está instalado
python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Advertencia: Pillow no está instalado
    echo 📦 Instalando Pillow...
    pip install Pillow
    if errorlevel 1 (
        echo ❌ Error: No se pudo instalar Pillow
        echo 💡 Intenta manualmente: pip install Pillow
        pause
        exit /b 1
    )
)

REM Ejecutar la GUI
python run_gui.py

REM Si llegamos aquí, probablemente hubo un error
if errorlevel 1 (
    echo.
    echo ❌ La aplicación se cerró con errores
    echo 🔍 Intenta ejecutar: python verify.py
    pause
)