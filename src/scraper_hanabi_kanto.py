"""
Scraper pour les feux d'artifice (hanabi) de la région Kanto
Source: https://hanabi.walkerplus.com/list/ar0300/
"""

import sys
import os

# Allow running as script (uv run src/scraper_hanabi_kanto.py)
# by ensuring the project root is in sys.path before src.* imports
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

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
from src.gps_extractor import GPSExtractor


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
        Stage 1: Scrape all pages (main Kanto + each prefecture) for event info.

        Returns:
            List of events with basic fields (deduplicated by event_id)
        """
        events = []
        event_ids_seen = set()

        # Collect all URLs to scrape: main Kanto + all paginated prefecture pages
        urls_to_scrape: List[tuple] = [(self.LIST_URL, "Kanto")]

        for code in self.PREFECTURES.keys():
            base_pref_url = f"{self.BASE_URL}/list/{code}/"
            # Discover pagination by fetching first page
            try:
                resp = self.session.get(base_pref_url, timeout=15)
                resp.raise_for_status()
                soup_first = BeautifulSoup(resp.content, 'html.parser')
                pager = soup_first.find('div', class_='pager')
                page_urls = [(base_pref_url, code, soup_first)]  # (url, label, already_fetched_soup)
                if pager:
                    for a in pager.find_all('a', href=re.compile(r'/list/' + code + r'/\d+\.html')):
                        pg_url = f"{self.BASE_URL}{a['href']}"
                        if pg_url not in [u for u, _, _ in page_urls]:
                            page_urls.append((pg_url, code, None))
                for item in page_urls:
                    urls_to_scrape.append(item)
            except requests.RequestException as e:
                print(f"  ⚠️ Erreur découverte pages {code}: {e}")
            time.sleep(0.3)

        # Scrape all collected URLs
        for i, item in enumerate(urls_to_scrape):
            if item[0] == self.LIST_URL:
                url, label = item[0], item[1]
                soup = None
            else:
                url, label, soup = item

            try:
                if soup is None:
                    response = self.session.get(url, timeout=15)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
            except requests.RequestException as e:
                print(f"  ⚠️ Erreur {label} ({url}): {e}")
                continue

            before = len(events)

            # JSON-LD (only on main Kanto page)
            if url == self.LIST_URL:
                for script in soup.find_all('script', type='application/ld+json'):
                    try:
                        data = json.loads(script.string)
                        items = data if isinstance(data, list) else [data]
                        for event_data in items:
                            if event_data.get('@type') == 'Event':
                                event = self._parse_json_ld_event(event_data)
                                if event and event.get('event_id') and event['event_id'] not in event_ids_seen:
                                    event_ids_seen.add(event['event_id'])
                                    events.append(event)
                    except json.JSONDecodeError:
                        continue

            # HTML cards
            for card in soup.find_all('li', class_='lists'):
                if not card.find('a', href=re.compile(r'/detail/ar\d+e\d+/')):
                    continue
                try:
                    event = self._parse_html_event_card(card)
                    if event and event.get('event_id') and event['event_id'] not in event_ids_seen:
                        event_ids_seen.add(event['event_id'])
                        events.append(event)
                except Exception as e:
                    print(f"  ⚠️ Erreur parsing card ({label}): {e}")

            added = len(events) - before
            print(f"  • {label} ({url.split('/')[-1] or 'p1'}): +{added} ({len(events)} total)")

            if i < len(urls_to_scrape) - 1:
                time.sleep(0.5)

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

            # --- Detect page structure ---
            # Kanto main page: p.name.bold + div.area_name
            # Prefecture pages: h2.name + div.area (format: "東京都・港区/会場")
            name_elem = link.find('p', class_='name') or link.find('h2', class_='name')
            name = name_elem.get_text(strip=True) if name_elem else ''

            if not name:
                return None

            # Skip cancelled events
            if re.search(r'【[^】]*(?:中止|非開催|開催なし|中断)[^】]*】', name):
                return None

            # City & venue extraction
            city = ''
            venue = None
            city_elem = link.find('div', class_='area_name')  # Kanto page
            if city_elem:
                city = re.sub(r'^.*?>', '', city_elem.get_text(strip=True)).strip()
            else:
                area_elem = link.find('div', class_='area')   # Prefecture pages
                if area_elem:
                    area_text = area_elem.get_text(strip=True)
                    # Format: "東京都・港区/お台場海浜公園" → city=港区, venue=お台場海浜公園
                    area_match = re.search(r'[都道府県]・(.+?)(?:/(.+))?$', area_text)
                    if area_match:
                        city = area_match.group(1)
                        venue = area_match.group(2) if area_match.group(2) else None

            # Date extraction — find div.detail with "期間："
            dates_text = ''
            start_time = None
            fireworks_count = None
            for detail_elem in link.find_all('div', class_='detail'):
                text = detail_elem.get_text(strip=True)
                if '期間：' in text:
                    dates_text = re.sub(r'^.*?期間：', '', text).strip()
                elif '開催時間：' in text:
                    time_text = re.sub(r'^.*?開催時間：', '', text).strip()
                    tm = re.search(r'(\d{1,2}:\d{2})', time_text)
                    if tm:
                        start_time = tm.group(1)

            # Fireworks count from status list (prefecture pages)
            fw_elem = link.find('li', class_=re.compile(r'icon-ico06'))
            if fw_elem:
                fw_text = fw_elem.get_text(strip=True)
                fw_match = re.search(r'((?:約|延べ)?[0-9万千百,]+[0-9]発|[0-9][0-9,]*発)', fw_text)
                if fw_match:
                    fireworks_count = fw_match.group(1)

            dates_list = parse_japanese_dates_list(dates_text) if dates_text else []
            detail_url = f"{self.BASE_URL}/detail/{event_id}/"

            return {
                'name': name,
                'event_id': event_id,
                'dates': dates_list,
                'start_date': dates_list[0] if dates_list else None,
                'end_date': dates_list[-1] if dates_list else None,
                'prefecture': prefecture,
                'city': city,
                'venue': venue,
                'description': '',
                'start_time': start_time,
                'fireworks_count': fireworks_count,
                'detail_url': detail_url,
                'googlemap_link': None
            }

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

            # Skip cancelled events
            if re.search(r'【[^】]*(?:中止|非開催|開催なし|中断)[^】]*】', name):
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

        # Build a dict of dl/dt/dd pairs (the page uses this structure for all key data)
        dl_data = {}
        for dl in soup.find_all('dl'):
            for dt in dl.find_all('dt'):
                dd = dt.find_next_sibling('dd')
                if dd:
                    key = dt.get_text(strip=True)
                    val = dd.get_text(strip=True)
                    dl_data[key] = val

        # Extract dates from "開催期間" entry
        if '開催期間' in dl_data:
            dates_text = dl_data['開催期間']
            dates_list = parse_japanese_dates_list(dates_text)
            if dates_list:
                detail_data['dates'] = dates_list
                detail_data['start_date'] = dates_list[0]
                detail_data['end_date'] = dates_list[-1]

        # Extract start time from "開催時間" entry (avoids picking up venue opening hours)
        if '開催時間' in dl_data:
            time_text = dl_data['開催時間']
            time_match = re.search(r'(\d{1,2}:\d{2})', time_text)
            if time_match:
                detail_data['start_time'] = time_match.group(1)

        # Extract venue from FAQ-style DT "打ち上げ場所はどこ？..."
        for key, val in dl_data.items():
            if '打ち上げ場所' in key or '会場' in key:
                # Pattern: "打ち上げ場所はXXXです。" → extract XXX
                venue_match = re.search(r'打ち上げ場所は(.+?)(?:です|。|会場アクセス)', val)
                if venue_match:
                    detail_data['venue'] = venue_match.group(1).strip()
                    break
                # Fallback: "会場：XXX"
                venue_match2 = re.search(r'会場[：:]\s*([^。\n]{3,50})', val)
                if venue_match2:
                    detail_data['venue'] = venue_match2.group(1).strip()
                    break

        # Extract fireworks count from FAQ-style DT "打ち上げ数は何発？"
        for key, val in dl_data.items():
            if '打ち上げ数' in key:
                # Pattern: "打ち上げ数は約1万3000発です。" → "約1万3000発"
                count_match = re.search(r'((?:約|延べ)?[0-9万千百,]+[0-9]発|[0-9][0-9,]*発)', val)
                if count_match:
                    detail_data['fireworks_count'] = count_match.group(1)
                break

        # Extract GPS from map page: /detail/{event_id}/map.html
        # The page has <div class="map_canvas"><iframe src="...maps/embed...q=LAT,LNG...">
        map_url = f"{self.BASE_URL}/detail/{event_id}/map.html"
        try:
            map_resp = self.session.get(map_url, timeout=10)
            if map_resp.status_code == 200:
                map_soup = BeautifulSoup(map_resp.content, 'html.parser')
                map_canvas = map_soup.find('div', class_='map_canvas')
                if map_canvas:
                    iframe = map_canvas.find('iframe')
                    if iframe:
                        src = iframe.get('src', '')
                        coords = re.search(r'[?&](?:q|center)=(-?\d+\.\d+),(-?\d+\.\d+)', src)
                        if coords:
                            detail_data['latitude'] = float(coords.group(1))
                            detail_data['longitude'] = float(coords.group(2))
        except requests.RequestException:
            pass

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

    def _enrich_with_gps(self, events: List[Dict]) -> int:
        """
        Enrichit les événements avec des coordonnées GPS depuis les liens Google Maps.

        Args:
            events: Liste d'événements à enrichir (modifiés en place)

        Returns:
            Nombre d'événements ayant reçu des coordonnées GPS
        """
        gps_extractor = GPSExtractor()
        gps_success = 0

        for event in events:
            if event.get('googlemap_link'):
                coords = gps_extractor.extract_from_googlemap_link(event['googlemap_link'])
                if coords:
                    event['latitude'], event['longitude'] = coords
                    gps_success += 1

        return gps_success

    def save_to_database(self, events: List[Dict], db_path: str = None):
        """
        Sauvegarde les hanabi dans la base de données SQLite.
        Extrait automatiquement les coordonnées GPS depuis les liens Google Maps.

        Args:
            events: Liste des événements hanabi
            db_path: Chemin vers la base de données (optionnel, par défaut data/tokyo_events.sqlite)

        Returns:
            int: Nombre d'événements sauvegardés
        """
        if not db_path:
            db_path = "data/tokyo_events.sqlite"

        gps_success = self._enrich_with_gps(events)

        db = EventDatabase(db_path)
        count = db.insert_events(events, event_type='hanabi')

        print(f"\n✓ {count} hanabi sauvegardés dans la base de données {db_path}")
        if gps_success > 0:
            print(f"✓ {gps_success}/{len(events)} coordonnées GPS extraites automatiquement")
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
    import sys
    import os

    # Fix imports when running as script (uv run src/scraper_hanabi_kanto.py)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Fix emoji encoding on Windows terminals
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    main()
