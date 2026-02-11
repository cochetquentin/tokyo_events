"""
Script pour peupler les coordonnées GPS de tous les événements.

Usage:
    uv run scripts/populate_gps_coordinates.py [--dry-run] [--event-type TYPE]
"""

import argparse
import logging
import sys
from pathlib import Path

# Ajouter le dossier parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import EventDatabase
from src.gps_extractor import GPSExtractor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def populate_coordinates(db_path: str, dry_run: bool = False, event_type: str = None):
    """
    Peuple les coordonnées GPS pour tous les événements.

    Args:
        db_path: Chemin vers la base de données SQLite
        dry_run: Si True, affiche ce qui serait fait sans modifier la DB
        event_type: Filtrer par type d'événement (None = tous)
    """
    db = EventDatabase(db_path)
    extractor = GPSExtractor()

    # Récupérer tous les événements
    events = db.get_events(event_type=event_type)
    logger.info(f"Traitement de {len(events)} événements...")

    stats = {
        'total': len(events),
        'with_link': 0,
        'success': 0,
        'failed': 0,
        'already_has_gps': 0
    }

    for i, event in enumerate(events, 1):
        name = event.get('name', 'Sans nom')
        googlemap_link = event.get('googlemap_link')

        # Vérifier si a déjà des coordonnées
        if event.get('latitude') and event.get('longitude'):
            logger.debug(f"[{i}/{len(events)}] {name} - Coordonnées déjà présentes")
            stats['already_has_gps'] += 1
            continue

        if not googlemap_link:
            logger.debug(f"[{i}/{len(events)}] {name} - Pas de lien Google Maps")
            continue

        stats['with_link'] += 1

        # Extraire coordonnées
        coords = extractor.extract_from_googlemap_link(googlemap_link)

        if coords:
            lat, lon = coords
            logger.info(f"[{i}/{len(events)}] {name} - Coordonnées: {lat}, {lon}")

            if not dry_run:
                # Mettre à jour la DB
                with db.get_connection() as conn:
                    conn.execute(
                        "UPDATE events SET latitude = ?, longitude = ? WHERE name = ?",
                        (lat, lon, name)
                    )
                    conn.commit()

            stats['success'] += 1
        else:
            logger.warning(f"[{i}/{len(events)}] {name} - Échec extraction GPS")
            stats['failed'] += 1

    # Afficher statistiques
    print("\n" + "="*60)
    print("STATISTIQUES DE POPULATION GPS")
    print("="*60)
    print(f"Événements totaux:          {stats['total']}")
    print(f"Avec lien Google Maps:      {stats['with_link']}")
    print(f"Déjà avec GPS:              {stats['already_has_gps']}")
    print(f"Extraction réussie:         {stats['success']}")
    print(f"Extraction échouée:         {stats['failed']}")

    if stats['with_link'] > 0:
        success_rate = (stats['success'] / stats['with_link']) * 100
        print(f"Taux de succès:             {success_rate:.1f}%")

    if dry_run:
        print("\n⚠️  MODE DRY-RUN: Aucune modification effectuée")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Peupler les coordonnées GPS des événements")
    parser.add_argument('--dry-run', action='store_true', help="Afficher ce qui serait fait sans modifier la DB")
    parser.add_argument('--event-type', choices=['festivals', 'expositions', 'hanabi', 'marches'], help="Filtrer par type")
    parser.add_argument('--db-path', default='data/tokyo_events.sqlite', help="Chemin vers la DB")

    args = parser.parse_args()

    populate_coordinates(args.db_path, args.dry_run, args.event_type)
