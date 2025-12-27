"""
Exemples d'utilisation du scraper de festivals Tokyo
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper_festivals_tokyo import TokyoFestivalScraper


def exemple_basique():
    """Scraper un mois spécifique"""
    scraper = TokyoFestivalScraper()

    # Scraper décembre 2025
    festivals = scraper.scrape_festivals(month=12, year=2025)

    # Sauvegarder
    scraper.save_to_json(festivals)
    scraper.save_to_csv(festivals)

    print(f"Trouvé {len(festivals)} festivals")


def exemple_plusieurs_mois():
    """Scraper plusieurs mois d'affilée"""
    scraper = TokyoFestivalScraper()

    # Scraper de janvier à juin 2026
    for month in range(1, 7):
        print(f"\n--- Mois {month}/2026 ---")
        festivals = scraper.scrape_festivals(month=month, year=2026)

        if festivals:
            scraper.save_to_json(festivals)
            scraper.save_to_csv(festivals)


def exemple_personnalise():
    """Exemple avec paramètres personnalisés"""
    scraper = TokyoFestivalScraper()

    # Scraper mars 2025
    festivals = scraper.scrape_festivals(month=3, year=2025)

    if festivals:
        # Sauvegarder avec un nom personnalisé
        scraper.save_to_json(festivals, filename="mes_festivals_mars_2025.json")
        scraper.save_to_csv(festivals, filename="mes_festivals_mars_2025.csv")

        # Afficher tous les festivals
        for festival in festivals:
            print(f"\n{festival['name']}")
            print(f"  📅 {festival.get('dates', 'Dates non spécifiées')}")
            print(f"  📍 {festival.get('location', 'Lieu non spécifié')}")
            if festival.get('features'):
                print(f"  ✨ {', '.join(festival['features'][:3])}")


def exemple_toute_annee():
    """Scraper tous les mois d'une année"""
    scraper = TokyoFestivalScraper()
    year = 2025

    tous_festivals = []

    print(f"Scraping de tous les festivals de {year}...\n")

    for month in range(1, 13):
        try:
            festivals = scraper.scrape_festivals(month=month, year=year)
            tous_festivals.extend(festivals)
        except Exception as e:
            print(f"Erreur pour {scraper.MONTHS_FR[month]} {year}: {e}")

    # Sauvegarder tous les festivals de l'année
    if tous_festivals:
        scraper.save_to_json(tous_festivals, filename=f"festivals_tokyo_{year}_complet.json")
        scraper.save_to_csv(tous_festivals, filename=f"festivals_tokyo_{year}_complet.csv")

        print(f"\n✓ Total: {len(tous_festivals)} festivals pour l'année {year}")


if __name__ == "__main__":
    print("=== Exemples d'utilisation ===\n")

    # Choisissez l'exemple à exécuter
    print("1. Exemple basique (décembre 2025)")
    exemple_basique()

    # Décommentez pour tester les autres exemples:
    # print("\n2. Exemple plusieurs mois")
    # exemple_plusieurs_mois()

    # print("\n3. Exemple personnalisé")
    # exemple_personnalise()

    # print("\n4. Scraper toute l'année")
    # exemple_toute_annee()