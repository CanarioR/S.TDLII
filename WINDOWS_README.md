# 🪟 INSTRUCCIONES PARA WINDOWS

## 🚀 **Inicio Súper Rápido**

### 1️⃣ **La forma más fácil:**
- Hacer **doble click** en `launch_gui.bat`
- ¡La interfaz gráfica se abrirá automáticamente!

### 2️⃣ **Usando comandos:**
```cmd
python run_gui.py
```

---

## 🛠️ **Si algo no funciona:**

### ❌ **Error: Python no reconocido**
- **Solución**: Instalar Python desde [python.org](https://python.org)
- ✅ **Importante**: Marcar "Add Python to PATH" durante la instalación

### ❌ **Error: Pillow no encontrado**
- **Solución**: Ejecutar en CMD/PowerShell:
```cmd
pip install Pillow
```

### ❌ **Error general**
- **Diagnóstico**: Ejecutar:
```cmd
python verify.py
```

---

## 📁 **Archivos Importantes**

| Archivo | Propósito |
|---------|-----------|
| `launch_gui.bat` | 🖱️ **Doble click para abrir GUI** |
| `run_gui.py` | 🐍 Launcher Python de la GUI |
| `main.py` | 📝 Compilador en línea de comandos |
| `verify.py` | 🔍 Verificar que todo funciona |

---

## 🎯 **Uso Típico**

1. **Abrir** → Doble click en `launch_gui.bat`
2. **Escribir código** en el editor
3. **Compilar** → Click en "🚀 Compilar Código"
4. **Ver resultados** en las pestañas de la derecha

---

## 🆘 **Soporte**

Si sigues teniendo problemas:
1. Ejecuta `python verify.py` y comparte la salida
2. Verifica que Python esté instalado: `python --version`
3. Verifica que Pillow esté instalado: `pip show Pillow`