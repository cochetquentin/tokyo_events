"""
Module d'extraction de coordonnées GPS depuis les liens Google Maps.
"""

import re
import requests
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class GPSExtractor:
    """Extrait les coordonnées GPS depuis les liens Google Maps."""

    # Regex pour extraire coordonnées des liens longs
    # Format: @35.6641302,139.6648484
    COORDS_PATTERN = re.compile(r'@(-?\d+\.\d+),(-?\d+\.\d+)')

    # Bounding box Tokyo/Kanto pour validation
    TOKYO_BOUNDS = {
        'lat_min': 35.0,
        'lat_max': 36.5,
        'lon_min': 138.5,
        'lon_max': 140.5
    }

    def __init__(self, timeout: int = 5):
        """
        Args:
            timeout: Timeout pour les requêtes HTTP (secondes)
        """
        self.timeout = timeout

    def extract_from_googlemap_link(self, url: str) -> Optional[Tuple[float, float]]:
        """
        Extrait latitude/longitude depuis un lien Google Maps.

        Gère 2 formats:
        1. Liens longs: https://maps.google.com/...@35.66,139.66
        2. Liens courts: https://maps.app.goo.gl/... (dépliage HTTP)

        Args:
            url: Lien Google Maps

        Returns:
            (latitude, longitude) ou None si extraction échoue
        """
        if not url:
            return None

        try:
            # Tenter extraction directe (liens longs)
            coords = self._extract_from_long_url(url)

            if coords:
                if self._validate_tokyo_coordinates(*coords):
                    return coords
                else:
                    logger.warning(f"Coordonnées hors Tokyo: {coords} pour {url}")
                    return None

            # Si échec, tenter dépliage URL (liens courts)
            if 'goo.gl' in url or 'maps.app.goo.gl' in url:
                coords = self._extract_from_short_url(url)

                if coords and self._validate_tokyo_coordinates(*coords):
                    return coords

            logger.debug(f"Aucune coordonnée trouvée pour {url}")
            return None

        except Exception as e:
            logger.error(f"Erreur extraction GPS pour {url}: {e}")
            return None

    def _extract_from_long_url(self, url: str) -> Optional[Tuple[float, float]]:
        """Extrait coordonnées via regex depuis lien long."""
        match = self.COORDS_PATTERN.search(url)
        if match:
            lat, lon = float(match.group(1)), float(match.group(2))
            logger.debug(f"Coordonnées extraites via regex: {lat}, {lon}")
            return (lat, lon)
        return None

    def _extract_from_short_url(self, url: str) -> Optional[Tuple[float, float]]:
        """Extrait coordonnées en suivant la redirection HTTP."""
        try:
            # Suivre la redirection sans télécharger le contenu
            response = requests.head(url, allow_redirects=True, timeout=self.timeout)
            final_url = response.url

            logger.debug(f"URL dépliée: {url} -> {final_url}")

            # Extraire coordonnées de l'URL finale
            return self._extract_from_long_url(final_url)

        except requests.RequestException as e:
            logger.warning(f"Échec dépliage URL {url}: {e}")
            return None

    def _validate_tokyo_coordinates(self, lat: float, lon: float) -> bool:
        """Valide que les coordonnées sont dans la région Tokyo/Kanto."""
        return (
            self.TOKYO_BOUNDS['lat_min'] <= lat <= self.TOKYO_BOUNDS['lat_max'] and
            self.TOKYO_BOUNDS['lon_min'] <= lon <= self.TOKYO_BOUNDS['lon_max']
        )
