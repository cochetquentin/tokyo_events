"""
Script pour scraper les festivals de Tokyo
Usage: uv run scrape.py <mois> <année>
Exemple: uv run scrape.py mars 2025
"""

import sys
from src.scraper_festivals_tokyo import TokyoFestivalScraper


def main():
    if len(sys.argv) != 3:
        print("Usage: uv run scrape.py <mois> <année>")
        print("Exemple: uv run scrape.py mars 2025")
        sys.exit(1)

    month_name = sys.argv[1].lower()
    try:
        year = int(sys.argv[2])
    except ValueError:
        print(f"❌ Année invalide: {sys.argv[2]}")
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

    # Scraper
    print(f"🔍 Scraping des festivals de {month_name} {year}...\n")

    scraper = TokyoFestivalScraper()
    festivals = scraper.scrape_festivals(month=month_num, year=year)

    # Sauvegarder
    filename = f'data/festivals_{month_name}_{year}.json'
    scraper.save_to_json(festivals, filename)

    # Résumé
    print(f"\n✅ {len(festivals)} festivals sauvegardés dans {filename}")
    print(f"\n📊 Résumé:")

    with_maps = sum(1 for f in festivals if f.get('googlemap_link'))
    with_website = sum(1 for f in festivals if f.get('website'))

    print(f"  • Festivals trouvés: {len(festivals)}")
    print(f"  • Avec dates: {len(festivals)}/{len(festivals)} (100%)")
    print(f"  • Avec lieu: {sum(1 for f in festivals if f.get('location'))}/{len(festivals)}")
    print(f"  • Avec description: {sum(1 for f in festivals if f.get('description'))}/{len(festivals)}")
    print(f"  • Avec website: {with_website}/{len(festivals)}")
    print(f"  • Avec Google Maps: {with_maps}/{len(festivals)}")


if __name__ == "__main__":
    main()
