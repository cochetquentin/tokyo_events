"""
Script de comparaison entre scraping automatique et référence manuelle
Usage: uv run tests/compare.py <mois> <année>
Exemple: uv run tests/compare.py mars 2025
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from src.scraper_festivals_tokyo import TokyoFestivalScraper


def compare(month_name: str, year: int):
    """Compare le scraping automatique avec la référence"""

    # Mapping des mois
    months = {
        'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12
    }

    month_num = months.get(month_name.lower())
    if not month_num:
        print(f"❌ Mois invalide: {month_name}")
        print(f"Mois valides: {', '.join(months.keys())}")
        return

    # Vérifier si la référence existe
    ref_file = f'data/reference/festivals_{month_name.lower()}_{year}_reference.json'
    if not os.path.exists(ref_file):
        print(f"⚠️  Pas de référence trouvée: {ref_file}")
        print(f"\n💡 Pour créer une référence, scrappe manuellement {month_name} {year}")
        print(f"   et sauvegarde dans {ref_file}")
        return

    # Charger la référence
    with open(ref_file, 'r', encoding='utf-8') as f:
        reference = json.load(f)
    ref_festivals = reference['festivals']

    # Scraper automatiquement
    print(f"🔍 Scraping {month_name} {year}...")
    scraper = TokyoFestivalScraper()
    scraped = scraper.scrape_festivals(month=month_num, year=year)

    print(f"\n📊 Référence: {len(ref_festivals)} festivals")
    print(f"📊 Scrapé: {len(scraped)} festivals")

    # Comparer champ par champ
    def normalize(name):
        return name.upper().strip()

    # Trouver les festivals manquants/en trop
    scraped_names = set(normalize(f['name']) for f in scraped)
    ref_names = set(normalize(f['name']) for f in ref_festivals)

    missing = ref_names - scraped_names
    extra = scraped_names - ref_names

    if missing:
        print(f"\n❌ Manquants ({len(missing)}):")
        for name in sorted(missing):
            print(f"   - {name}")

    if extra:
        print(f"\n➕ En trop ({len(extra)}):")
        for name in sorted(extra):
            print(f"   - {name}")

    print()

    perfect = 0
    differences = 0
    compared = 0

    for scraped_fest in scraped:
        name = scraped_fest.get('name', '')

        # Trouver dans la référence
        ref_fest = None
        for ref in ref_festivals:
            if normalize(ref['name']) == normalize(name):
                ref_fest = ref
                break

        if not ref_fest:
            continue

        compared += 1

        # Comparer les champs
        dates_ok = scraped_fest.get('dates') == ref_fest.get('dates')
        location_ok = scraped_fest.get('location') == ref_fest.get('location')
        desc_ok = (scraped_fest.get('description', '') or '')[:100] == (ref_fest.get('description', '') or '')[:100]
        website_ok = scraped_fest.get('website') == ref_fest.get('website')
        maps_ok = scraped_fest.get('googlemap_link') == ref_fest.get('googlemap_link')

        if dates_ok and location_ok and desc_ok and website_ok and maps_ok:
            perfect += 1
        else:
            differences += 1
            print(f"⚠️  {name}")

            if not dates_ok:
                print(f"  📅 Dates:")
                print(f"     Ref:  {ref_fest.get('dates')}")
                print(f"     Auto: {scraped_fest.get('dates')}")

            if not location_ok:
                print(f"  📍 Lieu:")
                print(f"     Ref:  {ref_fest.get('location')}")
                print(f"     Auto: {scraped_fest.get('location')}")

            if not desc_ok:
                ref_desc = (ref_fest.get('description', '') or '')[:80]
                auto_desc = (scraped_fest.get('description', '') or '')[:80]
                print(f"  📝 Description:")
                print(f"     Ref:  {ref_desc}...")
                print(f"     Auto: {auto_desc}...")

            if not website_ok:
                print(f"  🌐 Website:")
                print(f"     Ref:  {ref_fest.get('website')}")
                print(f"     Auto: {scraped_fest.get('website')}")

            if not maps_ok:
                ref_maps = ref_fest.get('googlemap_link', '') or ''
                auto_maps = scraped_fest.get('googlemap_link', '') or ''
                print(f"  🗺️  Google Maps:")
                print(f"     Ref:  {ref_maps[:60]}...")
                print(f"     Auto: {auto_maps[:60]}...")

            print()

    print(f"{'='*60}")
    print(f"✅ Parfaits: {perfect}/{compared} ({perfect*100//compared if compared else 0}%)")
    print(f"⚠️  Différences: {differences}/{compared}")
    if missing or extra:
        print(f"📊 Festivals comparés: {compared}/{len(scraped)} scrapés, {len(ref_festivals)} en référence")
    print(f"{'='*60}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: uv run tests/compare.py <mois> <année>")
        print("Exemple: uv run tests/compare.py mars 2025")
        sys.exit(1)

    month_name = sys.argv[1]
    try:
        year = int(sys.argv[2])
    except ValueError:
        print(f"❌ Année invalide: {sys.argv[2]}")
        sys.exit(1)

    compare(month_name, year)
