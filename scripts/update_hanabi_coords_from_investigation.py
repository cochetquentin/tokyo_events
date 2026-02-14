"""
Script pour mettre à jour les coordonnées des hanabi depuis l'investigation map.html.

Utilise les résultats de l'investigation pour peupler les coordonnées GPS.
"""

import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import EventDatabase


def main():
    """Update hanabi coordinates from investigation findings."""

    # Coordinates found during investigation
    coords_to_update = {
        'ar0314e541039': (35.45753, 139.642916),   # 横浜ナイトフラワーズ2025
        'ar0313e335967': (35.62494, 139.517534),   # よみうりランド 花火＆大迫力噴水ショー
    }

    db = EventDatabase()

    print("=" * 80)
    print("MAJ des coordonnées hanabi depuis investigation map.html")
    print("=" * 80)

    # Get all hanabi events
    hanabi_events = db.get_events(event_type='hanabi')
    print(f"\n[*] Hanabi events trouvés: {len(hanabi_events)}")

    updated_count = 0

    for event in hanabi_events:
        event_id = event.get('event_id')

        if event_id in coords_to_update:
            lat, lng = coords_to_update[event_id]

            print(f"\n[>] Event ID: {event_id}")
            print(f"    Coords avant: lat={event.get('latitude')}, lng={event.get('longitude')}")
            print(f"    Coords après: lat={lat}, lng={lng}")

            # Update in database
            with db.get_connection() as conn:
                conn.execute(
                    "UPDATE events SET latitude = ?, longitude = ? WHERE event_id = ? AND event_type = 'hanabi'",
                    (lat, lng, event_id)
                )
                conn.commit()

            updated_count += 1
            print(f"    [+] Mis à jour!")

    print(f"\n{'=' * 80}")
    print(f"RÉSUMÉ: {updated_count} événement(s) mis à jour")
    print(f"{'=' * 80}")

    # Verify
    print("\n[*] Vérification...")
    updated_events = db.get_events(event_type='hanabi')
    with_coords = sum(1 for e in updated_events if e.get('latitude') and e.get('longitude'))
    print(f"    Hanabi avec coordonnées: {with_coords}/{len(updated_events)}")


if __name__ == "__main__":
    main()
