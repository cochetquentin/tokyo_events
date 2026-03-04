"""Endpoints API pour les événements."""

from fastapi import APIRouter, Query
from typing import Optional
from web.models.schemas import EventsListResponse, EventFilters
from web.services.event_service import EventService

router = APIRouter()
event_service = EventService()


@router.get("/", response_model=EventsListResponse)
async def get_events(
    event_type: Optional[str] = Query(None, pattern="^(festivals|expositions|hanabi|marches|tokyo_cheapo)$"),
    event_types: Optional[str] = Query(None, description="Types d'événements séparés par virgules (ex: hanabi,festivals)"),
    category: Optional[str] = None,
    category_groups: Optional[str] = Query(None, description="Familles de catégories séparées par virgules (ex: culture_arts,nature_outdoor)"),
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
    has_coordinates: bool = Query(True, description="Uniquement événements avec GPS")
):
    """Liste des événements avec filtres."""
    # Parse category_groups et event_types si fournis
    groups_list = category_groups.split(',') if category_groups else None
    types_list = event_types.split(',') if event_types else None

    filters = EventFilters(
        event_type=event_type,
        event_types=types_list,
        category=category,
        category_groups=groups_list,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        has_coordinates=has_coordinates
    )
    return event_service.get_events(filters)


@router.get("/stats")
async def get_stats(
    event_type: Optional[str] = Query(None, pattern="^(festivals|expositions|hanabi|marches|tokyo_cheapo)$"),
    event_types: Optional[str] = Query(None, description="Types d'événements séparés par virgules"),
    category: Optional[str] = None,
    category_groups: Optional[str] = Query(None, description="Familles de catégories séparées par virgules"),
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
    has_coordinates: bool = Query(True, description="Uniquement événements avec GPS")
):
    """Statistiques avec filtres."""
    # Parse category_groups et event_types si fournis
    groups_list = category_groups.split(',') if category_groups else None
    types_list = event_types.split(',') if event_types else None

    filters = EventFilters(
        event_type=event_type,
        event_types=types_list,
        category=category,
        category_groups=groups_list,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        has_coordinates=has_coordinates
    )
    return event_service.get_statistics(filters)


@router.get("/category-groups")
async def get_category_groups():
    """Retourne les métadonnées des familles de catégories."""
    from web.config import CATEGORY_GROUPS
    return CATEGORY_GROUPS


@router.get("/all-categories")
async def get_all_categories():
    """Retourne toutes les catégories unifiées (types + groupes)."""
    from web.config import ALL_CATEGORIES
    return ALL_CATEGORIES
