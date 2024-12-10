import networkx as nx
import matplotlib.pyplot as plt
import folium
from folium.plugins import MarkerCluster


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
        pasos_totales = []

        for ruta in rutas:
            pasos = ruta['legs'][0]['steps']
            pasos_totales.extend(pasos)
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

        return G, nodos_iniciales, nodos_finales, pasos_totales

    def generar_mapa(self, G, etiquetas_nodos, ruta_mas_corta, pasos, nombre_archivo="mapa.html"):
        primer_nodo = next(iter(G.nodes()))
        mapa = folium.Map(location=[primer_nodo[0], primer_nodo[1]], zoom_start=15)

        marcador_cluster = MarkerCluster().add_to(mapa)

        # Agregar todos los nodos con sus etiquetas y distancias
        for nodo, etiqueta in etiquetas_nodos.items():
            # Buscar información adicional (distancia y duración) para el nodo
            paso_info = next((p for p in pasos if (p['start_location']['lat'], p['start_location']['lng']) == nodo),
                             None)
            distancia = paso_info['distance']['text'] if paso_info else "N/A"
            duracion = paso_info['duration']['text'] if paso_info else "N/A"

            popup_content = f"""
               <b>Nodo {etiqueta}</b><br>
               Distancia: {distancia}<br>
               Duración: {duracion}
               """
            folium.Marker(
                location=[nodo[0], nodo[1]],
                popup=popup_content,
                icon=folium.Icon(
                    color="green" if etiqueta == "A" else "red" if etiqueta == list(etiquetas_nodos.values())[
                        -1] else "blue")
            ).add_to(marcador_cluster)

        # Dibujar todas las aristas del grafo
        for u, v, data in G.edges(data=True):
            color = "blue" if (u, v) in zip(ruta_mas_corta, ruta_mas_corta[1:]) or (v, u) in zip(ruta_mas_corta,
                                                                                                 ruta_mas_corta[
                                                                                                 1:]) else "gray"
            folium.PolyLine(
                locations=[[u[0], u[1]], [v[0], v[1]]],
                color=color,
                weight=5,
                opacity=0.8
            ).add_to(mapa)
        mapa.save(nombre_archivo)
        return nombre_archivo

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

    def generar_etiqueta(self, indice):
        etiqueta = ""
        while indice >= 0:
            etiqueta = chr(65 + (indice % 26)) + etiqueta
            indice = (indice // 26) - 1
        return etiqueta
