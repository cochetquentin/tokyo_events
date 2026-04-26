"""
Tests unitaires pour les méthodes de parsing du scraper Tokyo Cheapo.
Ne testent PAS les requêtes HTTP — uniquement la logique de parsing.
"""

import pytest
from bs4 import BeautifulSoup
from src.scraper_tokyo_cheapo import TokyoCheapoScraper


@pytest.fixture
def scraper():
    return TokyoCheapoScraper()


def make_card(html: str) -> BeautifulSoup:
    """Helper: parse un fragment HTML en élément BeautifulSoup."""
    return BeautifulSoup(html, 'html.parser')


class TestMapCategoryToEventType:
    """Tests pour _map_category_to_event_type()"""

    def test_festival(self, scraper):
        assert scraper._map_category_to_event_type("festival") == "festivals"
        assert scraper._map_category_to_event_type("Festival") == "festivals"

    def test_exhibition(self, scraper):
        assert scraper._map_category_to_event_type("exhibition") == "expositions"
        assert scraper._map_category_to_event_type("art") == "expositions"
        assert scraper._map_category_to_event_type("art exhibition") == "expositions"

    def test_market(self, scraper):
        assert scraper._map_category_to_event_type("market") == "marches"
        assert scraper._map_category_to_event_type("flea market") == "marches"

    def test_fireworks(self, scraper):
        assert scraper._map_category_to_event_type("fireworks") == "hanabi"

    def test_unknown_category_defaults_to_tokyo_cheapo(self, scraper):
        assert scraper._map_category_to_event_type("comedy") == "tokyo_cheapo"
        assert scraper._map_category_to_event_type("nature") == "tokyo_cheapo"
        assert scraper._map_category_to_event_type("sport") == "tokyo_cheapo"

    def test_empty_category_defaults_to_tokyo_cheapo(self, scraper):
        assert scraper._map_category_to_event_type("") == "tokyo_cheapo"
        assert scraper._map_category_to_event_type(None) == "tokyo_cheapo"

    def test_case_insensitive(self, scraper):
        assert scraper._map_category_to_event_type("FESTIVAL") == "festivals"
        assert scraper._map_category_to_event_type("Exhibition") == "expositions"


class TestParseSingleDateBox:
    """Tests pour _parse_single_date_box() — variant CSS class 'single'"""

    def test_valid_single_date(self, scraper):
        html = """
        <div class="card--event__date-box single">
            <div class="day">Sun, Mar</div>
            <div class="date">01</div>
        </div>
        """
        date_box = make_card(html).select_one('.card--event__date-box')
        start, end = scraper._parse_single_date_box(date_box, 2026)
        assert start is not None
        assert start == end  # Single date: start == end
        assert "/03/01" in start

    def test_missing_day_elem(self, scraper):
        html = """
        <div class="card--event__date-box single">
            <div class="date">01</div>
        </div>
        """
        date_box = make_card(html).select_one('.card--event__date-box')
        start, end = scraper._parse_single_date_box(date_box, 2026)
        assert start is None
        assert end is None


class TestParseRangeDateBox:
    """Tests pour _parse_range_date_box() — variant CSS class 'multi'"""

    def test_valid_same_year_range(self, scraper):
        html = """
        <div class="card--event__date-box multi">
            <div class="date">Feb 28</div>
            <div class="date">Mar 15</div>
        </div>
        """
        date_box = make_card(html).select_one('.card--event__date-box')
        start, end = scraper._parse_range_date_box(date_box, 2026)
        assert start == "2026/02/28"
        assert end == "2026/03/15"

    def test_missing_date_elems(self, scraper):
        html = """<div class="card--event__date-box multi"></div>"""
        date_box = make_card(html).select_one('.card--event__date-box')
        start, end = scraper._parse_range_date_box(date_box, 2026)
        assert start is None
        assert end is None

    def test_only_one_date_elem(self, scraper):
        html = """
        <div class="card--event__date-box multi">
            <div class="date">Feb 28</div>
        </div>
        """
        date_box = make_card(html).select_one('.card--event__date-box')
        start, end = scraper._parse_range_date_box(date_box, 2026)
        assert start is None
        assert end is None


class TestParseMultiyearDateBox:
    """Tests pour _parse_multiyear_date_box() — variant CSS class 'multi-year'"""

    def test_cross_year_range(self, scraper):
        html = """
        <div class="card--event__date-box multi-year">
            <div class="date">Nov 17</div>
            <div class="date">Mar 1 2026</div>
        </div>
        """
        date_box = make_card(html).select_one('.card--event__date-box')
        start, end = scraper._parse_multiyear_date_box(date_box, 2026)
        assert start == "2025/11/17"
        assert end == "2026/03/01"

    def test_missing_date_elems(self, scraper):
        html = """<div class="card--event__date-box multi-year"></div>"""
        date_box = make_card(html).select_one('.card--event__date-box')
        start, end = scraper._parse_multiyear_date_box(date_box, 2026)
        assert start is None
        assert end is None


