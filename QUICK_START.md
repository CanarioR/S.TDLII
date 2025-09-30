# 🚀 GUÍA RÁPIDA DEL COMPILADOR

## ⚡ Inicio Rápido

### 🖥️ **Interfaz Gráfica (Recomendado)**

**Opción 1 - Archivo Batch (Windows):**
```cmd
launch_gui.bat
```
*Simplemente hacer doble click en el archivo*

**Opción 2 - Comando Python:**
```cmd
python run_gui.py
```

### 📝 **Línea de Comandos**
```cmd
python main.py
```

### 🔍 **Verificar Sistema**
```cmd
python verify.py
```

## 💻 **Para Windows**

### ✅ **Forma más fácil:**
1. Hacer **doble click** en `launch_gui.bat`
2. La aplicación se abrirá automáticamente

### ⚙️ **Comandos en PowerShell/CMD:**
```powershell
# Interfaz gráfica
python run_gui.py

# Línea de comandos
python main.py

# Verificar todo funciona
python verify.py
```

### ❌ **Si tienes problemas:**
1. Asegúrate de tener Python instalado
2. Ejecuta: `python verify.py`
3. Si falta Pillow: `pip install Pillow`

## 📁 **Estructura del Proyecto**

```
📦 Compilador/
├── 🚀 run_gui.py          # Lanzador de la GUI
├── 🖥️ gui.py              # Interfaz gráfica completa
├── ⚙️ main.py             # Compilador principal (CLI)
├── 🔤 lexer.py            # Analizador léxico
├── 🌳 parser.py           # Analizador sintáctico LR
├── 🧠 semantic_analyzer.py # Analizador semántico
├── 🛠️ utils.py            # Utilidades
├── 📋 compilador.lr       # Gramática
├── 📊 compilador.csv      # Tabla LR
├── ✅ verify.py           # Verificador del sistema
└── 📖 README.md           # Documentación completa
```

## 🎯 **Características de la GUI**

- ✅ **Editor de código** con números de línea
- ✅ **Compilación en tiempo real** con un click
- ✅ **Resultados organizados** en pestañas:
  - 📋 Resumen de compilación
  - ⚠️ Errores y advertencias
  - 🌳 Visualización del AST
  - 🖥️ Salida completa
- ✅ **Gestión de archivos** (abrir/guardar)
- ✅ **Código de ejemplo** incluido

## 🔧 **Análisis Realizado**

1. **📝 Léxico**: Tokens, comentarios, literales
2. **🌳 Sintáctico**: Parsing LR, construcción de AST
3. **🧠 Semántico**: Tipos, scopes, errores de compatibilidad

## 💡 **Ejemplo de Código**

```c
int a;

int suma(int a, int b) {
    return a + b;
}

int main() {
    float a;
    int b;
    int c;
    c = a + b;      // ❌ Error: float → int
    c = suma(8, 9); // ✅ OK: llamada válida
}
```

## 🆘 **Solución de Problemas**

### ❌ Error de dependencias
```bash
pip install Pillow
```

### ❌ Error de imports
```bash
python verify.py  # Verificar estado del sistema
```

### ❌ La GUI no abre
1. Verificar que Pillow esté instalado
2. Ejecutar: `python verify.py`
3. Probar: `python main.py` (CLI alternativo)

---
🎉 **¡El compilador está listo para usar!**