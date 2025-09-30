"""
Interfaz Gráfica para el Compilador
===================================
GUI amigable para el compilador con editor de código y visualización de resultados
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import tempfile
import os
import threading
from PIL import Image, ImageTk
import webbrowser

class CompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Compilador - Analizador Léxico, Sintáctico y Semántico")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')
        
        # Variables
        self.current_file = None
        self.ast_image = None
        
        # Configurar estilo
        self.setup_styles()
        
        # Crear la interfaz
        self.create_widgets()
        
        # Código de ejemplo
        self.load_sample_code()
        
    def setup_styles(self):
        """Configurar estilos para un look moderno"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 16, 'bold'),
                       background='#2b2b2b',
                       foreground='#ffffff')
        
        style.configure('Section.TLabel',
                       font=('Segoe UI', 10, 'bold'),
                       background='#2b2b2b',
                       foreground='#ffffff')
        
        style.configure('TButton',
                       font=('Segoe UI', 9),
                       padding=5)
        
        style.configure('Success.TLabel',
                       foreground='#4CAF50',
                       background='#2b2b2b')
        
        style.configure('Error.TLabel',
                       foreground='#f44336',
                       background='#2b2b2b')
        
        style.configure('Warning.TLabel',
                       foreground='#ff9800',
                       background='#2b2b2b')
    
    def create_widgets(self):
        """Crear todos los widgets de la interfaz"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_label = ttk.Label(main_frame, 
                               text="🔧 Compilador - Análisis Completo", 
                               style='Title.TLabel')
        title_label.pack(pady=(0, 10))
        
        # Frame superior - Editor y controles
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel izquierdo - Editor de código
        left_panel = ttk.LabelFrame(top_frame, text="📝 Editor de Código", padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Toolbar del editor
        editor_toolbar = ttk.Frame(left_panel)
        editor_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(editor_toolbar, text="📁 Abrir", 
                  command=self.open_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(editor_toolbar, text="💾 Guardar", 
                  command=self.save_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(editor_toolbar, text="🗑️ Limpiar", 
                  command=self.clear_editor).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(editor_toolbar, text="📄 Ejemplo", 
                  command=self.load_sample_code).pack(side=tk.LEFT, padx=(0, 5))
        
        # Editor de código con números de línea
        editor_frame = ttk.Frame(left_panel)
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        # Números de línea
        self.line_numbers = tk.Text(editor_frame, width=4, padx=3, takefocus=0,
                                   border=0, state='disabled', wrap='none',
                                   font=('Consolas', 10), bg='#404040', fg='#888888')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Editor principal
        self.code_editor = scrolledtext.ScrolledText(editor_frame, 
                                                    font=('Consolas', 11),
                                                    bg='#1e1e1e', fg='#dcdcdc',
                                                    insertbackground='white',
                                                    selectbackground='#264f78',
                                                    wrap=tk.NONE)
        self.code_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind para actualizar números de línea
        self.code_editor.bind('<KeyRelease>', self.update_line_numbers)
        self.code_editor.bind('<MouseWheel>', self.update_line_numbers)
        self.code_editor.bind('<Button-1>', self.update_line_numbers)
        
        # Panel derecho - Resultados
        right_panel = ttk.LabelFrame(top_frame, text="📊 Resultados", padding=10)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Botón de compilar
        compile_frame = ttk.Frame(right_panel)
        compile_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.compile_btn = ttk.Button(compile_frame, text="🚀 Compilar Código", 
                                     command=self.compile_code, style='TButton')
        self.compile_btn.pack(fill=tk.X)
        
        # Status
        self.status_label = ttk.Label(compile_frame, text="Listo para compilar", 
                                     style='Section.TLabel')
        self.status_label.pack(pady=(5, 0))
        
        # Notebook para resultados
        self.results_notebook = ttk.Notebook(right_panel)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Resumen
        summary_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(summary_frame, text="📋 Resumen")
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, 
                                                     font=('Segoe UI', 9),
                                                     bg='#2d2d2d', fg='#ffffff',
                                                     height=8)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 2: Errores y Advertencias
        errors_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(errors_frame, text="⚠️ Errores")
        
        self.errors_text = scrolledtext.ScrolledText(errors_frame, 
                                                    font=('Segoe UI', 9),
                                                    bg='#2d2d2d', fg='#ffffff',
                                                    height=8)
        self.errors_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 3: AST
        ast_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(ast_frame, text="🌳 AST")
        
        # Frame para controles del AST
        ast_controls = ttk.Frame(ast_frame)
        ast_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(ast_controls, text="🔍 Ver AST", 
                  command=self.view_ast).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(ast_controls, text="💾 Guardar PNG", 
                  command=self.save_ast_image).pack(side=tk.LEFT)
        
        # Canvas para mostrar AST
        self.ast_canvas = tk.Canvas(ast_frame, bg='white')
        self.ast_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 4: Salida completa
        output_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(output_frame, text="🖥️ Salida")
        
        self.output_text = scrolledtext.ScrolledText(output_frame, 
                                                    font=('Consolas', 9),
                                                    bg='#1e1e1e', fg='#dcdcdc',
                                                    height=15)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def update_line_numbers(self, event=None):
        """Actualizar números de línea"""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        
        # Contar líneas
        lines = self.code_editor.get('1.0', tk.END).count('\n')
        line_numbers_string = '\n'.join(str(i) for i in range(1, lines + 1))
        
        self.line_numbers.insert('1.0', line_numbers_string)
        self.line_numbers.config(state='disabled')
    
    def load_sample_code(self):
        """Cargar código de ejemplo"""
        sample_code = """int a;

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
        self.code_editor.delete('1.0', tk.END)
        self.code_editor.insert('1.0', sample_code)
        self.update_line_numbers()
        self.status_label.config(text="Código de ejemplo cargado")
    
    def clear_editor(self):
        """Limpiar el editor"""
        if messagebox.askyesno("Confirmar", "¿Estás seguro de que quieres limpiar el editor?"):
            self.code_editor.delete('1.0', tk.END)
            self.update_line_numbers()
            self.clear_results()
            self.status_label.config(text="Editor limpiado")
    
    def open_file(self):
        """Abrir archivo"""
        file_path = filedialog.askopenfilename(
            title="Abrir archivo de código",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.code_editor.delete('1.0', tk.END)
                self.code_editor.insert('1.0', content)
                self.update_line_numbers()
                self.current_file = file_path
                self.status_label.config(text=f"Archivo cargado: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{str(e)}")
    
    def save_file(self):
        """Guardar archivo"""
        if self.current_file:
            file_path = self.current_file
        else:
            file_path = filedialog.asksaveasfilename(
                title="Guardar archivo",
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
            )
        
        if file_path:
            try:
                content = self.code_editor.get('1.0', tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.current_file = file_path
                self.status_label.config(text=f"Archivo guardado: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{str(e)}")
    
    def compile_code(self):
        """Compilar el código en un hilo separado"""
        self.compile_btn.config(state='disabled', text="🔄 Compilando...")
        self.status_label.config(text="Compilando código...")
        
        # Ejecutar compilación en hilo separado para no bloquear la UI
        thread = threading.Thread(target=self._compile_thread)
        thread.daemon = True
        
        thread.start()
    
    def _compile_thread(self):
        """Hilo para ejecutar la compilación"""
        try:
            # Obtener código del editor
            code = self.code_editor.get('1.0', tk.END)
            
            # Detectar el ejecutable de Python correcto
            python_executable = self._get_python_executable()
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                           delete=False, encoding='utf-8') as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            # Ejecutar compilador con manejo robusto de codificación
            result = subprocess.run(
                [python_executable, 'main.py'],
                input=code,
                text=True,
                capture_output=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                encoding='utf-8',
                errors='replace',  # Reemplazar caracteres problemáticos
                timeout=30  # Timeout de 30 segundos
            )
            
            # Limpiar archivo temporal
            try:
                os.unlink(temp_file_path)
            except:
                pass
            
            # Actualizar UI en el hilo principal
            self.root.after(0, self._update_results, result)
            
        except subprocess.TimeoutExpired:
            self.root.after(0, self._compilation_error, "Timeout: La compilación tardó demasiado tiempo")
        except UnicodeDecodeError as e:
            self.root.after(0, self._compilation_error, f"Error de codificación: {e}")
        except Exception as e:
            self.root.after(0, self._compilation_error, str(e))
    
    def _get_python_executable(self):
        """Detectar el ejecutable de Python correcto"""
        # Intentar usar el Python del entorno virtual si existe
        venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   '.venv', 'Scripts', 'python.exe')
        
        if os.path.exists(venv_python):
            return venv_python
        
        # Fallback a python del sistema
        return 'python'
    
    def _compilation_error(self, error):
        """Manejar error de compilación"""
        self.compile_btn.config(state='normal', text="🚀 Compilar Código")
        self.status_label.config(text="Error en compilación")
        messagebox.showerror("Error de Compilación", f"Error al compilar:\n{error}")
    
    def _update_results(self, result):
        """Actualizar resultados en la UI"""
        self.compile_btn.config(state='normal', text="🚀 Compilar Código")
        
        # Combinar stdout y stderr de forma segura
        stdout_safe = result.stdout or ""
        stderr_safe = result.stderr or ""
        full_output = stdout_safe + stderr_safe
        
        # Si no hay salida, mostrar mensaje informativo
        if not full_output.strip():
            full_output = "[No hay salida del compilador]\n"
        
        # Actualizar salida completa
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert('1.0', full_output)
        
        # Procesar resultados
        self._process_results(full_output, result.returncode)
        
        # Actualizar status
        if result.returncode == 0:
            self.status_label.config(text="✅ Compilación exitosa")
        else:
            self.status_label.config(text="❌ Compilación con errores")
    
    def _process_results(self, output, return_code):
        """Procesar y mostrar resultados"""
        try:
            # Verificar que tenemos salida válida
            if not output or not output.strip():
                self._handle_empty_output()
                return
            
            lines = output.split('\n')
            
            # Extraer información clave
            errors = []
            warnings = []
            summary_info = []
            
            summary_info.append("=== RESUMEN DE COMPILACIÓN ===\n")
            
            # Buscar errores y advertencias
            in_errors = False
            in_warnings = False
            in_stats = False
            
            for line in lines:
                line = line.strip()
                
                if "ERRORES ENCONTRADOS" in line:
                    in_errors = True
                    in_warnings = False
                    in_stats = False
                    errors.append(line)
                    summary_info.append(f"🔴 {line}")
                    continue
                elif "ADVERTENCIAS" in line:
                    in_errors = False
                    in_warnings = True
                    in_stats = False
                    warnings.append(line)
                    summary_info.append(f"🟡 {line}")
                    continue
                elif "ESTADÍSTICAS" in line:
                    in_errors = False
                    in_warnings = False
                    in_stats = True
                    summary_info.append(f"\n📊 {line}")
                    continue
                elif line.startswith("==") or line.startswith("--"):
                    in_errors = False
                    in_warnings = False
                    in_stats = False
                    continue
                
                if in_errors and line and not line.startswith("="):
                    errors.append(f"  {line}")
                elif in_warnings and line and not line.startswith("="):
                    warnings.append(f"  {line}")
                elif in_stats and line and not line.startswith("="):
                    summary_info.append(f"  {line}")
            
            # Agregar información de fases
            for line in lines:
                if "Análisis léxico:" in line:
                    summary_info.append(f"✅ {line}")
                elif "Análisis sintáctico:" in line:
                    summary_info.append(f"✅ {line}")
                elif "Análisis semántico:" in line:
                    summary_info.append(f"📝 {line}")
            
            if return_code == 0:
                summary_info.append("\n🎉 COMPILACIÓN EXITOSA!")
            else:
                summary_info.append("\n❌ COMPILACIÓN FALLIDA")
            
            # Actualizar resumen
            self.summary_text.delete('1.0', tk.END)
            self.summary_text.insert('1.0', '\n'.join(summary_info))
            
            # Actualizar errores y advertencias
            error_summary = []
            if errors:
                error_summary.extend(["🔴 ERRORES:", ""] + errors + [""])
            if warnings:
                error_summary.extend(["🟡 ADVERTENCIAS:", ""] + warnings)
            
            if not error_summary:
                error_summary = ["✅ No se encontraron errores ni advertencias"]
            
            self.errors_text.delete('1.0', tk.END)
            self.errors_text.insert('1.0', '\n'.join(error_summary))
            
            # Cargar imagen AST con un pequeño retraso para asegurar que se haya generado
            self.root.after(200, self._load_ast_image)
            
        except Exception as e:
            # Manejo de errores en el procesamiento
            self._handle_processing_error(str(e))
    
    def _handle_empty_output(self):
        """Manejar caso de salida vacía"""
        message = "❌ No se recibió salida del compilador\n\nPosibles causas:\n- Error en el código fuente\n- Problema con el compilador\n- Error de codificación de caracteres"
        
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', message)
        
        self.errors_text.delete('1.0', tk.END)
        self.errors_text.insert('1.0', "⚠️ Sin información de errores disponible")
    
    def _handle_processing_error(self, error):
        """Manejar errores en el procesamiento de resultados"""
        message = f"❌ Error procesando resultados:\n{error}\n\nVerifica la salida completa en la pestaña 'Salida'"
        
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', message)
        
        self.errors_text.delete('1.0', tk.END)
        self.errors_text.insert('1.0', message)
    
    def _load_ast_image(self):
        """Cargar imagen del AST si existe"""
        ast_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ast.png')
        
        # Intentar cargar la imagen con reintentos para manejar problemas de timing
        max_attempts = 3
        for attempt in range(max_attempts):
            if os.path.exists(ast_path):
                try:
                    # Pequeña pausa para asegurar que el archivo esté completamente escrito
                    if attempt > 0:
                        import time
                        time.sleep(0.1)
                    
                    # Forzar la actualización del canvas
                    self.ast_canvas.update()
                    
                    # Cargar y redimensionar imagen
                    with Image.open(ast_path) as image:
                        # Obtener tamaño del canvas, usar valores por defecto si no está listo
                        canvas_width = self.ast_canvas.winfo_width()
                        canvas_height = self.ast_canvas.winfo_height()
                        
                        if canvas_width <= 1 or canvas_height <= 1:
                            # Canvas aún no está completamente inicializado
                            canvas_width, canvas_height = 400, 300
                        
                        # Crear una copia de la imagen para evitar problemas de cache
                        image_copy = image.copy()
                        image_copy.thumbnail((canvas_width - 20, canvas_height - 20), Image.Resampling.LANCZOS)
                        
                        self.ast_image = ImageTk.PhotoImage(image_copy)
                    
                    # Limpiar canvas y mostrar imagen
                    self.ast_canvas.delete("all")
                    
                    # Centrar la imagen en el canvas
                    x_center = max(canvas_width // 2, self.ast_image.width() // 2)
                    y_center = max(canvas_height // 2, self.ast_image.height() // 2)
                    
                    self.ast_canvas.create_image(
                        x_center, y_center,
                        image=self.ast_image,
                        anchor=tk.CENTER
                    )
                    
                    # Si llegamos aquí, la carga fue exitosa
                    return
                    
                except Exception as e:
                    if attempt == max_attempts - 1:  # Último intento
                        self.ast_canvas.delete("all")
                        self.ast_canvas.create_text(
                            200, 150,  # Usar coordenadas fijas
                            text=f"Error al cargar AST:\n{str(e)}",
                            anchor=tk.CENTER,
                            fill="red",
                            font=('Segoe UI', 10)
                        )
                        return
                    continue
            else:
                if attempt == max_attempts - 1:  # Último intento
                    self.ast_canvas.delete("all")
                    self.ast_canvas.create_text(
                        200, 150,  # Usar coordenadas fijas
                        text="AST no disponible\n(Se genera después de compilar)",
                        anchor=tk.CENTER,
                        fill="gray",
                        font=('Segoe UI', 10)
                    )
                    return
    
    def view_ast(self):
        """Ver AST en visor de imágenes del sistema y recargar en canvas"""
        ast_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ast.png')
        
        if os.path.exists(ast_path):
            try:
                # Primero recargar la imagen en el canvas
                self._load_ast_image()
                
                # Luego abrir en visor externo
                if os.name == 'nt':  # Windows
                    os.startfile(ast_path)
                else:  # Linux/Mac
                    subprocess.run(['xdg-open', ast_path])
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir la imagen:\n{str(e)}")
        else:
            messagebox.showwarning("Advertencia", "No hay imagen AST disponible. Compila el código primero.")
    
    def save_ast_image(self):
        """Guardar imagen AST"""
        ast_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ast.png')
        
        if os.path.exists(ast_path):
            save_path = filedialog.asksaveasfilename(
                title="Guardar imagen AST",
                defaultextension=".png",
                filetypes=[("Imágenes PNG", "*.png"), ("Todos los archivos", "*.*")]
            )
            
            if save_path:
                try:
                    import shutil
                    shutil.copy2(ast_path, save_path)
                    messagebox.showinfo("Éxito", f"Imagen guardada en:\n{save_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo guardar la imagen:\n{str(e)}")
        else:
            messagebox.showwarning("Advertencia", "No hay imagen AST disponible. Compila el código primero.")
    
    def clear_results(self):
        """Limpiar todos los resultados"""
        self.summary_text.delete('1.0', tk.END)
        self.errors_text.delete('1.0', tk.END)
        self.output_text.delete('1.0', tk.END)
        
        # Limpiar canvas AST
        self.ast_canvas.delete("all")
        self.ast_canvas.create_text(
            200, 150,  # Usar coordenadas fijas
            text="AST no disponible\n(Se genera después de compilar)",
            anchor=tk.CENTER,
            fill="gray",
            font=('Segoe UI', 10)
        )
        self.ast_image = None


def main():
    """Función principal"""
    try:
        root = tk.Tk()
        app = CompilerGUI(root)
        
        # Configurar el cierre de la aplicación
        def on_closing():
            root.quit()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Actualizar números de línea iniciales
        root.after(100, app.update_line_numbers)
        
        # Iniciar la aplicación
        root.mainloop()
        
    except ImportError as e:
        print("Error: Falta una dependencia necesaria.")
        print("Por favor instala Pillow: pip install Pillow")
        print(f"Error específico: {e}")
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")


if __name__ == "__main__":
    main()