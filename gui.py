import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import tempfile
import os
import threading
from PIL import Image, ImageTk
import webbrowser
import sys

class CompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Compilador - Analizador Léxico, Sintáctico y Semántico")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')
        
        self.current_file = None
        self.ast_image = None
        
        self.setup_styles()
        self.create_widgets()
        self.load_sample_code()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
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
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        title_label = ttk.Label(main_frame, 
                               text="MiniCompilador", 
                               style='Title.TLabel')
        title_label.pack(pady=(0, 10))
        
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True)
        
        left_panel = ttk.LabelFrame(top_frame, text="Editor de Código", padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        editor_toolbar = ttk.Frame(left_panel)
        editor_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(editor_toolbar, text="Abrir", 
                  command=self.open_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(editor_toolbar, text="Guardar", 
                  command=self.save_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(editor_toolbar, text="Limpiar", 
                  command=self.clear_editor).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(editor_toolbar, text="Ejemplo", 
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
        
        right_panel = ttk.LabelFrame(top_frame, text="Resultados", padding=10)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        compile_frame = ttk.Frame(right_panel)
        compile_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.compile_btn = ttk.Button(compile_frame, text="Compilar Código", 
                                     command=self.compile_code, style='TButton')
        self.compile_btn.pack(fill=tk.X)
        
        self.status_label = ttk.Label(compile_frame, text="Listo para compilar", 
                                     style='Section.TLabel')
        self.status_label.pack(pady=(5, 0))
        
        self.results_notebook = ttk.Notebook(right_panel)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)
        
        summary_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(summary_frame, text="Resumen")
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, 
                                                     font=('Segoe UI', 9),
                                                     bg='#2d2d2d', fg='#ffffff',
                                                     height=8)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        errors_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(errors_frame, text="Errores")
        
        self.errors_text = scrolledtext.ScrolledText(errors_frame, 
                                                    font=('Segoe UI', 9),
                                                    bg='#2d2d2d', fg='#ffffff',
                                                    height=8)
        self.errors_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ast_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(ast_frame, text="AST")
        
        ast_controls = ttk.Frame(ast_frame)
        ast_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(ast_controls, text="Ver AST", 
                  command=self.view_ast).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(ast_controls, text="Guardar PNG", 
                  command=self.save_ast_image).pack(side=tk.LEFT)
        
        self.ast_canvas = tk.Canvas(ast_frame, bg='white')
        self.ast_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Nueva pestaña para código ASM
        asm_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(asm_frame, text="Código ASM")
        
        asm_controls = ttk.Frame(asm_frame)
        asm_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(asm_controls, text="Guardar ASM", 
                  command=self.save_asm_code).pack(side=tk.LEFT, padx=(0, 5))
        
        self.asm_text = scrolledtext.ScrolledText(asm_frame, 
                                                 font=('Consolas', 9),
                                                 bg='#1e1e1e', fg='#dcdcdc',
                                                 height=15)
        self.asm_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Nueva pestaña para simulación ASM
        simulation_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(simulation_frame, text="Simulación")
        
        sim_controls = ttk.Frame(simulation_frame)
        sim_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(sim_controls, text="Simular Ejecución", 
                  command=self.simulate_asm).pack(side=tk.LEFT, padx=(0, 5))
        
        self.simulation_text = scrolledtext.ScrolledText(simulation_frame, 
                                                        font=('Consolas', 9),
                                                        bg='#0d1117', fg='#58a6ff',
                                                        height=15)
        self.simulation_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        output_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(output_frame, text="Salida")
        
        self.output_text = scrolledtext.ScrolledText(output_frame, 
                                                    font=('Consolas', 9),
                                                    bg='#1e1e1e', fg='#dcdcdc',
                                                    height=15)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def update_line_numbers(self, event=None):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        
        lines = self.code_editor.get('1.0', tk.END).count('\n')
        line_numbers_string = '\n'.join(str(i) for i in range(1, lines + 1))
        
        self.line_numbers.insert('1.0', line_numbers_string)
        self.line_numbers.config(state='disabled')
    
    def load_sample_code(self):
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
        # Limpiar el editor
        if messagebox.askyesno("Confirmar", "¿Estás seguro de que quieres limpiar el editor?"):
            self.code_editor.delete('1.0', tk.END)
            self.update_line_numbers()
            self.clear_results()
            self.status_label.config(text="Editor limpiado")
    
    def open_file(self):
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
        self.compile_btn.config(state='disabled', text="Compilando...")
        self.status_label.config(text="Compilando código...")
        
        thread = threading.Thread(target=self._compile_thread)
        thread.daemon = True
        
        thread.start()
    
    def _compile_thread(self):
        # Hilo para ejecutar la compilación
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
                errors='ignore',  # Ignorar caracteres problemáticos
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
        # Detectar ejecutable de Python correcto
        # Intentar usar el Python del entorno virtual si existe
        venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   '.venv', 'Scripts', 'python.exe')
        
        if os.path.exists(venv_python):
            return venv_python
        
        # Fallback a python del sistema
        return 'python'
    
    def _compilation_error(self, error):
        # Manejar error de compilación
        self.compile_btn.config(state='normal', text="🚀 Compilar Código")
        self.status_label.config(text="Error de compilación")
        
        # Actualizar las áreas de texto con el error
        error_message = f"ERROR DE COMPILACIÓN:\n{error}"
        
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', error_message)
        
        self.errors_text.delete('1.0', tk.END)
        self.errors_text.insert('1.0', f"ERROR INTERNO:\n{error}")
        
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert('1.0', f"Error interno del compilador:\n{error}")
        
        # Limpiar AST y ASM
        self._clear_ast_and_asm()
        
        # Mostrar mensaje popup (opcional)
        messagebox.showerror("Error de Compilación", f"Error al compilar:\n{error}")
    
    def _update_results(self, result):
        # Actualizar resultados en la UI
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
        
        # Procesar resultados y obtener estado
        compilation_status = self._process_results(full_output, result.returncode)
        
        # Actualizar status basado en el análisis de la salida
        # Debug temporal para diagnosticar el problema
        with open("debug_gui_output.txt", "w", encoding="utf-8") as f:
            f.write(f"Return code: {result.returncode}\n")
            f.write(f"Full output length: {len(full_output)}\n")
            f.write(f"Contains '✓ COMPILACIÓN EXITOSA': {'✓ COMPILACIÓN EXITOSA' in full_output}\n")
            f.write(f"Contains 'X COMPILACIÓN FALLIDA': {'X COMPILACIÓN FALLIDA' in full_output}\n")
            f.write(f"Full output:\n{full_output}\n")
        
        # Usar return code como indicador principal
        if result.returncode == 0:
            if "✓ COMPILACIÓN EXITOSA" in full_output:
                self.status_label.config(text="Compilación EXITOSA")
            else:
                self.status_label.config(text="Compilación exitosa")
        else:
            # Return code != 0 indica error
            if "X COMPILACIÓN FALLIDA" in full_output:
                self.status_label.config(text="Compilación FALLIDA")
            elif "sintáctico: FALLIDO" in full_output:
                self.status_label.config(text="Error sintáctico")
            else:
                self.status_label.config(text="Compilación FALLIDA")
    
    def _process_results(self, output, return_code):
        # Procesar y mostrar resultados
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
            
            summary_info.append("=== RESUMEN DE COMPILACION ===\n")
            
            # Buscar errores y advertencias
            in_errors = False
            in_warnings = False
            in_stats = False
            
            for line in lines:
                line = line.strip()
                
                # Detectar errores sintácticos específicos
                if "Errores sintácticos encontrados:" in line:
                    in_errors = True
                    in_warnings = False
                    in_stats = False
                    errors.append("ERRORES SINTÁCTICOS:")
                    summary_info.append(f"{line}")
                    continue
                elif "ERRORES ENCONTRADOS" in line:
                    in_errors = True
                    in_warnings = False
                    in_stats = False
                    errors.append(line)
                    summary_info.append(f"{line}")
                    continue
                elif "ADVERTENCIAS" in line:
                    in_errors = False
                    in_warnings = True
                    in_stats = False
                    warnings.append(line)
                    summary_info.append(f"{line}")
                    continue
                elif "ESTADISTICAS" in line:
                    in_errors = False
                    in_warnings = False
                    in_stats = True
                    summary_info.append(f"\n{line}")
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
            
            # Detectar estado de compilación y fases
            compilation_success = False
            compilation_failed = False
            syntax_failed = False
            
            for line in lines:
                # Detectar estado final de compilación
                if "✓ COMPILACIÓN EXITOSA" in line:
                    compilation_success = True
                    summary_info.append(f"{line}")
                elif "X COMPILACIÓN FALLIDA" in line:
                    compilation_failed = True
                    summary_info.append(f"{line}")
                elif "FALLIDO" in line and "sintáctico" in line:
                    syntax_failed = True
                    summary_info.append(f"{line}")
                # Detectar fases
                elif "Análisis léxico:" in line:
                    summary_info.append(f"{line}")
                elif "Análisis sintáctico:" in line and "FALLIDO" not in line:
                    summary_info.append(f"{line}")
                elif "Análisis semántico:" in line:
                    summary_info.append(f"{line}")
            
            # Determinar estado final
            if compilation_success:
                summary_info.append("\nCOMPILACIÓN EXITOSA")
                self.compilation_successful = True
            elif compilation_failed or syntax_failed:
                summary_info.append("\nCOMPILACIÓN FALLIDA")
                self.compilation_successful = False
            elif return_code != 0:
                summary_info.append("\n⚠️ COMPILACIÓN CON ERRORES")
                self.compilation_successful = False
            else:
                # Si no hay indicadores claros, usar return code
                if return_code == 0:
                    summary_info.append("\n✅ COMPILACIÓN EXITOSA")
                    self.compilation_successful = True
                else:
                    summary_info.append("\n❌ ERROR EN COMPILACIÓN")
                    self.compilation_successful = False
            
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
            
            # Solo cargar AST y ASM si la compilación fue exitosa
            if self.compilation_successful:
                # Cargar imagen AST con un pequeño retraso para asegurar que se haya generado
                self.root.after(200, self._load_ast_image)
                
                # Cargar código ASM si fue generado exitosamente
                self.root.after(100, self._load_asm_code)
            else:
                # Limpiar AST y ASM si la compilación falló
                self._clear_ast_and_asm()
            
        except Exception as e:
            # Manejo de errores en el procesamiento
            self._handle_processing_error(str(e))
    
    def _handle_empty_output(self):
        # Manejar caso de salida vacía
        message = "❌ No se recibió salida del compilador\n\nPosibles causas:\n- Error en el código fuente\n- Problema con el compilador\n- Error de codificación de caracteres"
        
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', message)
        
        self.errors_text.delete('1.0', tk.END)
        self.errors_text.insert('1.0', "Sin información de errores disponible")
    
    def _handle_processing_error(self, error):
        # Manejar errores en procesamiento
        message = f"❌ Error procesando resultados:\n{error}\n\nVerifica la salida completa en la pestaña 'Salida'"
        
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', message)
        
        self.errors_text.delete('1.0', tk.END)
        self.errors_text.insert('1.0', message)
    
    def _load_ast_image(self):
        # Cargar imagen del AST si existe
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
        # Ver AST en visor de imágenes
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
    
    def _load_asm_code(self):
        asm_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output.s')
        
        if os.path.exists(asm_path):
            try:
                with open(asm_path, 'r', encoding='utf-8') as f:
                    asm_content = f.read()
                
                # Actualizar el área de texto ASM
                self.asm_text.delete('1.0', tk.END)
                self.asm_text.insert('1.0', asm_content)
                
            except Exception as e:
                self.asm_text.delete('1.0', tk.END)
                self.asm_text.insert('1.0', f"Error al cargar código ASM:\n{str(e)}")
        else:
            # Si no hay archivo ASM, mostrar mensaje
            self.asm_text.delete('1.0', tk.END)
            self.asm_text.insert('1.0', "Código ASM no disponible\n(Se genera solo después de una compilación exitosa)")
    
    def _clear_ast_and_asm(self):
        # Limpiar código ASM
        self.asm_text.delete('1.0', tk.END)
        self.asm_text.insert('1.0', "Código ASM no disponible\n(La compilación falló)")
        
        # Limpiar canvas AST
        self.ast_canvas.delete("all")
        self.ast_canvas.create_text(
            200, 150,  # Usar coordenadas fijas
            text="AST no disponible\n(La compilación falló)",
            anchor=tk.CENTER,
            fill="red",
            font=('Segoe UI', 10)
        )
        self.ast_image = None

    def clear_results(self):
        self.summary_text.delete('1.0', tk.END)
        self.errors_text.delete('1.0', tk.END)
        self.output_text.delete('1.0', tk.END)
        
        # Limpiar código ASM
        self.asm_text.delete('1.0', tk.END)
        self.asm_text.insert('1.0', "Código ASM no disponible\n(Se genera después de compilar)")
        
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
    
    def save_asm_code(self):
        asm_content = self.asm_text.get('1.0', tk.END).strip()
        
        if not asm_content or asm_content == "Código ASM no disponible":
            messagebox.showwarning("Advertencia", "No hay código ASM para guardar. Compila el código primero.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Guardar código ASM",
            defaultextension=".s",
            filetypes=[("Archivos ASM", "*.s"), ("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(asm_content)
                messagebox.showinfo("Éxito", f"Código ASM guardado en:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{str(e)}")
    
    def simulate_asm(self):
        try:
            # Limpiar la pestaña de simulación
            self.simulation_text.delete('1.0', tk.END)
            self.simulation_text.insert(tk.END, "🔄 Compilando código para simulación...\n\n")
            
            # Obtener el código actual del editor
            current_code = self.code_editor.get('1.0', tk.END).strip()
            if not current_code:
                self.simulation_text.delete('1.0', tk.END)
                self.simulation_text.insert(tk.END, "❌ No hay código para simular.\nEscribe código C en el editor primero.")
                return
            
            # Compilar el código actual para generar ASM fresco
            python_exe = self._get_python_executable()
            
            # Crear archivo temporal con el código actual
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(current_code)
                temp_file_path = temp_file.name
            
            try:
                # Ejecutar compilación con generación forzada de ASM
                result = subprocess.run(
                    [python_exe, 'main.py', temp_file_path, '--force-asm'],
                    input="",  # Sin entrada adicional
                    text=True,
                    capture_output=True,
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    encoding='utf-8',
                    errors='ignore',
                    timeout=30
                )
                
                # Limpiar archivo temporal
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                
                # Verificar si la compilación fue exitosa
                if result.returncode != 0:
                    self.simulation_text.delete('1.0', tk.END)
                    self.simulation_text.insert(tk.END, f"Error de compilación:\n{result.stdout}\n{result.stderr}")
                    return
                
                # Leer el archivo ASM generado
                asm_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output.s')
                if not os.path.exists(asm_file_path):
                    self.simulation_text.delete('1.0', tk.END)
                    self.simulation_text.insert(tk.END, "No se generó archivo ASM.\nLa compilación no produjo código ensamblador.")
                    return
                
                # Leer el contenido ASM
                with open(asm_file_path, 'r', encoding='utf-8') as f:
                    asm_content = f.read()
                
                # Actualizar también la pestaña ASM con el código fresco
                self.asm_text.delete('1.0', tk.END)
                self.asm_text.insert('1.0', asm_content)
                
                # Simular la ejecución del ASM generado
                user_code = self.code_editor.get('1.0', tk.END).strip()
                simulation_result = self.simulate_asm_execution(asm_content, user_code)
                
                # Mostrar resultado en la pestaña
                self.simulation_text.delete('1.0', tk.END)
                self.simulation_text.insert(tk.END, simulation_result)
                
                # Cambiar a la pestaña de simulación
                self.results_notebook.select(3)  # Índice de la pestaña de simulación
                
            except subprocess.TimeoutExpired:
                self.simulation_text.delete('1.0', tk.END)
                self.simulation_text.insert(tk.END, "Timeout: La compilación tardó demasiado tiempo")
            except Exception as e:
                self.simulation_text.delete('1.0', tk.END)
                self.simulation_text.insert(tk.END, f"Error durante la compilación:\n{str(e)}")
            
        except Exception as e:
            self.simulation_text.delete('1.0', tk.END)
            self.simulation_text.insert(tk.END, f"Error durante la simulación:\n{str(e)}")
    
    def simulate_asm_execution(self, asm_content, user_code=""):
        output = []
        output.append("SIMULADOR DE EJECUCIÓN ASM")
        output.append("=" * 40)
        
        try:
            variables = {}
            functions = []
            
            # Extraer nombres de variables del código fuente del usuario
            var_names_map = self.extract_variable_names(user_code)
            global_vars = self.extract_global_variables(user_code)
            
            # Extraer variables de la sección .data
            output.append("Variables globales encontradas:")
            lines = asm_content.split('\n')
            
            # Buscar variables globales antes de section .data
            for i, line in enumerate(lines):
                line = line.strip()
                # Las variables globales aparecen antes de "section .data"
                if line == 'section .data':
                    break
                # Buscar líneas con formato "nombre: dq valor"
                if ':' in line and 'dq' in line:
                    var_name = line.split(':')[0].strip()
                    if not var_name.startswith('msg') and not var_name.startswith('newline') and not var_name.startswith('buffer'):
                        # Extraer valor inicial
                        if 'dq' in line:
                            value_part = line.split('dq')[1].strip()
                            try:
                                value = int(value_part)
                            except:
                                value = 0
                        else:
                            value = 0
                        variables[var_name] = value
                        # Usar nombre real de variables globales si está disponible
                        display_name = var_name if var_name in global_vars else var_name
                        output.append(f"  - {display_name} = {value}")
            
            if not variables:
                output.append("  (No se encontraron variables globales)")
            else:
                output.append("  NOTA: Variables globales son diferentes de las locales con el mismo nombre")
            
            # Extraer funciones definidas
            output.append("\nFunciones encontradas:")
            for line in lines:
                line = line.strip()
                if line.endswith(':') and not line.startswith('.') and not line.startswith('section'):
                    func_name = line[:-1]
                    if func_name not in ['_start', 'print_number']:
                        functions.append(func_name)
                        output.append(f"  - {func_name}()")
            
            if not variables and not functions:
                output.append("  (No se encontraron variables globales)")
            
            # Buscar la función main y simular su ejecución
            output.append("\nSimulando ejecución de función main:")
            
            main_start = asm_content.find('main:')
            if main_start == -1:
                output.append("No se encontró la función main")
                return "\n".join(output)
            
            main_section = asm_content[main_start:]
            # Buscar el final de main (siguiente función o print_number)
            main_end = -1
            for func in functions + ['print_number', '_start']:
                if func != 'main':
                    pos = main_section.find(f'\n{func}:')
                    if pos != -1 and (main_end == -1 or pos < main_end):
                        main_end = pos
            
            if main_end != -1:
                main_section = main_section[:main_end]
            
            # Analizar instrucciones de main
            main_lines = main_section.split('\n')
            rax = 0
            rbx = 0
            rcx = 0
            rdx = 0
            rdi = 0
            stack = []
            local_vars = {}  # Variables locales con valores asignados
            declared_vars = set()  # Variables declaradas pero no inicializadas
            instruction_count = 0
            
            for line in main_lines:
                line = line.strip()
                if not line or line.startswith(';') or line.endswith(':'):
                    continue
                
                instruction_count += 1
                if instruction_count > 50:  # Limitar para evitar bucles infinitos
                    output.append("  ... (más de 50 instrucciones, truncando simulación)")
                    break
                
                # Detectar asignaciones directas con mov dword [rbp-offset], valor
                if line.startswith('mov dword [rbp-') and '], ' in line:
                    try:
                        # Extraer offset y valor
                        offset_part = line.split('[rbp-')[1].split(']')[0]
                        offset = offset_part
                        value_part = line.split('], ')[1].strip()
                        
                        if value_part.isdigit() or (value_part.startswith('-') and value_part[1:].isdigit()):
                            value = int(value_part)
                            var_name = var_names_map.get(offset, f'var_{offset}')
                            local_vars[offset] = value
                            output.append(f"  mov dword [rbp-{offset}], {value} → {var_name} = {value}")
                            continue
                    except (ValueError, IndexError):
                        pass
                
                # Instrucciones MOV regulares
                if line.startswith('mov rax,') or line.startswith('mov rax, '):
                    value = line.split(',', 1)[1].strip()
                    if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                        rax = int(value)
                        output.append(f"  mov rax, {value} → rax = {rax}")
                    elif value.startswith('[rel ') and value.endswith(']'):
                        var_name = value[5:-1]
                        if var_name in variables:
                            rax = variables[var_name]
                            output.append(f"  mov rax, [rel {var_name}] → rax = {rax}")
                        else:
                            output.append(f"  mov rax, [rel {var_name}] → rax = 0 (variable no inicializada)")
                            rax = 0
                    elif value.startswith('[rbp-') and value.endswith(']'):
                        # Variable local en el stack
                        offset = value[5:-1]  # Extraer número después de rbp-
                        var_name = var_names_map.get(offset, f'var_{offset}')
                        if offset in local_vars:
                            rax = local_vars[offset]
                            output.append(f"  mov rax, [rbp-{offset}] → rax = {rax} ({var_name})")
                        else:
                            # Variable no inicializada - contiene valor basura
                            declared_vars.add(offset)  # Marcar como declarada pero no inicializada
                            rax = 0  # Simular como 0 pero marcar como no inicializada
                            output.append(f"  mov rax, [rbp-{offset}] → rax = ? ({var_name} NO INICIALIZADA - valor basura)")
                    elif value == '0':
                        rax = 0
                        output.append(f"  mov rax, 0 → rax = 0")
                        
                elif line.startswith('mov eax,') or line.startswith('mov eax, '):
                    value = line.split(',', 1)[1].strip()
                    if value.startswith('dword [rbp-') and value.endswith(']'):
                        # Variable local en el stack (32 bits)
                        offset = value.split('[rbp-')[1].split(']')[0]
                        var_name = var_names_map.get(offset, f'var_{offset}')
                        if offset in local_vars:
                            rax = local_vars[offset]  # eax es parte de rax
                            output.append(f"  mov eax, dword [rbp-{offset}] → eax = {rax} ({var_name})")
                        else:
                            # Variable no inicializada - contiene valor basura
                            declared_vars.add(offset)  # Marcar como declarada pero no inicializada
                            rax = 0  # Simular como 0 pero marcar como no inicializada
                            output.append(f"  mov eax, dword [rbp-{offset}] → eax = ? ({var_name} NO INICIALIZADA - valor basura)")
                    elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                        rax = int(value)
                        output.append(f"  mov eax, {value} → eax = {rax}")
                        
                elif line.startswith('mov [rbp-') and ', rax' in line:
                    # Guardar en variable local
                    offset = line.split('[rbp-')[1].split(']')[0]
                    local_vars[offset] = rax
                    # Dar nombres más amigables a las variables
                    var_name = var_names_map.get(offset, f'var_{offset}')
                    output.append(f"  mov [rbp-{offset}], rax → {var_name} = {rax}")
                
                elif line.startswith('mov dword [rbp-') and ', eax' in line:
                    # Guardar en variable local (32 bits)
                    offset = line.split('[rbp-')[1].split(']')[0]
                    local_vars[offset] = rax  # eax es parte de rax
                    var_name = var_names_map.get(offset, f'var_{offset}')
                    output.append(f"  mov dword [rbp-{offset}], eax → {var_name} = {rax}")
                        
                elif line.startswith('push rax') or line.startswith('push rax '):
                    stack.append(rax)
                    output.append(f"  push rax → pila = {stack}")
                    
                elif line.startswith('mov rcx,') or line.startswith('mov rcx, '):
                    value = line.split(',', 1)[1].strip()
                    if value == 'rax':
                        rcx = rax
                        output.append(f"  mov rcx, rax → rcx = {rcx}")
                    elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                        rcx = int(value)
                        output.append(f"  mov rcx, {value} → rcx = {rcx}")
                    elif value.startswith('[rel ') and value.endswith(']'):
                        var_name = value[5:-1]
                        if var_name in variables:
                            rcx = variables[var_name]
                            output.append(f"  mov rcx, [rel {var_name}] → rcx = {rcx}")
                        else:
                            output.append(f"  mov rcx, [rel {var_name}] → rcx = 0 (variable no inicializada)")
                            rcx = 0
                
                elif line.startswith('mov rdx,') or line.startswith('mov rdx, '):
                    value = line.split(',', 1)[1].strip()
                    if value == 'rax':
                        rdx = rax
                        output.append(f"  mov rdx, rax → rdx = {rdx}")
                    elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                        rdx = int(value)
                        output.append(f"  mov rdx, {value} → rdx = {rdx}")
                    elif value.startswith('[rel ') and value.endswith(']'):
                        var_name = value[5:-1]
                        if var_name in variables:
                            rdx = variables[var_name]
                            output.append(f"  mov rdx, [rel {var_name}] → rdx = {rdx}")
                        else:
                            output.append(f"  mov rdx, [rel {var_name}] → rdx = 0 (variable no inicializada)")
                            rdx = 0
                        
                elif line.startswith('mov rbx,') or line.startswith('mov rbx, '):
                    value = line.split(',', 1)[1].strip()
                    if value == 'rax':
                        rbx = rax
                        output.append(f"  mov rbx, rax → rbx = {rbx}")
                    elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                        rbx = int(value)
                        output.append(f"  mov rbx, {value} → rbx = {rbx}")
                    elif value.startswith('[rel ') and value.endswith(']'):
                        var_name = value[5:-1]
                        if var_name in variables:
                            rbx = variables[var_name]
                            output.append(f"  mov rbx, [rel {var_name}] → rbx = {rbx}")
                        else:
                            output.append(f"  mov rbx, [rel {var_name}] → rbx = 0 (variable no inicializada)")
                            rbx = 0
                        
                elif line.startswith('pop rax') or line.startswith('pop rax '):
                    if stack:
                        rax = stack.pop()
                        output.append(f"  pop rax → rax = {rax}, pila = {stack}")
                    else:
                        output.append(f"  pop rax → pila vacía, rax = {rax}")
                        
                # Operaciones aritméticas
                elif line.startswith('add rax, rbx') or line.startswith('add rax,rbx'):
                    result = rax + rbx
                    output.append(f"  add rax, rbx → {rax} + {rbx} = {result}")
                    rax = result
                
                elif line.startswith('imul rax, rbx') or line.startswith('imul rax,rbx'):
                    result = rax * rbx
                    output.append(f"  imul rax, rbx → {rax} * {rbx} = {result}")
                    rax = result
                
                elif line.startswith('add eax, dword [rbp-') and ']' in line:
                    # Suma con variable local (32 bits)
                    offset = line.split('[rbp-')[1].split(']')[0]
                    var_name = var_names_map.get(offset, f'var_{offset}')
                    if offset in local_vars:
                        operand = local_vars[offset]
                        result = rax + operand
                        output.append(f"  add eax, dword [rbp-{offset}] → eax = {rax} + {operand} = {result}")
                        rax = result
                    else:
                        output.append(f"  add eax, dword [rbp-{offset}] → {var_name} no inicializada, asumiendo 0")
                        local_vars[offset] = 0
                    
                elif line.startswith('imul rax, rbx') or line.startswith('imul rax,rbx'):
                    result = rax * rbx
                    output.append(f"  imul rax, rbx → {rax} * {rbx} = {result}")
                    rax = result
                    
                elif line.startswith('sub rax, rbx') or line.startswith('sub rax,rbx'):
                    result = rax - rbx
                    output.append(f"  sub rax, rbx → {rax} - {rbx} = {result}")
                    rax = result
                    
                elif line.startswith('mov [rel ') and (', rax' in line or ',rax' in line):
                    var_part = line.split('[rel ')[1].split(']')[0]
                    variables[var_part] = rax
                    output.append(f"  mov [rel {var_part}], rax → {var_part} = {rax}")
                
                # Llamadas a funciones
                elif line.startswith('call '):
                    func_name = line.split('call ')[1].strip()
                    if func_name in functions:
                        output.append(f"  call {func_name} → llamando función {func_name}")
                        # Simular ejecución dinámica de la función basándose en su contenido ASM
                        # Buscar valores literales en el código fuente para funciones con parámetros literales
                        literal_params = self.extract_literal_parameters(user_code, func_name)
                        if literal_params is None:
                            # Verificar si es error de tipos
                            import re
                            pattern = rf'{func_name}\s*\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)'
                            matches = re.findall(pattern, user_code)
                            
                            if matches:
                                output.append(f"    → ERROR DE TIPOS: Los parámetros pasados a {func_name} no coinciden con los tipos declarados")
                                rax = 0  # Valor por defecto en caso de error
                            else:
                                # Usar valores de registros como antes
                                func_result = self.simulate_function_call(func_name, rcx, rdx, asm_content)
                                rax = func_result
                                output.append(f"    → resultado: {func_name}({rcx}, {rdx}) = {rax}")
                        else:
                            # Usar parámetros literales del código fuente
                            param1, param2 = literal_params[0], literal_params[1] if len(literal_params) > 1 else 0
                            func_result = self.simulate_function_call(func_name, param1, param2, asm_content)
                            rax = func_result
                            output.append(f"    → resultado: {func_name}({param1}, {param2}) = {rax}")
                    else:
                        output.append(f"  call {func_name} → llamada a función del sistema")
                
                # Otras instrucciones importantes
                elif line.startswith('push ') and not line.startswith('push rax'):
                    value = line.split('push ')[1].strip()
                    if value.isdigit():
                        stack.append(int(value))
                        output.append(f"  push {value} → pila = {stack}")
                elif line.startswith('mov rdi,') or line.startswith('mov rdi, '):
                    value = line.split(',', 1)[1].strip()
                    if value.isdigit():
                        rdi = int(value)
                        output.append(f"  mov rdi, {value} → rdi = {rdi}")
                elif 'ret' in line:
                    output.append(f"  ret → retornando {rax}")
                    break
            
            # Comentar la sección de estado final de registros
            # output.append(f"\nESTADO FINAL DE REGISTROS:")
            # output.append(f"  rax = {rax}")
            # if rbx != 0:
            #     output.append(f"  rbx = {rbx}")
            # if rdi != 0:
            #     output.append(f"  rdi = {rdi}")
            
            output.append(f"\nVARIABLES GLOBALES FINALES:")
            if variables:
                for var_name, value in variables.items():
                    if not var_name.startswith('msg') and not var_name.startswith('newline') and not var_name.startswith('buffer'):
                        output.append(f"  {var_name} = {value}")
            else:
                output.append("  (No hay variables globales modificadas)")
            
            # Mostrar variables locales si existen
            if local_vars or declared_vars:
                output.append(f"\nVARIABLES LOCALES FINALES:")
                
                # Mostrar variables inicializadas
                for offset, value in local_vars.items():
                    var_name = var_names_map.get(offset, f'var_{offset}')
                    output.append(f"  {var_name} ([rbp-{offset}]) = {value}")
                
                # Mostrar variables declaradas pero no inicializadas
                for offset in declared_vars:
                    if offset not in local_vars:  # Solo si no fue inicializada después
                        var_name = var_names_map.get(offset, f'var_{offset}')
                        output.append(f"  {var_name} ([rbp-{offset}]) = ? (NO INICIALIZADA - valor basura)")
            
            output.append(f"\nEl programa mostraría: 'Resultado: {rax}'")
            
            # Información adicional sobre problemas detectados
            if instruction_count <= 5:
                output.append(f"\nOBSERVACIÓN: La función main tiene muy pocas instrucciones ({instruction_count}).")
                output.append("   Esto puede indicar que el generador de código no está")
                output.append("   procesando correctamente el código fuente.")
            
        except Exception as e:
            output.append(f"Error durante la simulación: {e}")
            import traceback
            output.append(f"Detalles: {traceback.format_exc()}")
        
        return "\n".join(output)
    
    def extract_variable_names(self, user_code):
        var_names = {}
        lines = user_code.split('\n')
        offset_counter = 8  # Empezar en rbp-8
        in_main = False
        
        for line in lines:
            line = line.strip()
            
            # Detectar si estamos dentro de main
            if 'int main(' in line:
                in_main = True
                continue
            elif line.startswith('}') and in_main:
                in_main = False
                continue
            
            # Solo procesar declaraciones dentro de main para variables locales
            if in_main and line.startswith('int ') and ';' in line:
                # Extraer nombre de variable
                var_part = line[4:].split(';')[0].strip()
                if '=' in var_part:
                    var_name = var_part.split('=')[0].strip()
                else:
                    var_name = var_part.strip()
                
                # Mapear offset a nombre real
                var_names[str(offset_counter)] = var_name
                offset_counter += 8  # Siguiente offset
        
        # Si no se encontraron variables en el código, usar nombres por defecto
        if not var_names:
            var_names = {'8': 'var1', '16': 'var2', '24': 'var3', '32': 'var4'}
        
        return var_names
    
    def simulate_function_call(self, func_name, param1, param2, asm_content):
        try:
            # Buscar la función en el código ASM
            func_start = asm_content.find(f'{func_name}:')
            if func_start == -1:
                return 0  # Función no encontrada
            
            # Extraer el contenido de la función
            func_section = asm_content[func_start:]
            # Buscar el final de la función (siguiente función o final)
            func_end = -1
            lines = func_section.split('\n')[1:]  # Excluir la línea del label
            
            # Simular registros locales de la función
            local_rax = 0
            local_rbx = 0
            local_rcx = param1  # Primer parámetro
            local_rdx = param2  # Segundo parámetro
            local_stack = {}    # Stack local de la función [rbp-offset]
            local_push_stack = []  # Pila para push/pop
            
            for line in lines:
                line = line.strip()
                
                # Fin de función
                if line == 'ret' or line.startswith('ret '):
                    return local_rax
                
                # Nueva función (fin de la actual)
                if line.endswith(':') and not line.startswith('.'):
                    break
                
                # Ignorar líneas vacías, comentarios y setup de función
                if not line or line.startswith(';') or line in ['push rbp', 'mov rbp, rsp', 'pop rbp'] or line.startswith('sub rsp,') or line.startswith('add rsp,'):
                    continue
                
                # Operaciones con stack local [rbp-offset]
                if line.startswith('mov [rbp-') and ', rcx' in line:
                    # mov [rbp-8], rcx - guardar primer parámetro en stack
                    offset = line.split('[rbp-')[1].split(']')[0]
                    local_stack[offset] = local_rcx
                
                elif line.startswith('mov [rbp-') and ', rdx' in line:
                    # mov [rbp-16], rdx - guardar segundo parámetro en stack
                    offset = line.split('[rbp-')[1].split(']')[0]
                    local_stack[offset] = local_rdx
                
                elif line.startswith('mov rax, [rbp-') and ']' in line:
                    # mov rax, [rbp-8] - cargar desde stack local
                    offset = line.split('[rbp-')[1].split(']')[0]
                    if offset in local_stack:
                        local_rax = local_stack[offset]
                
                elif line.startswith('mov rbx, [rbp-') and ']' in line:
                    # mov rbx, [rbp-16] - cargar desde stack local
                    offset = line.split('[rbp-')[1].split(']')[0]
                    if offset in local_stack:
                        local_rbx = local_stack[offset]
                
                # Procesar instrucciones básicas de registros
                elif line.startswith('mov rax,') or line.startswith('mov rax, '):
                    value = line.split(',', 1)[1].strip()
                    if value == 'rcx':
                        local_rax = local_rcx
                    elif value == 'rdx':
                        local_rax = local_rdx
                    elif value == 'rbx':
                        local_rax = local_rbx
                    elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                        local_rax = int(value)
                
                elif line.startswith('mov rbx,') or line.startswith('mov rbx, '):
                    value = line.split(',', 1)[1].strip()
                    if value == 'rcx':
                        local_rbx = local_rcx
                    elif value == 'rdx':
                        local_rbx = local_rdx
                    elif value == 'rax':
                        local_rbx = local_rax
                    elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                        local_rbx = int(value)
                
                # Operaciones push/pop
                elif line.startswith('push rax'):
                    local_push_stack.append(local_rax)
                
                elif line.startswith('pop rax'):
                    if local_push_stack:
                        local_rax = local_push_stack.pop()
                
                # Operaciones aritméticas
                elif line.startswith('add rax, rbx') or line.startswith('add rax,rbx'):
                    local_rax = local_rax + local_rbx
                
                elif line.startswith('imul rax, rbx') or line.startswith('imul rax,rbx'):
                    local_rax = local_rax * local_rbx
                
                elif line.startswith('sub rax, rbx') or line.startswith('sub rax,rbx'):
                    local_rax = local_rax - local_rbx
                
                elif line.startswith('add rax, rcx') or line.startswith('add rax,rcx'):
                    local_rax = local_rax + local_rcx
                
                elif line.startswith('imul rax, rcx') or line.startswith('imul rax,rcx'):
                    local_rax = local_rax * local_rcx
                
                elif line.startswith('add rax, rdx') or line.startswith('add rax,rdx'):
                    local_rax = local_rax + local_rdx
                
                elif line.startswith('imul rax, rdx') or line.startswith('imul rax,rdx'):
                    local_rax = local_rax * local_rdx
            
            return local_rax
            
        except Exception:
            return param1 + param2  # Fallback: asumir suma si hay error
    
    def extract_global_variables(self, user_code):
        global_vars = []
        lines = user_code.split('\n')
        in_function = False
        
        for line in lines:
            line = line.strip()
            
            # Detectar inicio de función
            if ('(' in line and ')' in line and '{' in line) or line.endswith('{'):
                in_function = True
                continue
            elif line.startswith('}'):
                in_function = False
                continue
            
            # Solo procesar declaraciones fuera de funciones (globales)
            if not in_function and line.startswith('int ') and ';' in line:
                var_part = line[4:].split(';')[0].strip()
                if '=' in var_part:
                    var_name = var_part.split('=')[0].strip()
                else:
                    var_name = var_part.strip()
                global_vars.append(var_name)
        
        return global_vars
    
    def extract_literal_parameters(self, user_code, func_name):
        import re
        
        try:
            # Primero verificar el tipo de función declarada
            func_type_pattern = rf'(int|float)\s+{func_name}\s*\(\s*(int|float)\s+\w+\s*,\s*(int|float)\s+\w+\s*\)'
            func_match = re.search(func_type_pattern, user_code)
            
            if not func_match:
                return None  # No se encontró la declaración de función
                
            return_type, param1_type, param2_type = func_match.groups()
            
            # Buscar llamadas a la función en el código fuente
            # Patrón mejorado que detecta tanto enteros como floats
            pattern = rf'{func_name}\s*\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)'
            matches = re.findall(pattern, user_code)
            
            if matches:
                # Convertir los parámetros string a número (int o float según corresponda)
                param1_str, param2_str = matches[0]  # Primera coincidencia
                
                # Detectar el tipo del parámetro pasado
                param1_is_float = '.' in param1_str
                param2_is_float = '.' in param2_str
                
                # Verificar compatibilidad de tipos
                if param1_type == 'int' and param1_is_float:
                    return None  # Error: pasando float a parámetro int
                if param2_type == 'int' and param2_is_float:
                    return None  # Error: pasando float a parámetro int
                
                # Convertir según el tipo esperado
                if param1_type == 'float':
                    param1 = float(param1_str)
                else:
                    param1 = int(float(param1_str))  # Convertir a int (truncar si es necesario)
                    
                if param2_type == 'float':
                    param2 = float(param2_str)
                else:
                    param2 = int(float(param2_str))  # Convertir a int (truncar si es necesario)
                
                return [param1, param2]
            
            return None
        except Exception:
            return None

    
def main():
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