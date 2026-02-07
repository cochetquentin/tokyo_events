"""
Script pour scraper les festivals et expositions de Tokyo
Usage: uv run scrape.py <type> <mois> <année>
Exemples:
  uv run scrape.py festivals mars 2025
  uv run scrape.py expositions janvier 2026
"""

import sys
import io

# Fix encoding issues on Windows - doit être fait AVANT les imports des scrapers
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.scraper_festivals_tokyo import TokyoFestivalScraper
from src.scraper_expositions_tokyo import TokyoExpositionScraper
from src.scraper_hanabi_kanto import KantoHanabiScraper
from datetime import datetime


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run scrape.py <type> [options]")
        print("Exemples:")
        print("  uv run scrape.py festivals mars 2025")
        print("  uv run scrape.py expositions janvier 2026")
        print("  uv run scrape.py hanabi [mois_avance]  # Par défaut: 6 mois")
        sys.exit(1)

    scrape_type = sys.argv[1].lower()

    # Valider le type
    if scrape_type not in ['festivals', 'expositions', 'hanabi']:
        print(f"❌ Type invalide: {scrape_type}")
        print("Types valides: festivals, expositions, hanabi")
        sys.exit(1)

    # Handle hanabi (different parameter structure)
    if scrape_type == 'hanabi':
        # Usage: uv run scrape.py hanabi [mois_avance]
        months_ahead = 6  # Par défaut
        if len(sys.argv) >= 3:
            try:
                months_ahead = int(sys.argv[2])
            except ValueError:
                print(f"❌ Nombre de mois invalide: {sys.argv[2]}")
                sys.exit(1)

        print(f"🎆 Scraping des hanabi Kanto (prochains {months_ahead} mois)...\n")
        scraper = KantoHanabiScraper()
        events = scraper.scrape_hanabi(months_ahead=months_ahead)

        # Déterminer année pour nom fichier
        year = datetime.now().year
        if events and events[0].get('start_date'):
            year = events[0]['start_date'].split('/')[0]

        filename = f'data/hanabi_kanto_{year}.json'
        scraper.save_to_json(events, filename)

        # Résumé
        print(f"\n✅ {len(events)} hanabi sauvegardés dans {filename}")
        print(f"\n📊 Résumé:")
        print(f"  • Événements trouvés: {len(events)}")
        total_dates = sum(len(e.get('dates', [])) for e in events)
        print(f"  • Total de dates individuelles: {total_dates}")
        print(f"  • Avec horaires: {sum(1 for e in events if e.get('start_time'))}/{len(events)}")
        print(f"  • Avec nb de feux: {sum(1 for e in events if e.get('fireworks_count'))}/{len(events)}")
        print(f"  • Avec Google Maps: {sum(1 for e in events if e.get('googlemap_link'))}/{len(events)}")
        return

    # Handle festivals/expositions (month-based)
    if len(sys.argv) != 4:
        print("Usage: uv run scrape.py <type> <mois> <année>")
        print("Exemples:")
        print("  uv run scrape.py festivals mars 2025")
        print("  uv run scrape.py expositions janvier 2026")
        sys.exit(1)

    month_name = sys.argv[2].lower()
    try:
        year = int(sys.argv[3])
    except ValueError:
        print(f"❌ Année invalide: {sys.argv[3]}")
        sys.exit(1)

    # Mapping des mois
    months = {
        'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12
    }

    month_num = months.get(month_name)
    if not month_num:
        print(f"❌ Mois invalide: {month_name}")
        print(f"Mois valides: {', '.join(months.keys())}")
        sys.exit(1)

    # Scraper selon le type
    if scrape_type == 'festivals':
        print(f"🔍 Scraping des festivals de {month_name} {year}...\n")
        scraper = TokyoFestivalScraper()
        items = scraper.scrape_festivals(month=month_num, year=year)
        filename = f'data/festivals_{month_name}_{year}.json'
        item_type = "festivals"
    else:  # expositions
        print(f"🔍 Scraping des expositions de {month_name} {year}...\n")
        scraper = TokyoExpositionScraper()
        items = scraper.scrape_expositions(month=month_num, year=year)
        filename = f'data/expositions_{month_name}_{year}.json'
        item_type = "expositions"

    # Sauvegarder
    scraper.save_to_json(items, filename)

    # Résumé
    print(f"\n✅ {len(items)} {item_type} sauvegardés dans {filename}")
    print(f"\n📊 Résumé:")

    with_maps = sum(1 for item in items if item.get('googlemap_link'))
    with_website = sum(1 for item in items if item.get('website'))

    print(f"  • {item_type.capitalize()} trouvés: {len(items)}")
    print(f"  • Avec dates: {len(items)}/{len(items)} (100%)")
    print(f"  • Avec lieu: {sum(1 for item in items if item.get('location'))}/{len(items)}")
    print(f"  • Avec description: {sum(1 for item in items if item.get('description'))}/{len(items)}")
    print(f"  • Avec website: {with_website}/{len(items)}")
    print(f"  • Avec Google Maps: {with_maps}/{len(items)}")


if __name__ == "__main__":
    main()
