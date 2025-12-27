"""
Script simple pour scraper les festivals de Tokyo
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper_festivals_tokyo import TokyoFestivalScraper

# Créer le scraper
scraper = TokyoFestivalScraper()

# Scraper décembre 2025
print("Scraping des festivals de Tokyo pour décembre 2025...")
festivals = scraper.scrape_festivals(month=12, year=2025)

# Sauvegarder les résultats
if festivals:
    scraper.save_to_json(festivals)
    scraper.save_to_csv(festivals)

    print(f"\n✓ {len(festivals)} festivals récupérés avec succès!")
    print("\nPremiers festivals :")
    for i, festival in enumerate(festivals[:5], 1):
        print(f"{i}. {festival['name']}")
else:
    print("Aucun festival trouvé")

# Pour scraper un autre mois, changez simplement month et year:
# festivals = scraper.scrape_festivals(month=1, year=2026)  # Janvier 2026
# festivals = scraper.scrape_festivals(month=6, year=2025)  # Juin 2025
