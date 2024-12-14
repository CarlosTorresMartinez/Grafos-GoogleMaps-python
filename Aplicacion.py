import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox, Listbox

from PIL import Image, ImageTk

from GoogleMapsRepository import GoogleMapsRepository
from RutasController import RutasController


class Aplicacion(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.title("Visualizador de Rutas con Google Maps")
        self.geometry("1000x750")
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.origen = tk.StringVar()
        self.destino = tk.StringVar()
        self.modo_transporte = tk.StringVar(value="walking")
        self.grafo_ventana = None
        self.img_original = None
        self.img_scaled = None
        self.offset_x = 0
        self.offset_y = 0
        self.start_x = 0
        self.start_y = 0
        self.crear_widgets()

    def crear_widgets(self):
        frame_izquierdo = ttk.Frame(self, padding="10 10 10 10")
        frame_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.agregar_campos_origen(frame_izquierdo)
        self.agregar_campos_destino(frame_izquierdo)
        self.agregar_campo_modo_transporte(frame_izquierdo)

        ttk.Button(frame_izquierdo, text="Calcular rutas", command=self.obtener_mostrar_rutas,
                   style="Accent.TButton").pack(pady=10)

        self.crear_lista_rutas()

    def agregar_campos_origen(self, frame):
        ttk.Label(frame, text="Origen:", font=("Arial", 12, "bold")).pack(pady=5)

        ancho_entrada = 40
        origen_entry = ttk.Entry(frame, textvariable=self.origen, font=("Arial", 12), width=ancho_entrada)
        origen_entry.pack(pady=5)
        origen_entry.bind("<KeyRelease>", self.actualizar_sugerencias_origen)

        self.lista_origen = Listbox(frame, height=5, font=("Arial", 10), bg="#f7f7f7", selectbackground="#d0e0f0",
                                    width=ancho_entrada)
        self.lista_origen.pack(pady=5, fill=tk.X)
        self.lista_origen.bind("<<ListboxSelect>>", self.seleccionar_origen)

    def agregar_campos_destino(self, frame):
        ttk.Label(frame, text="Destino:", font=("Arial", 12, "bold")).pack(pady=5)

        ancho_entrada = 40
        destino_entry = ttk.Entry(frame, textvariable=self.destino, font=("Arial", 12), width=ancho_entrada)
        destino_entry.pack(pady=5)
        destino_entry.bind("<KeyRelease>", self.actualizar_sugerencias_destino)

        self.lista_destino = Listbox(frame, height=5, font=("Arial", 10), bg="#f7f7f7", selectbackground="#d0e0f0",
                                     width=ancho_entrada)
        self.lista_destino.pack(pady=5, fill=tk.X)
        self.lista_destino.bind("<<ListboxSelect>>", self.seleccionar_destino)

    def agregar_campo_modo_transporte(self, frame):
        ttk.Label(frame, text="Modo de transporte:", font=("Arial", 12, "bold")).pack(pady=5)
        opciones_transporte = ["Conduciendo", "Caminando"]
        self.valores_transporte = {"Conduciendo": "driving", "Caminando": "walking"}

        transporte_combobox = ttk.Combobox(frame, values=opciones_transporte, textvariable=self.modo_transporte,
                                           state="readonly", font=("Arial", 11))
        transporte_combobox.set("Caminando")
        transporte_combobox.pack(pady=5)

    def crear_lista_rutas(self):
        frame_derecho = ttk.Frame(self, padding="10 10 10 10")
        frame_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Label(frame_derecho, text="Todas las rutas posibles", font=("Arial", 14, "bold")).pack(pady=10)

        scroll_frame = ttk.Frame(frame_derecho)
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        x_scroll = ttk.Scrollbar(scroll_frame, orient=tk.HORIZONTAL)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        y_scroll = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.lista_rutas = Listbox(scroll_frame, height=20, width=50, font=("Arial", 10), bg="#f7f7f7",
                                   selectbackground="#d0e0f0",
                                   xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        self.lista_rutas.pack(fill=tk.BOTH, expand=True)

        x_scroll.config(command=self.lista_rutas.xview)
        y_scroll.config(command=self.lista_rutas.yview)

    def mostrar_mapa(self, G, etiquetas_nodos, ruta_mas_corta, pasos):
        mapa_html = self.controller.generar_mapa(G, etiquetas_nodos, ruta_mas_corta, pasos)
        webbrowser.open(mapa_html)

    def obtener_mostrar_rutas(self):
        origen = self.origen. get()
        destino = self.destino.get()

        if origen == destino:
            messagebox.showwarning(title='Ubicaciones repetidas',
                                   message='Las ubicaciones escritas no pueden ser las mismas.')
            return

        modo = self.valores_transporte.get(self.modo_transporte.get(), "walking")
        if origen and destino:
            try:
                rutas = self.controller.obtener_rutas(origen, destino, modo)
                G, nodos_iniciales, nodos_finales, pasos_totales = self.controller.crear_grafo(rutas)
                etiquetas_nodos = {nodo: self.controller.generar_etiqueta(i) for i, nodo in enumerate(G.nodes())}
                nodo_inicial = nodos_iniciales[0]
                nodo_final = nodos_finales[0]

                todas_las_rutas = self.controller.calcular_todas_las_rutas(G, nodo_inicial, nodo_final, etiquetas_nodos)
                self.actualizar_lista_rutas(todas_las_rutas)

                _, _, ruta_mas_corta = self.controller.calcular_ruta_mas_corta(G, nodo_inicial, nodo_final, etiquetas_nodos)

                # Generar y mostrar el mapa interactivo con los pasos
                self.mostrar_mapa(G, etiquetas_nodos, ruta_mas_corta, pasos_totales)

            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {e}")
        else:
            messagebox.showwarning("Advertencia", "Por favor ingresa origen y destino.")

    def actualizar_lista_rutas(self, rutas_posibles):
        self.lista_rutas.delete(0, tk.END)
        if rutas_posibles:
            ruta_minima = min(rutas_posibles, key=lambda x: x[1])
        else:
            ruta_minima = None

        for i, (ruta, distancia) in enumerate(rutas_posibles):
            self.lista_rutas.insert(tk.END,
                                    f"{ruta}: {distancia / 1000:.1f} km" if distancia >= 1000 else f"{distancia} mts")
            if ruta_minima and ruta_minima[0] == ruta:
                self.lista_rutas.itemconfig(i, bg="lightblue", fg="darkblue")

    def iniciar_movimiento(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def mover_imagen(self, event):
        delta_x = event.x - self.start_x
        delta_y = event.y - self.start_y
        self.offset_x += delta_x
        self.offset_y += delta_y

        self.grafo_ventana.label_img.place(x=self.offset_x, y=self.offset_y)
        self.start_x = event.x
        self.start_y = event.y

    def zoom_imagen(self, event):
        if self.img_original:
            factor = 1.1 if event.delta > 0 else 0.9
            nuevo_ancho = int(self.img_scaled.width * factor)
            nuevo_alto = int(self.img_scaled.height * factor)

            self.img_scaled = self.img_original.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(self.img_scaled)

            self.grafo_ventana.label_img.config(image=img_tk)
            self.grafo_ventana.label_img.image = img_tk

    def actualizar_sugerencias_origen(self, event):
        try:
            sugerencias = self.controller.obtener_sugerencias(self.origen.get())
            self.lista_origen.delete(0, tk.END)
            for sugerencia in sugerencias:
                self.lista_origen.insert(tk.END, sugerencia)
        except Exception:
            pass

    def actualizar_sugerencias_destino(self, event):
        try:
            sugerencias = self.controller.obtener_sugerencias(self.destino.get())
            self.lista_destino.delete(0, tk.END)
            for sugerencia in sugerencias:
                self.lista_destino.insert(tk.END, sugerencia)
        except Exception:
            pass

    def seleccionar_origen(self, event):
        seleccion = self.lista_origen.curselection()
        if seleccion:
            self.origen.set(self.lista_origen.get(seleccion[0]))
            self.lista_origen.delete(0, tk.END)

    def seleccionar_destino(self, event):
        seleccion = self.lista_destino.curselection()
        if seleccion:
            self.destino.set(self.lista_destino.get(seleccion[0]))
            self.lista_destino.delete(0, tk.END)


if __name__ == "__main__":
    api_key = "AIzaSyBO9ods-p3dyVwvdtqN1m_bsKpTC3cGUTo"
    repository = GoogleMapsRepository(api_key)
    controller = RutasController(repository)
    app = Aplicacion(controller)
    app.mainloop()
