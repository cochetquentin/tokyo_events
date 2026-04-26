"""
Script de nettoyage global des doublons inter-event_types.

Détecte et fusionne les doublons entre différentes sources (hanabi, festivals, tokyo_cheapo, etc.)
en respectant les priorités définies dans le deduplicator.
"""

import sys
from src.database import EventDatabase
from src.deduplicator import EventDeduplicator


def safe_print(text):
    """Print avec gestion d'erreurs Unicode sur Windows."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback : encoder en ASCII en ignorant les caractères non-ASCII
        print(text.encode('ascii', 'ignore').decode('ascii'))


def cleanup_cross_type_duplicates(db_path: str = "data/tokyo_events.sqlite", dry_run: bool = False):
    """
    Nettoie les doublons entre différents event_types.

    Priorités (1 = plus prioritaire):
    1. hanabi
    2. festivals
    3. expositions
    4. marches
    5. tokyo_cheapo

    Args:
        db_path: Chemin vers la DB
        dry_run: Si True, affiche seulement les doublons sans les supprimer
    """
    db = EventDatabase(db_path)
    deduplicator = EventDeduplicator()

    # Récupérer TOUS les événements
    all_events = db.get_events()
    print(f"Total événements dans la DB: {len(all_events)}")
    print("=" * 80)

    # Normaliser tous les événements
    normalized_events = []
    for event in all_events:
        norm_event = deduplicator._normalize_event(event)
        # Ajouter l'ID pour pouvoir identifier l'événement original
        normalized_events.append(norm_event)

    # Détecter les doublons inter-types
    duplicates_to_remove = []
    duplicates_to_merge = []

    print("\nRecherche de doublons inter-types...")
    print("-" * 80)

    for i in range(len(normalized_events)):
        for j in range(i + 1, len(normalized_events)):
            event1 = normalized_events[i]
            event2 = normalized_events[j]

            # Ne comparer que si event_types différents
            if event1['event_type'] == event2['event_type']:
                continue

            # Vérifier si doublons
            is_dup, reason = deduplicator._are_duplicates(event1, event2)

            if is_dup:
                # Déterminer lequel garder selon priorité
                prio1 = deduplicator._get_source_priority(event1['event_type'])
                prio2 = deduplicator._get_source_priority(event2['event_type'])

                if prio1 < prio2:
                    # Event1 plus prioritaire, supprimer event2
                    primary = event1
                    to_remove = event2
                else:
                    # Event2 plus prioritaire, supprimer event1
                    primary = event2
                    to_remove = event1

                duplicates_to_remove.append(to_remove)
                duplicates_to_merge.append({
                    'primary': primary,
                    'secondary': to_remove,
                    'reason': reason
                })

    print(f"\nDoublons inter-types détectés: {len(duplicates_to_merge)}")

    if duplicates_to_merge:
        print("\nDétails des doublons:")
        print("-" * 80)

        for i, dup in enumerate(duplicates_to_merge, 1):
            primary = dup['primary']
            secondary = dup['secondary']

            safe_print(f"\n{i}. GARDER [{primary['event_type']}] {primary['name'][:50]}")
            safe_print(f"   SUPPRIMER [{secondary['event_type']}] {secondary['name'][:50]}")
            safe_print(f"   Raison: {dup['reason']}")
            safe_print(f"   Dates: {primary.get('start_date')} -> {primary.get('end_date')}")

    if not dry_run and duplicates_to_remove:
        print("\n" + "=" * 80)
        print("SUPPRESSION DES DOUBLONS")
        print("=" * 80)

        # Supprimer les doublons en utilisant une requête SQL directe
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for dup_event in duplicates_to_remove:
            # Identifier l'événement par (event_type, name, start_date, location)
            cursor.execute("""
                DELETE FROM events
                WHERE event_type = ?
                  AND name = ?
                  AND start_date = ?
                  AND COALESCE(location, '') = ?
            """, (
                dup_event['event_type'],
                dup_event['name'],
                dup_event.get('start_date', ''),
                dup_event.get('location', '')
            ))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"\n[OK] {deleted} doublons supprimes")

    elif dry_run and duplicates_to_merge:
        print("\n" + "=" * 80)
        print("MODE DRY-RUN: Aucune modification effectuée")
        print("=" * 80)
        print(f"Pour supprimer ces {len(duplicates_to_merge)} doublons, relancez sans --dry-run")

    else:
        print("\n[OK] Aucun doublon inter-types detecte")

    # Statistiques finales
    print("\n" + "=" * 80)
    print("STATISTIQUES FINALES")
    print("=" * 80)

    final_count = db.count_events()
    print(f"Total événements après nettoyage: {final_count}")

    for event_type in ['hanabi', 'festivals', 'expositions', 'marches', 'tokyo_cheapo']:
        count = db.count_events(event_type)
        print(f"  - {event_type:15s}: {count}")


if __name__ == "__main__":
    import sys

    dry_run = '--dry-run' in sys.argv

    print("=" * 80)
    print("NETTOYAGE DES DOUBLONS INTER-TYPES")
    print("=" * 80)

    if dry_run:
        print("\n[!] MODE DRY-RUN: Simulation uniquement, aucune modification")
    else:
        print("\n[!] MODE REEL: Les doublons seront supprimes")

    print()

    cleanup_cross_type_duplicates(dry_run=dry_run)
