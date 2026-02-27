"""
Script de migration pour ajouter 'tokyo_cheapo' au CHECK constraint
"""

import sys
import io

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import sqlite3
import shutil
from datetime import datetime

DB_PATH = "data/tokyo_events.sqlite"
BACKUP_PATH = f"data/tokyo_events.sqlite.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def migrate_database():
    """Migrer la base de données pour accepter tokyo_cheapo"""

    # Faire une backup
    print(f"📦 Creating backup: {BACKUP_PATH}")
    shutil.copy2(DB_PATH, BACKUP_PATH)

    # Connexion à la base de données
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Créer une nouvelle table avec le nouveau constraint
        print("🔧 Creating new table with updated constraint...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Identification
                event_type TEXT NOT NULL CHECK(event_type IN ('festivals', 'expositions', 'hanabi', 'marches', 'tokyo_cheapo')),
                name TEXT NOT NULL,

                -- Dates (format YYYY/MM/DD)
                start_date TEXT,
                end_date TEXT,
                dates TEXT,  -- JSON array pour marches/hanabi avec dates multiples

                -- Localisation commune (festivals/expositions/marches)
                location TEXT,

                -- Localisation hanabi (spécifique)
                prefecture TEXT,
                city TEXT,
                venue TEXT,

                -- Détails de l'événement
                description TEXT,
                website TEXT,
                googlemap_link TEXT,
                hours TEXT,
                fee TEXT,

                -- Coordonnées GPS (extraites automatiquement depuis googlemap_link)
                latitude REAL,
                longitude REAL,

                -- Métadonnées hanabi (spécifiques)
                event_id TEXT,  -- ID unique de l'événement (hanabi)
                start_time TEXT,  -- Heure de début (hanabi)
                fireworks_count TEXT,  -- Nombre de feux d'artifice (hanabi)
                detail_url TEXT,  -- URL de la page de détail (hanabi)

                -- Horodatage
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- Contrainte d'unicité
                UNIQUE(event_type, name, start_date, location)
            )
        """)

        # Copier toutes les données de l'ancienne table vers la nouvelle
        print("📋 Copying existing data...")
        cursor.execute("""
            INSERT INTO events_new
            SELECT * FROM events
        """)

        # Supprimer l'ancienne table
        print("🗑️  Dropping old table...")
        cursor.execute("DROP TABLE events")

        # Renommer la nouvelle table
        print("✨ Renaming new table...")
        cursor.execute("ALTER TABLE events_new RENAME TO events")

        # Créer les index
        print("🔍 Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_start_date ON events(start_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_end_date ON events(end_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_location ON events(location)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_coordinates ON events(latitude, longitude)")

        # Commit
        conn.commit()

        print("✅ Migration completed successfully!")
        print(f"   Backup saved to: {BACKUP_PATH}")

        # Afficher quelques stats
        cursor.execute("SELECT COUNT(*) FROM events")
        total = cursor.fetchone()[0]
        print(f"   Total events in database: {total}")

        cursor.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type")
        for event_type, count in cursor.fetchall():
            print(f"     - {event_type}: {count}")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        print(f"⚠️  Restoring from backup: {BACKUP_PATH}")
        shutil.copy2(BACKUP_PATH, DB_PATH)
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    print("=== Tokyo Events Database Migration ===\n")
    migrate_database()
