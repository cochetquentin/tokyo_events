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

    def generate_map(self, filters: EventFilters) -> str:
        """Génère carte HTML avec événements."""
        result = self.event_service.get_events(filters)

        # Créer carte centrée sur Tokyo
        m = folium.Map(
            location=[MAP_CENTER_LAT, MAP_CENTER_LON],
            zoom_start=MAP_DEFAULT_ZOOM,
            tiles='OpenStreetMap'
        )

        # Cluster de marqueurs
        marker_cluster = MarkerCluster()

        # Ajouter marqueurs
        for event in result.events:
            if not (event.get('latitude') and event.get('longitude')):
                continue

            color = EVENT_COLORS.get(event.get('event_type', 'festivals'), 'gray')
            popup_html = self._create_popup_html(event)

            folium.Marker(
                location=[event['latitude'], event['longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=event['name'],
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(marker_cluster)

        marker_cluster.add_to(m)
        self._add_legend(m)

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

    def _add_legend(self, map_obj):
        """Ajoute légende."""
        legend_html = """
        <div style="position: fixed; bottom: 50px; left: 50px; width: 180px;
                    background-color: white; z-index:9999; border:2px solid grey;
                    border-radius: 5px; padding: 10px;">
            <p style="margin: 0 0 10px 0; font-weight: bold;">Types d'evenements</p>
        """

        for event_type, color in EVENT_COLORS.items():
            legend_html += f"""
            <p style="margin: 5px 0;">
                <i class="fa fa-map-marker" style="color:{color}"></i>
                {event_type.capitalize()}
            </p>
            """

        legend_html += "</div>"
        map_obj.get_root().html.add_child(folium.Element(legend_html))
