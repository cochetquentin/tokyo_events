"""Configuration de l'application web."""

import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / "data" / "tokyo_events.sqlite"

# Serveur
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Carte
MAP_CENTER_LAT = 35.6762
MAP_CENTER_LON = 139.6503
MAP_DEFAULT_ZOOM = 11

# Couleurs par type d'événement
EVENT_COLORS = {
    'festivals': 'red',
    'expositions': 'blue',
    'hanabi': 'orange',
    'marches': 'green',
    'tokyo_cheapo': 'purple'
}

# Mapping des catégories sources vers des familles de catégories
CATEGORY_GROUPS = {
    'culture_arts': {
        'label': 'Culture & Arts',
        'icon': 'paint-brush',
        'color': 'purple',
        'categories': ['Art', 'Film', 'Fashion', 'Anime']
    },
    'nature_outdoor': {
        'label': 'Nature & Extérieur',
        'icon': 'tree',
        'color': 'green',
        'categories': ['Nature', 'Illumination', 'Fireworks']
    },
    'entertainment': {
        'label': 'Divertissement & Spectacle',
        'icon': 'music',
        'color': 'red',
        'categories': ['Music', 'Comedy', 'Party', 'Festival']
    },
    'sport_activities': {
        'label': 'Sport & Activités',
        'icon': 'running',
        'color': 'orange',
        'categories': ['Sport', 'Workshop']
    },
    'food_markets': {
        'label': 'Gastronomie & Marchés',
        'icon': 'utensils',
        'color': 'blue',
        'categories': ['Food', 'Market']
    },
    'community': {
        'label': 'Communauté & Engagement',
        'icon': 'handshake',
        'color': 'cadetblue',
        'categories': ['Charity', 'Volunteering', 'Trade Show']
    }
}

# Reverse mapping : category source → group key
CATEGORY_TO_GROUP = {
    cat: group_key
    for group_key, group_data in CATEGORY_GROUPS.items()
    for cat in group_data['categories']
}

# Configuration unifiée : tous les types/catégories au même niveau
ALL_CATEGORIES = {
    # Types existants (filtrage par event_type)
    'hanabi': {
        'label': 'Hanabi',
        'icon': 'fire',
        'color': 'orange',
        'filter_type': 'event_type',
        'filter_value': 'hanabi'
    },
    'festivals': {
        'label': 'Festivals',
        'icon': 'music',
        'color': 'darkred',
        'filter_type': 'event_type',
        'filter_value': 'festivals'
    },
    'expositions': {
        'label': 'Expositions',
        'icon': 'palette',
        'color': 'blue',
        'filter_type': 'event_type',
        'filter_value': 'expositions'
    },
    'marches': {
        'label': 'Marchés aux puces',
        'icon': 'store',
        'color': 'darkgreen',
        'filter_type': 'event_type',
        'filter_value': 'marches'
    },

    # Category groups (filtrage par category_groups)
    'culture_arts': {
        'label': 'Culture & Arts',
        'icon': 'paint-brush',
        'color': 'purple',
        'filter_type': 'category_group',
        'categories': ['Art', 'Film', 'Fashion', 'Anime']
    },
    'nature_outdoor': {
        'label': 'Nature & Extérieur',
        'icon': 'tree',
        'color': 'green',
        'filter_type': 'category_group',
        'categories': ['Nature', 'Illumination', 'Fireworks']
    },
    'entertainment': {
        'label': 'Divertissement',
        'icon': 'music',
        'color': 'red',
        'filter_type': 'category_group',
        'categories': ['Music', 'Comedy', 'Party', 'Festival']
    },
    'sport_activities': {
        'label': 'Sport & Activités',
        'icon': 'running',
        'color': 'orange',
        'filter_type': 'category_group',
        'categories': ['Sport', 'Workshop']
    },
    'food_markets': {
        'label': 'Gastronomie',
        'icon': 'utensils',
        'color': 'lightblue',
        'filter_type': 'category_group',
        'categories': ['Food', 'Market']
    },
    'community': {
        'label': 'Communauté',
        'icon': 'handshake',
        'color': 'cadetblue',
        'filter_type': 'category_group',
        'categories': ['Charity', 'Volunteering', 'Trade Show']
    }
}
