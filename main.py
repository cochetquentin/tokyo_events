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
from src.scraper_marches_tokyo import TokyoMarcheScraper
from src.scraper_tokyo_cheapo import TokyoCheapoScraper
from src.database import EventDatabase
from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Set


def get_existing_events(db_path: str, event_type: str) -> Set[str]:
    """Récupérer les événements existants pour un type donné"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, start_date FROM events WHERE event_type = ?", (event_type,))
    existing = set()
    for name, start_date in cursor.fetchall():
        key = f"{name}|{start_date or 'no-date'}"
        existing.add(key)
    conn.close()
    return existing


def identify_new_events(scraped_events: List[Dict], existing: Set[str]) -> List[Dict]:
    """Identifier les événements nouveaux"""
    new_events = []
    for event in scraped_events:
        key = f"{event['name']}|{event.get('start_date', 'no-date')}"
        if key not in existing:
            new_events.append(event)
    return new_events


def get_database_stats(db_path: str = "data/tokyo_events.sqlite") -> Dict:
    """Récupérer les statistiques de la base de données"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    stats = {}
    cursor.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type")
    stats['by_type'] = dict(cursor.fetchall())
    cursor.execute("SELECT COUNT(*) FROM events")
    stats['total'] = cursor.fetchone()[0]
    today = datetime.now().strftime('%Y/%m/%d')
    cursor.execute("SELECT COUNT(*) FROM events WHERE start_date >= ? OR end_date >= ?", (today, today))
    stats['future'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM events WHERE end_date < ? OR (end_date IS NULL AND start_date < ?)", (today, today))
    stats['past'] = cursor.fetchone()[0]
    conn.close()
    return stats


def print_stats(stats: Dict):
    """Afficher les statistiques"""
    print(f"   Total événements        : {stats['total']}")
    print(f"   Événements futurs       : {stats['future']}")
    print(f"   Événements passés       : {stats['past']}")
    print(f"\n   Par type:")
    for event_type, count in sorted(stats['by_type'].items()):
        print(f"      - {event_type:20s}: {count:4d}")


def clean_old_events(db_path: str, days_old: int = 30) -> int:
    """Nettoyer les événements passés"""
    cutoff_date = (datetime.now() - timedelta(days=days_old)).strftime('%Y/%m/%d')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE (end_date < ? OR (end_date IS NULL AND start_date < ?))", (cutoff_date, cutoff_date))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def update_all_events(dry_run: bool = False):
    """Mise à jour globale de tous les scrapers"""
    db_path = "data/tokyo_events.sqlite"

    print("=" * 80)
    print("🔄 MISE À JOUR GLOBALE DE TOUS LES ÉVÉNEMENTS")
    print("=" * 80)

    print("\n📊 État de la base de données AVANT mise à jour:")
    stats_before = get_database_stats(db_path)
    print_stats(stats_before)

    results = {}

    # Tokyo Cheapo
    print("\n" + "=" * 80)
    print("🏙️  TOKYO CHEAPO EVENTS")
    print("=" * 80)
    existing = get_existing_events(db_path, 'tokyo_cheapo')
    print(f"📊 Événements existants: {len(existing)}")
    scraper = TokyoCheapoScraper()
    print(f"🕷️  Scraping Tokyo Cheapo (5 pages)...")
    scraped = scraper.scrape_events(max_pages=5)
    print(f"   ✓ {len(scraped)} événements scrapés")
    new_events = identify_new_events(scraped, existing)
    print(f"🆕 {len(new_events)} nouveaux événements")
    saved = 0
    if not dry_run and len(new_events) > 0:
        print(f"💾 Sauvegarde...")
        saved = scraper.save_to_database(new_events, db_path)
        print(f"   ✓ {saved} événements sauvegardés")
    results['tokyo_cheapo'] = {'scraped': len(scraped), 'new': len(new_events), 'saved': saved}

    # Festivals (mois en cours)
    print("\n" + "=" * 80)
    print("🎊 FESTIVALS")
    print("=" * 80)
    month, year = datetime.now().month, datetime.now().year
    month_names = {1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
                   7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"}
    print(f"📅 Mois cible: {month_names[month]} {year}")
    existing = get_existing_events(db_path, 'festivals')
    print(f"📊 Événements existants: {len(existing)}")
    scraper_f = TokyoFestivalScraper()
    print(f"🕷️  Scraping festivals...")
    scraped = scraper_f.scrape_festivals(month=month, year=year)
    print(f"   ✓ {len(scraped)} événements scrapés")
    new_events = identify_new_events(scraped, existing)
    print(f"🆕 {len(new_events)} nouveaux événements")
    if len(new_events) == 0:
        print("   ⏭️  Mois déjà scrapé, skip")
        results['festivals'] = {'scraped': len(scraped), 'new': 0, 'saved': 0}
    else:
        saved = 0
        if not dry_run:
            print(f"💾 Sauvegarde...")
            saved = scraper_f.save_to_database(scraped, db_path)
            print(f"   ✓ {saved} événements sauvegardés")
        results['festivals'] = {'scraped': len(scraped), 'new': len(new_events), 'saved': saved}

    # Expositions (mois en cours)
    print("\n" + "=" * 80)
    print("🎨 EXPOSITIONS")
    print("=" * 80)
    print(f"📅 Mois cible: {month_names[month]} {year}")
    existing = get_existing_events(db_path, 'expositions')
    print(f"📊 Événements existants: {len(existing)}")
    scraper_e = TokyoExpositionScraper()
    print(f"🕷️  Scraping expositions...")
    scraped = scraper_e.scrape_expositions(month=month, year=year)
    print(f"   ✓ {len(scraped)} événements scrapés")
    new_events = identify_new_events(scraped, existing)
    print(f"🆕 {len(new_events)} nouveaux événements")
    if len(new_events) == 0:
        print("   ⏭️  Mois déjà scrapé, skip")
        results['expositions'] = {'scraped': len(scraped), 'new': 0, 'saved': 0}
    else:
        saved = 0
        if not dry_run:
            print(f"💾 Sauvegarde...")
            saved = scraper_e.save_to_database(scraped, db_path)
            print(f"   ✓ {saved} événements sauvegardés")
        results['expositions'] = {'scraped': len(scraped), 'new': len(new_events), 'saved': saved}

    # Marchés
    print("\n" + "=" * 80)
    print("🏪 MARCHÉS AUX PUCES")
    print("=" * 80)
    existing = get_existing_events(db_path, 'marches')
    print(f"📊 Événements existants: {len(existing)}")
    scraper_m = TokyoMarcheScraper()
    print(f"🕷️  Scraping marchés...")
    scraped = scraper_m.scrape_marches(month=month, year=year)
    print(f"   ✓ {len(scraped)} événements scrapés")
    new_events = identify_new_events(scraped, existing)
    print(f"🆕 {len(new_events)} nouveaux événements")
    if len(new_events) == 0:
        print("   ⏭️  Déjà scrapé, skip")
        results['marches'] = {'scraped': len(scraped), 'new': 0, 'saved': 0}
    else:
        saved = 0
        if not dry_run:
            print(f"💾 Sauvegarde...")
            saved = scraper_m.save_to_database(scraped, db_path)
            print(f"   ✓ {saved} événements sauvegardés")
        results['marches'] = {'scraped': len(scraped), 'new': len(new_events), 'saved': saved}

    # Hanabi (3 prochains mois)
    print("\n" + "=" * 80)
    print("🎆 FEUX D'ARTIFICE (HANABI)")
    print("=" * 80)
    print(f"📅 Période: 5 prochains mois")
    existing = get_existing_events(db_path, 'hanabi')
    print(f"📊 Événements existants: {len(existing)}")
    scraper_h = KantoHanabiScraper()
    print(f"🕷️  Scraping hanabi...")
    scraped = scraper_h.scrape_hanabi(months_ahead=5)
    print(f"   ✓ {len(scraped)} événements scrapés")
    new_events = identify_new_events(scraped, existing)
    print(f"🆕 {len(new_events)} nouveaux événements")
    saved = 0
    if not dry_run and len(new_events) > 0:
        print(f"💾 Sauvegarde...")
        saved = scraper_h.save_to_database(scraped, db_path)
        print(f"   ✓ {saved} événements sauvegardés")
    results['hanabi'] = {'scraped': len(scraped), 'new': len(new_events), 'saved': saved}

    # Nettoyage
    cleaned = 0
    if not dry_run:
        print(f"\n🧹 Nettoyage des événements passés (>30 jours)...")
        cleaned = clean_old_events(db_path, days_old=30)
        if cleaned > 0:
            print(f"   ✓ {cleaned} événements supprimés")
        else:
            print(f"   ✓ Aucun événement à nettoyer")

    # Statistiques après
    print("\n📊 État de la base de données APRÈS mise à jour:")
    stats_after = get_database_stats(db_path)
    print_stats(stats_after)

    # Résumé
    print("\n" + "=" * 80)
    print("✅ MISE À JOUR GLOBALE TERMINÉE")
    print("=" * 80)
    total_saved = sum(r['saved'] for r in results.values())
    total_new = sum(r['new'] for r in results.values())
    total_scraped = sum(r['scraped'] for r in results.values())
    print(f"\n📊 RÉSUMÉ PAR TYPE:")
    for event_type, result in results.items():
        print(f"   {event_type:20s}: {result['saved']:3d} sauvegardés / {result['new']:3d} nouveaux / {result['scraped']:3d} scrapés")
    print(f"\n📈 TOTAUX:")
    print(f"   Événements scrapés      : {total_scraped}")
    print(f"   Nouveaux événements     : {total_new}")
    print(f"   Événements sauvegardés  : {total_saved}")
    print(f"   Événements nettoyés     : {cleaned}")
    print(f"   Différence totale       : +{total_saved - cleaned}")


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run main.py <type> [options]")
        print("Exemples:")
        print("  uv run main.py festivals mars 2025")
        print("  uv run main.py expositions janvier 2026")
        print("  uv run main.py marches  # Scrape tous les marchés aux puces")
        print("  uv run main.py hanabi [mois_avance]  # Par défaut: 6 mois")
        print("  uv run main.py update-all  # Mise à jour globale de tous les scrapers")
        print("  uv run main.py stats       # Afficher les statistiques")
        sys.exit(1)

    scrape_type = sys.argv[1].lower()

    # Commandes spéciales
    if scrape_type == 'stats':
        print("=" * 80)
        print("📊 STATISTIQUES DE LA BASE DE DONNÉES")
        print("=" * 80)
        stats = get_database_stats()
        print_stats(stats)
        return

    if scrape_type == 'update-all':
        dry_run = '--dry-run' in sys.argv
        update_all_events(dry_run=dry_run)
        return

    # Valider le type
    if scrape_type not in ['festivals', 'expositions', 'hanabi', 'marches']:
        print(f"❌ Type invalide: {scrape_type}")
        print("Types valides: festivals, expositions, marches, hanabi, update-all, stats")
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

        scraper.save_to_database(events)

        # Résumé
        print(f"\n✅ {len(events)} hanabi sauvegardés dans la base de données")
        print(f"\n📊 Résumé:")
        print(f"  • Événements trouvés: {len(events)}")
        print(f"  • Avec horaires: {sum(1 for e in events if e.get('start_time'))}/{len(events)}")
        print(f"  • Avec nb de feux: {sum(1 for e in events if e.get('fireworks_count'))}/{len(events)}")
        print(f"  • Avec Google Maps: {sum(1 for e in events if e.get('googlemap_link'))}/{len(events)}")
        return

    # Handle marches (no date parameter - scrapes all)
    if scrape_type == 'marches':
        print(f"🛍️ Scraping des marchés aux puces de Tokyo...\n")
        scraper = TokyoMarcheScraper()
        month = datetime.now().month
        year = datetime.now().year
        events = scraper.scrape_marches(month=month, year=year)

        scraper.save_to_database(events)

        # Résumé
        print(f"\n✅ {len(events)} marchés sauvegardés dans la base de données")
        print(f"\n📊 Résumé:")
        print(f"  • Marchés trouvés: {len(events)}")
        print(f"  • Avec dates: {sum(1 for e in events if e.get('start_date'))}/{len(events)}")
        print(f"  • Avec lieu: {sum(1 for e in events if e.get('location'))}/{len(events)}")
        print(f"  • Avec horaires: {sum(1 for e in events if e.get('hours'))}/{len(events)}")
        print(f"  • Avec tarif: {sum(1 for e in events if e.get('fee'))}/{len(events)}")
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
        item_type = "festivals"
    else:  # expositions
        print(f"🔍 Scraping des expositions de {month_name} {year}...\n")
        scraper = TokyoExpositionScraper()
        items = scraper.scrape_expositions(month=month_num, year=year)
        item_type = "expositions"

    # Sauvegarder
    scraper.save_to_database(items)

    # Résumé
    print(f"\n✅ {len(items)} {item_type} sauvegardés dans la base de données")
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