class TestParseDateBox:
    """Tests pour _parse_date_box() — dispatch vers le bon variant"""

    def test_single_variant_dispatched(self, scraper):
        card_html = """
        <article class="card--event">
            <div class="card--event__date-box single">
                <div class="day">Mon, Apr</div>
                <div class="date">05</div>
            </div>
        </article>
        """
        card = make_card(card_html).select_one('article')
        start, end = scraper._parse_date_box(card)
        assert start is not None
        assert start == end
        assert "/04/05" in start

    def test_multi_variant_dispatched(self, scraper):
        card_html = """
        <article class="card--event">
            <div class="card--event__date-box multi">
                <div class="date">Jan 10</div>
                <div class="date">Feb 20</div>
            </div>
        </article>
        """
        card = make_card(card_html).select_one('article')
        start, end = scraper._parse_date_box(card)
        assert start == "2026/01/10"
        assert end == "2026/02/20"

    def test_no_date_box_returns_none(self, scraper):
        card_html = """<article class="card--event"><h3>Event</h3></article>"""
        card = make_card(card_html).select_one('article')
        start, end = scraper._parse_date_box(card)
        assert start is None
        assert end is None

    def test_unknown_variant_returns_none(self, scraper):
        card_html = """
        <article class="card--event">
            <div class="card--event__date-box other-class"></div>
        </article>
        """
        card = make_card(card_html).select_one('article')
        start, end = scraper._parse_date_box(card)
        assert start is None
        assert end is None


class TestParseAttributes:
    """Tests pour _parse_attributes()"""

    def test_extract_hours(self, scraper):
        html = """
        <article>
            <div class="card--event__attribute">
                <div class="cheapo-icon" title="Start/end time"></div>
                <span>10:00 - 18:00</span>
            </div>
        </article>
        """
        card = make_card(html).select_one('article')
        attrs = scraper._parse_attributes(card)
        assert attrs.get('hours') == "10:00 - 18:00"

    def test_extract_category(self, scraper):
        html = """
        <article>
            <div class="card--event__attribute">
                <div class="cheapo-icon" title="Category"></div>
                <a href="/category/festival/">Festival</a>
            </div>
        </article>
        """
        card = make_card(html).select_one('article')
        attrs = scraper._parse_attributes(card)
        assert attrs.get('category') == "Festival"

    def test_extract_location(self, scraper):
        html = """
        <article>
            <div class="card__category label">
                <a href="/area/shibuya/">Shibuya</a>
            </div>
        </article>
        """
        card = make_card(html).select_one('article')
        attrs = scraper._parse_attributes(card)
        assert attrs.get('location') == "Shibuya"

    def test_empty_card(self, scraper):
        html = """<article></article>"""
        card = make_card(html).select_one('article')
        attrs = scraper._parse_attributes(card)
        assert attrs == {}

    def test_multiple_attributes(self, scraper):
        html = """
        <article>
            <div class="card--event__attribute">
                <div class="cheapo-icon" title="Start/end time"></div>
                <span>10:00 - 18:00</span>
            </div>
            <div class="card--event__attribute">
                <div class="cheapo-icon" title="Category"></div>
                <a href="/cat/art/">Art Exhibition</a>
            </div>
            <div class="card__category label">
                <a href="/area/shinjuku/">Shinjuku</a>
            </div>
        </article>
        """
        card = make_card(html).select_one('article')
        attrs = scraper._parse_attributes(card)
        assert attrs.get('hours') == "10:00 - 18:00"
        assert attrs.get('category') == "Art Exhibition"
        assert attrs.get('location') == "Shinjuku"


class TestEnrichWithGps:
    """Tests pour _enrich_with_gps()"""

    def test_enriches_event_with_valid_coords(self, scraper):
        events = [
            {
                'name': 'Test Event',
                'googlemap_link': 'https://www.google.com/maps/@35.7147,139.7967,17z'
            }
        ]
        count = scraper._enrich_with_gps(events)
        assert count == 1
        assert 'latitude' in events[0]
        assert 'longitude' in events[0]

    def test_skips_event_without_googlemap_link(self, scraper):
        events = [{'name': 'Test Event', 'googlemap_link': None}]
        count = scraper._enrich_with_gps(events)
        assert count == 0
        assert 'latitude' not in events[0]

    def test_skips_coords_outside_tokyo(self, scraper):
        events = [
            {
                'name': 'Paris Event',
                'googlemap_link': 'https://maps.google.com/@48.8566,2.3522,15z'
            }
        ]
        count = scraper._enrich_with_gps(events)
        assert count == 0
        assert 'latitude' not in events[0]

    def test_empty_list(self, scraper):
        count = scraper._enrich_with_gps([])
        assert count == 0
