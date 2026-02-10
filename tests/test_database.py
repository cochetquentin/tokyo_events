"""
Tests unitaires pour le module database.

Tests couvrant toutes les opérations CRUD et cas limites de la base de données.
Utilise des bases de données en mémoire (:memory:) pour rapidité et isolation.
"""

import pytest
import json
from src.database import EventDatabase


class TestEventDatabaseInit:
    """Tests d'initialisation de la base de données."""

    def test_init_creates_tables(self, in_memory_db):
        """Test que l'initialisation crée la table events."""
        with in_memory_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
            )
            result = cursor.fetchone()
            assert result is not None
            assert result['name'] == 'events'

    def test_init_creates_indexes(self, in_memory_db):
        """Test que l'initialisation crée les index."""
        with in_memory_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
            )
            indexes = [row['name'] for row in cursor.fetchall()]

            assert 'idx_event_type' in indexes
            assert 'idx_start_date' in indexes
            assert 'idx_end_date' in indexes
            assert 'idx_location' in indexes


class TestInsertEvents:
    """Tests d'insertion d'événements."""

    def test_insert_festivals(self, in_memory_db, sample_festivals):
        """Test insertion de festivals."""
        count = in_memory_db.insert_events(sample_festivals, 'festivals')
        assert count == len(sample_festivals)

        # Vérifier dans la DB
        events = in_memory_db.get_events(event_type='festivals')
        assert len(events) == len(sample_festivals)
        assert events[0]['name'] == sample_festivals[0]['name']

    def test_insert_expositions(self, in_memory_db, sample_expositions):
        """Test insertion d'expositions."""
        count = in_memory_db.insert_events(sample_expositions, 'expositions')
        assert count == len(sample_expositions)

        events = in_memory_db.get_events(event_type='expositions')
        assert len(events) == len(sample_expositions)

    def test_insert_hanabi_with_dates_array(self, in_memory_db, sample_hanabi):
        """Test insertion de hanabi avec champ dates (JSON array)."""
        count = in_memory_db.insert_events(sample_hanabi, 'hanabi')
        assert count == len(sample_hanabi)

        # Vérifier que les dates sont désérialisées correctement
        events = in_memory_db.get_events(event_type='hanabi')
        assert events[0]['dates'] == sample_hanabi[0]['dates']
        assert isinstance(events[0]['dates'], list)
        assert len(events[0]['dates']) == 3

    def test_insert_marches_with_dates_array(self, in_memory_db, sample_marches):
        """Test insertion de marchés avec dates multiples."""
        count = in_memory_db.insert_events(sample_marches, 'marches')
        assert count == len(sample_marches)

        events = in_memory_db.get_events(event_type='marches')
        assert events[0]['dates'] == sample_marches[0]['dates']
        assert isinstance(events[0]['dates'], list)

    def test_insert_empty_list(self, in_memory_db):
        """Test insertion d'une liste vide."""
        count = in_memory_db.insert_events([], 'festivals')
        assert count == 0

    def test_insert_invalid_event_type(self, in_memory_db, sample_festivals):
        """Test insertion avec type d'événement invalide."""
        with pytest.raises(ValueError, match="event_type doit être"):
            in_memory_db.insert_events(sample_festivals, 'invalid_type')

    def test_insert_hanabi_specific_fields(self, in_memory_db, sample_hanabi):
        """Test que les champs spécifiques hanabi sont bien stockés."""
        in_memory_db.insert_events(sample_hanabi, 'hanabi')
        events = in_memory_db.get_events(event_type='hanabi')

        # Vérifier champs spécifiques hanabi
        assert events[0]['prefecture'] == sample_hanabi[0]['prefecture']
        assert events[0]['city'] == sample_hanabi[0]['city']
        assert events[0]['venue'] == sample_hanabi[0]['venue']
        assert events[0]['event_id'] == sample_hanabi[0]['event_id']
        assert events[0]['start_time'] == sample_hanabi[0]['start_time']
        assert events[0]['fireworks_count'] == sample_hanabi[0]['fireworks_count']
        assert events[0]['detail_url'] == sample_hanabi[0]['detail_url']

        # Vérifier que location est NULL pour hanabi
        assert 'location' not in events[0]  # Supprimé car NULL

    def test_insert_festival_no_hanabi_fields(self, in_memory_db, sample_festivals):
        """Test que les festivals n'ont pas les champs spécifiques hanabi."""
        in_memory_db.insert_events(sample_festivals, 'festivals')
        events = in_memory_db.get_events(event_type='festivals')

        # Vérifier champs hanabi absents (ou NULL)
        assert 'prefecture' not in events[0]
        assert 'city' not in events[0]
        assert 'venue' not in events[0]
        assert 'event_id' not in events[0]


