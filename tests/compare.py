"""
Script de comparaison entre scraping automatique et référence manuelle
Usage: uv run tests/compare.py <type> <mois> <année>
       uv run tests/compare.py <type> all
Exemples:
  uv run tests/compare.py festivals mars 2025
  uv run tests/compare.py festivals all
  uv run tests/compare.py expositions janvier 2026
  uv run tests/compare.py expositions all
"""

import sys
import io
import os

# Fix encoding issues on Windows
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.platform == 'win32' and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
from pathlib import Path
from src.scraper_festivals_tokyo import TokyoFestivalScraper
from src.scraper_expositions_tokyo import TokyoExpositionScraper


def get_month_mapping():
    """Retourne le mapping des mois"""
    return {
        'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12
    }


def find_all_references(item_type='festivals'):
    """Trouve tous les fichiers de référence disponibles

    Args:
        item_type: 'festivals' ou 'expositions'
    """
    ref_dir = Path('data/reference')
    if not ref_dir.exists():
        return []

    references = []
    pattern = re.compile(rf'{item_type}_([a-z]+)_(\d{{4}})_reference\.json')

    for file in ref_dir.glob(f'{item_type}_*_reference.json'):
        match = pattern.match(file.name)
        if match:
            month_name, year = match.groups()
            references.append((month_name, int(year), str(file)))

    return sorted(references, key=lambda x: (x[1], get_month_mapping().get(x[0], 0)))


def compare(month_name: str, year: int, item_type: str = 'festivals'):
    """Compare le scraping automatique avec la référence

    Args:
        month_name: Nom du mois
        year: Année
        item_type: 'festivals' ou 'expositions'
    """

    months = get_month_mapping()

    month_num = months.get(month_name.lower())
    if not month_num:
        print(f"❌ Mois invalide: {month_name}")
        print(f"Mois valides: {', '.join(months.keys())}")
        return

    # Vérifier si la référence existe
    ref_file = f'data/reference/{item_type}_{month_name.lower()}_{year}_reference.json'
    if not os.path.exists(ref_file):
        print(f"Pas de référence trouvée: {ref_file}")
        print(f"\nPour créer une référence, scrappe manuellement {month_name} {year}")
        print(f"   et sauvegarde dans {ref_file}")
        return

    # Charger la référence
    with open(ref_file, 'r', encoding='utf-8') as f:
        reference = json.load(f)
    ref_items = reference[item_type]

    # Scraper automatiquement
    print(f"Scraping {month_name} {year}...")
    if item_type == 'festivals':
        scraper = TokyoFestivalScraper()
        scraped = scraper.scrape_festivals(month=month_num, year=year)
    else:  # expositions
        scraper = TokyoExpositionScraper()
        scraped = scraper.scrape_expositions(month=month_num, year=year)

    print(f"\nRéférence: {len(ref_items)} {item_type}")
    print(f"Scrapé: {len(scraped)} {item_type}")

    # Comparer champ par champ
    def normalize(name):
        return name.upper().strip()

    # Trouver les items manquants/en trop
    scraped_names = set(normalize(f['name']) for f in scraped)
    ref_names = set(normalize(f['name']) for f in ref_items)

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

    for scraped_item in scraped:
        name = scraped_item.get('name', '')

        # Trouver dans la référence
        ref_item = None
        for ref in ref_items:
            if normalize(ref['name']) == normalize(name):
                ref_item = ref
                break

        if not ref_item:
            continue

        compared += 1

        # Comparer les champs
        start_date_ok = scraped_item.get('start_date') == ref_item.get('start_date')
        end_date_ok = scraped_item.get('end_date') == ref_item.get('end_date')
        dates_ok = start_date_ok and end_date_ok
        location_ok = scraped_item.get('location') == ref_item.get('location')
        desc_ok = (scraped_item.get('description', '') or '')[:100] == (ref_item.get('description', '') or '')[:100]
        website_ok = scraped_item.get('website') == ref_item.get('website')
        maps_ok = scraped_item.get('googlemap_link') == ref_item.get('googlemap_link')

        if dates_ok and location_ok and desc_ok and website_ok and maps_ok:
            perfect += 1
        else:
            differences += 1
            print(f"DIFF: {name}")

            if not start_date_ok or not end_date_ok:
                print(f"  📅 Dates:")
                if not start_date_ok:
                    print(f"     Start Date - Ref:  {ref_item.get('start_date')}")
                    print(f"     Start Date - Auto: {scraped_item.get('start_date')}")
                if not end_date_ok:
                    print(f"     End Date - Ref:  {ref_item.get('end_date')}")
                    print(f"     End Date - Auto: {scraped_item.get('end_date')}")

            if not location_ok:
                print(f"  📍 Lieu:")
                print(f"     Ref:  {ref_item.get('location')}")
                print(f"     Auto: {scraped_item.get('location')}")

            if not desc_ok:
                ref_desc = (ref_item.get('description', '') or '')[:80]
                auto_desc = (scraped_item.get('description', '') or '')[:80]
                print(f"  📝 Description:")
                print(f"     Ref:  {ref_desc}...")
                print(f"     Auto: {auto_desc}...")

            if not website_ok:
                print(f"  🌐 Website:")
                print(f"     Ref:  {ref_item.get('website')}")
                print(f"     Auto: {scraped_item.get('website')}")

            if not maps_ok:
                ref_maps = ref_item.get('googlemap_link', '') or ''
                auto_maps = scraped_item.get('googlemap_link', '') or ''
                print(f"  🗺️  Google Maps:")
                print(f"     Ref:  {ref_maps[:60]}...")
                print(f"     Auto: {auto_maps[:60]}...")

            print()

    print(f"{'='*60}")
    print(f"Parfaits: {perfect}/{compared} ({perfect*100//compared if compared else 0}%)")
    print(f"Différences: {differences}/{compared}")
    if missing or extra:
        print(f"{item_type.capitalize()} comparés: {compared}/{len(scraped)} scrapés, {len(ref_items)} en référence")
    print(f"{'='*60}")

    return perfect, compared, differences, len(missing), len(extra)


