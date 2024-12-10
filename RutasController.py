import json

import networkx as nx
import matplotlib.pyplot as plt

class RutasController:
    def __init__(self, repository):
        self.repository = repository

    def obtener_sugerencias(self, direccion):
        return self.repository.obtener_sugerencias(direccion)

    def obtener_rutas(self, origen, destino, modo):
        return self.repository.obtener_rutas(origen, destino, modo)

    def crear_grafo(self, rutas):
        G = nx.Graph()
        nodos_iniciales = []
        nodos_finales = []

        for ruta in rutas:
            pasos = ruta['legs'][0]['steps']
            for i, paso in enumerate(pasos):
                print(json.dumps(paso, indent=4))
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

    def calcular_todas_las_rutas(self, G, nodo_inicial, nodo_final, etiquetas_nodos):
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

    def calcular_ruta_mas_corta(self, G, nodo_inicial, nodo_final, etiquetas_nodos):
        try:
            ruta = nx.shortest_path(G, source=nodo_inicial, target=nodo_final, weight='distancia')
            distancia_total = sum(G[u][v]['distancia'] for u, v in zip(ruta, ruta[1:]))
            ruta_letras = " -> ".join(etiquetas_nodos[nodo] for nodo in ruta)
            return ruta_letras, distancia_total, ruta
        except nx.NetworkXNoPath:
            return None, None, None

    def visualizar_grafo(self, G, nodos_iniciales, nodos_finales, ruta_mas_corta):
        plt.figure(figsize=(25, 25))
        pos = nx.spring_layout(G, seed=42)

        nodos_ordenados = list(G.nodes())
        etiquetas_nodos = {nodo: self.generar_etiqueta(i) for i, nodo in enumerate(nodos_ordenados)}

        colores_nodos = ['green' if nodo in nodos_iniciales else 'red' if nodo in nodos_finales else 'lightblue'
                         for nodo in G.nodes()]

        colores_aristas = ['blue' if ruta_mas_corta and (
                edge in zip(ruta_mas_corta, ruta_mas_corta[1:]) or edge[::-1] in zip(ruta_mas_corta,
                                                                                     ruta_mas_corta[1:]))
                           else 'gray' for edge in G.edges()]

        nx.draw(G, pos, with_labels=False, node_size=200, node_color=colores_nodos,
                edge_color=colores_aristas, width=7, style='solid')
        nx.draw_networkx_labels(G, pos, labels=etiquetas_nodos, font_size=15, font_color='black')

        labels = nx.get_edge_attributes(G, 'distancia')
        nx.draw_networkx_edge_labels(G, pos,
                                     edge_labels={k: (f"{v / 1000:.1f} km" if v >= 1000 else f"{v} mts") for k, v in
                                                  labels.items()},
                                     font_size=13)

        plt.savefig("grafos.png", format="png")
        plt.close()

    def generar_etiqueta(self, indice):
        etiqueta = ""
        while indice >= 0:
            etiqueta = chr(65 + (indice % 26)) + etiqueta
            indice = (indice // 26) - 1
        return etiqueta
