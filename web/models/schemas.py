"""Schémas Pydantic pour validation API."""

from pydantic import BaseModel, Field
from typing import Optional, List


class EventResponse(BaseModel):
    """Événement avec coordonnées."""
    name: str
    event_type: str
    category: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    googlemap_link: Optional[str] = None
    hours: Optional[str] = None
    fee: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EventsListResponse(BaseModel):
    """Liste d'événements."""
    events: List[EventResponse]
    total: int
    filters_applied: dict


class EventFilters(BaseModel):
    """Filtres pour requêtes."""
    event_type: Optional[str] = None
    category: Optional[str] = None
    start_date_from: Optional[str] = None
    start_date_to: Optional[str] = None
    has_coordinates: bool = True
