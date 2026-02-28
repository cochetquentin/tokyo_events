"""
Scraper pour les événements Tokyo Cheapo
Source: https://tokyocheapo.com/events/
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional, Tuple
import re
import json
from datetime import datetime

from src.database import EventDatabase
from src.gps_extractor import GPSExtractor
from src.date_utils_en import parse_english_date, parse_english_date_range, parse_single_date_components


class TokyoCheapoScraper:
    """
    Scraper for Tokyo Cheapo events (tokyocheapo.com/events/)

    Features:
    - Two-stage scraping: list pages + detail pages
    - English date parsing (format: "Feb 28", "Mar 1 2026")
    - Pagination auto-detection
    - Rate limiting (0.5s between detail requests)
    - Category mapping to existing event types
    """

    BASE_URL = "https://tokyocheapo.com"
    LIST_URL = "https://tokyocheapo.com/events/"

    # Category mapping (Tokyo Cheapo → our event_type)
    CATEGORY_MAP = {
        'festival': 'festivals',
        'exhibition': 'expositions',
        'art': 'expositions',
        'art exhibition': 'expositions',
        'market': 'marches',
        'flea market': 'marches',
        # Default: 'tokyo_cheapo' for unmapped categories
    }

    def __init__(self):
        """Initialize session with User-Agent header"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def scrape_events(self, max_pages: int = None) -> List[Dict]:
        """
        Main entry point: scrape all events from list + detail pages

        Args:
            max_pages: Limit pagination (None = all pages)

        Returns:
            List of event dicts with standardized schema
        """
        try:
            # Stage 1: List pages
            print(f"📋 Scraping list pages...")
            events = self._scrape_list_pages(max_pages)
            print(f"✓ {len(events)} events found on list pages")

            # Stage 2: Detail pages
            if events:
                print(f"\n📝 Scraping detail pages ({len(events)} events)...")
                events = self._enrich_with_details(events)
                print(f"✓ Detail scraping complete")

            return events

        except requests.RequestException as e:
            print(f"❌ Network error: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _scrape_list_pages(self, max_pages: int = None) -> List[Dict]:
        """
        Stage 1: Scrape all list pages for event stubs

        Args:
            max_pages: Maximum number of pages to scrape (None = all)

        Returns:
            List of event dicts with basic data + detail URLs
        """
        try:
            # Get page 1 to detect total pages
            response = self.session.get(self.LIST_URL, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            total_pages = self._detect_total_pages(soup)
            if max_pages:
                total_pages = min(total_pages, max_pages)

            print(f"📄 Detected {total_pages} pages to scrape")

            events = []

            # Scrape page 1
            page_events = self._parse_list_page(soup)
            events.extend(page_events)
            print(f"  Page 1/{total_pages}: {len(page_events)} events")

            # Scrape remaining pages
            for page_num in range(2, total_pages + 1):
                url = f"{self.BASE_URL}/events/page/{page_num}/"

                try:
                    response = self.session.get(url, timeout=15)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_events = self._parse_list_page(soup)
                    events.extend(page_events)
                    print(f"  Page {page_num}/{total_pages}: {len(page_events)} events")

                    # Small delay between pages
                    if page_num < total_pages:
                        time.sleep(0.2)

                except requests.RequestException as e:
                    print(f"  ⚠️ Error on page {page_num}: {e}")
                    continue

            return events

        except requests.RequestException as e:
            print(f"❌ Error fetching list pages: {e}")
            return []

    def _detect_total_pages(self, soup: BeautifulSoup) -> int:
        """
        Auto-detect total pages from pagination nav

        Returns:
            Max page number (default: 1 if no pagination)
        """
        nav = soup.select_one("nav.post-nav")
        if not nav:
            return 1

        # Find all page links
        page_links = nav.select(".post-page a")
        if not page_links:
            return 1

        # Extract page numbers and find max
        page_numbers = []
        for link in page_links:
            text = link.get_text(strip=True)
            if text.isdigit():
                page_numbers.append(int(text))

        return max(page_numbers) if page_numbers else 1

    def _parse_list_page(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Parse a single list page for event cards

        Returns:
            List of event dicts from this page
        """
        events = []

        # Find all event cards (filters out ads/hotels)
        cards = soup.select('article.card--event')

        for card in cards:
            event = self._parse_event_card(card)
            if event:
                events.append(event)

        return events

    def _parse_event_card(self, card_elem) -> Optional[Dict]:
        """
        Parse single event card from list page

        Returns:
            Event dict or None if parsing fails
        """
        try:
            # Extract title and detail URL
            title_elem = card_elem.select_one('h3.card__title a')
            if not title_elem:
                return None

            name = title_elem.get_text(strip=True)
            detail_url = title_elem.get('href', '')

            if not name or not detail_url:
                return None

            # Make detail URL absolute
            if detail_url.startswith('/'):
                detail_url = self.BASE_URL + detail_url

            # Parse dates
            start_date, end_date = self._parse_date_box(card_elem)

            # Parse attributes (hours, fee, category, location)
            attrs = self._parse_attributes(card_elem)

            # Extract short description
            excerpt_elem = card_elem.select_one('p.card__excerpt')
            description = excerpt_elem.get_text(strip=True) if excerpt_elem else ''

            # Build event dict
            event = {
                'name': name,
                'detail_url': detail_url,
                'start_date': start_date,
                'end_date': end_date,
                'location': attrs.get('location'),
                'description': description,
                'category': attrs.get('category'),
                'hours': attrs.get('hours'),
                'fee': attrs.get('fee'),
                'website': None,  # Will be enriched from detail page
                'googlemap_link': None,  # Will be enriched from detail page
            }

            return event

        except Exception as e:
            print(f"⚠️ Error parsing event card: {e}")
            return None

    def _parse_date_box(self, card_elem) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse date box (3 variants: single, multi, multi-year)

        Returns:
            (start_date, end_date) in YYYY/MM/DD format
        """
        # Find date box
        date_box = card_elem.select_one('.card--event__date-box')
        if not date_box:
            return None, None

        classes = date_box.get('class', [])
        current_year = datetime.now().year

        try:
            # Variant 3: Single date
            if 'single' in classes:
                day_elem = date_box.select_one('div.day')
                date_elem = date_box.select_one('div.date')

                if day_elem and date_elem:
                    day_text = day_elem.get_text(strip=True)  # "Sun, Mar"
                    date_num = date_elem.get_text(strip=True)  # "01"

                    date = parse_single_date_components(day_text, date_num, current_year)
                    return date, date  # Same date for start and end

            # Variant 2: Multi-year range
            elif 'multi-year' in classes:
                date_elems = date_box.select('div.date')
                if len(date_elems) >= 2:
                    start_str = date_elems[0].get_text(strip=True)  # "Nov 17"
                    end_str = date_elems[1].get_text(strip=True)    # "Mar 1 2026"

                    return parse_english_date_range(start_str, end_str, current_year)

            # Variant 1: Same-year range
            elif 'multi' in classes:
                date_elems = date_box.select('div.date')
                if len(date_elems) >= 2:
                    start_str = date_elems[0].get_text(strip=True)  # "Feb 28"
                    end_str = date_elems[1].get_text(strip=True)    # "Mar 1"

                    return parse_english_date_range(start_str, end_str, current_year)

        except Exception as e:
            print(f"⚠️ Error parsing date box: {e}")

        return None, None

    def _parse_attributes(self, card_elem) -> Dict:
        """
        Extract hours, fee, category, location from attribute blocks

        Uses title="..." attribute to distinguish field types

        Returns:
            Dict with 'hours', 'fee', 'category', 'location'
        """
        attrs = {}

        # Find all attribute blocks
        attr_blocks = card_elem.select('div.card--event__attribute')

        for block in attr_blocks:
            icon = block.select_one('div.cheapo-icon')
            if not icon:
                continue

            title = icon.get('title', '')

            if title == 'Start/end time':
                # Hours: value in <span>
                span = block.find('span')
                if span:
                    attrs['hours'] = span.get_text(strip=True)

            elif title == 'Entry':
                # Fee: direct text (not in span)
                # Get all text and remove icon artifacts
                text = block.get_text(separator=' ', strip=True)
                # Clean up: remove extra whitespace
                text = re.sub(r'\s+', ' ', text)
                attrs['fee'] = text if text else None

            elif title == 'Category':
                # Category: in <a> tag
                link = block.find('a')
                if link:
                    attrs['category'] = link.get_text(strip=True)

        # Location: separate block with class "card__category label"
        loc_elem = card_elem.select_one('div.card__category.label a')
        if loc_elem:
            attrs['location'] = loc_elem.get_text(strip=True)

        return attrs

    def _enrich_with_details(self, events: List[Dict]) -> List[Dict]:
        """
        Stage 2: Enrich events with detail page data

        Args:
            events: List of event stubs from list pages

        Returns:
            Events enriched with detail data
        """
        total = len(events)

        for i, event in enumerate(events, 1):
            detail_url = event.get('detail_url')
            if not detail_url:
                continue

            print(f"  [{i}/{total}] {event['name'][:50]}...")

            try:
                detail_data = self._scrape_detail_page(detail_url)
                event.update(detail_data)
            except requests.RequestException as e:
                print(f"    ⚠️ Error fetching detail: {e}")
                continue
            except Exception as e:
                print(f"    ⚠️ Error parsing detail: {e}")
                continue

            # Rate limiting: 0.5s between requests (except last)
            if i < total:
                time.sleep(0.5)

        return events

    def _scrape_detail_page(self, detail_url: str) -> Dict:
        """
        Scrape single detail page for extended info

        Returns:
            Dict with extended fields (description, website, googlemap_link, etc.)
        """
        try:
            response = self.session.get(detail_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            detail_data = {}

            # Extract full description from article content
            # Look for the main content area
            content = soup.select_one('div.article__content')
            if content:
                # Get all paragraphs
                paragraphs = content.find_all('p', recursive=False)
                if paragraphs:
                    # Combine first few paragraphs for description
                    desc_parts = []
                    for p in paragraphs[:3]:  # First 3 paragraphs
                        text = p.get_text(strip=True)
                        if text and len(text) > 20:  # Skip short/empty paragraphs
                            desc_parts.append(text)
                    if desc_parts:
                        detail_data['description'] = ' '.join(desc_parts)

            # Extract GPS coordinates from Apple Maps JSON (Primary method)
            # Tokyo Cheapo uses Apple Maps with embedded JSON in HTML source
            map_div = soup.find('div', {'component-name': 'apple-maps'})
            if map_div:
                json_script = map_div.find('script', {'type': 'application/json'})
                if json_script and json_script.string:
                    try:
                        map_data = json.loads(json_script.string)

                        # Extract GPS coordinates (stored as strings)
                        lat_str = map_data.get('lat')
                        lng_str = map_data.get('lng')

                        if lat_str and lng_str:
                            detail_data['latitude'] = float(lat_str)
                            detail_data['longitude'] = float(lng_str)

                        # Bonus: extract venue and address if not already set
                        if map_data.get('title'):
                            detail_data['venue_name'] = map_data.get('title')
                        if map_data.get('addr'):
                            detail_data['address'] = map_data.get('addr')

                    except (json.JSONDecodeError, ValueError, TypeError) as e:
                        print(f"      ⚠️ Error parsing Apple Maps JSON: {e}")

            # Extract Google Maps link (fallback - rarely used now)
            # Look for links containing "google.com/maps" or "goo.gl"
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                if 'google.com/maps' in href or 'goo.gl' in href:
                    detail_data['googlemap_link'] = href

                    # Extract GPS from googlemap_link if we have one but no coordinates yet
                    if 'latitude' not in detail_data:
                        gps_extractor = GPSExtractor()
                        lat, lon = gps_extractor.extract_from_google_maps_url(href)
                        if lat:
                            detail_data['latitude'] = lat
                            detail_data['longitude'] = lon
                    break

            # Extract official website
            # Look for links in info-box or article content
            # Prioritize links with text like "website", "official", "site"
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()

                # Skip internal tokyocheapo links, google maps, social media
                if any(skip in href for skip in ['tokyocheapo.com', 'google.com/maps', 'facebook.com', 'twitter.com', 'instagram.com', 'goo.gl']):
                    continue

                # Prioritize links with "website" or "official" in text
                if 'website' in text or 'official' in text or 'site' in text:
                    detail_data['website'] = href
                    break

            # If no website found with keywords, take first external link
            if not detail_data.get('website'):
                for link in all_links:
                    href = link.get('href', '')
                    if href.startswith('http') and 'tokyocheapo.com' not in href and 'google.com' not in href:
                        detail_data['website'] = href
                        break

            return detail_data

        except Exception as e:
            print(f"    ⚠️ Error in detail scraping: {e}")
            return {}

    def _map_category_to_event_type(self, category: str) -> str:
        """
        Map Tokyo Cheapo category to our event_type

        Args:
            category: Category from Tokyo Cheapo

        Returns:
            Event type for database ('festivals', 'expositions', etc.)
        """
        if not category:
            return 'tokyo_cheapo'

        category_lower = category.lower().strip()
        return self.CATEGORY_MAP.get(category_lower, 'tokyo_cheapo')

    def save_to_database(self, events: List[Dict], db_path: str = None):
        """
        Save events to database with GPS extraction

        Args:
            events: List of event dicts
            db_path: Database path (default: data/tokyo_events.sqlite)

        Returns:
            Number of events saved
        """
        if not db_path:
            db_path = "data/tokyo_events.sqlite"

        # Extract GPS coordinates
        gps_extractor = GPSExtractor()
        gps_success = 0

        for event in events:
            # Map category to event_type
            event['event_type'] = self._map_category_to_event_type(event.get('category'))

            # Extract GPS from Google Maps link
            if event.get('googlemap_link'):
                coords = gps_extractor.extract_from_googlemap_link(event['googlemap_link'])
                if coords:
                    event['latitude'], event['longitude'] = coords
                    gps_success += 1

        # Group events by type for database insertion
        events_by_type = {}
        for event in events:
            event_type = event.get('event_type', 'tokyo_cheapo')
            if event_type not in events_by_type:
                events_by_type[event_type] = []
            events_by_type[event_type].append(event)

        db = EventDatabase(db_path)
        total_saved = 0

        # Insert by type
        for event_type, type_events in events_by_type.items():
            count = db.insert_events(type_events, event_type=event_type)
            total_saved += count
            print(f"✓ {count} {event_type} events saved")

        if gps_success > 0:
            print(f"✓ {gps_success}/{len(events)} GPS coordinates extracted")

        return total_saved


def main():
    """
    Test function for scraper
    """
    scraper = TokyoCheapoScraper()

    print("=== Tokyo Cheapo Events Scraper ===\n")

    # Scrape all available events (no page limit)
    events = scraper.scrape_events(max_pages=None)

    if events:
        # Save to database
        print(f"\n💾 Saving to database...")
        scraper.save_to_database(events)

        # Print summary
        print(f"\n📊 Summary:")
        print(f"  • Total events: {len(events)}")
        print(f"  • With dates: {sum(1 for e in events if e.get('start_date'))}/{len(events)}")
        print(f"  • With location: {sum(1 for e in events if e.get('location'))}/{len(events)}")
        print(f"  • With hours: {sum(1 for e in events if e.get('hours'))}/{len(events)}")
        print(f"  • With fee: {sum(1 for e in events if e.get('fee'))}/{len(events)}")
        print(f"  • With website: {sum(1 for e in events if e.get('website'))}/{len(events)}")
        print(f"  • With Google Maps: {sum(1 for e in events if e.get('googlemap_link'))}/{len(events)}")

        # Event type breakdown
        from collections import Counter
        types = Counter(e.get('event_type', 'unknown') for e in events)
        print(f"\n  Event types:")
        for event_type, count in types.items():
            print(f"    - {event_type}: {count}")

        # Show first 3 events
        print(f"\n=== First 3 events ===")
        for i, event in enumerate(events[:3], 1):
            print(f"\n{i}. {event['name']}")
            if event.get('start_date'):
                print(f"   Dates: {event['start_date']} - {event.get('end_date', 'N/A')}")
            if event.get('location'):
                print(f"   Location: {event['location']}")
            if event.get('category'):
                print(f"   Category: {event['category']} → {event.get('event_type', 'N/A')}")
            if event.get('hours'):
                print(f"   Hours: {event['hours']}")
            if event.get('fee'):
                print(f"   Fee: {event['fee']}")


if __name__ == "__main__":
    import sys
    import io
    # Fix Windows console encoding for emojis (seulement quand exécuté directement)
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    main()
