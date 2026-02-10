"""
Module de gestion de la base de données SQLite pour les événements Tokyo.

Ce module fournit une interface pour stocker et récupérer les événements
(festivals, expositions, hanabi, marches) dans une base SQLite.
"""

import sqlite3
import json
import os
from typing import List, Dict, Optional
from contextlib import contextmanager
from datetime import datetime


class EventDatabase:
    """
    Gestionnaire de base de données pour les événements Tokyo.

    Utilise SQLite avec une table unifiée pour tous les types d'événements.
    Gère les insertions avec stratégie UPSERT (INSERT OR REPLACE) pour
    éviter les doublons basés sur une clé composite unique.
    """

    def __init__(self, db_path: str = "data/tokyo_events.sqlite"):
        """
        Initialise la connexion à la base de données.

        Args:
            db_path: Chemin vers le fichier SQLite (ou ":memory:" pour BD en mémoire)
        """
        self.db_path = db_path
        self._memory_conn = None  # Connexion persistante pour :memory:
        self._ensure_directory()
        self._init_db()

    def _ensure_directory(self):
        """Crée le dossier data/ s'il n'existe pas."""
        if self.db_path != ":memory:":
            directory = os.path.dirname(self.db_path)
            if directory:
                os.makedirs(directory, exist_ok=True)

    def _init_db(self):
        """Crée les tables et index s'ils n'existent pas."""
        with self.get_connection() as conn:
            # Activer le mode WAL pour meilleures performances concurrentes
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")

            # Créer la table events
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    -- Identification
                    event_type TEXT NOT NULL CHECK(event_type IN ('festivals', 'expositions', 'hanabi', 'marches')),
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

                    -- Informations communes
                    description TEXT,
                    website TEXT,
                    googlemap_link TEXT,
                    hours TEXT,
                    fee TEXT,

                    -- Champs spécifiques hanabi
                    event_id TEXT,
                    start_time TEXT,
                    fireworks_count TEXT,
                    detail_url TEXT,

                    -- Métadonnées
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Créer un index unique avec expressions pour gérer les NULL
            # Utilise COALESCE pour traiter NULL comme chaîne vide
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_event
                ON events(event_type, name, COALESCE(start_date, ''), COALESCE(location, ''))
            """)

            # Créer les autres index pour performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_start_date ON events(start_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_end_date ON events(end_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_location ON events(location)")

            conn.commit()

    @contextmanager
    def get_connection(self):
        """
        Context manager pour les connexions à la base de données.

        Pour :memory:, utilise une connexion persistante qui reste ouverte.
        Pour les fichiers, crée une nouvelle connexion à chaque appel.
        Configure row_factory pour retourner des Row objects (dict-like).

        Yields:
            sqlite3.Connection: Connexion à la base de données
        """
        # Pour :memory:, utiliser connexion persistante
        if self.db_path == ":memory:":
            if self._memory_conn is None:
                self._memory_conn = sqlite3.connect(self.db_path)
                self._memory_conn.row_factory = sqlite3.Row
            yield self._memory_conn
        else:
            # Pour fichiers, créer nouvelle connexion
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def insert_events(self, events: List[Dict], event_type: str) -> int:
        """
        Insère ou met à jour des événements dans la base de données.

        Utilise INSERT OR REPLACE pour gérer les doublons automatiquement.
        Les doublons sont détectés via la clé unique composite:
        (event_type, name, start_date, location)

        Args:
            events: Liste de dictionnaires d'événements
            event_type: Type d'événement ('festivals', 'expositions', 'hanabi', 'marches')

        Returns:
            Nombre d'événements insérés/mis à jour

        Raises:
            ValueError: Si event_type n'est pas valide
        """
        valid_types = ['festivals', 'expositions', 'hanabi', 'marches']
        if event_type not in valid_types:
            raise ValueError(f"event_type doit être l'un de {valid_types}, reçu: {event_type}")

        if not events:
            return 0

        inserted = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()

            for event in events:
                # Convertir dict en format DB
                row = self._dict_to_db_row(event, event_type)

                # Construire la requête INSERT OR REPLACE
                columns = ', '.join(row.keys())
                placeholders = ', '.join(['?' for _ in row])

                query = f"""
                    INSERT OR REPLACE INTO events ({columns})
                    VALUES ({placeholders})
                """

                cursor.execute(query, list(row.values()))
                inserted += 1

            conn.commit()

        return inserted

    def get_events(self,
                   event_type: Optional[str] = None,
                   start_date_from: Optional[str] = None,
                   start_date_to: Optional[str] = None,
                   location: Optional[str] = None) -> List[Dict]:
        """
        Récupère des événements avec filtres optionnels.

        Args:
            event_type: Filtrer par type (None = tous les types)
            start_date_from: Filtrer événements débutant après cette date (YYYY/MM/DD)
            start_date_to: Filtrer événements débutant avant cette date (YYYY/MM/DD)
            location: Filtrer par lieu (recherche LIKE, insensible à la casse)

        Returns:
            Liste de dictionnaires d'événements
        """
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        if start_date_from:
            query += " AND start_date >= ?"
            params.append(start_date_from)

        if start_date_to:
            query += " AND start_date <= ?"
            params.append(start_date_to)

        if location:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")

        query += " ORDER BY start_date, name"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [self._db_row_to_dict(row) for row in rows]

    def count_events(self, event_type: Optional[str] = None) -> int:
        """
        Compte le nombre d'événements.

        Args:
            event_type: Type d'événement à compter (None = tous)

        Returns:
            Nombre d'événements
        """
        query = "SELECT COUNT(*) FROM events"
        params = []

        if event_type:
            query += " WHERE event_type = ?"
            params.append(event_type)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()[0]

    def delete_events_by_type(self, event_type: str) -> int:
        """
        Supprime tous les événements d'un type donné.

        Args:
            event_type: Type d'événement à supprimer

        Returns:
            Nombre d'événements supprimés
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE event_type = ?", (event_type,))
            deleted = cursor.rowcount
            conn.commit()

        return deleted

    def _dict_to_db_row(self, event: Dict, event_type: str) -> Dict:
        """
        Convertit un dictionnaire d'événement en format de ligne DB.

        Gère:
        - Sérialisation JSON du champ 'dates'
        - Mapping NULL pour champs type-spécifiques
        - Timestamp updated_at

        Args:
            event: Dictionnaire d'événement
            event_type: Type d'événement

        Returns:
            Dictionnaire formaté pour insertion DB
        """
        # Champs communs
        row = {
            'event_type': event_type,
            'name': event['name'],
            'start_date': event.get('start_date'),
            'end_date': event.get('end_date'),
            'description': event.get('description'),
            'website': event.get('website'),
            'googlemap_link': event.get('googlemap_link'),
            'hours': event.get('hours'),
            'fee': event.get('fee'),
            'updated_at': datetime.now().isoformat()
        }

        # Gestion du champ dates (JSON array)
        if 'dates' in event and event['dates']:
            row['dates'] = json.dumps(event['dates'], ensure_ascii=False)
        else:
            row['dates'] = None

        # Champs type-spécifiques
        if event_type == 'hanabi':
            # Hanabi utilise prefecture/city/venue au lieu de location
            row['location'] = None
            row['prefecture'] = event.get('prefecture')
            row['city'] = event.get('city')
            row['venue'] = event.get('venue')
            row['event_id'] = event.get('event_id')
            row['start_time'] = event.get('start_time')
            row['fireworks_count'] = event.get('fireworks_count')
            row['detail_url'] = event.get('detail_url')
        else:
            # Festivals, expositions, marches utilisent location commune
            row['location'] = event.get('location')
            row['prefecture'] = None
            row['city'] = None
            row['venue'] = None
            row['event_id'] = None
            row['start_time'] = None
            row['fireworks_count'] = None
            row['detail_url'] = None

        return row

    def _db_row_to_dict(self, row: sqlite3.Row) -> Dict:
        """
        Convertit une ligne DB en dictionnaire d'événement.

        Gère:
        - Désérialisation JSON du champ 'dates'
        - Suppression des champs NULL pour sortie plus propre
        - Suppression des champs metadata (id, created_at, updated_at, event_type)

        Args:
            row: Ligne de résultat SQLite

        Returns:
            Dictionnaire d'événement
        """
        # Convertir Row en dict
        event = dict(row)

        # Désérialiser le champ dates s'il existe
        if event.get('dates'):
            try:
                event['dates'] = json.loads(event['dates'])
            except json.JSONDecodeError:
                event['dates'] = None

        # Supprimer les champs metadata pour compatibilité avec format original
        for field in ['id', 'created_at', 'updated_at', 'event_type']:
            event.pop(field, None)

        # Supprimer les champs NULL pour sortie plus propre
        event = {k: v for k, v in event.items() if v is not None}

        return event
