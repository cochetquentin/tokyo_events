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
