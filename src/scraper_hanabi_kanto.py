"""
Scraper pour les feux d'artifice (hanabi) de la région Kanto
Source: https://hanabi.walkerplus.com/list/ar0300/
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Optional
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from src.date_utils import parse_japanese_dates, parse_japanese_dates_list, format_date_range
from src.database import EventDatabase


class KantoHanabiScraper:
    """
    Scraper for Kanto region hanabi (fireworks) events from walkerplus.com

    Features:
    - Two-stage scraping: list page (basic) + detail pages (extended)
    - Japanese date parsing (YYYY年MM月DD日 → YYYY/MM/DD)
    - Region-based (entire Kanto, not monthly pages)
    - Rate limiting (0.5s between requests)
    """

    BASE_URL = "https://hanabi.walkerplus.com"
    LIST_URL = "https://hanabi.walkerplus.com/list/ar0300/"

    # Prefecture codes in Kanto region
    PREFECTURES = {
        'ar0313': '東京都',      # Tokyo
        'ar0314': '神奈川県',    # Kanagawa
        'ar0312': '千葉県',      # Chiba
        'ar0311': '埼玉県',      # Saitama
        'ar0310': '群馬県',      # Gunma
        'ar0309': '栃木県',      # Tochigi
        'ar0308': '茨城県'       # Ibaraki
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def scrape_hanabi(self, months_ahead: int = 6) -> List[Dict]:
        """
        Main entry point: scrape hanabi events for upcoming months

        Args:
            months_ahead: Number of months ahead to filter (default: 6)

        Returns:
            List of hanabi events with complete data (13 fields)
        """
        print(f"📋 Scraping liste Kanto...")

        # Stage 1: Get all events from list page
        events = self._scrape_list_page()

        print(f"✓ {len(events)} événements trouvés sur la page liste")

        # Filter by date range
        events = self._filter_by_date_range(events, months_ahead)

        print(f"✓ {len(events)} événements dans les {months_ahead} prochains mois")

        # Stage 2: Enrich with detail data
        print(f"\n📝 Scraping des détails ({len(events)} événements)...")
        events = self._enrich_with_details(events)

        return events

    def _scrape_list_page(self) -> List[Dict]:
        """
        Stage 1: Scrape list page for basic event info

        Uses JSON-LD data embedded in the page (schema.org Event data)

        Returns:
            List of events with basic fields
        """
        try:
            response = self.session.get(self.LIST_URL, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ Erreur lors du chargement de la page liste: {e}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        event_ids_seen = set()

        # Method 1: Parse JSON-LD data (more reliable, but limited to ~7 events)
        json_ld_scripts = soup.find_all('script', type='application/ld+json')

        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                # Data can be a list or a single object
                if isinstance(data, list):
                    for event_data in data:
                        if event_data.get('@type') == 'Event':
                            event = self._parse_json_ld_event(event_data)
                            if event and event.get('event_id'):
                                event_ids_seen.add(event['event_id'])
                                events.append(event)
                elif isinstance(data, dict) and data.get('@type') == 'Event':
                    event = self._parse_json_ld_event(data)
                    if event and event.get('event_id'):
                        event_ids_seen.add(event['event_id'])
                        events.append(event)
            except json.JSONDecodeError as e:
                print(f"  ⚠️ Erreur JSON: {e}")
                continue

        print(f"  • {len(events)} événements depuis JSON-LD")

        # Method 2: Parse HTML cards (to get ALL events)
        # Structure: <li class="lists"><a href="/detail/...">
        event_cards = soup.find_all('li', class_='lists')

        for card in event_cards:
            link = card.find('a', href=re.compile(r'/detail/ar\d+e\d+/'))
            if not link:
                continue

            try:
                event = self._parse_html_event_card(card)
                if event and event.get('event_id'):
                    # Skip if already parsed from JSON-LD
                    if event['event_id'] not in event_ids_seen:
                        event_ids_seen.add(event['event_id'])
                        events.append(event)
            except Exception as e:
                print(f"  ⚠️ Erreur parsing HTML card: {e}")
                continue

        print(f"  • {len(events)} événements au total (JSON-LD + HTML)")

        return events

    def _parse_html_event_card(self, card_elem) -> Optional[Dict]:
        """
        Parse event data from HTML card element

        Args:
            card_elem: BeautifulSoup element for event card

        Returns:
            Event dict with our fields or None
        """
        try:
            # Find link to detail page
            link = card_elem.find('a', href=re.compile(r'/detail/ar\d+e\d+/'))
            if not link:
                return None

            # Extract event_id from URL
            href = link.get('href', '')
            event_id_match = re.search(r'/detail/(ar\d+e\d+)/', href)
            if not event_id_match:
                return None

            event_id = event_id_match.group(1)

            # Extract prefecture from event_id (ar0313 → Tokyo)
            prefecture_code = event_id[:6]
            prefecture = self.PREFECTURES.get(prefecture_code, '')

            # Extract city: <div class="area_name">
            city_elem = link.find('div', class_='area_name')
            city = city_elem.get_text(strip=True) if city_elem else ''
            # Remove icon text
            city = re.sub(r'^.*?>', '', city).strip()

            # Extract name: <p class="name">
            name_elem = link.find('p', class_='name')
            name = name_elem.get_text(strip=True) if name_elem else ''

            if not name:
                return None

            # Extract dates: <div class="detail">
            detail_elem = link.find('div', class_='detail')
            dates_text = ''
            if detail_elem:
                # Remove "期間：" prefix
                dates_text = detail_elem.get_text(strip=True)
                dates_text = re.sub(r'^.*?期間：', '', dates_text).strip()

            # Parse dates - get full list
            dates_list = parse_japanese_dates_list(dates_text) if dates_text else []

            # Build location string
            location = f"{city}, {prefecture}" if city and prefecture else (city or prefecture or '')

            # Build detail URL
            detail_url = f"{self.BASE_URL}/detail/{event_id}/" if event_id else None

            # Create event dict
            event = {
                # Core fields
                'name': name,
                'event_id': event_id,
                'dates': dates_list,  # List of all individual dates ["2026/01/17", "2026/01/24", ...]
                'start_date': dates_list[0] if dates_list else None,  # First date (for filtering)
                'end_date': dates_list[-1] if dates_list else None,  # Last date (for filtering)

                # Location fields
                'prefecture': prefecture,
                'city': city,
                'venue': None,  # Will be filled in detail scraping

                # Event details
                'description': '',  # Will be filled in detail scraping
                'start_time': None,  # Will be filled in detail scraping
                'fireworks_count': None,  # Will be filled in detail scraping

                # Links
                'detail_url': detail_url,  # Direct link to event page on walkerplus
                'googlemap_link': None
            }

            return event

        except Exception as e:
            print(f"  ⚠️ Erreur parsing HTML card: {e}")
            return None

    def _parse_json_ld_event(self, event_data: dict) -> Optional[Dict]:
        """
        Parse event data from JSON-LD schema.org format

        Args:
            event_data: Event dict from JSON-LD

        Returns:
            Event dict with our fields or None
        """
        try:
            # Extract basic info
            name = event_data.get('name', '')
            if not name:
                return None

            # Extract dates (format: "2026-01-17")
            start_date_iso = event_data.get('startDate')
            end_date_iso = event_data.get('endDate')

            # Convert ISO format to our format: 2026-01-17 → 2026/01/17
            start_date = start_date_iso.replace('-', '/') if start_date_iso else None
            end_date = end_date_iso.replace('-', '/') if end_date_iso else None

            # Extract location info
            location_data = event_data.get('location', {})
            venue = location_data.get('name', '')

            address_data = location_data.get('address', {})
            city = address_data.get('addressLocality', '')
            prefecture = address_data.get('addressRegion', '')

            # Extract event_id and URL from JSON-LD
            url = event_data.get('url', '')
            event_id_match = re.search(r'/detail/(ar\d+e\d+)/', url)
            event_id = event_id_match.group(1) if event_id_match else None

            # Full detail URL
            detail_url = f"{self.BASE_URL}{url}" if url and url.startswith('/') else url

            # Extract description
            description = event_data.get('description', '')

            # Build dates list (JSON-LD doesn't have detailed dates, will be limited)
            dates_list = [start_date] if start_date == end_date and start_date else []
            if not dates_list and start_date and end_date:
                dates_list = [start_date, end_date]

            # Create event dict
            event = {
                # Core fields
                'name': name,
                'event_id': event_id,
                'dates': dates_list,  # List of individual dates
                'start_date': start_date,
                'end_date': end_date,

                # Location fields
                'prefecture': prefecture,
                'city': city,
                'venue': venue,

                # Event details
                'description': description[:500] if description else '',  # Limit to 500 chars
                'start_time': None,  # Will be filled in detail scraping
                'fireworks_count': None,  # Will be filled in detail scraping

                # Links
                'detail_url': detail_url,  # Direct link to event page on walkerplus
                'googlemap_link': None  # Will be filled in detail scraping
            }

            return event

        except Exception as e:
            print(f"  ⚠️ Erreur parsing JSON-LD event: {e}")
            return None

    def _filter_by_date_range(self, events: List[Dict], months_ahead: int) -> List[Dict]:
        """
        Filter events to keep only upcoming events within N months

        Keeps events where:
        - end_date >= today (event not yet finished)
        - start_date <= today + N months (event starts within the next N months)

        Args:
            events: List of events
            months_ahead: Number of months ahead

        Returns:
            Filtered list of events
        """
        if months_ahead <= 0:
            return events

        # Calculate date range: today to today + N months
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = today + relativedelta(months=months_ahead)

        filtered = []
        for event in events:
            start_date_str = event.get('start_date')
            end_date_str = event.get('end_date')

            if not end_date_str:
                continue

            try:
                # Parse dates: "2026/01/17" → datetime
                end_date = datetime.strptime(end_date_str, '%Y/%m/%d')
                start_date = datetime.strptime(start_date_str, '%Y/%m/%d') if start_date_str else end_date

                # Keep event if:
                # 1. Event is not yet finished: end_date >= today
                # 2. Event starts within the next N months: start_date <= cutoff_date
                if end_date >= today and start_date <= cutoff_date:
                    filtered.append(event)

            except ValueError:
                # Skip events with invalid date format
                print(f"  ⚠️ Date invalide ignorée: {start_date_str} / {end_date_str} pour {event.get('name', 'Unknown')[:50]}")
                continue

        return filtered

    def _scrape_detail_page(self, event_id: str) -> Dict:
        """
        Stage 2: Scrape detail page for extended info

        Args:
            event_id: Event ID (e.g., "ar0313e335967")

        Returns:
            Dict with extended fields including detailed dates list
        """
        detail_url = f"{self.BASE_URL}/detail/{event_id}/"

        try:
            response = self.session.get(detail_url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"  ⚠️ Erreur page détail {event_id}: {e}")
            return {}

        soup = BeautifulSoup(response.content, 'html.parser')
        detail_data = {}

        # Extract full page text for pattern matching
        page_text = soup.get_text(separator=' ')

        # Extract detailed dates from "開催期間" section
        # Pattern: "開催期間 2026年1月17日(土)・24日(土)・31日(土)、2月7日(土)・14日(土)"
        dates_match = re.search(r'開催期間\s+(.+?)(?:開催時間|$)', page_text, re.DOTALL)
        if dates_match:
            dates_text = dates_match.group(1).strip()
            # Remove line breaks and extra spaces
            dates_text = re.sub(r'\s+', ' ', dates_text)
            # Parse all individual dates
            dates_list = parse_japanese_dates_list(dates_text)
            if dates_list:
                detail_data['dates'] = dates_list
                detail_data['start_date'] = dates_list[0]
                detail_data['end_date'] = dates_list[-1]

        # Extract start time: pattern "19:15～19:25" or "19:15~19:25"
        time_match = re.search(r'(\d{1,2}:\d{2})[～〜~](\d{1,2}:\d{2})', page_text)
        if time_match:
            detail_data['start_time'] = time_match.group(1)

        # Extract fireworks count: pattern "1200発" or "延べ6000発"
        fireworks_match = re.search(r'([\d,]+)発', page_text)
        if fireworks_match:
            # Try to find more context (e.g., "1日1200発×5日間で、延べ6000発")
            context_match = re.search(r'(.{0,50}[\d,]+発.{0,50})', page_text)
            if context_match:
                detail_data['fireworks_count'] = context_match.group(1).strip()
            else:
                detail_data['fireworks_count'] = f"{fireworks_match.group(1)}発"

        # Extract venue/location name
        # Usually near "会場" or at the top of the page
        venue_match = re.search(r'会場[：:]\s*([^\n<]+)', page_text)
        if venue_match:
            detail_data['venue'] = venue_match.group(1).strip()

        # Extract description: look for main content area
        # Typically in a specific div or section
        description_elem = soup.find('div', class_=re.compile(r'description|content|detail'))
        if description_elem:
            desc_text = description_elem.get_text(separator=' ', strip=True)
            if len(desc_text) > 50:
                detail_data['description'] = desc_text[:500]  # Limit to 500 chars

        # Extract Google Maps link
        maps_link = soup.find('a', href=re.compile(r'google.*maps|maps\.app\.goo\.gl'))
        if maps_link:
            detail_data['googlemap_link'] = maps_link.get('href')

        return detail_data

    def _enrich_with_details(self, events: List[Dict]) -> List[Dict]:
        """
        Enrich events with detail page data

        Args:
            events: List of events with basic data

        Returns:
            List of events with enriched data
        """
        total = len(events)

        for i, event in enumerate(events, 1):
            event_id = event.get('event_id')
            if not event_id:
                continue

            print(f"  [{i}/{total}] {event['name'][:50]}...")

            # Scrape detail page
            detail_data = self._scrape_detail_page(event_id)

            # Merge detail data into event
            event.update(detail_data)

            # Rate limiting: wait 0.5s between requests (except for last event)
            if i < total:
                time.sleep(0.5)

        print(f"\n✓ Scraping détails terminé")
        return events

    def save_to_database(self, events: List[Dict], db_path: str = None):
        """
        Sauvegarde les hanabi dans la base de données SQLite.

        Args:
            events: Liste des événements hanabi
            db_path: Chemin vers la base de données (optionnel, par défaut data/tokyo_events.sqlite)

        Returns:
            int: Nombre d'événements sauvegardés
        """
        if not db_path:
            db_path = "data/tokyo_events.sqlite"

        db = EventDatabase(db_path)
        count = db.insert_events(events, event_type='hanabi')

        print(f"\n✓ {count} hanabi sauvegardés dans la base de données {db_path}")
        return count


def main():
    """
    Test function
    """
    scraper = KantoHanabiScraper()

    print("=== Scraper Hanabi Kanto ===\n")

    events = scraper.scrape_hanabi(months_ahead=6)

    if events:
        scraper.save_to_database(events)

        print(f"\n📊 Résumé:")
        print(f"  • Événements trouvés: {len(events)}")
        print(f"  • Avec horaires: {sum(1 for e in events if e.get('start_time'))}/{len(events)}")
        print(f"  • Avec nb de feux: {sum(1 for e in events if e.get('fireworks_count'))}/{len(events)}")
        print(f"  • Avec website: {sum(1 for e in events if e.get('website'))}/{len(events)}")
        print(f"  • Avec Google Maps: {sum(1 for e in events if e.get('googlemap_link'))}/{len(events)}")

        # Display first 3 events
        print(f"\n=== Aperçu des 3 premiers événements ===")
        for i, event in enumerate(events[:3], 1):
            print(f"\n{i}. {event['name']}")
            if event.get('start_date'):
                dates = format_date_range(event['start_date'], event['end_date'])
                print(f"   Dates: {dates}")
            if event.get('location'):
                print(f"   Lieu: {event['location']}")
            if event.get('start_time'):
                print(f"   Heure: {event['start_time']}")


if __name__ == "__main__":
    main()
