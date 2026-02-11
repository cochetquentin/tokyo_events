"""
Script de comparaison entre scraping automatique et référence manuelle
Supporte: festivals, expositions, hanabi, marches

Usage:
  uv run tests/compare.py <type> <mois> <année>
  uv run tests/compare.py <type> all
  uv run tests/compare.py all

Exemples:
  uv run tests/compare.py festivals mars 2025
  uv run tests/compare.py festivals all
  uv run tests/compare.py expositions janvier 2026
  uv run tests/compare.py hanabi
  uv run tests/compare.py all
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
from src.scraper_hanabi_kanto import KantoHanabiScraper
from src.scraper_marches_tokyo import TokyoMarcheScraper


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
        item_type: 'festivals', 'expositions', 'hanabi', ou 'marches'
    """
    ref_dir = Path('data/reference')
    if not ref_dir.exists():
        return []

    references = []

    if item_type == 'hanabi':
        # Format spécial pour hanabi: hanabi_kanto_reference.json
        ref_file = ref_dir / 'hanabi_kanto_reference.json'
        if ref_file.exists():
            return [(None, None, str(ref_file))]
        return []

    # Format standard: {type}_{mois}_{année}_reference.json
    pattern = re.compile(rf'{item_type}_([a-z]+)_(\d{{4}})_reference\.json')

    for file in ref_dir.glob(f'{item_type}_*_reference.json'):
        match = pattern.match(file.name)
        if match:
            month_name, year = match.groups()
            references.append((month_name, int(year), str(file)))

    return sorted(references, key=lambda x: (x[1], get_month_mapping().get(x[0], 0)))


