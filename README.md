# Compilador para Lenguaje C Simplificado

Compilador completo en Python que implementa análisis léxico, sintáctico, semántico y **generación de código ensamblador x86-64** para un subconjunto del lenguaje C. Incluye interfaz de línea de comandos e interfaz gráfica con simulador dinámico de ASM integrado.

## Características - Interfaz Gráfica

### GUI
- Editor de código con números de línea
- Compilación con botón dedicado
- **Simulador dinámico de ASM**: Ejecuta el código generado paso a paso
- Visualización de resultados en pestañas:
  - Resumen: Estado general de la compilación
  - Errores: Errores y advertencias detallados
  - AST: Visualización del árbol sintáctico (ver ejemplo abajo)
  - Salida: Output completo del compilador
  - **Simulador**: Ejecución dinámica del código ASM con análisis de tipos
- Gestión de archivos: Abrir, guardar, limpiar
- Código de ejemplo incluido

![Ejemplo de AST generado](ast.png)
*Árbol Sintáctico Abstracto (AST) generado automáticamente por el compilador*

### Uso
```powershell
# Interfaz Gráfica
python run_gui.py

# Línea de comandos (Tradicional)
python main.py
```

## Características del Compilador

### Analizador Léxico
- Reconoce tokens del lenguaje C: tipos de datos, identificadores, operadores, literales
- Manejo de comentarios de línea (`//`) y bloque (`/* */`)
- Detección de errores léxicos con información de línea y columna
- Soporte para cadenas con caracteres de escape

### Analizador Sintáctico LR
- Parser LR completo con tabla de parsing externa
- Construcción de AST con desglose completo de la estructura sintáctica
- Soporte para gramática R1-R52 con 52 reglas de producción
- Manejo de conflictos reduce-reduce con priorización por validez de GOTO
- Optimización de nodos recursivos para evitar anidamiento excesivo

### Analizador Semántico
- Verificación de tipos: Detecta asignaciones incompatibles (float → int)
- **Validación estricta de llamadas a función**: Tipos de argumentos verificados
- Tabla de símbolos: Manejo de scopes y declaraciones
- Detección de errores: Variables no inicializadas, funciones no declaradas
- Análisis de uso: Identifica funciones y variables no utilizadas
- Verificación de retorno: Asegura que funciones retornen valores apropiados

### Generador de Código ASM (Nuevo)
- **Generación de código ensamblador x86-64 para Linux**
- **Convención de llamadas Linux x86-64**: Argumentos en `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9`
- **Syscalls de Linux**: `sys_write` (1) y `sys_exit` (60)
- **Compatible con compiladores en línea**: Usa estándar Linux (NASM + ld)
- Funciones de salida: Conversión de números a ASCII para `printf`
- Optimización de pila y registros
- Archivo generado: `output.s` listo para ensamblar y enlazar

### Estructuras soportadas
- Variables: Declaraciones simples y listas (`int x, y, z;`)
- Funciones: Definición con parámetros y cuerpo (`int suma(int a, int b) { ... }`)
- Expresiones: Aritméticas, relacionales, lógicas, asignaciones
- Sentencias: if-else, while, return, bloques
- Llamadas a función: Con argumentos múltiples (`suma(x, y)`)
- Scope: Variables locales y globales con verificación semántica

## Requisitos
- Python 3.8 o superior
- Pillow (para la interfaz gráfica): `pip install Pillow`
- (Opcional) Graphviz para visualización de AST (`dot` en PATH)
 

## Uso

### Interfaz Gráfica (Recomendado)
```powershell
python run_gui.py
```

Características de la GUI:
- Editor con números de línea
- Compilación con un click
- Resultados organizados en pestañas
- Visualización de AST integrada
- Gestión de archivos
- Código de ejemplo incluido

### Línea de Comandos
```powershell
python main.py
```

### Ejemplos soportados

El compilador puede procesar programas C como:

```c
// Variables globales
int x, y;

// Función con parámetros
int suma(int a, int b) {
    return a + b;
}

// Función main con variables locales
int main() {
    int resultado;
    resultado = suma(x, y);
    return resultado;
}
```

### Salida del programa
1. **Tokens**: Lista detallada de todos los tokens reconocidos
2. **Debugging LR**: Trazas del proceso de parsing (estados, transiciones, reducciones)
3. **AST textual**: Representación jerárquica del árbol sintáctico
4. **AST gráfico**: 
   - `ast.dot`: Archivo DOT para Graphviz
   - `ast.png`: Imagen del AST (si Graphviz está disponible)
