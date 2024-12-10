import googlemaps

class GoogleMapsRepository:
    def __init__(self, api_key):
        self.gmaps = googlemaps.Client(key=api_key)

    def obtener_sugerencias(self, direccion):
        try:
            resultados = self.gmaps.places_autocomplete(
                input_text=direccion,
                components={"country": "PE"},
                language="es"
            )
            return [resultado['description'] for resultado in resultados]
        except Exception as e:
            print(f"Error al obtener sugerencias: {e}")
            return []

    def obtener_rutas(self, origen, destino, modo="walking"):
        try:
            rutas = self.gmaps.directions(
                origin=origen,
                destination=destino,
                alternatives=True,
                mode=modo,
                language="es"
            )
            return rutas
        except Exception as e:
            print(f"Error al obtener rutas: {e}")
            return []
