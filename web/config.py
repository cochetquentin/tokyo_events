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