class TestInsertOrReplace:
    """Tests de la stratégie UPSERT (INSERT OR REPLACE)."""

    def test_insert_or_replace_prevents_duplicates(self, in_memory_db, sample_festivals):
        """Test que INSERT OR REPLACE empêche les doublons."""
        # Insérer deux fois
        count1 = in_memory_db.insert_events(sample_festivals, 'festivals')
        count2 = in_memory_db.insert_events(sample_festivals, 'festivals')

        assert count1 == len(sample_festivals)
        assert count2 == len(sample_festivals)

        # Vérifier qu'il n'y a toujours que le nombre original
        total = in_memory_db.count_events('festivals')
        assert total == len(sample_festivals)

    def test_insert_or_replace_updates_existing(self, in_memory_db, sample_festivals):
        """Test que INSERT OR REPLACE met à jour les événements existants."""
        # Insérer original
        in_memory_db.insert_events(sample_festivals, 'festivals')

        # Modifier et ré-insérer
        modified = [sample_festivals[0].copy()]
        modified[0]['description'] = 'Description mise à jour'
        modified[0]['fee'] = '500 yens'
        in_memory_db.insert_events(modified, 'festivals')

        # Vérifier mise à jour
        events = in_memory_db.get_events(event_type='festivals')
        updated_event = next(e for e in events if e['name'] == modified[0]['name'])
        assert updated_event['description'] == 'Description mise à jour'
        assert updated_event['fee'] == '500 yens'

    def test_unique_constraint_with_null_start_date(self, in_memory_db):
        """Test contrainte unique avec start_date NULL."""
        event1 = {
            'name': 'Event Without Date',
            'start_date': None,
            'end_date': None,
            'location': 'Test Location',
            'description': 'First version'
        }

        event2 = {
            'name': 'Event Without Date',
            'start_date': None,
            'end_date': None,
            'location': 'Test Location',
            'description': 'Second version'
        }

        in_memory_db.insert_events([event1], 'festivals')
        in_memory_db.insert_events([event2], 'festivals')

        # Devrait être traité comme doublon grâce à COALESCE
        total = in_memory_db.count_events('festivals')
        assert total == 1

        # Vérifier que c'est la dernière version
        events = in_memory_db.get_events(event_type='festivals')
        assert events[0]['description'] == 'Second version'


