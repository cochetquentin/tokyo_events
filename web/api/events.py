"""Endpoints API pour les événements."""

from fastapi import APIRouter, Query
from typing import Optional
from web.models.schemas import EventsListResponse, EventFilters
from web.services.event_service import EventService

router = APIRouter()
event_service = EventService()


@router.get("/", response_model=EventsListResponse)
async def get_events(
    event_type: Optional[str] = Query(None, pattern="^(festivals|expositions|hanabi|marches)$"),
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
    has_coordinates: bool = Query(True, description="Uniquement événements avec GPS")
):
    """Liste des événements avec filtres."""
    filters = EventFilters(
        event_type=event_type,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        has_coordinates=has_coordinates
    )
    return event_service.get_events(filters)


@router.get("/stats")
async def get_stats():
    """Statistiques."""
    return event_service.get_statistics()