def compare_hanabi(reference_file: str = None):
    """Compare hanabi scraped vs reference

    Args:
        reference_file: Path to reference JSON (optional)
    """
    print("=== Comparaison Scraper Hanabi ===\n")

    # Load reference
    if not reference_file:
        reference_file = 'data/reference/hanabi_kanto_reference.json'

    if not os.path.exists(reference_file):
        print(f"⚠️ Fichier de référence non trouvé: {reference_file}")
        print("   Pour créer une référence, scraper quelques événements manuellement")
        print("   et sauvegarder dans data/reference/hanabi_kanto_reference.json")
        return None, None, None, None, None

    with open(reference_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    reference = data.get('hanabi', [])

    # Scrape live data
    print("📋 Scraping en temps réel...\n")
    scraper = KantoHanabiScraper()
    scraped = scraper.scrape_hanabi(months_ahead=12)

    print(f"\n📊 Résultats de la comparaison:\n")

    # Compare counts
    ref_count = len(reference)
    scraped_count = len(scraped)

    print(f"  • Événements référence: {ref_count}")
    print(f"  • Événements scrapés: {scraped_count}")

    # Check required fields
    print(f"\n📝 Validation des champs requis:")

    required_fields = ['name', 'start_date', 'end_date', 'event_id', 'prefecture', 'city']
    optional_fields = ['start_time', 'fireworks_count', 'venue', 'website', 'googlemap_link']

    missing_required = 0
    for event in scraped:
        for field in required_fields:
            if not event.get(field):
                print(f"  ⚠️ Champ requis manquant '{field}' pour: {event.get('name', 'Unknown')}")
                missing_required += 1

    if missing_required == 0:
        print(f"  ✅ Tous les champs requis sont présents ({len(scraped)} événements)")

    # Check optional fields coverage
    print(f"\n📊 Couverture des champs optionnels:")
    for field in optional_fields:
        count = sum(1 for e in scraped if e.get(field))
        percentage = (count / len(scraped) * 100) if scraped else 0
        print(f"  • {field}: {count}/{len(scraped)} ({percentage:.1f}%)")

    # Check date format
    print(f"\n📅 Validation du format des dates:")
    invalid_dates = 0
    date_pattern = re.compile(r'^\d{4}/\d{2}/\d{2}$')

    for event in scraped:
        start = event.get('start_date')
        end = event.get('end_date')

        if start and not date_pattern.match(start):
            print(f"  ❌ Format de start_date invalide: {start} ({event.get('name', 'Unknown')})")
            invalid_dates += 1

        if end and not date_pattern.match(end):
            print(f"  ❌ Format de end_date invalide: {end} ({event.get('name', 'Unknown')})")
            invalid_dates += 1

    if invalid_dates == 0:
        print(f"  ✅ Toutes les dates sont au format YYYY/MM/DD")

    # Check prefecture/city coherence
    print(f"\n🗾 Cohérence ville/préfecture:")
    incoherent = 0
    for event in scraped:
        location = event.get('location', '')
        city = event.get('city', '')
        prefecture = event.get('prefecture', '')

        # location should be "{city}, {prefecture}"
        expected = f"{city}, {prefecture}" if city else prefecture
        if location != expected:
            print(f"  ⚠️ Incohérence location: '{location}' vs attendu '{expected}'")
            incoherent += 1

    if incoherent == 0:
        print(f"  ✅ Cohérence ville/préfecture vérifiée")

    # Compare specific events if reference available
    perfect = 0
    compared = 0
    differences = 0
    missing = []
    extra = []

    if reference:
        print(f"\n🔍 Comparaison des événements de référence:")

        # Find scraped event IDs
        scraped_ids = set(e.get('event_id') for e in scraped)
        ref_ids = set(e.get('event_id') for e in reference)

        # Find missing and extra
        missing_ids = ref_ids - scraped_ids
        extra_ids = scraped_ids - ref_ids

        # Try to match reference events by name or event_id
        for ref_event in reference:
            ref_name = ref_event.get('name')
            ref_id = ref_event.get('event_id')

            # Find matching scraped event
            matched = None
            for scraped_event in scraped:
                if scraped_event.get('event_id') == ref_id:
                    matched = scraped_event
                    break
                elif scraped_event.get('name') == ref_name:
                    matched = scraped_event
                    break

            if matched:
                compared += 1
                has_diff = False

                print(f"\n  ✅ Trouvé: {ref_name[:60]}")

                # Compare key fields
                for field in required_fields + optional_fields:
                    ref_val = ref_event.get(field)
                    scraped_val = matched.get(field)

                    if ref_val and scraped_val != ref_val:
                        has_diff = True
                        print(f"     ⚠️ Différence {field}:")
                        print(f"        Référence: {ref_val}")
                        print(f"        Scrapé:    {scraped_val}")

                if not has_diff:
                    perfect += 1
                else:
                    differences += 1
            else:
                missing.append(ref_name)
                print(f"\n  ❌ Non trouvé: {ref_name[:60]}")

    print(f"\n{'='*60}")
    print(f"Parfaits: {perfect}/{compared} ({perfect*100//compared if compared else 0}%)")
    print(f"Différences: {differences}/{compared}")
    print(f"Manquants: {len(missing)}")
    print(f"En trop: {len(extra)}")
    print(f"{'='*60}")
    print(f"\n✅ Comparaison terminée")

    return perfect, compared, differences, len(missing), len(extra)


def compare(month_name: str, year: int, item_type: str = 'festivals'):
    """Compare le scraping automatique avec la référence

    Args:
        month_name: Nom du mois
        year: Année
        item_type: 'festivals', 'expositions', 'hanabi', ou 'marches'
    """

    # Cas spécial pour hanabi
    if item_type == 'hanabi':
        return compare_hanabi()

    months = get_month_mapping()

    month_num = months.get(month_name.lower())
    if not month_num:
        print(f"❌ Mois invalide: {month_name}")
        print(f"Mois valides: {', '.join(months.keys())}")
        return None, None, None, None, None

    # Vérifier si la référence existe
    ref_file = f'data/reference/{item_type}_{month_name.lower()}_{year}_reference.json'
    if not os.path.exists(ref_file):
        print(f"Pas de référence trouvée: {ref_file}")
        print(f"\nPour créer une référence, scrappe manuellement {month_name} {year}")
        print(f"   et sauvegarde dans {ref_file}")
        return None, None, None, None, None

    # Charger la référence
    with open(ref_file, 'r', encoding='utf-8') as f:
        reference = json.load(f)
    ref_items = reference[item_type]

    # Scraper automatiquement
    print(f"Scraping {month_name} {year}...")
    if item_type == 'festivals':
        scraper = TokyoFestivalScraper()
        scraped = scraper.scrape_festivals(month=month_num, year=year)
    elif item_type == 'expositions':
        scraper = TokyoExpositionScraper()
        scraped = scraper.scrape_expositions(month=month_num, year=year)
    elif item_type == 'marches':
        scraper = TokyoMarcheScraper()
        scraped = scraper.scrape_marches(month=month_num, year=year)
    else:
        print(f"❌ Type inconnu: {item_type}")
        return None, None, None, None, None

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
        item_type: 'festivals', 'expositions', 'hanabi', ou 'marches'
    """

    # Cas spécial pour hanabi
    if item_type == 'hanabi':
        if os.path.exists('data/reference/hanabi_kanto_reference.json'):
            print(f"📂 Test de hanabi\n")
            return compare_hanabi()
        else:
            print(f"❌ Aucun fichier de référence hanabi trouvé")
            return

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

        result = compare(month_name, year, item_type)
        if result[0] is None:
            continue

        perfect, compared, differences, missing, extra = result

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
    print(f"RÉSUMÉ GLOBAL - {len(results)} mois testés ({item_type})")
    print(f"{'='*60}\n")

    for result in results:
        status = "✅" if result['differences'] == 0 and result['missing'] == 0 and result['extra'] == 0 else "⚠️"
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
        # Compare tous les types
        print("🔍 Comparaison de TOUS les types d'événements\n")
        for item_type in ['festivals', 'expositions', 'hanabi', 'marches']:
            print(f"\n\n{'#'*60}")
            print(f"# {item_type.upper()}")
            print(f"{'#'*60}\n")
            compare_all(item_type)
    elif len(sys.argv) == 2:
        # Format: uv run tests/compare.py festivals
        item_type = sys.argv[1].lower()
        if item_type not in ['festivals', 'expositions', 'hanabi', 'marches']:
            print(f"❌ Type invalide: {item_type}")
            print("Types valides: festivals, expositions, hanabi, marches")
            sys.exit(1)
        compare_all(item_type)
    elif len(sys.argv) == 3 and sys.argv[2].lower() == 'all':
        # Format: uv run tests/compare.py festivals all
        item_type = sys.argv[1].lower()
        if item_type not in ['festivals', 'expositions', 'hanabi', 'marches']:
            print(f"❌ Type invalide: {item_type}")
            print("Types valides: festivals, expositions, hanabi, marches")
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

        if item_type not in ['festivals', 'expositions', 'hanabi', 'marches']:
            print(f"❌ Type invalide: {item_type}")
            print("Types valides: festivals, expositions, hanabi, marches")
            sys.exit(1)

        compare(month_name, year, item_type)
    else:
        print(__doc__)
        sys.exit(1)
