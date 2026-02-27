"""
Script pour visualiser les événements Tokyo Cheapo scrapés
"""

import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import sqlite3
from datetime import datetime

DB_PATH = "data/tokyo_events.sqlite"


def view_tokyo_cheapo_events():
    """Afficher tous les événements Tokyo Cheapo"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Statistiques globales
    print("=" * 80)
    print("📊 STATISTIQUES DES ÉVÉNEMENTS")
    print("=" * 80)

    cursor.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type ORDER BY COUNT(*) DESC")
    total = 0
    for event_type, count in cursor.fetchall():
        print(f"  {event_type:20s}: {count:4d} événements")
        total += count
    print(f"  {'TOTAL':20s}: {total:4d} événements")

    # Événements Tokyo Cheapo
    print("\n" + "=" * 80)
    print("🎯 ÉVÉNEMENTS TOKYO CHEAPO")
    print("=" * 80)

    cursor.execute("""
        SELECT
            name,
            start_date,
            end_date,
            location,
            fee,
            hours,
            website,
            googlemap_link,
            latitude,
            longitude,
            description
        FROM events
        WHERE event_type = 'tokyo_cheapo'
        ORDER BY start_date
    """)

    events = cursor.fetchall()

    if not events:
        print("\n⚠️  Aucun événement tokyo_cheapo trouvé dans la base de données")
        conn.close()
        return

    print(f"\nNombre total : {len(events)} événements\n")

    for i, event in enumerate(events, 1):
        name, start_date, end_date, location, fee, hours, website, gmap, lat, lon, description = event

        print(f"\n{'─' * 80}")
        print(f"{i}. {name}")
        print(f"{'─' * 80}")

        # Dates
        if start_date:
            date_str = f"📅 Dates: {start_date}"
            if end_date and end_date != start_date:
                date_str += f" → {end_date}"
            print(date_str)

        # Lieu
        if location:
            print(f"📍 Lieu: {location}")

        # Description
        if description:
            desc_short = description[:150] + "..." if len(description) > 150 else description
            print(f"📝 Description: {desc_short}")

        # Horaires
        if hours:
            print(f"🕐 Horaires: {hours}")

        # Prix
        if fee:
            print(f"💰 Prix: {fee}")

        # Coordonnées GPS
        if lat and lon:
            print(f"🗺️  GPS: {lat:.6f}, {lon:.6f}")

        # Website
        if website:
            print(f"🌐 Site: {website}")

        # Google Maps
        if gmap:
            print(f"📌 Maps: {gmap}")

    # Événements avec/sans GPS
    print("\n" + "=" * 80)
    print("📊 ANALYSE DES DONNÉES")
    print("=" * 80)

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN start_date IS NOT NULL THEN 1 ELSE 0 END) as with_dates,
            SUM(CASE WHEN location IS NOT NULL THEN 1 ELSE 0 END) as with_location,
            SUM(CASE WHEN hours IS NOT NULL THEN 1 ELSE 0 END) as with_hours,
            SUM(CASE WHEN fee IS NOT NULL THEN 1 ELSE 0 END) as with_fee,
            SUM(CASE WHEN website IS NOT NULL THEN 1 ELSE 0 END) as with_website,
            SUM(CASE WHEN googlemap_link IS NOT NULL THEN 1 ELSE 0 END) as with_gmap,
            SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END) as with_gps
        FROM events
        WHERE event_type = 'tokyo_cheapo'
    """)

    stats = cursor.fetchone()
    total, with_dates, with_location, with_hours, with_fee, with_website, with_gmap, with_gps = stats

    print(f"\nTaux de complétude des données :")
    print(f"  ✅ Dates        : {with_dates}/{total} ({100*with_dates/total:.1f}%)")
    print(f"  ✅ Lieu         : {with_location}/{total} ({100*with_location/total:.1f}%)")
    print(f"  ✅ Horaires     : {with_hours}/{total} ({100*with_hours/total:.1f}%)")
    print(f"  ✅ Prix         : {with_fee}/{total} ({100*with_fee/total:.1f}%)")
    print(f"  ✅ Site web     : {with_website}/{total} ({100*with_website/total:.1f}%)")
    print(f"  ✅ Google Maps  : {with_gmap}/{total} ({100*with_gmap/total:.1f}%)")
    print(f"  ✅ Coordonnées GPS : {with_gps}/{total} ({100*with_gps/total:.1f}%)")

    conn.close()
    print("\n" + "=" * 80)


if __name__ == "__main__":
    view_tokyo_cheapo_events()
