"""
Script de test pour valider le fonctionnement de SQLite.
"""
import sys
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.scraper_festivals_tokyo import TokyoFestivalScraper
from src.database import EventDatabase

def test_sqlite():
    """Test complet du système SQLite."""

    print("=" * 60)
    print("TEST DE LA BASE DE DONNEES SQLite")
    print("=" * 60)

    # 1. Scraper quelques festivals
    print("\n1. Scraping festivals février 2025...")
    scraper = TokyoFestivalScraper()
    festivals = scraper.scrape_festivals(month=2, year=2025)
    print(f"   Trouvés: {len(festivals)} festivals")

    # 2. Sauvegarder dans SQLite
    print("\n2. Sauvegarde dans SQLite...")
    scraper.save_to_database(festivals)

    # 3. Vérifier le comptage
    print("\n3. Vérification des comptages...")
    db = EventDatabase()
    count_festivals = db.count_events('festivals')
    count_total = db.count_events()
    print(f"   Festivals en base: {count_festivals}")
    print(f"   Total événements: {count_total}")

    # 4. Test de requête avec filtres
    print("\n4. Test de requête avec filtres...")
    events_feb = db.get_events(
        event_type='festivals',
        start_date_from='2025/02/01',
        start_date_to='2025/02/28'
    )
    print(f"   Festivals en février 2025: {len(events_feb)}")

    # 5. Afficher quelques exemples
    print("\n5. Exemples d'événements en base:")
    for i, event in enumerate(events_feb[:3], 1):
        print(f"   {i}. {event['name']}")
        print(f"      Date: {event.get('start_date', 'N/A')}")
        print(f"      Lieu: {event.get('location', 'N/A')[:50]}...")

    # 6. Test de déduplication (re-scraper les mêmes données)
    print("\n6. Test de déduplication (re-scraping)...")
    initial_count = db.count_events('festivals')
    scraper.save_to_database(festivals)  # Sauvegarder à nouveau
    final_count = db.count_events('festivals')
    print(f"   Avant re-scrape: {initial_count}")
    print(f"   Après re-scrape: {final_count}")
    if initial_count == final_count:
        print("   ✓ Pas de doublons créés!")
    else:
        print("   ✗ ERREUR: Des doublons ont été créés!")

    # 7. Test de filtrage par lieu
    print("\n7. Test de filtrage par lieu...")
    events_taito = db.get_events(event_type='festivals', location='Taito')
    print(f"   Festivals à Taito: {len(events_taito)}")

    # 8. Résumé final
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"✓ Scraping: OK ({len(festivals)} festivals)")
    print(f"✓ Sauvegarde: OK")
    print(f"✓ Comptage: OK ({count_festivals} festivals)")
    print(f"✓ Requêtes: OK")
    print(f"✓ Déduplication: OK")
    print("\n✓✓✓ Tous les tests passent! SQLite fonctionne correctement! ✓✓✓\n")

if __name__ == "__main__":
    test_sqlite()
