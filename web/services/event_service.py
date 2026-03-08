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
        from web.config import CATEGORY_TO_DISPLAY

        events = self.db.get_events(
            event_type=filters.event_type,
            event_types=filters.event_types,
            category=filters.category,
            category_groups=filters.category_groups,
            start_date_from=filters.start_date_from,
            start_date_to=filters.start_date_to
        )

        # Filtrer par coordonnées
        if filters.has_coordinates:
            events = [e for e in events if e.get('latitude') and e.get('longitude')]

        # Calculer display_category pour chaque événement
        for event in events:
            event_type = event.get('event_type')
            category = event.get('category')

            # Types directs (hanabi, festivals, expositions, marches)
            if event_type in ['hanabi', 'festivals', 'expositions', 'marches']:
                event['display_category'] = event_type
            # Tokyo Cheapo avec catégorie mappée
            elif event_type == 'tokyo_cheapo' and category and category in CATEGORY_TO_DISPLAY:
                event['display_category'] = CATEGORY_TO_DISPLAY[category]
            # Fallback pour Tokyo Cheapo sans catégorie ou catégorie non mappée
            else:
                event['display_category'] = 'autres'

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
            event_types=filters.event_types,
            category=filters.category,
            category_groups=filters.category_groups,
            start_date_from=filters.start_date_from,
            start_date_to=filters.start_date_to
        )

        # Filtrer par coordonnées si demandé
        if filters.has_coordinates:
            all_events = [e for e in all_events if e.get('latitude') and e.get('longitude')]

        total = len(all_events)
        with_gps = sum(1 for e in all_events if e.get('latitude') and e.get('longitude'))

        # Compter par display_category
        from web.config import ALL_CATEGORIES, CATEGORY_TO_DISPLAY
        by_display_category = {key: 0 for key in ALL_CATEGORIES.keys()}

        for event in all_events:
            event_type = event.get('event_type')
            category = event.get('category')

            # Calculer la display_category (même logique que get_events)
            if event_type in ['hanabi', 'festivals', 'expositions', 'marches']:
                display_cat = event_type
            elif event_type == 'tokyo_cheapo' and category and category in CATEGORY_TO_DISPLAY:
                display_cat = CATEGORY_TO_DISPLAY[category]
            else:
                display_cat = 'autres'

            by_display_category[display_cat] += 1

        return {
            'total_events': total,
            'by_display_category': by_display_category,
            'with_gps_coordinates': with_gps,
            'gps_coverage_percent': round((with_gps / total * 100), 2) if total > 0 else 0
        }
