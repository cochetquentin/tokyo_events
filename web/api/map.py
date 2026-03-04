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
    event_types: Optional[str] = None,
    category: Optional[str] = None,
    category_groups: Optional[str] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
    center_lat: Optional[float] = None,
    center_lon: Optional[float] = None,
    zoom: Optional[int] = None,
):
    """Génère carte HTML avec événements filtrés."""
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
        has_coordinates=True
    )
    return map_service.generate_map(filters, center_lat, center_lon, zoom)
