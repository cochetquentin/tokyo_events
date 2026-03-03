"""Script pour créer l'index sur la colonne category."""

import sqlite3
from pathlib import Path

def create_category_index():
    """Crée un index sur la colonne category pour optimiser les performances."""
    db_path = Path(__file__).parent.parent / "data" / "tokyo_events.sqlite"

    print(f"Connexion à la base de données: {db_path}")

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Créer l'index s'il n'existe pas déjà
        print("Création de l'index idx_category...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_category
            ON events(category)
        """)

        conn.commit()
        print("Index créé avec succès!")

        # Vérifier que l'index existe
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_category'
        """)
        result = cursor.fetchone()

        if result:
            print(f"Confirmation: Index '{result[0]}' existe dans la base de données")
        else:
            print("Attention: L'index n'a pas été trouvé!")

if __name__ == "__main__":
    create_category_index()
