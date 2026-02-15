"""Service métier pour les événements."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import EventDatabase
from web.models.schemas import EventFilters, EventsListResponse
from web.config import DB_PATH


class EventService:
    """Gestion des événements."""

    def __init__(self):
        self.db = EventDatabase(str(DB_PATH))

    def get_events(self, filters: EventFilters) -> EventsListResponse:
        """Récupère événements avec filtres."""
        from web.models.schemas import EventResponse

        events = self.db.get_events(
            event_type=filters.event_type,
            start_date_from=filters.start_date_from,
            start_date_to=filters.start_date_to
        )

        # Filtrer par coordonnées
        if filters.has_coordinates:
            events = [e for e in events if e.get('latitude') and e.get('longitude')]

        # Convertir en EventResponse objects
        event_responses = [EventResponse(**event) for event in events]

        return EventsListResponse(
            events=event_responses,
            total=len(event_responses),
            filters_applied=filters.dict(exclude_none=True)
        )

    def get_statistics(self, filters: EventFilters = None):
        """Statistiques avec filtres optionnels."""
        if filters is None:
            filters = EventFilters()

        # Récupérer les événements avec les filtres appliqués
        all_events = self.db.get_events(
            event_type=filters.event_type,
            start_date_from=filters.start_date_from,
            start_date_to=filters.start_date_to
        )

        # Filtrer par coordonnées si demandé
        if filters.has_coordinates:
            all_events = [e for e in all_events if e.get('latitude') and e.get('longitude')]

        total = len(all_events)
        with_gps = sum(1 for e in all_events if e.get('latitude') and e.get('longitude'))

        # Compter par type
        by_type = {
            'festivals': sum(1 for e in all_events if e.get('event_type') == 'festivals'),
            'expositions': sum(1 for e in all_events if e.get('event_type') == 'expositions'),
            'hanabi': sum(1 for e in all_events if e.get('event_type') == 'hanabi'),
            'marches': sum(1 for e in all_events if e.get('event_type') == 'marches')
        }

        return {
            'total_events': total,
            'by_type': by_type,
            'with_gps_coordinates': with_gps,
            'gps_coverage_percent': round((with_gps / total * 100), 2) if total > 0 else 0
        }
