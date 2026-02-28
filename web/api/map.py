"""Endpoint pour génération carte."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from typing import Optional
from web.services.map_service import MapService
from web.models.schemas import EventFilters

router = APIRouter()
map_service = MapService()


@router.get("/generate", response_class=HTMLResponse)
async def generate_map(
    event_type: Optional[str] = None,
    category: Optional[str] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
    center_lat: Optional[float] = None,
    center_lon: Optional[float] = None,
    zoom: Optional[int] = None,
):
    """Génère carte HTML avec événements filtrés."""
    filters = EventFilters(
        event_type=event_type,
        category=category,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        has_coordinates=True
    )
    return map_service.generate_map(filters, center_lat, center_lon, zoom)
