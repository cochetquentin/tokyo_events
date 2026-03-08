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

# Mapping des catégories sources vers les catégories d'affichage
CATEGORY_TO_DISPLAY = {
    # Tokyo Cheapo categories → Display categories
    'Music': 'concerts',
    'Food': 'food',
    'Sport': 'sport',
    'Illumination': 'illuminations',
    'Comedy': 'spectacles',
    'Film': 'spectacles',
    'Party': 'autres',
    'Workshop': 'autres',
    'Nature': 'autres',
    'Anime': 'autres',
    'Fashion': 'autres',
    'Charity': 'autres',
    'Volunteering': 'autres',
    'Trade Show': 'autres',
    'Living': 'autres',
}

# Groupes de catégories pour le filtrage backend
# Chaque clé correspond à une display_category, avec les source categories associées
CATEGORY_GROUPS = {
    'concerts': {
        'label': 'Concerts',
        'categories': ['Music']
    },
    'food': {
        'label': 'Food & Restaurants',
        'categories': ['Food']
    },
    'sport': {
        'label': 'Sport',
        'categories': ['Sport']
    },
    'illuminations': {
        'label': 'Illuminations',
        'categories': ['Illumination']
    },
    'spectacles': {
        'label': 'Spectacles',
        'categories': ['Comedy', 'Film']
    },
    'autres': {
        'label': 'Autres',
        'categories': ['Party', 'Workshop', 'Nature', 'Anime', 'Fashion', 'Charity', 'Volunteering', 'Trade Show', 'Living']
    }
}

# Configuration des catégories d'affichage (10 catégories simples)
ALL_CATEGORIES = {
    'hanabi': {
        'label': 'Hanabi',
        'icon': 'fire',
        'color': '#ff6b35',
        'filter_type': 'event_type',
        'filter_value': 'hanabi'
    },
    'festivals': {
        'label': 'Festivals',
        'icon': 'torii-gate',
        'color': '#ff385c',
        'filter_type': 'event_type',
        'filter_value': 'festivals'
    },
    'expositions': {
        'label': 'Expositions',
        'icon': 'palette',
        'color': '#5b7fff',
        'filter_type': 'event_type',
        'filter_value': 'expositions'
    },
    'marches': {
        'label': 'Marchés',
        'icon': 'store',
        'color': '#00c896',
        'filter_type': 'event_type',
        'filter_value': 'marches'
    },
    'concerts': {
        'label': 'Concerts',
        'icon': 'music',
        'color': '#e91e63',
        'filter_type': 'category_group',
        'categories': ['Music']
    },
    'food': {
        'label': 'Food & Restaurants',
        'icon': 'utensils',
        'color': '#ff9800',
        'filter_type': 'category_group',
        'categories': ['Food']
    },
    'sport': {
        'label': 'Sport',
        'icon': 'running',
        'color': '#4caf50',
        'filter_type': 'category_group',
        'categories': ['Sport']
    },
    'illuminations': {
        'label': 'Illuminations',
        'icon': 'lightbulb',
        'color': '#ffd700',
        'filter_type': 'category_group',
        'categories': ['Illumination']
    },
    'spectacles': {
        'label': 'Spectacles',
        'icon': 'masks-theater',
        'color': '#9c27b0',
        'filter_type': 'category_group',
        'categories': ['Comedy', 'Film']
    },
    'autres': {
        'label': 'Autres',
        'icon': 'calendar',
        'color': '#607d8b',
        'filter_type': 'category_group',
        'categories': ['Party', 'Workshop', 'Nature', 'Anime', 'Fashion', 'Charity', 'Volunteering', 'Trade Show', 'Living']
    }
}

# Backward compatibility
CATEGORY_TO_GROUP = CATEGORY_TO_DISPLAY