def compare_all(item_type='festivals'):
    """Compare tous les fichiers de référence disponibles

    Args:
        item_type: 'festivals' ou 'expositions'
    """
    references = find_all_references(item_type)

    if not references:
        print(f"❌ Aucun fichier de référence {item_type} trouvé dans data/reference/")
        return

    print(f"📂 {len(references)} fichiers de référence {item_type} trouvés\n")

    total_perfect = 0
    total_compared = 0
    total_differences = 0
    total_missing = 0
    total_extra = 0

    results = []

    for i, (month_name, year, _) in enumerate(references, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(references)}: {month_name.capitalize()} {year}")
        print(f"{'='*60}\n")

        perfect, compared, differences, missing, extra = compare(month_name, year, item_type)

        total_perfect += perfect
        total_compared += compared
        total_differences += differences
        total_missing += missing
        total_extra += extra

        results.append({
            'month': month_name.capitalize(),
            'year': year,
            'perfect': perfect,
            'compared': compared,
            'differences': differences,
            'missing': missing,
            'extra': extra
        })

    # Résumé global
    print(f"\n\n{'='*60}")
    print(f"RÉSUMÉ GLOBAL - {len(references)} mois testés ({item_type})")
    print(f"{'='*60}\n")

    for result in results:
        status = "OK" if result['differences'] == 0 and result['missing'] == 0 and result['extra'] == 0 else "DIFF"
        percentage = result['perfect'] * 100 // result['compared'] if result['compared'] else 0
        print(f"{status} {result['month']} {result['year']}: {result['perfect']}/{result['compared']} parfaits ({percentage}%)")

    print(f"\n{'='*60}")
    overall_percentage = total_perfect * 100 // total_compared if total_compared else 0
    print(f"Total parfaits: {total_perfect}/{total_compared} ({overall_percentage}%)")
    print(f"Total différences: {total_differences}")
    print(f"Total manquants: {total_missing}")
    print(f"Total en trop: {total_extra}")
    print(f"{'='*60}")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1].lower() == 'all':
        # Format: uv run tests/compare.py all
        # Compare festivals et expositions
        print("🔍 Comparaison de TOUS les festivals et expositions\n")
        compare_all('festivals')
        print("\n\n")
        compare_all('expositions')
    elif len(sys.argv) == 3 and sys.argv[2].lower() == 'all':
        # Format: uv run tests/compare.py festivals all
        item_type = sys.argv[1].lower()
        if item_type not in ['festivals', 'expositions']:
            print(f"❌ Type invalide: {item_type}")
            print("Types valides: festivals, expositions")
            sys.exit(1)
        compare_all(item_type)
    elif len(sys.argv) == 4:
        # Format: uv run tests/compare.py festivals mars 2025
        item_type = sys.argv[1].lower()
        month_name = sys.argv[2]
        try:
            year = int(sys.argv[3])
        except ValueError:
            print(f"❌ Année invalide: {sys.argv[3]}")
            sys.exit(1)

        if item_type not in ['festivals', 'expositions']:
            print(f"❌ Type invalide: {item_type}")
            print("Types valides: festivals, expositions")
            sys.exit(1)

        compare(month_name, year, item_type)
    else:
        print("Usage: uv run tests/compare.py <type> <mois> <année>")
        print("       uv run tests/compare.py <type> all")
        print("       uv run tests/compare.py all")
        print("\nExemples:")
        print("  uv run tests/compare.py festivals mars 2025")
        print("  uv run tests/compare.py festivals all")
        print("  uv run tests/compare.py expositions janvier 2026")
        print("  uv run tests/compare.py expositions all")
        print("  uv run tests/compare.py all  # Compare tous les festivals ET expositions")
        sys.exit(1)
