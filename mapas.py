import tkinter as tk
from tkinter import ttk, messagebox, Listbox, Toplevel
import googlemaps
import networkx as nx
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from PIL.Image import Resampling

gmaps = googlemaps.Client(key='Token')

CONSTANTS = {
    "language": "es",
    "country": "PE"
}

def obtener_sugerencias(direccion):
    try:
        resultados = gmaps.places_autocomplete(
            input_text=direccion,
            components={"country": CONSTANTS['country']},
            language=CONSTANTS['language']
        )
        return [resultado['description'] for resultado in resultados]
    except Exception as e:
        print(f"Error al obtener sugerencias: {e}")
        return []


def obtener_rutas(origen, destino, modo="walking"):
    try:
        rutas = gmaps.directions(
            origin=origen,
            destination=destino,
            alternatives=True,
            mode=modo,
            language=CONSTANTS['language']
        )
        return rutas
    except Exception as e:
        print(f"Error al obtener rutas: {e}")
        return []


def calcular_ruta_mas_corta(G, nodo_inicial, nodo_final, etiquetas_nodos):
    try:
        ruta = nx.shortest_path(G, source=nodo_inicial, target=nodo_final, weight='distancia')
        distancia_total = sum(G[u][v]['distancia'] for u, v in zip(ruta, ruta[1:]))
        ruta_letras = " -> ".join(etiquetas_nodos[nodo] for nodo in ruta)
        return ruta_letras, distancia_total, ruta
    except nx.NetworkXNoPath:
        return None, None, None


def crear_grafo(rutas):
    G = nx.Graph()
    nodos_iniciales = []
    nodos_finales = []

    for ruta in rutas:
        pasos = ruta['legs'][0]['steps']
        for i, paso in enumerate(pasos):
            inicio = paso['start_location']
            fin = paso['end_location']
            distancia = paso['distance']['value']

            nodo_inicio = (inicio['lat'], inicio['lng'])
            nodo_fin = (fin['lat'], fin['lng'])

            G.add_node(nodo_inicio)
            G.add_node(nodo_fin)
            G.add_edge(nodo_inicio, nodo_fin, distancia=distancia)

            if i == 0:
                nodos_iniciales.append(nodo_inicio)
            if i == len(pasos) - 1:
                nodos_finales.append(nodo_fin)

    return G, nodos_iniciales, nodos_finales


def calcular_todas_las_rutas(G, nodo_inicial, nodo_final, etiquetas_nodos):
    todas_las_rutas = []
    try:
        rutas = list(nx.all_simple_paths(G, source=nodo_inicial, target=nodo_final))
        for ruta in rutas:
            distancia_total = sum(G[u][v]['distancia'] for u, v in zip(ruta, ruta[1:]))
            ruta_letras = " -> ".join(etiquetas_nodos[nodo] for nodo in ruta)
            todas_las_rutas.append((ruta_letras, distancia_total))
    except nx.NetworkXNoPath:
        todas_las_rutas = []

    return todas_las_rutas


