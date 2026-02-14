"""
Script pour supprimer les doublons d'événements dans la base de données.

Les doublons sont détectés en normalisant les noms (insensible à la casse).
Pour chaque groupe de doublons, on garde le plus récent (updated_at).

Usage: uv run scripts/remove_duplicates.py
"""

import sys
import io
from pathlib import Path

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ajouter le dossier parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import EventDatabase


def remove_duplicates(db_path: str = "data/tokyo_events.sqlite"):
    """Supprime les doublons d'événements."""
    db = EventDatabase(db_path)

    with db.get_connection() as conn:
        # Trouver les doublons (insensible à la casse)
        query = """
        SELECT LOWER(name) as normalized_name, event_type, start_date, COUNT(*) as count
        FROM events
        GROUP BY LOWER(name), event_type, COALESCE(start_date, '')
        HAVING COUNT(*) > 1
        """

        duplicates = conn.execute(query).fetchall()

        if not duplicates:
            print("✓ Aucun doublon trouvé")
            return

        print(f"Doublons trouvés: {len(duplicates)} groupes\n")

        total_deleted = 0

        for dup in duplicates:
            normalized_name = dup[0]
            event_type = dup[1]
            start_date = dup[2]
            count = dup[3]

            # Récupérer tous les événements de ce groupe
            find_query = """
            SELECT id, name, updated_at
            FROM events
            WHERE LOWER(name) = ?
              AND event_type = ?
              AND COALESCE(start_date, '') = ?
            ORDER BY updated_at DESC
            """

            events = conn.execute(find_query, (normalized_name, event_type, start_date)).fetchall()

            if len(events) <= 1:
                continue

            # Garder le plus récent, supprimer les autres
            keep_id = events[0][0]
            keep_name = events[0][1]

            ids_to_delete = [e[0] for e in events[1:]]

            print(f"Groupe: {normalized_name} ({event_type})")
            print(f"  Garder: ID={keep_id} - {keep_name}")
            print(f"  Supprimer: {len(ids_to_delete)} événement(s)")

            # Supprimer les doublons
            placeholders = ','.join(['?' for _ in ids_to_delete])
            delete_query = f"DELETE FROM events WHERE id IN ({placeholders})"
            conn.execute(delete_query, ids_to_delete)

            total_deleted += len(ids_to_delete)

        conn.commit()

        print(f"\n✓ {total_deleted} doublons supprimés")

        # Afficher les statistiques finales
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        print(f"✓ Total événements restants: {total}")


if __name__ == "__main__":
    remove_duplicates()