class TestGetEvents:
    """Tests de récupération d'événements avec filtres."""

    def test_get_all_events(self, in_memory_db, sample_festivals, sample_hanabi):
        """Test récupération de tous les événements."""
        in_memory_db.insert_events(sample_festivals, 'festivals')
        in_memory_db.insert_events(sample_hanabi, 'hanabi')

        all_events = in_memory_db.get_events()
        assert len(all_events) == len(sample_festivals) + len(sample_hanabi)

    def test_get_events_filter_by_type(self, in_memory_db, sample_festivals, sample_hanabi):
        """Test filtrage par type d'événement."""
        in_memory_db.insert_events(sample_festivals, 'festivals')
        in_memory_db.insert_events(sample_hanabi, 'hanabi')

        festivals = in_memory_db.get_events(event_type='festivals')
        hanabi = in_memory_db.get_events(event_type='hanabi')

        assert len(festivals) == len(sample_festivals)
        assert len(hanabi) == len(sample_hanabi)

        # Vérifier qu'on a bien le bon type
        assert all('prefecture' in h for h in hanabi)  # Champ hanabi
        assert all('location' in f for f in festivals)  # Champ festival

    def test_get_events_filter_by_date_range(self, in_memory_db, sample_festivals):
        """Test filtrage par plage de dates."""
        in_memory_db.insert_events(sample_festivals, 'festivals')

        # Filtrer février 2025
        events = in_memory_db.get_events(
            start_date_from='2025/02/01',
            start_date_to='2025/02/28'
        )

        assert len(events) >= 1
        for event in events:
            assert '2025/02' in event['start_date']

    def test_get_events_filter_by_date_from(self, in_memory_db, sample_festivals):
        """Test filtrage par date de début minimum."""
        in_memory_db.insert_events(sample_festivals, 'festivals')

        events = in_memory_db.get_events(start_date_from='2025/03/01')

        for event in events:
            assert event['start_date'] >= '2025/03/01'

    def test_get_events_filter_by_date_to(self, in_memory_db, sample_festivals):
        """Test filtrage par date de début maximum."""
        in_memory_db.insert_events(sample_festivals, 'festivals')

        events = in_memory_db.get_events(start_date_to='2025/02/28')

        for event in events:
            assert event['start_date'] <= '2025/02/28'

    def test_get_events_filter_by_location(self, in_memory_db, sample_festivals):
        """Test filtrage par lieu (LIKE)."""
        in_memory_db.insert_events(sample_festivals, 'festivals')

        # Rechercher Taito-ku
        events = in_memory_db.get_events(location='Taito')

        assert len(events) >= 1
        for event in events:
            assert 'Taito' in event['location']

    def test_get_events_combined_filters(self, in_memory_db, sample_festivals):
        """Test combinaison de plusieurs filtres."""
        in_memory_db.insert_events(sample_festivals, 'festivals')

        events = in_memory_db.get_events(
            event_type='festivals',
            start_date_from='2025/02/01',
            start_date_to='2025/02/28',
            location='Senso'
        )

        assert len(events) >= 1
        for event in events:
            assert event['start_date'] >= '2025/02/01'
            assert event['start_date'] <= '2025/02/28'
            assert 'Senso' in event['location']

    def test_get_events_empty_result(self, in_memory_db):
        """Test récupération sans résultat."""
        events = in_memory_db.get_events(event_type='festivals')
        assert events == []


class TestCountEvents:
    """Tests de comptage d'événements."""

    def test_count_all_events(self, in_memory_db, sample_festivals, sample_hanabi):
        """Test comptage de tous les événements."""
        in_memory_db.insert_events(sample_festivals, 'festivals')
        in_memory_db.insert_events(sample_hanabi, 'hanabi')

        total = in_memory_db.count_events()
        assert total == len(sample_festivals) + len(sample_hanabi)

    def test_count_events_by_type(self, in_memory_db, sample_festivals, sample_hanabi):
        """Test comptage par type."""
        in_memory_db.insert_events(sample_festivals, 'festivals')
        in_memory_db.insert_events(sample_hanabi, 'hanabi')

        assert in_memory_db.count_events('festivals') == len(sample_festivals)
        assert in_memory_db.count_events('hanabi') == len(sample_hanabi)
        assert in_memory_db.count_events('marches') == 0

    def test_count_empty_database(self, in_memory_db):
        """Test comptage sur base vide."""
        assert in_memory_db.count_events() == 0
        assert in_memory_db.count_events('festivals') == 0


class TestDeleteEvents:
    """Tests de suppression d'événements."""

    def test_delete_events_by_type(self, in_memory_db, sample_festivals, sample_hanabi):
        """Test suppression par type."""
        in_memory_db.insert_events(sample_festivals, 'festivals')
        in_memory_db.insert_events(sample_hanabi, 'hanabi')

        deleted = in_memory_db.delete_events_by_type('festivals')
        assert deleted == len(sample_festivals)

        # Vérifier que seuls les hanabi restent
        assert in_memory_db.count_events('festivals') == 0
        assert in_memory_db.count_events('hanabi') == len(sample_hanabi)

    def test_delete_nonexistent_type(self, in_memory_db, sample_festivals):
        """Test suppression d'un type qui n'existe pas."""
        in_memory_db.insert_events(sample_festivals, 'festivals')

        deleted = in_memory_db.delete_events_by_type('marches')
        assert deleted == 0

        # Festivals toujours présents
        assert in_memory_db.count_events('festivals') == len(sample_festivals)


