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
        events = self.db.get_events(
            event_type=filters.event_type,
            start_date_from=filters.start_date_from,
            start_date_to=filters.start_date_to
        )

        # Filtrer par coordonnées
        if filters.has_coordinates:
            events = [e for e in events if e.get('latitude') and e.get('longitude')]

        return EventsListResponse(
            events=events,
            total=len(events),
            filters_applied=filters.dict(exclude_none=True)
        )

    def get_statistics(self):
        """Statistiques globales."""
        total = self.db.count_events()
        all_events = self.db.get_events()
        with_gps = sum(1 for e in all_events if e.get('latitude') and e.get('longitude'))

        return {
            'total_events': total,
            'by_type': {
                'festivals': self.db.count_events('festivals'),
                'expositions': self.db.count_events('expositions'),
                'hanabi': self.db.count_events('hanabi'),
                'marches': self.db.count_events('marches')
            },
            'with_gps_coordinates': with_gps,
            'gps_coverage_percent': round((with_gps / total * 100), 2) if total > 0 else 0
        }
