"""
Investigation script to analyze hanabi map.html pages for geographic coordinates.

This script:
1. Queries sample hanabi events from the database
2. Fetches /map.html pages for each event
3. Analyzes HTML structure for coordinate data
4. Generates a detailed report with findings
"""

import sys
import os
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Optional, Tuple
import json

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import EventDatabase


class HanabiMapInvestigator:
    """Investigates hanabi map.html pages for coordinate extraction possibilities."""

    BASE_URL = "https://hanabi.walkerplus.com"

    def __init__(self, db_path: str = "data/tokyo_events.sqlite"):
        self.db = EventDatabase(db_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.findings = []

    def get_sample_events(self) -> Dict[str, List[Dict]]:
        """
        Get sample hanabi events for investigation.

        Returns:
            Dict with 'with_coords', 'without_coords', and 'random' event lists
        """
        print("[*] Récupération des événements hanabi...")

        # Get all hanabi events
        all_hanabi = self.db.get_events(event_type='hanabi')

        # Separate by coordinate availability
        with_coords = [e for e in all_hanabi if e.get('latitude') and e.get('longitude')]
        without_coords = [e for e in all_hanabi if not (e.get('latitude') and e.get('longitude'))]

        print(f"  - Total hanabi: {len(all_hanabi)}")
        print(f"  - Avec coordonnées: {len(with_coords)}")
        print(f"  - Sans coordonnées: {len(without_coords)}")

        # Sample selection
        sample = {
            'with_coords': with_coords[:5],  # First 5 with coordinates
            'without_coords': without_coords[:5],  # First 5 without coordinates
            'random': all_hanabi[10:15] if len(all_hanabi) > 15 else []  # Random middle section
        }

        total_sample = len(sample['with_coords']) + len(sample['without_coords']) + len(sample['random'])
        print(f"\n[+] Échantillon sélectionné: {total_sample} événements")

        return sample

    def fetch_map_page(self, event_id: str) -> Tuple[Optional[str], int]:
        """
        Fetch /map.html page for an event.

        Args:
            event_id: Event ID (e.g., "ar0313e335967")

        Returns:
            Tuple of (HTML content, status_code)
        """
        url = f"{self.BASE_URL}/detail/{event_id}/map.html"

        try:
            response = self.session.get(url, timeout=15)
            return response.text, response.status_code
        except requests.RequestException as e:
            print(f"    [!] Erreur HTTP: {e}")
            return None, 0

    def analyze_coordinate_patterns(self, html: str, event_name: str) -> Dict:
        """
        Analyze HTML for coordinate extraction patterns.

        Args:
            html: HTML content
            event_name: Event name for logging

        Returns:
            Dict with analysis results
        """
        soup = BeautifulSoup(html, 'html.parser')
        analysis = {
            'patterns_found': [],
            'coordinates': None,
            'extraction_methods': []
        }

        # Pattern 1: JavaScript variables (var lat, var lng, etc.)
        js_var_patterns = [
            r'var\s+lat\s*=\s*([\d.]+)',
            r'var\s+lng\s*=\s*([\d.]+)',
            r'var\s+latitude\s*=\s*([\d.]+)',
            r'var\s+longitude\s*=\s*([\d.]+)',
            r'lat\s*:\s*([\d.]+)',
            r'lng\s*:\s*([\d.]+)',
        ]

        page_text = soup.get_text()
        for pattern in js_var_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                analysis['patterns_found'].append(f"JavaScript variable: {pattern}")
                analysis['extraction_methods'].append('javascript_variables')

        # Pattern 2: Data attributes
        elements_with_coords = soup.find_all(attrs={'data-lat': True})
        elements_with_coords += soup.find_all(attrs={'data-latitude': True})
        elements_with_coords += soup.find_all(attrs={'data-lng': True})
        elements_with_coords += soup.find_all(attrs={'data-longitude': True})

        if elements_with_coords:
            analysis['patterns_found'].append(f"Data attributes found in {len(elements_with_coords)} elements")
            analysis['extraction_methods'].append('data_attributes')

            # Try to extract coordinates
            for elem in elements_with_coords:
                lat = elem.get('data-lat') or elem.get('data-latitude')
                lng = elem.get('data-lng') or elem.get('data-longitude')
                if lat and lng:
                    analysis['coordinates'] = (float(lat), float(lng))
                    break

        # Pattern 3: Google Maps iframe embeds
        iframes = soup.find_all('iframe', src=re.compile(r'google.*maps'))
        if iframes:
            analysis['patterns_found'].append(f"Google Maps iframes: {len(iframes)}")
            analysis['extraction_methods'].append('google_maps_iframe')

            # Try to extract from iframe URL
            for iframe in iframes:
                src = iframe.get('src', '')
                # Pattern: @lat,lng or q=lat,lng
                coord_match = re.search(r'[@q=]([\d.]+),([\d.]+)', src)
                if coord_match:
                    lat, lng = float(coord_match.group(1)), float(coord_match.group(2))
                    if not analysis['coordinates']:
                        analysis['coordinates'] = (lat, lng)

        # Pattern 4: Google Maps links in <a> tags
        map_links = soup.find_all('a', href=re.compile(r'google.*maps|maps\.app\.goo\.gl'))
        if map_links:
            analysis['patterns_found'].append(f"Google Maps links: {len(map_links)}")
            analysis['extraction_methods'].append('google_maps_links')

            for link in map_links:
                href = link.get('href', '')
                # Pattern: @lat,lng
                coord_match = re.search(r'@([\d.]+),([\d.]+)', href)
                if coord_match:
                    lat, lng = float(coord_match.group(1)), float(coord_match.group(2))
                    if not analysis['coordinates']:
                        analysis['coordinates'] = (lat, lng)

        # Pattern 5: JSON-LD schema.org
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Check for geo property
                    geo = data.get('geo') or data.get('location', {}).get('geo')
                    if geo and isinstance(geo, dict):
                        lat = geo.get('latitude')
                        lng = geo.get('longitude')
                        if lat and lng:
                            analysis['patterns_found'].append("JSON-LD GeoCoordinates")
                            analysis['extraction_methods'].append('json_ld')
                            if not analysis['coordinates']:
                                analysis['coordinates'] = (float(lat), float(lng))
            except json.JSONDecodeError:
                pass

        # Pattern 6: OpenStreetMap embeds
        osm_iframes = soup.find_all('iframe', src=re.compile(r'openstreetmap'))
        if osm_iframes:
            analysis['patterns_found'].append(f"OpenStreetMap iframes: {len(osm_iframes)}")
            analysis['extraction_methods'].append('osm_iframe')

        return analysis

    def investigate_event(self, event: Dict, category: str) -> Dict:
        """
        Investigate a single event's map.html page.

        Args:
            event: Event dictionary from database
            category: Sample category ('with_coords', 'without_coords', 'random')

        Returns:
            Investigation result dictionary
        """
        event_id = event.get('event_id')
        event_name = event.get('name', 'Unknown')

        print(f"\n[>] [{category}] {event_name[:60]}")
        print(f"   ID: {event_id}")

        # Check existing coordinates
        existing_coords = None
        if event.get('latitude') and event.get('longitude'):
            existing_coords = (event['latitude'], event['longitude'])
            print(f"   [*] Coords existantes: {existing_coords}")
        else:
            print(f"   [-] Pas de coords existantes")

        # Fetch map.html
        html, status_code = self.fetch_map_page(event_id)

        result = {
            'event_id': event_id,
            'event_name': event_name,
            'category': category,
            'existing_coords': existing_coords,
            'map_page_status': status_code,
            'map_page_exists': status_code == 200,
            'analysis': None,
            'found_coords': None,
            'coords_match': None
        }

        if status_code == 200 and html:
            print(f"   [+] map.html trouvé (status {status_code})")

            # Analyze HTML
            analysis = self.analyze_coordinate_patterns(html, event_name)
            result['analysis'] = analysis

            if analysis['coordinates']:
                result['found_coords'] = analysis['coordinates']
                print(f"   [+] Coordonnées trouvées: {analysis['coordinates']}")
                print(f"   [*] Méthodes: {', '.join(set(analysis['extraction_methods']))}")

                # Compare with existing
                if existing_coords:
                    lat_diff = abs(existing_coords[0] - analysis['coordinates'][0])
                    lng_diff = abs(existing_coords[1] - analysis['coordinates'][1])
                    match = lat_diff < 0.001 and lng_diff < 0.001
                    result['coords_match'] = match
                    match_symbol = '[+]' if match else '[!]'
                    print(f"   {match_symbol} Comparaison: {'MATCH' if match else f'DIFFÉRENT (Δlat={lat_diff:.6f}, Δlng={lng_diff:.6f})'}")
            else:
                print(f"   [-] Aucune coordonnée extraite")
                if analysis['patterns_found']:
                    print(f"   [*] Patterns détectés: {', '.join(analysis['patterns_found'][:3])}")
        else:
            print(f"   [-] map.html non disponible (status {status_code})")

        return result

    def run_investigation(self):
        """Run full investigation and generate report."""
        print("=" * 80)
        print("INVESTIGATION: Hanabi Map.html Pages")
        print("=" * 80)

        # Get sample
        samples = self.get_sample_events()

        # Investigate each category
        all_results = []

        for category, events in samples.items():
            if not events:
                continue

            print(f"\n{'=' * 80}")
            print(f"Catégorie: {category.upper()}")
            print(f"{'=' * 80}")

            for event in events:
                result = self.investigate_event(event, category)
                all_results.append(result)
                self.findings.append(result)

                # Be respectful with rate limiting
                time.sleep(0.5)

        # Generate report
        print(f"\n{'=' * 80}")
        print("Génération du rapport...")
        print(f"{'=' * 80}")

        self.generate_report(all_results)

    def generate_report(self, results: List[Dict]):
        """Generate markdown report with findings."""
        report_path = project_root / "docs" / "hanabi_map_investigation.md"

        # Statistics
        total = len(results)
        map_exists = sum(1 for r in results if r['map_page_exists'])
        coords_found = sum(1 for r in results if r['found_coords'])
        coords_match = sum(1 for r in results if r['coords_match'] is True)

        # Extraction methods used
        all_methods = []
        for r in results:
            if r.get('analysis') and r['analysis'].get('extraction_methods'):
                all_methods.extend(r['analysis']['extraction_methods'])
        method_counts = {m: all_methods.count(m) for m in set(all_methods)}

        # Generate markdown
        report = f"""# Investigation: Hanabi Map.html Pages for Coordinate Extraction

**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Objectif:** Analyser si les pages `/map.html` des événements hanabi contiennent des données de coordonnées géographiques exploitables.

## Résumé Exécutif

- **Événements testés:** {total}
- **Pages map.html existantes:** {map_exists}/{total} ({map_exists/total*100:.1f}%)
- **Coordonnées trouvées:** {coords_found}/{map_exists} ({coords_found/map_exists*100:.1f}% des pages existantes)
- **Correspondance avec coords existantes:** {coords_match}/{coords_found if coords_found > 0 else 1}

## Méthodes d'Extraction Détectées

"""

        if method_counts:
            for method, count in sorted(method_counts.items(), key=lambda x: -x[1]):
                report += f"- **{method}**: {count} occurrences\n"
        else:
            report += "Aucune méthode d'extraction viable détectée.\n"

        report += "\n## Résultats Détaillés\n\n"

        # Group by category
        for category in ['with_coords', 'without_coords', 'random']:
            category_results = [r for r in results if r['category'] == category]
            if not category_results:
                continue

            report += f"\n### {category.replace('_', ' ').title()}\n\n"

            for r in category_results:
                report += f"#### {r['event_name']}\n\n"
                report += f"- **Event ID:** `{r['event_id']}`\n"
                report += f"- **Coordonnées existantes:** {r['existing_coords'] if r['existing_coords'] else 'Aucune'}\n"
                map_status = '✅ Existe' if r['map_page_exists'] else f"❌ Non trouvée (HTTP {r['map_page_status']})"
                report += f"- **Page map.html:** {map_status}\n"

                if r['found_coords']:
                    report += f"- **Coordonnées trouvées:** {r['found_coords']}\n"
                    if r['analysis'] and r['analysis']['extraction_methods']:
                        methods = ', '.join(set(r['analysis']['extraction_methods']))
                        report += f"- **Méthodes d'extraction:** {methods}\n"
                    if r['coords_match'] is not None:
                        report += f"- **Correspondance:** {'✅ OUI' if r['coords_match'] else '⚠️ NON (différence détectée)'}\n"
                elif r['map_page_exists']:
                    report += f"- **Coordonnées trouvées:** ❌ Aucune\n"
                    if r['analysis'] and r['analysis']['patterns_found']:
                        patterns = ', '.join(r['analysis']['patterns_found'][:3])
                        report += f"- **Patterns détectés (non exploitables):** {patterns}\n"

                report += "\n"

        # Recommendations
        report += "\n## Recommandations\n\n"

        if coords_found > 0:
            report += f"""### ✅ Implémentation Recommandée

Les pages map.html contiennent des coordonnées exploitables. Il est recommandé d'intégrer cette extraction dans le scraper.

**Actions suggérées:**
1. Ajouter une méthode `_scrape_map_page()` dans `src/scraper_hanabi_kanto.py`
2. Appeler cette méthode pendant l'enrichissement des détails
3. Utiliser les méthodes d'extraction suivantes (par ordre de fiabilité):
"""
            for method in sorted(method_counts.keys(), key=lambda x: -method_counts[x]):
                report += f"   - {method}\n"

            report += f"""
4. Comparer avec les coordonnées existantes (Google Maps links) pour validation
5. Mettre à jour la base de données avec les nouvelles coordonnées

**Impact estimé:** +{coords_found}/{map_exists} événements avec coordonnées ({coords_found/map_exists*100:.1f}% d'amélioration)
"""
        else:
            report += f"""### ❌ Implémentation Non Recommandée

Les pages map.html n'offrent pas de données de coordonnées exploitables supplémentaires.

**Conclusion:**
- Les pages map.html existent pour {map_exists}/{total} événements
- Cependant, aucune coordonnée n'a pu être extraite de manière fiable
- La méthode actuelle (extraction via Google Maps links) reste la meilleure option

**Alternative suggérée:**
- Continuer à utiliser `scripts/populate_gps_coordinates.py` pour améliorer la couverture
- Investiguer d'autres sources de données (API officielles, geocoding, etc.)
"""

        # Write report
        os.makedirs(report_path.parent, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n[+] Rapport généré: {report_path}")
        print(f"\n{'=' * 80}")
        print("RÉSUMÉ")
        print(f"{'=' * 80}")
        print(f"Pages map.html: {map_exists}/{total}")
        print(f"Coordonnées trouvées: {coords_found}/{map_exists}")
        print(f"Taux de succès: {coords_found/map_exists*100 if map_exists > 0 else 0:.1f}%")
        print(f"{'=' * 80}")


def main():
    """Main entry point."""
    investigator = HanabiMapInvestigator()
    investigator.run_investigation()


if __name__ == "__main__":
    main()