class TestDatabaseConnection:
    """Tests de gestion des connexions."""

    def test_connection_context_manager(self, in_memory_db):
        """Test que le context manager fonctionne correctement."""
        with in_memory_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_row_factory_returns_dict_like(self, in_memory_db, sample_festivals):
        """Test que row_factory retourne des objets dict-like."""
        in_memory_db.insert_events(sample_festivals, 'festivals')

        with in_memory_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events LIMIT 1")
            row = cursor.fetchone()

            # Vérifier accès par clé (dict-like)
            assert 'name' in row.keys()
            assert row['event_type'] == 'festivals'


class TestJSONSerialization:
    """Tests de sérialisation/désérialisation JSON."""

    def test_dates_field_serialization(self, in_memory_db, sample_marches):
        """Test sérialisation du champ dates."""
        in_memory_db.insert_events(sample_marches, 'marches')

        # Vérifier que dates est stocké en JSON dans la DB
        with in_memory_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT dates FROM events WHERE event_type='marches' LIMIT 1")
            row = cursor.fetchone()
            dates_json = row['dates']

            # Vérifier que c'est bien du JSON
            assert isinstance(dates_json, str)
            dates_list = json.loads(dates_json)
            assert isinstance(dates_list, list)
            assert len(dates_list) == 4

    def test_dates_field_deserialization(self, in_memory_db, sample_hanabi):
        """Test désérialisation du champ dates."""
        in_memory_db.insert_events(sample_hanabi, 'hanabi')
        events = in_memory_db.get_events(event_type='hanabi')

        # Vérifier que dates est retourné comme liste
        assert isinstance(events[0]['dates'], list)
        assert events[0]['dates'] == sample_hanabi[0]['dates']

    def test_dates_field_null_handling(self, in_memory_db, sample_festivals):
        """Test gestion des dates NULL."""
        in_memory_db.insert_events(sample_festivals, 'festivals')
        events = in_memory_db.get_events(event_type='festivals')

        # Les festivals n'ont pas de champ dates
        assert 'dates' not in events[0]


class TestNullFieldHandling:
    """Tests de gestion des champs NULL."""

    def test_null_fields_removed_from_output(self, in_memory_db):
        """Test que les champs NULL sont supprimés de la sortie."""
        event = {
            'name': 'Test Event',
            'start_date': '2025/03/01',
            'end_date': '2025/03/01',
            'location': 'Test Location',
            'description': 'Test',
            'website': None,  # NULL
            'googlemap_link': None,  # NULL
            'hours': None,  # NULL
            'fee': None  # NULL
        }

        in_memory_db.insert_events([event], 'festivals')
        events = in_memory_db.get_events(event_type='festivals')

        # Vérifier que les champs NULL ne sont pas dans la sortie
        assert 'website' not in events[0]
        assert 'googlemap_link' not in events[0]
        assert 'hours' not in events[0]
        assert 'fee' not in events[0]

        # Mais les champs avec valeur sont présents
        assert 'name' in events[0]
        assert 'description' in events[0]

    def test_metadata_fields_removed_from_output(self, in_memory_db, sample_festivals):
        """Test que les champs metadata sont supprimés de la sortie."""
        in_memory_db.insert_events(sample_festivals, 'festivals')
        events = in_memory_db.get_events(event_type='festivals')

        # Vérifier que les champs metadata ne sont pas dans la sortie
        assert 'id' not in events[0]
        assert 'created_at' not in events[0]
        assert 'updated_at' not in events[0]
        assert 'event_type' not in events[0]
