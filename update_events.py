"""
Script de mise à jour automatique des événements Tokyo Cheapo

Usage:
    python update_events.py              # Mise à jour complète
    python update_events.py --dry-run    # Simulation sans sauvegarde
    python update_events.py --stats      # Afficher seulement les statistiques
"""

import argparse
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Set
from collections import Counter

from src.scraper_tokyo_cheapo import TokyoCheapoScraper


class EventUpdater:
    """Gestionnaire de mise à jour des événements"""

    def __init__(self, db_path: str = "data/tokyo_events.sqlite"):
        self.db_path = db_path
        self.scraper = TokyoCheapoScraper()

    def get_existing_events(self) -> Set[str]:
        """
        Récupérer les événements existants dans la base

        Returns:
            Set de tuples (name, start_date) pour identifier les événements
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, start_date
            FROM events
            WHERE event_type IN ('tokyo_cheapo', 'festivals', 'expositions', 'marches')
        """)

        existing = set()
        for name, start_date in cursor.fetchall():
            # Créer une clé unique (nom + date)
            key = f"{name}|{start_date or 'no-date'}"
            existing.add(key)

        conn.close()
        return existing

    def get_database_stats(self) -> Dict:
        """Récupérer les statistiques de la base de données"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total par type
        cursor.execute("""
            SELECT event_type, COUNT(*)
            FROM events
            GROUP BY event_type
        """)
        stats['by_type'] = dict(cursor.fetchall())

        # Total général
        cursor.execute("SELECT COUNT(*) FROM events")
        stats['total'] = cursor.fetchone()[0]

        # Événements futurs
        today = datetime.now().strftime('%Y/%m/%d')
        cursor.execute("""
            SELECT COUNT(*)
            FROM events
            WHERE start_date >= ? OR end_date >= ?
        """, (today, today))
        stats['future'] = cursor.fetchone()[0]

        # Événements passés
        cursor.execute("""
            SELECT COUNT(*)
            FROM events
            WHERE end_date < ? OR (end_date IS NULL AND start_date < ?)
        """, (today, today))
        stats['past'] = cursor.fetchone()[0]

        # Dernière mise à jour
        cursor.execute("""
            SELECT MAX(updated_at)
            FROM events
            WHERE event_type = 'tokyo_cheapo'
        """)
        last_update = cursor.fetchone()[0]
        stats['last_update'] = last_update

        conn.close()
        return stats

    def identify_new_events(self, scraped_events: List[Dict], existing: Set[str]) -> List[Dict]:
        """
        Identifier les événements nouveaux ou modifiés

        Args:
            scraped_events: Événements scrapés
            existing: Set des événements existants

        Returns:
            Liste des nouveaux événements
        """
        new_events = []

        for event in scraped_events:
            key = f"{event['name']}|{event.get('start_date', 'no-date')}"

            if key not in existing:
                new_events.append(event)

        return new_events

    def clean_old_events(self, days_old: int = 30) -> int:
        """
        Nettoyer les événements passés

        Args:
            days_old: Nombre de jours avant suppression

        Returns:
            Nombre d'événements supprimés
        """
        cutoff_date = (datetime.now() - timedelta(days=days_old)).strftime('%Y/%m/%d')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM events
            WHERE (end_date < ? OR (end_date IS NULL AND start_date < ?))
            AND event_type IN ('tokyo_cheapo', 'festivals', 'expositions', 'marches')
        """, (cutoff_date, cutoff_date))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted

    def update_events(self, max_pages: int = None, dry_run: bool = False, clean_old: bool = True) -> Dict:
        """
        Mettre à jour les événements

        Args:
            max_pages: Nombre max de pages à scraper (None = toutes)
            dry_run: Si True, simulation sans sauvegarde
            clean_old: Si True, nettoyer les vieux événements

        Returns:
            Dict avec les statistiques de mise à jour
        """
        print("=" * 80)
        print("🔄 MISE À JOUR DES ÉVÉNEMENTS TOKYO CHEAPO")
        print("=" * 80)

        # Statistiques avant
        print("\n📊 État de la base de données AVANT mise à jour:")
        stats_before = self.get_database_stats()
        self._print_stats(stats_before)

        # Récupérer les événements existants
        print("\n🔍 Récupération des événements existants...")
        existing = self.get_existing_events()
        print(f"   ✓ {len(existing)} événements déjà en base")

        # Scraper les nouveaux événements
        print(f"\n🕷️  Scraping des événements (max_pages={max_pages or 'all'})...")
        scraped_events = self.scraper.scrape_events(max_pages=max_pages)
        print(f"   ✓ {len(scraped_events)} événements scrapés")

        # Identifier les nouveaux
        print("\n🆕 Identification des nouveaux événements...")
        new_events = self.identify_new_events(scraped_events, existing)
        print(f"   ✓ {len(new_events)} nouveaux événements détectés")

        if len(new_events) == 0:
            print("\n✅ Aucun nouvel événement à ajouter")
            return {
                'scraped': len(scraped_events),
                'new': 0,
                'saved': 0,
                'cleaned': 0,
                'dry_run': dry_run
            }

        # Afficher les nouveaux événements
        print("\n📝 Aperçu des nouveaux événements:")
        for i, event in enumerate(new_events[:5], 1):
            print(f"   {i}. {event['name']}")
            if event.get('start_date'):
                print(f"      📅 {event['start_date']}")
            if event.get('location'):
                print(f"      📍 {event['location']}")

        if len(new_events) > 5:
            print(f"   ... et {len(new_events) - 5} autres")

        # Sauvegarder (si pas en mode dry-run)
        saved = 0
        if not dry_run:
            print(f"\n💾 Sauvegarde des nouveaux événements...")
            saved = self.scraper.save_to_database(new_events, self.db_path)
            print(f"   ✓ {saved} événements sauvegardés")
        else:
            print(f"\n⚠️  MODE DRY-RUN: Aucune sauvegarde effectuée")

        # Nettoyer les vieux événements
        cleaned = 0
        if clean_old and not dry_run:
            print(f"\n🧹 Nettoyage des événements passés (>30 jours)...")
            cleaned = self.clean_old_events(days_old=30)
            if cleaned > 0:
                print(f"   ✓ {cleaned} événements supprimés")
            else:
                print(f"   ✓ Aucun événement à nettoyer")

        # Statistiques après
        print("\n📊 État de la base de données APRÈS mise à jour:")
        stats_after = self.get_database_stats()
        self._print_stats(stats_after)

        # Résumé
        print("\n" + "=" * 80)
        print("✅ MISE À JOUR TERMINÉE")
        print("=" * 80)
        print(f"   Événements scrapés      : {len(scraped_events)}")
        print(f"   Nouveaux événements     : {len(new_events)}")
        print(f"   Événements sauvegardés  : {saved}")
        print(f"   Événements nettoyés     : {cleaned}")
        print(f"   Différence totale       : +{saved - cleaned}")

        return {
            'scraped': len(scraped_events),
            'new': len(new_events),
            'saved': saved,
            'cleaned': cleaned,
            'dry_run': dry_run
        }

    def _print_stats(self, stats: Dict):
        """Afficher les statistiques de manière formatée"""
        print(f"   Total événements        : {stats['total']}")
        print(f"   Événements futurs       : {stats['future']}")
        print(f"   Événements passés       : {stats['past']}")
        print(f"\n   Par type:")
        for event_type, count in sorted(stats['by_type'].items()):
            print(f"      - {event_type:20s}: {count:4d}")
        if stats.get('last_update'):
            print(f"\n   Dernière mise à jour    : {stats['last_update']}")


def main():
    """Point d'entrée du script"""
    parser = argparse.ArgumentParser(
        description="Mise à jour automatique des événements Tokyo Cheapo"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Mode simulation (pas de sauvegarde)"
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help="Afficher uniquement les statistiques"
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        help="Nombre maximum de pages à scraper (défaut: toutes)"
    )
    parser.add_argument(
        '--no-clean',
        action='store_true',
        help="Ne pas nettoyer les vieux événements"
    )

    args = parser.parse_args()

    updater = EventUpdater()

    # Mode stats uniquement
    if args.stats:
        print("=" * 80)
        print("📊 STATISTIQUES DE LA BASE DE DONNÉES")
        print("=" * 80)
        stats = updater.get_database_stats()
        updater._print_stats(stats)
        return

    # Mise à jour
    try:
        result = updater.update_events(
            max_pages=args.max_pages,
            dry_run=args.dry_run,
            clean_old=not args.no_clean
        )

        # Code de sortie basé sur le résultat
        if result['new'] > 0 and not result['dry_run']:
            sys.exit(0)  # Succès avec nouveaux événements
        elif result['new'] == 0:
            sys.exit(0)  # Succès mais rien de nouveau
        else:
            sys.exit(0)  # Dry-run

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
