"""
Script de migration pour ajouter la colonne category.

Usage:
    uv run scripts/migrate_add_category_column.py
"""

import sqlite3
import sys
from pathlib import Path

# Ajouter le dossier parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))


def migrate_database(db_path: str = "data/tokyo_events.sqlite"):
    """
    Ajoute la colonne category à la table events.

    Args:
        db_path: Chemin vers la base de données SQLite
    """
    print(f"Migration de la base de données: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Vérifier si la colonne existe déjà
        cursor.execute("PRAGMA table_info(events)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'category' in columns:
            print("[OK] La colonne category existe deja")
            return

        # Ajouter la colonne
        print("Ajout de la colonne category...")
        cursor.execute("ALTER TABLE events ADD COLUMN category TEXT")

        # Créer l'index
        print("Creation de l'index sur category...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON events(category)")

        conn.commit()
        print("[OK] Migration reussie!")

        # Statistiques
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_type = 'tokyo_cheapo'")
        tokyo_cheapo_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM events")
        total = cursor.fetchone()[0]

        print(f"\nNombre total d'evenements: {total}")
        print(f"Evenements Tokyo Cheapo: {tokyo_cheapo_count}")
        print("\nLes categories seront peuplees lors du prochain scraping:")
        print("  make scrape-tokyo-cheapo")

    except Exception as e:
        print(f"[ERREUR] Erreur lors de la migration: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    migrate_database()
