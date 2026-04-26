"""
Tests unitaires pour les méthodes du scraper Marchés aux Puces.
Ne testent PAS les requêtes HTTP — uniquement la logique pure.
"""

import pytest
from bs4 import BeautifulSoup
from src.scraper_marches_tokyo import TokyoMarcheScraper


@pytest.fixture
def scraper():
    return TokyoMarcheScraper()


class TestParsePageBasic:
    """Tests pour _parse_page() — comportements fondamentaux"""

    def _make_soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, 'html.parser')

    def _make_marche_html(self, name: str, description: str = None, date_text: str = None) -> str:
        """Helper: génère le HTML minimal d'un marché valide.

        Un marché n'est retenu que s'il a une start_date OU une description > 20 chars.
        """
        p = ""
        if date_text:
            p += f"<p>{date_text}</p>"
        if description:
            p += f"<p>{description}</p>"
        return f"""
        <html><body>
            <h2 class="wp-block-heading">{name}</h2>
            {p}
        </body></html>
        """

    def test_extracts_marche_name_from_h2(self, scraper):
        html = self._make_marche_html(
            "Marché Arai Yakushi",
            description="Grand marché aux puces mensuel avec antiquités et objets d'occasion"
        )
        result = scraper._parse_page(self._make_soup(html))
        assert len(result) >= 1
        assert any(m['name'] == 'Marché Arai Yakushi' for m in result)

    def test_ignores_noise_keywords(self, scraper):
        html = f"""
        <html><body>
            <h2 class="wp-block-heading">Articles similaires</h2>
            <h2 class="wp-block-heading">Marché Arai Yakushi</h2>
            <p>Grand marché aux puces mensuel avec antiquités et objets d'occasion</p>
        </body></html>
        """
        result = scraper._parse_page(self._make_soup(html))
        names = [m['name'] for m in result]
        assert not any('Articles similaires' in n for n in names)
        assert any('Arai Yakushi' in n for n in names)

    def test_ignores_short_names(self, scraper):
        html = f"""
        <html><body>
            <h2 class="wp-block-heading">AB</h2>
            <h2 class="wp-block-heading">Marché Togo Shrine</h2>
            <p>Grand marché aux puces mensuel avec antiquités et objets d'occasion</p>
        </body></html>
        """
        result = scraper._parse_page(self._make_soup(html))
        names = [m['name'] for m in result]
        assert 'AB' not in names
        assert any('Togo' in n for n in names)

    def test_empty_page_returns_empty_list(self, scraper):
        html = """<html><body></body></html>"""
        result = scraper._parse_page(self._make_soup(html))
        assert result == []

    def test_marche_has_required_keys(self, scraper):
        html = self._make_marche_html(
            "Marché Togo Shrine",
            description="Grand marché aux puces mensuel avec antiquités et objets d'occasion"
        )
        result = scraper._parse_page(self._make_soup(html))
        assert len(result) >= 1
        marche = result[0]
        assert 'name' in marche
        assert 'start_date' in marche
        assert 'dates' in marche


class TestEnrichWithGps:
    """Tests pour _enrich_with_gps()"""

    def test_enriches_marche_with_valid_coords(self, scraper):
        marches = [
            {
                'name': 'Marché Senso-ji',
                'googlemap_link': 'https://www.google.com/maps/@35.7148,139.7967,17z'
            }
        ]
        count = scraper._enrich_with_gps(marches)
        assert count == 1
        assert 'latitude' in marches[0]
        assert 'longitude' in marches[0]

    def test_skips_marche_without_link(self, scraper):
        marches = [{'name': 'Marché', 'googlemap_link': None}]
        count = scraper._enrich_with_gps(marches)
        assert count == 0

    def test_empty_list(self, scraper):
        count = scraper._enrich_with_gps([])
        assert count == 0
