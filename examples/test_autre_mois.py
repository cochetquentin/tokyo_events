"""
Test du scraper pour différents mois de 2025
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper_festivals_tokyo import TokyoFestivalScraper

scraper = TokyoFestivalScraper()

# Tester plusieurs mois de 2025
mois_a_tester = [
    (1, 2025, "Janvier"),
    (2, 2025, "Février"),
    (3, 2025, "Mars"),
    (4, 2025, "Avril"),
    (5, 2025, "Mai"),
    (6, 2025, "Juin"),
]

print("Test du scraper pour différents mois de 2025\n")
print("=" * 60)

for month, year, nom_mois in mois_a_tester:
    print(f"\n{nom_mois} {year}:")
    try:
        festivals = scraper.scrape_festivals(month=month, year=year)
        if festivals:
            scraper.save_to_json(festivals)
            scraper.save_to_csv(festivals)
            print(f"  ✓ Succès - {len(festivals)} festivals trouvés")
        else:
            print(f"  ⚠ Aucun festival trouvé (la page existe mais est vide)")
    except Exception as e:
        print(f"  ✗ Erreur: {e}")

print("\n" + "=" * 60)
print("Test terminé!")
