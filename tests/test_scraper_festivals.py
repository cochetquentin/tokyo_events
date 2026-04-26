"""
Tests unitaires pour les méthodes du scraper Festivals.
Ne testent PAS les requêtes HTTP — uniquement la logique pure.
"""

import pytest
from src.scraper_festivals_tokyo import TokyoFestivalScraper


@pytest.fixture
def scraper():
    return TokyoFestivalScraper()


class TestGetUrl:
    """Tests pour get_url()"""

    def test_url_format_march_2025(self, scraper):
        url = scraper.get_url(3, 2025)
        assert "mars" in url
        assert "2025" in url

    def test_url_format_january(self, scraper):
        url = scraper.get_url(1, 2026)
        assert "janvier" in url
        assert "2026" in url

    def test_url_format_december(self, scraper):
        url = scraper.get_url(12, 2025)
        assert "decembre" in url

    def test_url_format_all_months(self, scraper):
        expected_names = {
            1: "janvier", 2: "fevrier", 3: "mars", 4: "avril",
            5: "mai", 6: "juin", 7: "juillet", 8: "aout",
            9: "septembre", 10: "octobre", 11: "novembre", 12: "decembre"
        }
        for month, name in expected_names.items():
            url = scraper.get_url(month, 2025)
            assert name in url, f"Month {month}: expected '{name}' in URL '{url}'"

    def test_invalid_month_raises(self, scraper):
        with pytest.raises(ValueError):
            scraper.get_url(0, 2025)

    def test_invalid_month_13_raises(self, scraper):
        with pytest.raises(ValueError):
            scraper.get_url(13, 2025)

    def test_url_is_string(self, scraper):
        url = scraper.get_url(4, 2025)
        assert isinstance(url, str)
        assert url.startswith("http")


class TestEnrichWithGps:
    """Tests pour _enrich_with_gps()"""

    def test_enriches_festival_with_valid_coords(self, scraper):
        festivals = [
            {
                'name': 'Senso-ji Festival',
                'googlemap_link': 'https://www.google.com/maps/@35.7148,139.7967,17z'
            }
        ]
        count = scraper._enrich_with_gps(festivals)
        assert count == 1
        assert 'latitude' in festivals[0]
        assert 'longitude' in festivals[0]
        assert abs(festivals[0]['latitude'] - 35.7148) < 0.001

    def test_skips_festival_without_link(self, scraper):
        festivals = [{'name': 'Festival', 'googlemap_link': None}]
        count = scraper._enrich_with_gps(festivals)
        assert count == 0
        assert 'latitude' not in festivals[0]

    def test_skips_coords_outside_tokyo(self, scraper):
        festivals = [
            {
                'name': 'Non-Tokyo Event',
                'googlemap_link': 'https://maps.google.com/@48.8566,2.3522,15z'
            }
        ]
        count = scraper._enrich_with_gps(festivals)
        assert count == 0

    def test_multiple_festivals_mixed(self, scraper):
        festivals = [
            {'name': 'A', 'googlemap_link': 'https://www.google.com/maps/@35.7148,139.7967,17z'},
            {'name': 'B', 'googlemap_link': None},
            {'name': 'C', 'googlemap_link': 'https://maps.google.com/@35.6762,139.6503,17z'},
        ]
        count = scraper._enrich_with_gps(festivals)
        assert count == 2
        assert 'latitude' in festivals[0]
        assert 'latitude' not in festivals[1]
        assert 'latitude' in festivals[2]

    def test_empty_list(self, scraper):
        count = scraper._enrich_with_gps([])
        assert count == 0
