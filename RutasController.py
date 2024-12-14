import folium
import networkx as nx
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
        # Determina el centro inicial del mapa (primer nodo)
        primer_nodo = next(iter(G.nodes()))
        mapa = folium.Map(location=[primer_nodo[0], primer_nodo[1]], zoom_start=15)

        marcador_cluster = MarkerCluster().add_to(mapa)

        # Identificar nodo de origen y destino
        nodo_origen = (pasos[0]['start_location']['lat'], pasos[0]['start_location']['lng'])
        nodo_destino = (pasos[-1]['end_location']['lat'], pasos[-1]['end_location']['lng'])

        # Calcular total de distancia y tiempo para la ruta más corta
        total_distancia = 0
        total_duracion = 0

        for i in range(len(ruta_mas_corta) - 1):
            u = ruta_mas_corta[i]
            v = ruta_mas_corta[i + 1]
            paso_info = next((p for p in pasos if (
                    (p['start_location']['lat'], p['start_location']['lng']) == u and
                    (p['end_location']['lat'], p['end_location']['lng']) == v
            )), None)
            if paso_info:
                total_distancia += paso_info['distance']['value']  # En metros
                total_duracion += paso_info['duration']['value']  # En segundos

        # Convertir total de distancia y duración
        total_distancia_txt = f"{total_distancia / 1000:.1f} km" if total_distancia >= 1000 else f"{total_distancia} mts"
        total_duracion_txt = f"{total_duracion // 3600} hr {total_duracion % 3600 // 60} min" if total_duracion >= 3600 else \
            f"{total_duracion // 60} min"

        # Agregar todos los nodos con sus etiquetas y distancias
        for nodo, etiqueta in etiquetas_nodos.items():
            # Buscar información adicional (distancia y duración) para el nodo
            paso_info = next((p for p in pasos if (p['start_location']['lat'], p['start_location']['lng']) == nodo),
                             None)
            if paso_info:
                distancia = paso_info['distance']['value']
                duracion = paso_info['duration']['value']
                distancia_txt = f"{distancia / 1000:.1f} km" if distancia >= 1000 else f"{distancia} mts"
                duracion_txt = f"{duracion // 3600} hr {duracion % 3600 // 60} min" if duracion >= 3600 else \
                    f"{duracion // 60} min"
            else:
                distancia_txt = "N/A"
                duracion_txt = "N/A"

            # Para el nodo de destino, mostrar totales
            if nodo == nodo_destino:
                distancia_txt = total_distancia_txt
                duracion_txt = total_duracion_txt

            # Configurar color del marcador
            color = "green" if nodo == nodo_origen else "red" if nodo == nodo_destino else "blue"

            popup_content = f"""
            <b>Nodo {etiqueta}</b><br>
            Distancia: {distancia_txt}<br>
            Duración: {duracion_txt}
            """
            folium.Marker(
                location=[nodo[0], nodo[1]],
                popup=popup_content,
                icon=folium.Icon(color=color)
            ).add_to(marcador_cluster)

        # Dibujar todas las aristas del grafo con nombres
        for u, v, data in G.edges(data=True):
            # Encontrar el paso asociado a esta arista
            paso_info = next((p for p in pasos if (
                    (p['start_location']['lat'], p['start_location']['lng']) == u and
                    (p['end_location']['lat'], p['end_location']['lng']) == v
            )), None)
            instruccion = paso_info['html_instructions'].replace('<b>', '').replace('</b>', '') if paso_info else "N/A"

            color = "blue" if (u, v) in zip(ruta_mas_corta, ruta_mas_corta[1:]) or (v, u) in zip(ruta_mas_corta,
                                                                                                 ruta_mas_corta[
                                                                                                 1:]) else "gray"

            # Línea con etiqueta personalizada
            folium.PolyLine(
                locations=[[u[0], u[1]], [v[0], v[1]]],
                color=color,
                weight=5,
                opacity=0.8,
                popup=f"{instruccion}"
            ).add_to(mapa)

        # Guardar el mapa en un archivo HTML
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