5. **Código ensamblador**: 
   - `output.s`: Código ASM x86-64 compatible con Linux
   - Listo para ensamblar con NASM: `nasm -f elf64 output.s && ld output.o -o programa`
   - Compatible con compiladores en línea basados en Linux

### Compilación del código generado

Para compilar y ejecutar el código ASM generado:

```bash
# Ensamblar y enlazar (Linux)
nasm -f elf64 output.s
ld output.o -o programa
./programa

# El programa mostrará: "Resultado: X" donde X es el valor de retorno de main()
```

**Nota**: El código generado está optimizado para Linux x86-64 y usa syscalls estándar (`sys_write`, `sys_exit`). Es compatible con compiladores en línea como [OnlineGDB](https://www.onlinegdb.com/), [Compiler Explorer](https://godbolt.org/), etc.

## Arquitectura del sistema

### Archivos principales
- `main.py` — Analizador completo con lexer y parser LR
- `semantic_analyzer.py` — Análisis semántico con verificación de tipos estricta
- `code_generator.py` — Generador de código ensamblador x86-64 para Linux
- `gui.py` — Interfaz gráfica con simulador dinámico integrado
- `compilador.lr` — 52 reglas de gramática y tabla LR (95×46)
- `compilador.csv` — Mapeo de 24 terminales y 22 no terminales
- `ast.dot` / `ast.png` — Visualización del AST generado
- `output.s` — Código ASM x86-64 generado

### Gramática soportada (R1-R52)
El sistema implementa una gramática completa para:
- **R1-R3**: Programa y definiciones
- **R4-R6**: Definiciones de variables y funciones  
- **R7-R8**: Listas de variables
- **R9-R14**: Definiciones de funciones y bloques
- **R15-R26**: Definiciones locales y sentencias
- **R27-R42**: Expresiones y términos
- **R43-R52**: Argumentos y llamadas a función

## Funcionalidades avanzadas

### 🔧 **Sistema de debugging**
- Trazas completas del proceso LR con estados y transiciones
- Información detallada de candidatos en conflictos reduce-reduce
- Mapeo explícito entre reglas internas (0-51) y gramática formal (R1-R52)

### 🎯 **Manejo de errores robusto**
- `LexicalError`: Errores de tokenización con posición exacta
- `SyntaxError`: Errores de parsing con contexto del estado LR
- `SemanticError`: Errores de tipo y scope con mensajes descriptivos
- Validación de tabla LR y detección de GOTOs inválidos

### 🌲 **Optimización de AST**
- Combinación inteligente de nodos recursivos
- Preservación de estructura sintáctica completa
- Representación textual y gráfica optimizada

### 🖥️ **Simulador dinámico de ASM**
- Ejecución paso a paso del código ensamblador generado
- Análisis inteligente de llamadas a función con extracción de parámetros
- Validación de tipos en tiempo de ejecución
- Soporte para operaciones aritméticas, llamadas a función y control de flujo
- Interfaz integrada en la GUI con resultados en tiempo real

### ⚙️ **Generación de código optimizada**
- Convención de llamadas Linux x86-64 estándar
- Uso eficiente de registros y pila
- Syscalls nativos de Linux para E/S
- Compatible con herramientas estándar (NASM, ld)
- Código ASM portable entre sistemas Linux

## Personalización

Para analizar otros programas, modifica la variable `ejemplo` en `main.py`:

```python
ejemplo = """
// Tu código C aquí
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
"""
```

## Contribución y desarrollo

### Estructura del código
- **Clase `Token`**: Representación de tokens con tipo, valor y posición
- **Clase `Node`**: Nodos del AST con estado (TERMINAL/NO_TERMINAL)
- **Clase `CodeGenerator`**: Generador de código ASM x86-64 con optimización
- **Función `analizar()`**: Analizador léxico completo
- **Método `parse_lr()`**: Parser LR con manejo de conflictos
- **Función `ast_to_dot()`**: Generador de visualización DOT
- **GUI con simulador**: Interfaz completa con ejecución dinámica de ASM

### Debugging y desarrollo
El sistema incluye traces detallados que se pueden usar para:
- Analizar el comportamiento del parser LR
- Identificar problemas en la gramática
- Optimizar el rendimiento del análisis
- Validar la generación de código ASM
- Depurar el simulador dinámico

Para habilitar más debugging, busca las líneas `print(f"[DEBUG]")` en el código.

## Tecnologías y estándares

- **Lenguaje**: Python 3.8+
- **Arquitectura destino**: x86-64 (64-bit)
- **Sistema operativo**: Linux (syscalls nativos)
- **Ensamblador**: NASM
- **Convención de llamadas**: System V AMD64 ABI (Linux)
- **Formato de objeto**: ELF64
- **Visualización**: Graphviz (DOT)

