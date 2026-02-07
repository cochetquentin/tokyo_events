"""
Script de comparaison pour tester le scraper hanabi
Compare les données scrapées avec un fichier de référence manuel

Usage: uv run tests/compare_hanabi.py [reference_file]
"""

import sys
import json
import os
from src.scraper_hanabi_kanto import KantoHanabiScraper


def load_reference(reference_file: str = None):
    """
    Charge le fichier de référence

    Args:
        reference_file: Path to reference JSON

    Returns:
        Dict with reference data or None
    """
    if not reference_file:
        reference_file = 'data/reference/hanabi_kanto_reference.json'

    if not os.path.exists(reference_file):
        print(f"⚠️ Fichier de référence non trouvé: {reference_file}")
        return None

    with open(reference_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get('hanabi', [])


def compare_hanabi(reference_file: str = None):
    """
    Compare hanabi scraped vs reference

    Args:
        reference_file: Path to reference JSON (optional)
    """
    print("=== Comparaison Scraper Hanabi ===\n")

    # Load reference
    reference = load_reference(reference_file)

    # Scrape live data
    print("📋 Scraping en temps réel...\n")
    scraper = KantoHanabiScraper()
    scraped = scraper.scrape_hanabi(months_ahead=12)  # 12 months to catch all reference events

    print(f"\n📊 Résultats de la comparaison:\n")

    # Compare counts
    ref_count = len(reference) if reference else 0
    scraped_count = len(scraped)

    print(f"  • Événements référence: {ref_count}")
    print(f"  • Événements scrapés: {scraped_count}")

    if not reference:
        print("\n⚠️ Pas de fichier de référence disponible")
        print("   Pour créer une référence, scraper quelques événements manuellement")
        print("   et sauvegarder dans data/reference/hanabi_kanto_reference.json")
        return

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
    import re
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
    if reference:
        print(f"\n🔍 Comparaison des événements de référence:")

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
                print(f"\n  ✅ Trouvé: {ref_name[:60]}")

                # Compare key fields
                for field in required_fields + optional_fields:
                    ref_val = ref_event.get(field)
                    scraped_val = matched.get(field)

                    if ref_val and scraped_val != ref_val:
                        print(f"     ⚠️ Différence {field}:")
                        print(f"        Référence: {ref_val}")
                        print(f"        Scrapé:    {scraped_val}")
            else:
                print(f"\n  ❌ Non trouvé: {ref_name[:60]}")

    print(f"\n✅ Comparaison terminée")


def main():
    """
    Main entry point
    """
    reference_file = None
    if len(sys.argv) >= 2:
        reference_file = sys.argv[1]

    compare_hanabi(reference_file)


if __name__ == "__main__":
    main()