def generar_etiqueta(indice):
    etiqueta = ""
    while indice >= 0:
        etiqueta = chr(65 + (indice % 26)) + etiqueta
        indice = (indice // 26) - 1
    return etiqueta


def visualizar_grafo(G, nodos_iniciales, nodos_finales, ruta_mas_corta):
    plt.figure(figsize=(25, 25))
    pos = nx.spring_layout(G, seed=42)

    nodos_ordenados = list(G.nodes())
    etiquetas_nodos = {nodo: generar_etiqueta(i) for i, nodo in enumerate(nodos_ordenados)}

    colores_nodos = ['green' if nodo in nodos_iniciales else 'red' if nodo in nodos_finales else 'lightblue'
                     for nodo in G.nodes()]

    colores_aristas = ['blue' if ruta_mas_corta and (
            edge in zip(ruta_mas_corta, ruta_mas_corta[1:]) or edge[::-1] in zip(ruta_mas_corta,
                                                                                 ruta_mas_corta[1:]))
                       else 'gray' for edge in G.edges()]

    nx.draw(G, pos, with_labels=False, node_size=300, node_color=colores_nodos,
            edge_color=colores_aristas, width=8, style='solid')
    nx.draw_networkx_labels(G, pos, labels=etiquetas_nodos, font_size=20, font_color='black')

    labels = nx.get_edge_attributes(G, 'distancia')
    nx.draw_networkx_edge_labels(G, pos,
                                 edge_labels={k: (f"{v / 1000:.1f} km" if v >= 1000 else f"{v} mts") for k, v in
                                              labels.items()},
                                 font_size=15)

    plt.savefig("grafos.png", format="png")
    plt.close()


class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Visualizador de Rutas con Google Maps")
        self.geometry("900x700")
        self.resizable(True, True)
        self.origen = tk.StringVar()
        self.destino = tk.StringVar()
        self.modo_transporte = tk.StringVar(value="walking")  # Modo por defecto
        self.grafo_ventana = None
        self.img_original = None
        self.img_scaled = None
        self.offset_x = 0
        self.offset_y = 0
        self.start_x = 0
        self.start_y = 0
        self.crear_widgets()

    def crear_widgets(self):
        frame_izquierdo = tk.Frame(self, width=400)
        frame_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame_izquierdo, text="Origen:", font=("Arial", 12, "bold")).pack(pady=5)
        origen_entry = ttk.Entry(frame_izquierdo, textvariable=self.origen, font=("Arial", 12))
        origen_entry.pack(pady=5)
        origen_entry.bind("<KeyRelease>", self.actualizar_sugerencias_origen)

        self.lista_origen = Listbox(frame_izquierdo, height=5, font=("Arial", 10))
        self.lista_origen.pack(pady=5)
        self.lista_origen.bind("<<ListboxSelect>>", self.seleccionar_origen)

        ttk.Label(frame_izquierdo, text="Destino:", font=("Arial", 12, "bold")).pack(pady=5)
        destino_entry = ttk.Entry(frame_izquierdo, textvariable=self.destino, font=("Arial", 12))
        destino_entry.pack(pady=5)
        destino_entry.bind("<KeyRelease>", self.actualizar_sugerencias_destino)

        self.lista_destino = Listbox(frame_izquierdo, height=5, font=("Arial", 10))
        self.lista_destino.pack(pady=5)
        self.lista_destino.bind("<<ListboxSelect>>", self.seleccionar_destino)

        ttk.Label(frame_izquierdo, text="Modo de transporte:", font=("Arial", 12, "bold")).pack(pady=5)
        opciones_transporte = ["Conduciendo", "Caminando"]
        valores_transporte = {"Conduciendo": "driving", "Caminando": "walking"}

        self.valores_transporte = valores_transporte
        transporte_combobox = ttk.Combobox(frame_izquierdo, values=opciones_transporte,
                                           textvariable=self.modo_transporte, state="readonly")
        transporte_combobox.set("Caminando")
        transporte_combobox.pack(pady=5)

        ttk.Button(frame_izquierdo, text="Calcular rutas", command=self.obtener_mostrar_rutas).pack(pady=10)

        frame_derecho = tk.Frame(self, width=500)
        frame_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(frame_derecho, text="Todas las rutas posibles", font=("Arial", 14, "bold")).pack(pady=10)
        self.lista_rutas = Listbox(frame_derecho, height=30, width=50, font=("Arial", 10))
        self.lista_rutas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def obtener_mostrar_rutas(self):
        origen = self.origen.get()
        destino = self.destino.get()
        modo = self.valores_transporte.get(self.modo_transporte.get(), "walking")
        if origen and destino:
            try:
                rutas = obtener_rutas(origen, destino, modo)
                G, nodos_iniciales, nodos_finales = crear_grafo(rutas)
                etiquetas_nodos = {nodo: generar_etiqueta(i) for i, nodo in enumerate(G.nodes())}
                nodo_inicial = nodos_iniciales[0]
                nodo_final = nodos_finales[0]

                todas_las_rutas = calcular_todas_las_rutas(G, nodo_inicial, nodo_final, etiquetas_nodos)
                self.actualizar_lista_rutas(todas_las_rutas)

                _, _, ruta_mas_corta = calcular_ruta_mas_corta(G, nodo_inicial, nodo_final, etiquetas_nodos)

                visualizar_grafo(G, nodos_iniciales, nodos_finales, ruta_mas_corta)
                self.mostrar_grafo()
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
            if distancia >= 1000:
                distancia_str = f"{distancia / 1000:.1f} km"
            else:
                distancia_str = f"{distancia} mts"

            self.lista_rutas.insert(tk.END, f"{ruta}: {distancia_str}")

            if ruta_minima and ruta_minima[0] == ruta:
                self.lista_rutas.itemconfig(i, bg="lightblue", fg="darkblue")

    def mostrar_grafo(self):
        if not self.grafo_ventana or not tk.Toplevel.winfo_exists(self.grafo_ventana):
            self.grafo_ventana = Toplevel(self)
            self.grafo_ventana.title("Visualización del Grafo")
            self.grafo_ventana.geometry("800x800")
            self.grafo_ventana.resizable(True, True)
            self.grafo_ventana.label_img = None  # Inicializar el atributo para la imagen

        # Mostrar la imagen actualizada
        try:
            self.img_original = Image.open("grafos.png")
            self.img_scaled = self.img_original.resize((750, 750), Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(self.img_scaled)

            if self.grafo_ventana.label_img:
                self.grafo_ventana.label_img.destroy()  # Eliminar la imagen anterior

            self.grafo_ventana.label_img = tk.Label(self.grafo_ventana, image=img_tk)
            self.grafo_ventana.label_img.image = img_tk  # Guardar referencia
            self.grafo_ventana.label_img.place(x=self.offset_x, y=self.offset_y)

            # Añadir eventos para zoom y movimiento
            self.grafo_ventana.bind("<MouseWheel>", self.zoom_imagen)
            self.grafo_ventana.bind("<ButtonPress-1>", self.iniciar_movimiento)
            self.grafo_ventana.bind("<B1-Motion>", self.mover_imagen)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen: {e}")

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
            # Ajustar el tamaño de la imagen según el evento del mouse
            factor = 1.1 if event.delta > 0 else 0.9
            nuevo_ancho = int(self.img_scaled.width * factor)
            nuevo_alto = int(self.img_scaled.height * factor)

            # Escalar la imagen y actualizarla
            self.img_scaled = self.img_original.resize((nuevo_ancho, nuevo_alto), Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(self.img_scaled)

            self.grafo_ventana.label_img.config(image=img_tk)
            self.grafo_ventana.label_img.image = img_tk





    def actualizar_sugerencias_origen(self, event):
        try:
            sugerencias = obtener_sugerencias(self.origen.get())
            self.lista_origen.delete(0, tk.END)
            for sugerencia in sugerencias:
                self.lista_origen.insert(tk.END, sugerencia)
        except Exception:
            pass

    def actualizar_sugerencias_destino(self, event):
        try:
            sugerencias = obtener_sugerencias(self.destino.get())
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
    app = Aplicacion()
    app.mainloop()
