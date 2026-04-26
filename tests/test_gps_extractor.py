"""
Tests unitaires pour GPSExtractor (sans requêtes HTTP)
"""

import pytest
from src.gps_extractor import GPSExtractor


@pytest.fixture
def extractor():
    return GPSExtractor()


class TestExtractFromLongUrl:
    """Tests pour _extract_from_long_url() — extraction regex directe"""

    def test_standard_google_maps_url(self, extractor):
        url = "https://www.google.com/maps/place/Senso-ji/@35.7147651,139.7966719,17z"
        result = extractor._extract_from_long_url(url)
        assert result is not None
        lat, lon = result
        assert abs(lat - 35.7147651) < 0.0001
        assert abs(lon - 139.7966719) < 0.0001

    def test_url_with_negative_coordinates(self, extractor):
        """Coordonnées négatives (hors Tokyo, mais extraction doit fonctionner)"""
        url = "https://maps.google.com/maps?@-33.8688,151.2093"
        result = extractor._extract_from_long_url(url)
        assert result is not None
        lat, lon = result
        assert lat == -33.8688
        assert lon == 151.2093

    def test_url_without_coordinates(self, extractor):
        url = "https://www.google.com/maps/search/Tokyo+Station"
        result = extractor._extract_from_long_url(url)
        assert result is None

    def test_empty_url(self, extractor):
        result = extractor._extract_from_long_url("")
        assert result is None

    def test_non_maps_url(self, extractor):
        url = "https://tokyocheapo.com/events/"
        result = extractor._extract_from_long_url(url)
        assert result is None

    def test_url_with_multiple_at_signs(self, extractor):
        """Prend le premier groupe @lat,lon trouvé"""
        url = "https://maps.google.com/maps/@35.6762,139.6503,15z/data=abc"
        result = extractor._extract_from_long_url(url)
        assert result is not None
        lat, lon = result
        assert abs(lat - 35.6762) < 0.0001


class TestValidateTokyoCoordinates:
    """Tests pour _validate_tokyo_coordinates()"""

    def test_valid_tokyo_center(self, extractor):
        assert extractor._validate_tokyo_coordinates(35.6762, 139.6503) is True

    def test_valid_kanto_edge_north(self, extractor):
        """Limite nord de la bounding box"""
        assert extractor._validate_tokyo_coordinates(36.4, 139.5) is True

    def test_valid_kanto_edge_south(self, extractor):
        assert extractor._validate_tokyo_coordinates(35.1, 139.0) is True

    def test_invalid_too_far_north(self, extractor):
        assert extractor._validate_tokyo_coordinates(37.0, 139.6) is False

    def test_invalid_too_far_south(self, extractor):
        assert extractor._validate_tokyo_coordinates(34.5, 139.6) is False

    def test_invalid_too_far_east(self, extractor):
        assert extractor._validate_tokyo_coordinates(35.6, 141.0) is False

    def test_invalid_too_far_west(self, extractor):
        assert extractor._validate_tokyo_coordinates(35.6, 138.0) is False

    def test_invalid_paris_coordinates(self, extractor):
        assert extractor._validate_tokyo_coordinates(48.8566, 2.3522) is False

    def test_invalid_sydney_coordinates(self, extractor):
        assert extractor._validate_tokyo_coordinates(-33.8688, 151.2093) is False

    def test_exact_bounds(self, extractor):
        """Les bornes exactes doivent être valides (inclusive)"""
        assert extractor._validate_tokyo_coordinates(35.0, 138.5) is True
        assert extractor._validate_tokyo_coordinates(36.5, 140.5) is True


class TestExtractFromGooglemapLink:
    """Tests pour extract_from_googlemap_link() — sans HTTP"""

    def test_valid_tokyo_long_url(self, extractor):
        url = "https://www.google.com/maps/@35.7147651,139.7966719,17z"
        result = extractor.extract_from_googlemap_link(url)
        assert result is not None
        lat, lon = result
        assert abs(lat - 35.7147651) < 0.0001

    def test_coordinates_outside_tokyo_returns_none(self, extractor):
        """Coordonnées hors Tokyo → None même si extraction réussit"""
        url = "https://maps.google.com/@48.8566,2.3522,15z"
        result = extractor.extract_from_googlemap_link(url)
        assert result is None

    def test_empty_url_returns_none(self, extractor):
        assert extractor.extract_from_googlemap_link("") is None

    def test_none_url_returns_none(self, extractor):
        assert extractor.extract_from_googlemap_link(None) is None

    def test_url_without_coords_returns_none(self, extractor):
        url = "https://www.google.com/maps/place/Tokyo+Station"
        result = extractor.extract_from_googlemap_link(url)
        assert result is None
