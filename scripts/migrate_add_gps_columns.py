"""
Script de migration pour ajouter les colonnes latitude et longitude.

Usage:
    uv run scripts/migrate_add_gps_columns.py
"""

import sqlite3
import sys
from pathlib import Path

# Ajouter le dossier parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))


def migrate_database(db_path: str = "data/tokyo_events.sqlite"):
    """
    Ajoute les colonnes latitude et longitude à la table events.

    Args:
        db_path: Chemin vers la base de données SQLite
    """
    print(f"Migration de la base de données: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Vérifier si les colonnes existent déjà
        cursor.execute("PRAGMA table_info(events)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'latitude' in columns and 'longitude' in columns:
            print("[OK] Les colonnes latitude et longitude existent deja")
            return

        # Ajouter les colonnes
        print("Ajout des colonnes latitude et longitude...")
        cursor.execute("ALTER TABLE events ADD COLUMN latitude REAL")
        cursor.execute("ALTER TABLE events ADD COLUMN longitude REAL")

        # Créer l'index
        print("Creation de l'index sur les coordonnees...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_coordinates ON events(latitude, longitude)")

        conn.commit()
        print("[OK] Migration reussie!")

        # Statistiques
        cursor.execute("SELECT COUNT(*) FROM events")
        total = cursor.fetchone()[0]
        print(f"\nNombre total d'evenements: {total}")
        print("Les coordonnees GPS peuvent maintenant etre peuplees avec:")
        print("  uv run scripts/populate_gps_coordinates.py")

    except Exception as e:
        print(f"[ERREUR] Erreur lors de la migration: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    migrate_database()
