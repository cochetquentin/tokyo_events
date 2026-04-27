"""Service de génération de carte Folium."""

import folium
from folium.plugins import MarkerCluster
from web.services.event_service import EventService
from web.models.schemas import EventFilters
from web.config import MAP_CENTER_LAT, MAP_CENTER_LON, MAP_DEFAULT_ZOOM, EVENT_COLORS


class MapService:
    """Génération de cartes Folium."""

    def __init__(self):
        self.event_service = EventService()

    def generate_map(self, filters: EventFilters, center_lat: float = None, center_lon: float = None, zoom: int = None) -> str:
        """Génère carte HTML avec événements."""
        result = self.event_service.get_events(filters)

        # Utiliser le centre personnalisé ou Tokyo par défaut
        lat = center_lat if center_lat is not None else MAP_CENTER_LAT
        lon = center_lon if center_lon is not None else MAP_CENTER_LON
        zoom_level = zoom if zoom is not None else MAP_DEFAULT_ZOOM

        # Créer carte
        m = folium.Map(
            location=[lat, lon],
            zoom_start=zoom_level,
            tiles='CartoDB Voyager',
            width='100%',
            height='100%'
        )

        # Cluster de marqueurs
        marker_cluster = MarkerCluster()

        # Ajouter marqueurs
        for event in result.events:
            # Convertir Pydantic object en dict
            event_dict = event.model_dump()

            if not (event_dict.get('latitude') and event_dict.get('longitude')):
                continue

            # Utiliser display_category pour tous les événements
            color, icon_name = self._get_category_marker_style(event_dict)

            popup_html = self._create_popup_html(event_dict)

            folium.Marker(
                location=[event_dict['latitude'], event_dict['longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=event_dict['name'],
                icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
            ).add_to(marker_cluster)

        marker_cluster.add_to(m)

        # Générer HTML et forcer la carte à prendre 100% de hauteur
        html = m._repr_html_()

        # Injecter du CSS pour forcer la carte à remplir l'iframe sans scroll
        custom_css = """
        <style>
            html, body {
                width: 100%;
                height: 100%;
                margin: 0;
                padding: 0;
                overflow: hidden;
            }
            .folium-map {
                width: 100% !important;
                height: 100% !important;
            }
        </style>
        """

        # Injecter le CSS au début du HTML
        if '<head>' in html:
            html = html.replace('<head>', '<head>' + custom_css)
        else:
            html = custom_css + html

        return html

    def _get_category_marker_style(self, event: dict) -> tuple:
        """Retourne (color, icon) basé sur la display_category de l'événement."""
        from web.config import ALL_CATEGORIES

        display_category = event.get('display_category', 'autres')

        if display_category in ALL_CATEGORIES:
            cat_data = ALL_CATEGORIES[display_category]
            # Convertir hex color en nom de couleur Folium
            color = self._hex_to_folium_color(cat_data['color'])
            icon = cat_data['icon']
            return color, icon

        # Fallback
        return 'gray', 'calendar'

    def _hex_to_folium_color(self, hex_color: str) -> str:
        """Convertit une couleur hex en nom de couleur Folium."""
        # Mapping approximatif hex → folium colors
        color_map = {
            '#ff6b35': 'orange',
            '#ff385c': 'red',
            '#5b7fff': 'blue',
            '#00c896': 'green',
            '#e91e63': 'pink',
            '#ff9800': 'orange',
            '#4caf50': 'green',
            '#ffd700': 'yellow',
            '#9c27b0': 'purple',
            '#607d8b': 'gray',
        }
        return color_map.get(hex_color, 'gray')

    def _create_popup_html(self, event: dict) -> str:
        """Crée HTML du popup."""
        html = f"<div style='font-family: Arial; min-width: 250px;'>"
        html += f"<h4 style='margin-top: 0;'>{event['name']}</h4>"
        html += f"<p><strong>Type:</strong> {event.get('event_type', 'N/A')}</p>"

        if event.get('category'):
            html += f"<p><strong>Catégorie:</strong> {event['category']}</p>"

        if event.get('start_date'):
            dates = event['start_date']
            if event.get('end_date') and event['end_date'] != event['start_date']:
                dates += f" - {event['end_date']}"
            html += f"<p><strong>Dates:</strong> {dates}</p>"

        if event.get('start_time'):
            time_str = event['start_time']
            if event.get('end_time'):
                time_str += f"～{event['end_time']}"
            html += f"<p><strong>Heure :</strong> {time_str}</p>"

        if event.get('location'):
            html += f"<p><strong>Lieu:</strong> {event['location']}</p>"

        if event.get('hours'):
            html += f"<p><strong>Horaires:</strong> {event['hours']}</p>"

        if event.get('fee'):
            html += f"<p><strong>Tarif:</strong> {event['fee']}</p>"

        if event.get('description'):
            desc = event['description'][:150] + ("..." if len(event['description']) > 150 else "")
            html += f"<p style='font-size: 12px;'>{desc}</p>"

        links = []
        if event.get('website'):
            links.append(f"<a href='{event['website']}' target='_blank'>Site officiel</a>")
        if event.get('detail_url'):
            links.append(f"<a href='{event['detail_url']}' target='_blank'>Walkerplus</a>")
        maps_url = event.get('googlemap_link')
        if not maps_url and event.get('latitude') and event.get('longitude'):
            maps_url = f"https://www.google.com/maps/dir/?api=1&destination={event['latitude']},{event['longitude']}"
        if maps_url:
            links.append(f"<a href='{maps_url}' target='_blank'>Google Maps</a>")

        if links:
            html += f"<p>{' | '.join(links)}</p>"

        html += "</div>"
        return html
