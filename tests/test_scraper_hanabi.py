"""
Tests unitaires pour les méthodes de parsing du scraper Hanabi.
Ne testent PAS les requêtes HTTP — uniquement la logique de parsing.
"""

import pytest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from src.scraper_hanabi_kanto import KantoHanabiScraper


@pytest.fixture
def scraper():
    return KantoHanabiScraper()


class TestParseJsonLdEvent:
    """Tests pour _parse_json_ld_event()"""

    def test_valid_event(self, scraper):
        data = {
            'name': 'Sumida River Fireworks',
            'startDate': '2026-07-25',
            'endDate': '2026-07-25',
            'location': {
                'name': 'Sumida River',
                'address': {
                    'addressLocality': '台東区',
                    'addressRegion': '東京都'
                }
            },
            'url': '/detail/ar0313e123456/',
            'description': 'Grand fireworks festival'
        }
        result = scraper._parse_json_ld_event(data)
        assert result is not None
        assert result['name'] == 'Sumida River Fireworks'
        assert result['start_date'] == '2026/07/25'
        assert result['end_date'] == '2026/07/25'
        assert result['venue'] == 'Sumida River'
        assert result['city'] == '台東区'
        assert result['prefecture'] == '東京都'
        assert result['event_id'] == 'ar0313e123456'

    def test_iso_date_converted_to_slash_format(self, scraper):
        data = {
            'name': 'Test Hanabi',
            'startDate': '2026-08-01',
            'endDate': '2026-08-01',
            'location': {},
            'url': '/detail/ar0313e999999/'
        }
        result = scraper._parse_json_ld_event(data)
        assert result['start_date'] == '2026/08/01'
        assert result['end_date'] == '2026/08/01'

    def test_cancelled_event_returns_none(self, scraper):
        data = {
            'name': '【中止】Sumida River Fireworks',
            'startDate': '2026-07-25',
            'endDate': '2026-07-25',
            'location': {},
            'url': '/detail/ar0313e123456/'
        }
        result = scraper._parse_json_ld_event(data)
        assert result is None

    def test_other_cancellation_keywords(self, scraper):
        for keyword in ['非開催', '開催なし', '中断']:
            data = {
                'name': f'【{keyword}】Hanabi Event',
                'startDate': '2026-07-25',
                'endDate': '2026-07-25',
                'location': {},
                'url': '/detail/ar0313e100001/'
            }
            result = scraper._parse_json_ld_event(data)
            assert result is None, f"Should be None for keyword {keyword}"

    def test_missing_name_returns_none(self, scraper):
        data = {
            'startDate': '2026-07-25',
            'endDate': '2026-07-25',
            'location': {},
            'url': '/detail/ar0313e123456/'
        }
        result = scraper._parse_json_ld_event(data)
        assert result is None

    def test_event_id_extracted_from_url(self, scraper):
        data = {
            'name': 'Test Hanabi',
            'startDate': '2026-07-25',
            'endDate': '2026-07-25',
            'location': {},
            'url': '/detail/ar0314e999888/'
        }
        result = scraper._parse_json_ld_event(data)
        assert result['event_id'] == 'ar0314e999888'

    def test_description_truncated_to_500_chars(self, scraper):
        long_desc = "A" * 600
        data = {
            'name': 'Test Hanabi',
            'startDate': '2026-07-25',
            'endDate': '2026-07-25',
            'location': {},
            'url': '/detail/ar0313e111/',
            'description': long_desc
        }
        result = scraper._parse_json_ld_event(data)
        assert len(result['description']) == 500

    def test_same_start_end_date_creates_single_date_list(self, scraper):
        data = {
            'name': 'Test Hanabi',
            'startDate': '2026-07-25',
            'endDate': '2026-07-25',
            'location': {},
            'url': '/detail/ar0313e111/'
        }
        result = scraper._parse_json_ld_event(data)
        assert result['dates'] == ['2026/07/25']

    def test_different_start_end_creates_two_date_list(self, scraper):
        data = {
            'name': 'Test Hanabi',
            'startDate': '2026-07-25',
            'endDate': '2026-07-26',
            'location': {},
            'url': '/detail/ar0313e111/'
        }
        result = scraper._parse_json_ld_event(data)
        assert '2026/07/25' in result['dates']
        assert '2026/07/26' in result['dates']


class TestFilterByDateRange:
    """Tests pour _filter_by_date_range()"""

    def _make_event(self, start: str, end: str) -> dict:
        return {'name': 'Test', 'start_date': start, 'end_date': end}

    def test_upcoming_event_kept(self, scraper):
        today = datetime.now()
        future_start = (today + timedelta(days=10)).strftime('%Y/%m/%d')
        future_end = (today + timedelta(days=30)).strftime('%Y/%m/%d')
        events = [self._make_event(future_start, future_end)]
        result = scraper._filter_by_date_range(events, months_ahead=3)
        assert len(result) == 1

    def test_past_event_removed(self, scraper):
        past_start = "2020/01/01"
        past_end = "2020/01/10"
        events = [self._make_event(past_start, past_end)]
        result = scraper._filter_by_date_range(events, months_ahead=3)
        assert len(result) == 0

    def test_event_too_far_in_future_removed(self, scraper):
        today = datetime.now()
        far_future = today + relativedelta(months=12)
        future_start = far_future.strftime('%Y/%m/%d')
        future_end = (far_future + timedelta(days=5)).strftime('%Y/%m/%d')
        events = [self._make_event(future_start, future_end)]
        result = scraper._filter_by_date_range(events, months_ahead=3)
        assert len(result) == 0

    def test_ongoing_event_kept(self, scraper):
        """Événement en cours (démarré avant aujourd'hui, pas encore fini)"""
        today = datetime.now()
        started = (today - timedelta(days=5)).strftime('%Y/%m/%d')
        ends = (today + timedelta(days=5)).strftime('%Y/%m/%d')
        events = [self._make_event(started, ends)]
        result = scraper._filter_by_date_range(events, months_ahead=3)
        assert len(result) == 1

    def test_missing_end_date_removed(self, scraper):
        events = [{'name': 'Test', 'start_date': '2026/07/01', 'end_date': None}]
        result = scraper._filter_by_date_range(events, months_ahead=3)
        assert len(result) == 0

    def test_zero_months_returns_all(self, scraper):
        """months_ahead=0 → pas de filtrage"""
        events = [
            self._make_event("2020/01/01", "2020/01/10"),
            self._make_event("2030/01/01", "2030/01/10"),
        ]
        result = scraper._filter_by_date_range(events, months_ahead=0)
        assert len(result) == 2

    def test_invalid_date_format_skipped(self, scraper):
        events = [{'name': 'Test', 'start_date': 'not-a-date', 'end_date': 'also-not'}]
        result = scraper._filter_by_date_range(events, months_ahead=3)
        assert len(result) == 0


class TestEnrichWithGps:
    """Tests pour _enrich_with_gps()"""

    def test_enriches_event_with_valid_coords(self, scraper):
        events = [
            {
                'name': 'Test Hanabi',
                'googlemap_link': 'https://www.google.com/maps/@35.7147,139.7967,17z'
            }
        ]
        count = scraper._enrich_with_gps(events)
        assert count == 1
        assert 'latitude' in events[0]
        assert 'longitude' in events[0]

    def test_skips_event_without_link(self, scraper):
        events = [{'name': 'Test Hanabi', 'googlemap_link': None}]
        count = scraper._enrich_with_gps(events)
        assert count == 0

    def test_empty_list(self, scraper):
        count = scraper._enrich_with_gps([])
        assert count == 0
