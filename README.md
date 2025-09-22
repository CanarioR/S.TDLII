# Analizador LR (compilador.lr)

Este repositorio contiene un analizador léxico y sintáctico simple en Python que utiliza una tabla LR externa (`compilador.lr`) junto con su archivo de columnas CSV (`compilador.csv`). El script principal es `main.py`.

## Qué hace
- Tokeniza un programa de ejemplo (variable `ejemplo` dentro de `main.py`).
- Carga la gramática y la tabla LR desde `compilador.lr` y su CSV asociado.
- Realiza un análisis sintáctico tipo LR (tabla-driven) y construye un árbol sintáctico (AST).
- Exporta el AST en formato DOT (`ast.dot`). Si tienes Graphviz (`dot`) en tu PATH, puede generar `ast.png`.

## Requisitos
- Python 3.8 o superior.
- (Opcional) Graphviz si quieres generar la imagen PNG del AST (`dot` en PATH).

Instalar dependencias opcionales (Windows PowerShell):

Instalar Graphviz en Windows:
- Descarga e instala desde https://graphviz.org/download/ o usa un gestor de paquetes (por ejemplo `choco install graphviz` si usas Chocolatey). Asegúrate de añadir `dot` al PATH.

## Uso
Ejecuta el analizador con:

```powershell
python main.py
```

Salida esperada:
- Se imprimirán los tokens generados (por el analizador léxico).
- Se mostrará el AST en la consola (representación por nodos Python).
- Se guardará `ast.dot` en la carpeta del proyecto.
- Si `dot` está disponible, también se generará `ast.png`.

Si quieres usar otro programa de entrada, edita la variable `ejemplo` dentro de `main.py` (al final del archivo). Actualmente el ejemplo incluido es:

```c
    int main(){ int a,b; 
    a = 3;
    }
```

Para generar manualmente el PNG desde el DOT (si `dot` está instalado):

```powershell
dot -Tpng ast.dot -o ast.png
```

## Manejo de errores
- Errores léxicos lanzan `LexicalError` con información de línea y columna.
- Errores sintácticos y problemas con la tabla LR lanzan `SyntaxError` o `RuntimeError` con mensajes descriptivos.

## Archivos importantes
- `main.py` — Analizador léxico y sintáctico, exportador de AST.
- `compilador.lr` — Archivo con las reglas y la tabla LR (no modificar; el parser los carga tal cual).
- `compilador.csv` — Cabeceras de columnas que se usan para mapear tokens y GOTO.
