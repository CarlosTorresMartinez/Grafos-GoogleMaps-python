import tkinter as tk
from tkinter import ttk, messagebox, Listbox
import googlemaps
import networkx as nx
import matplotlib.pyplot as plt

gmaps = googlemaps.Client(key='Token')


def obtener_sugerencias(direccion):
    resultados = gmaps.places_autocomplete(direccion, components={"country": "PE"})
    return [resultado['description'] for resultado in resultados]


def obtener_rutas(origen, destino):
    rutas = gmaps.directions(origen, destino, alternatives=True)
    return rutas


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


def calcular_ruta_mas_corta(G, nodo_inicial, nodo_final, etiquetas_nodos):
    try:
        ruta = nx.shortest_path(G, source=nodo_inicial, target=nodo_final, weight='distancia')
        distancia_total = sum(G[u][v]['distancia'] for u, v in zip(ruta, ruta[1:]))
        ruta_letras = " -> ".join(etiquetas_nodos[nodo] for nodo in ruta)
        return ruta_letras, distancia_total, ruta
    except nx.NetworkXNoPath:
        return None, None, None


def visualizar_grafo(G, nodos_iniciales, nodos_finales, ruta_mas_corta):
    plt.figure(figsize=(14, 8))
    pos = nx.spring_layout(G, seed=42)

    nodos_ordenados = list(G.nodes())
    etiquetas_nodos = {nodo: chr(65 + i) for i, nodo in enumerate(nodos_ordenados)}

    colores_nodos = []
    for nodo in G.nodes():
        if nodo in nodos_iniciales:
            colores_nodos.append('green')
        elif nodo in nodos_finales:
            colores_nodos.append('red')
        else:
            colores_nodos.append('lightblue')

    colores_aristas = []
    for edge in G.edges():
        if ruta_mas_corta and (edge in zip(ruta_mas_corta, ruta_mas_corta[1:]) or edge[::-1] in zip(ruta_mas_corta, ruta_mas_corta[1:])):
            colores_aristas.append('blue')
        else:
            colores_aristas.append('gray')

    nx.draw(
        G, pos, with_labels=False, node_size=100, node_color=colores_nodos,
        edge_color=colores_aristas, width=2, style='solid'
    )

    nx.draw_networkx_labels(G, pos, labels=etiquetas_nodos, font_size=12, font_color='black')

    labels = nx.get_edge_attributes(G, 'distancia')
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels={k: (f"{v / 1000:.1f} km" if v >= 1000 else f"{v} mts") for k, v in labels.items()},
        font_size=10
    )

    plt.show()


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


class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ruta con Google Maps")
        self.geometry("700x600")
        self.resizable(0, 0)
        self.origen = tk.StringVar()
        self.destino = tk.StringVar()
        self.crear_widgets()

    def crear_widgets(self):
        frame_izquierdo = tk.Frame(self, width=400)
        frame_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame_izquierdo, text="Origen:").pack(pady=5)
        origen_entry = ttk.Entry(frame_izquierdo, textvariable=self.origen)
        origen_entry.pack(pady=5)
        origen_entry.bind("<KeyRelease>", self.actualizar_sugerencias_origen)

        self.lista_origen = Listbox(frame_izquierdo)
        self.lista_origen.pack(pady=5)
        self.lista_origen.bind("<<ListboxSelect>>", self.seleccionar_origen)

        ttk.Label(frame_izquierdo, text="Destino:").pack(pady=5)
        destino_entry = ttk.Entry(frame_izquierdo, textvariable=self.destino)
        destino_entry.pack(pady=5)
        destino_entry.bind("<KeyRelease>", self.actualizar_sugerencias_destino)

        self.lista_destino = Listbox(frame_izquierdo)
        self.lista_destino.pack(pady=5)
        self.lista_destino.bind("<<ListboxSelect>>", self.seleccionar_destino)

        ttk.Button(frame_izquierdo, text="Obtener Rutas", command=self.obtener_mostrar_rutas).pack(pady=20)

        frame_derecho = tk.Frame(self, width=300)
        frame_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(frame_derecho, text="Todas las rutas posibles", font=("Arial", 14, "bold")).pack(pady=10)

        self.lista_rutas = Listbox(frame_derecho, height=25, width=40)
        self.lista_rutas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def actualizar_sugerencias_origen(self, event):
        sugerencias = obtener_sugerencias(self.origen.get())
        self.lista_origen.delete(0, tk.END)
        for sugerencia in sugerencias:
            self.lista_origen.insert(tk.END, sugerencia)

    def actualizar_sugerencias_destino(self, event):
        sugerencias = obtener_sugerencias(self.destino.get())
        self.lista_destino.delete(0, tk.END)
        for sugerencia in sugerencias:
            self.lista_destino.insert(tk.END, sugerencia)

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

    def obtener_mostrar_rutas(self):
        origen = self.origen.get()
        destino = self.destino.get()
        if origen and destino:
            try:
                rutas = obtener_rutas(origen, destino)
                G, nodos_iniciales, nodos_finales = crear_grafo(rutas)
                etiquetas_nodos = {nodo: chr(65 + i) for i, nodo in enumerate(G.nodes())}
                nodo_inicial = nodos_iniciales[0]
                nodo_final = nodos_finales[0]

                # Calcular todas las rutas posibles
                todas_las_rutas = calcular_todas_las_rutas(G, nodo_inicial, nodo_final, etiquetas_nodos)
                self.actualizar_lista_rutas(todas_las_rutas)

                # Calcular la ruta más corta
                _, _, ruta_mas_corta = calcular_ruta_mas_corta(G, nodo_inicial, nodo_final, etiquetas_nodos)
                visualizar_grafo(G, nodos_iniciales, nodos_finales, ruta_mas_corta)
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {e}")
        else:
            messagebox.showwarning("Advertencia", "Por favor ingresa origen y destino.")

    def actualizar_lista_rutas(self, rutas_posibles):
        self.lista_rutas.delete(0, tk.END)
        for ruta, distancia in rutas_posibles:
            self.lista_rutas.insert(tk.END, f"{ruta}: {distancia} mts")


if __name__ == "__main__":
    app = Aplicacion()
    app.mainloop()
