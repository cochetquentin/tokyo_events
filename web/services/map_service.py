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
            tiles='CartoDB Voyager'
        )

        # Cluster de marqueurs
        marker_cluster = MarkerCluster()

        # Ajouter marqueurs
        for event in result.events:
            # Convertir Pydantic object en dict
            event_dict = event.model_dump()

            if not (event_dict.get('latitude') and event_dict.get('longitude')):
                continue

            color = EVENT_COLORS.get(event_dict.get('event_type', 'festivals'), 'gray')
            popup_html = self._create_popup_html(event_dict)

            # Icônes personnalisées par type d'événement
            event_icons = {
                'hanabi': 'fire',
                'festivals': 'music',
                'expositions': 'palette',
                'marches': 'store'
            }
            icon_name = event_icons.get(event_dict.get('event_type', 'festivals'), 'info-sign')

            folium.Marker(
                location=[event_dict['latitude'], event_dict['longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=event_dict['name'],
                icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
            ).add_to(marker_cluster)

        marker_cluster.add_to(m)

        return m._repr_html_()

    def _create_popup_html(self, event: dict) -> str:
        """Crée HTML du popup."""
        html = f"<div style='font-family: Arial; min-width: 250px;'>"
        html += f"<h4 style='margin-top: 0;'>{event['name']}</h4>"
        html += f"<p><strong>Type:</strong> {event.get('event_type', 'N/A')}</p>"

        if event.get('start_date'):
            dates = event['start_date']
            if event.get('end_date') and event['end_date'] != event['start_date']:
                dates += f" - {event['end_date']}"
            html += f"<p><strong>Dates:</strong> {dates}</p>"

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
        if event.get('googlemap_link'):
            links.append(f"<a href='{event['googlemap_link']}' target='_blank'>Google Maps</a>")

        if links:
            html += f"<p>{' | '.join(links)}</p>"

        html += "</div>"
        return html
