"""
Utilidades del Compilador
=========================
Módulo que contiene funciones auxiliares para carga de gramática,
generación de diagramas AST y otras utilidades.
"""

import os
import csv
import subprocess
import shutil


def cargar_gramatica_lr(ruta):
    """
    Lee el archivo de gramática LR y retorna los vectores y la tabla LR en un diccionario.
    
    Args:
        ruta (str): Ruta al archivo de gramática
        
    Returns:
        dict: Diccionario con la información de la gramática LR
    """
    with open(ruta, 'r', encoding='utf-8') as f:
        lineas = [line.strip() for line in f if line.strip()]

    # Leer cantidad de reglas
    n_reglas = int(lineas[0])
    idRegla = []
    lonRegla = []
    nombreRegla = []
    
    # Leer los 3 vectores de reglas
    for i in range(1, n_reglas + 1):
        partes = lineas[i].split('\t')
        idRegla.append(int(partes[0]))
        lonRegla.append(int(partes[1]))
        nombreRegla.append(partes[2])

    # Leer dimensiones de la tabla LR
    idx_dim = n_reglas + 1
    filas, columnas = map(int, lineas[idx_dim].split('\t'))

    # Leer la tabla LR
    tabla_lr = []
    for i in range(idx_dim + 1, idx_dim + 1 + filas):
        fila = list(map(int, lineas[i].split('\t')))
        tabla_lr.append(fila)

    # Leer nombres de columna directamente del archivo CSV asociado
    columnas_csv = []
    csv_path = os.path.splitext(ruta)[0] + '.csv'
    if os.path.exists(csv_path):
        with open(csv_path, encoding='utf-8') as fcsv:
            reader = csv.reader(fcsv)
            columnas_csv = next(reader)[1:]
    else:
        columnas_csv = [str(i) for i in range(columnas)]

    # Mapeo de nombre de columna a índice
    token_a_columna = {nombre: idx for idx, nombre in enumerate(columnas_csv)}
    
    # Separar terminales y no terminales 
    num_term = 0
    for i, nombre in enumerate(columnas_csv):
        if nombre == 'programa':
            num_term = i
            break
    nonterminal_a_columna = {nombre: idx for idx, nombre in enumerate(columnas_csv[num_term:], start=num_term)}

    print("[DEBUG] Mapeo de columnas de terminales:")
    for nombre, idx in token_a_columna.items():
        if idx < num_term:
            print(f"  {nombre}: columna {idx}")
    
    print("[DEBUG] Mapeo de columnas de no terminales (GOTO):")
    for nombre, idx in nonterminal_a_columna.items():
        print(f"  {nombre}: columna {idx}")
    
    print(f"[DEBUG] Número de terminales: {num_term}")
    print(f"[DEBUG] Número de no terminales: {len(nonterminal_a_columna)}")
    print(f"[DEBUG] Total columnas en tabla LR: {columnas}")

    return {
        'n_reglas': n_reglas,
        'idRegla': idRegla,
        'lonRegla': lonRegla,
        'nombreRegla': nombreRegla,
        'tabla_lr': tabla_lr,
        'token_a_columna': token_a_columna,
        'nonterminal_a_columna': nonterminal_a_columna,
        'columnas_csv': columnas_csv,
        'num_terminales': num_term
    }


def ast_to_dot(node, level=0):
    """
    Convierte un nodo AST a formato DOT para visualización con Graphviz.
    
    Args:
        node: Nodo del AST
        level (int): Nivel de profundidad (para IDs únicos)
        
    Returns:
        str: Representación en formato DOT
    """
    if node is None:
        return ""
    
    # Crear ID único para este nodo
    node_id = f"node_{id(node)}"
    
    # Determinar etiqueta del nodo
    if hasattr(node, 'state') and node.state == 1:  # TERMINAL
        label = f"{node.name}\\n{node.token.lexema if hasattr(node, 'token') else ''}"
        shape = 'box'
        color = 'lightblue'
    else:  # NO_TERMINAL
        label = node.name if hasattr(node, 'name') else str(node)
        shape = 'ellipse'
        color = 'lightgreen'
    
    # Crear definición del nodo
    dot = f'  {node_id} [label="{label}", shape={shape}, style=filled, fillcolor={color}];\n'
    
    # Procesar hijos si existen
    if hasattr(node, 'children') and node.children:
        for child in node.children:
            if child is not None:
                child_id = f"node_{id(child)}"
                dot += f'  {node_id} -> {child_id};\n'
                dot += ast_to_dot(child, level + 1)
    
    return dot


def save_ast_dot(root, path_dot):
    """
    Guarda el AST en formato DOT.
    
    Args:
        root: Nodo raíz del AST
        path_dot (str): Ruta donde guardar el archivo DOT
    """
    dot = ast_to_dot(root)
    with open(path_dot, 'w', encoding='utf-8') as f:
        f.write("digraph AST {\n")
        f.write("  rankdir=TB;\n")
        f.write("  node [fontname=\"Arial\"];\n")
        f.write(dot)
        f.write("}\n")
    print(f"AST DOT guardado en: {path_dot}")


def generate_png_from_dot(path_dot, path_png):
    """
    Genera un archivo PNG desde un archivo DOT usando Graphviz.
    
    Args:
        path_dot (str): Ruta al archivo DOT
        path_png (str): Ruta donde guardar el PNG
    """
    try:
        # Verificar si Graphviz está instalado
        if shutil.which('dot') is None:
            print("Graphviz no está instalado. Instálalo para generar imágenes PNG.")
            return
        
        # Ejecutar dot para generar PNG
        subprocess.run(['dot', '-Tpng', path_dot, '-o', path_png], 
                      check=True, capture_output=True)
        print(f"AST PNG generado en: {path_png}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error al generar PNG: {e}")
    except FileNotFoundError:
        print("Graphviz no encontrado. Asegúrate de que esté instalado y en el PATH.")


def print_grammar_info(grammar_data):
    """
    Imprime información sobre la gramática cargada.
    
    Args:
        grammar_data (dict): Datos de la gramática LR
    """
    print(f"\nGramática LR cargada:")
    print(f"Cantidad de reglas: {grammar_data['n_reglas']}")
    print(f"Dimensiones tabla LR: {len(grammar_data['tabla_lr'])} x {len(grammar_data['columnas_csv'])}")