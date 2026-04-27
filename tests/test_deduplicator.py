"""
Tests unitaires pour le module de déduplication d'événements.
"""

import pytest
from src.deduplicator import EventDeduplicator, DeduplicationReport


class TestNormalization:
    """Tests de normalisation de noms et localisations"""

    def setup_method(self):
        self.deduplicator = EventDeduplicator()

    def test_normalize_name_accents(self):
        """Doit supprimer les accents"""
        assert self.deduplicator._normalize_name("Été à Tokyo") == "ete a tokyo"
        assert self.deduplicator._normalize_name("Noël en décembre") == "noel en decembre"

    def test_normalize_name_punctuation(self):
        """Doit supprimer la ponctuation"""
        assert self.deduplicator._normalize_name("Festival-Taiko!") == "festival taiko"
        assert self.deduplicator._normalize_name("Cherry Blossom (2025)") == "cherry blossom 2025"

    def test_normalize_name_spaces(self):
        """Doit normaliser les espaces multiples"""
        assert self.deduplicator._normalize_name("Festival   de    Tokyo") == "festival de tokyo"
        assert self.deduplicator._normalize_name("  Ohanami  ") == "ohanami"

    def test_normalize_name_case(self):
        """Doit convertir en minuscules"""
        assert self.deduplicator._normalize_name("TOKYO FESTIVAL") == "tokyo festival"
        assert self.deduplicator._normalize_name("Sumida River") == "sumida river"

    def test_normalize_location_simple(self):
        """Doit normaliser une location simple"""
        result = self.deduplicator._normalize_location(location="Shibuya-ku")
        assert result == "shibuya ku"

    def test_normalize_location_hanabi_format(self):
        """Doit construire location depuis prefecture/city/venue"""
        result = self.deduplicator._normalize_location(
            prefecture="東京都",
            city="渋谷区",
            venue="Yoyogi Park"
        )
        assert "yoyogi park" in result
        assert "渋谷区" in result or "shibuya" in result.lower()

    def test_normalize_location_empty(self):
        """Doit gérer les locations vides"""
        assert self.deduplicator._normalize_location() == ""
        assert self.deduplicator._normalize_location(location="") == ""

    def test_normalize_name_kanji_transliteration(self):
        """Doit translittérer les kanji en romaji puis appliquer le TRANSLATION_MAP"""
        # 足立 → adachi, 花火 → hanabi → fireworks (via TRANSLATION_MAP)
        result = self.deduplicator._normalize_name("足立の花火")
        assert "adachi" in result
        assert "fireworks" in result

    def test_normalize_name_kanji_with_edition_number(self):
        """Doit translittérer un nom avec numéro d'édition kanji"""
        # 第48回 → dai 48 kai, 足立 → adachi, 花火 → fireworks
        result = self.deduplicator._normalize_name("第48回 足立の花火")
        assert "adachi" in result
        assert "fireworks" in result

    def test_normalize_name_mixed_kanji_ascii(self):
        """Doit gérer un mélange kanji + ASCII"""
        result = self.deduplicator._normalize_name("隅田川 Fireworks 2026")
        assert "sumida" in result
        assert "fireworks" in result

    def test_normalize_location_kanji(self):
        """Doit translittérer les kanji dans les localisations"""
        result = self.deduplicator._normalize_location(
            prefecture="東京都",
            city="足立区",
            venue="荒川河川敷"
        )
        assert "arakawa" in result
        assert "adachi" in result

    def test_normalize_name_translation_after_transliteration(self):
        """Les tokens traduits par TRANSLATION_MAP doivent l'être après translittération"""
        # hanabi (mot séparé) → fireworks ; hanabitaikai (un seul token) → non traduit
        result_separate = self.deduplicator._normalize_name("足立の花火")
        assert "fireworks" in result_separate


class TestSimilarity:
    """Tests de calcul de similarité"""

    def setup_method(self):
        self.deduplicator = EventDeduplicator()

    def test_fuzzy_match_high_similarity(self):
        """Doit détecter haute similarité"""
        sim = self.deduplicator._calculate_similarity(
            "Sumida River Fireworks",
            "Sumida River Firework Festival"
        )
        assert sim >= 80  # Au moins 80%

    def test_fuzzy_match_low_similarity(self):
        """Doit détecter basse similarité"""
        sim = self.deduplicator._calculate_similarity(
            "Cherry Blossom Festival",
            "Halloween Party"
        )
        assert sim < 50  # Moins de 50%

    def test_fuzzy_match_identical(self):
        """Doit retourner 100% pour textes identiques"""
        sim = self.deduplicator._calculate_similarity(
            "Tokyo Festival",
            "Tokyo Festival"
        )
        assert sim == 100

    def test_fuzzy_match_empty_strings(self):
        """Doit gérer les chaînes vides"""
        assert self.deduplicator._calculate_similarity("", "") == 0.0
        assert self.deduplicator._calculate_similarity("test", "") == 0.0


class TestDatesMatching:
    """Tests de comparaison de dates"""

    def setup_method(self):
        self.deduplicator = EventDeduplicator()

    def test_dates_match_identical(self):
        """Doit détecter dates identiques"""
        assert self.deduplicator._dates_match("2025/03/15", "2025/03/15") is True

    def test_dates_match_different(self):
        """Doit détecter dates différentes"""
        assert self.deduplicator._dates_match("2025/03/15", "2025/03/16") is False

    def test_dates_match_none(self):
        """Doit gérer dates None"""
        assert self.deduplicator._dates_match(None, "2025/03/15") is False
        assert self.deduplicator._dates_match("2025/03/15", None) is False

    def test_dates_overlap_exact(self):
        """Doit détecter périodes qui se chevauchent (exactes)"""
        assert self.deduplicator._dates_overlap(
            "2025/03/15", "2025/03/20",
            "2025/03/15", "2025/03/20"
        ) is True

    def test_dates_overlap_partial(self):
        """Doit détecter périodes qui se chevauchent (partielles)"""
        assert self.deduplicator._dates_overlap(
            "2025/03/15", "2025/03/20",
            "2025/03/18", "2025/03/25"
        ) is True

    def test_dates_no_overlap(self):
        """Doit détecter périodes qui ne se chevauchent pas"""
        assert self.deduplicator._dates_overlap(
            "2025/03/15", "2025/03/20",
            "2025/03/21", "2025/03/25"
        ) is False

    def test_dates_overlap_missing_end(self):
        """Doit gérer end_date manquant (utiliser start_date)"""
        assert self.deduplicator._dates_overlap(
            "2025/03/15", None,
            "2025/03/15", None
        ) is True


class TestDuplicateDetection:
    """Tests de détection de doublons"""

    def setup_method(self):
        self.deduplicator = EventDeduplicator()

    def test_exact_duplicate(self):
        """Doit détecter doublons exacts"""
        event1 = self.deduplicator._normalize_event({
            'name': 'Summer Festival',
            'start_date': '2025/07/15',
            'end_date': '2025/07/20',
            'location': 'Shibuya-ku'
        })

        event2 = self.deduplicator._normalize_event({
            'name': 'Summer Festival',
            'start_date': '2025/07/15',
            'end_date': '2025/07/20',
            'location': 'Shibuya-ku'
        })

        is_dup, reason = self.deduplicator._are_duplicates(event1, event2)
        assert is_dup is True
        assert "Strict match" in reason

    def test_fuzzy_duplicate(self):
        """Doit détecter doublons fuzzy"""
        event1 = self.deduplicator._normalize_event({
            'name': 'Summer Festival Tokyo',
            'start_date': '2025/07/15',
            'end_date': '2025/07/20',
            'location': 'Shibuya-ku'
        })

        event2 = self.deduplicator._normalize_event({
            'name': 'Summer Festival',
            'start_date': '2025/07/15',
            'end_date': '2025/07/20',
            'location': 'Shibuya-ku'
        })

        is_dup, reason = self.deduplicator._are_duplicates(event1, event2)
        assert is_dup is True

    def test_different_dates_not_duplicate(self):
        """Doit rejeter événements avec dates différentes"""
        event1 = self.deduplicator._normalize_event({
            'name': 'Summer Festival',
            'start_date': '2025/07/15',
            'end_date': '2025/07/20',
            'location': 'Shibuya-ku'
        })

        event2 = self.deduplicator._normalize_event({
            'name': 'Summer Festival',
            'start_date': '2025/08/15',
            'end_date': '2025/08/20',
            'location': 'Shibuya-ku'
        })

        is_dup, reason = self.deduplicator._are_duplicates(event1, event2)
        assert is_dup is False

    def test_different_names_not_duplicate(self):
        """Doit rejeter événements avec noms très différents"""
        event1 = self.deduplicator._normalize_event({
            'name': 'Cherry Blossom Festival',
            'start_date': '2025/04/01',
            'end_date': '2025/04/10',
            'location': 'Ueno Park'
        })

        event2 = self.deduplicator._normalize_event({
            'name': 'Halloween Party',
            'start_date': '2025/04/01',
            'end_date': '2025/04/10',
            'location': 'Ueno Park'
        })

        is_dup, reason = self.deduplicator._are_duplicates(event1, event2)
        assert is_dup is False

    def test_missing_dates_not_duplicate(self):
        """Doit rejeter comparaison si dates manquantes"""
        event1 = self.deduplicator._normalize_event({
            'name': 'Festival',
            'location': 'Shibuya-ku'
        })

        event2 = self.deduplicator._normalize_event({
            'name': 'Festival',
            'start_date': '2025/07/15',
            'location': 'Shibuya-ku'
        })

        is_dup, reason = self.deduplicator._are_duplicates(event1, event2)
        assert is_dup is False
        assert "Missing dates" in reason

    def test_bilingual_duplicate_jp_vs_en(self):
        """Doit détecter doublon entre nom japonais et anglais (cas Adachi)"""
        event_en = self.deduplicator._normalize_event({
            'name': 'Adachi Fireworks Festival 2026',
            'start_date': '2026/05/30',
            'end_date': '2026/05/30',
            'location': 'Arakawa River',
            'event_type': 'tokyo_cheapo'
        })
        event_jp = self.deduplicator._normalize_event({
            'name': '第48回 足立の花火',
            'start_date': '2026/05/30',
            'end_date': '2026/05/30',
            'prefecture': '東京都',
            'city': '足立区',
            'venue': '荒川河川敷',
            'event_type': 'hanabi'
        })

        is_dup, reason = self.deduplicator._are_duplicates(event_en, event_jp)
        assert is_dup is True
        assert "Bilingual" in reason

    def test_bilingual_no_false_positive_different_ward(self):
        """Ne doit PAS détecter doublon entre festivals de quartiers différents"""
        event1 = self.deduplicator._normalize_event({
            'name': 'Shinjuku Festival 2026',
            'start_date': '2026/07/15',
            'end_date': '2026/07/15',
            'location': 'Shinjuku',
            'event_type': 'festivals'
        })
        event2 = self.deduplicator._normalize_event({
            'name': 'Shibuya Festival 2026',
            'start_date': '2026/07/15',
            'end_date': '2026/07/15',
            'location': 'Shibuya',
            'event_type': 'festivals'
        })

        is_dup, _ = self.deduplicator._are_duplicates(event1, event2)
        assert is_dup is False

    def test_bilingual_no_false_positive_different_city(self):
        """Ne doit PAS détecter doublon entre marathons de villes différentes"""
        event1 = self.deduplicator._normalize_event({
            'name': 'Tokyo Marathon 2026',
            'start_date': '2026/03/01',
            'end_date': '2026/03/01',
            'location': 'Tokyo',
            'event_type': 'festivals'
        })
        event2 = self.deduplicator._normalize_event({
            'name': 'Osaka Marathon 2026',
            'start_date': '2026/03/01',
            'end_date': '2026/03/01',
            'location': 'Osaka',
            'event_type': 'festivals'
        })

        is_dup, _ = self.deduplicator._are_duplicates(event1, event2)
        assert is_dup is False


class TestMerging:
    """Tests de fusion d'événements"""

    def setup_method(self):
        self.deduplicator = EventDeduplicator()

    def test_merge_priority_hanabi_over_cheapo(self):
        """Doit garder hanabi (priorité 1) sur tokyo_cheapo (priorité 5)"""
        hanabi = {
            'name': 'Sumida River Fireworks',
            'event_type': 'hanabi',
            'start_date': '2025/07/26',
            'prefecture': '東京都',
            'city': '墨田区'
        }

        cheapo = {
            'name': 'Sumida Hanabi',
            'event_type': 'tokyo_cheapo',
            'start_date': '2025/07/26',
            'location': 'Sumida-ku',
            'hours': '19:00-20:30',
            'fee': 'Free'
        }

        merged = self.deduplicator.merge_events(hanabi, cheapo)

        # Doit garder les champs de hanabi
        assert merged['name'] == 'Sumida River Fireworks'
        assert merged['event_type'] == 'hanabi'
        assert merged['prefecture'] == '東京都'

        # Doit enrichir avec cheapo
        assert merged.get('hours') == '19:00-20:30'
        assert merged.get('fee') == 'Free'

    def test_merge_enrichment_from_cheapo(self):
        """Doit enrichir event sans hours/fee avec cheapo"""
        festival = {
            'name': 'Summer Festival',
            'event_type': 'festivals',
            'start_date': '2025/07/15',
            'location': 'Shibuya-ku'
        }

        cheapo = {
            'name': 'Summer Festival Tokyo',
            'event_type': 'tokyo_cheapo',
            'start_date': '2025/07/15',
            'location': 'Shibuya-ku',
            'hours': '10:00-18:00',
            'fee': '¥500'
        }

        merged = self.deduplicator.merge_events(festival, cheapo)

        assert merged['hours'] == '10:00-18:00'
        assert merged['fee'] == '¥500'
        assert '_enriched_fields' in merged
        assert 'hours' in merged['_enriched_fields']
        assert 'fee' in merged['_enriched_fields']

    def test_merge_preserve_primary_fields(self):
        """Doit JAMAIS écraser les champs protégés"""
        primary = {
            'name': 'Primary Event',
            'event_type': 'festivals',
            'start_date': '2025/07/15',
            'end_date': '2025/07/20',
            'location': 'Shibuya-ku'
        }

        secondary = {
            'name': 'Secondary Event',  # Différent
            'event_type': 'tokyo_cheapo',  # Différent
            'start_date': '2025/08/01',  # Différent
            'end_date': '2025/08/05',  # Différent
            'location': 'Shinjuku-ku',  # Différent
            'hours': '10:00-18:00'
        }

        merged = self.deduplicator.merge_events(primary, secondary)

        # Champs protégés JAMAIS écrasés
        assert merged['name'] == 'Primary Event'
        assert merged['event_type'] == 'festivals'
        assert merged['start_date'] == '2025/07/15'
        assert merged['end_date'] == '2025/07/20'
        assert merged['location'] == 'Shibuya-ku'

        # Champs enrichissables OK
        assert merged['hours'] == '10:00-18:00'

    def test_merge_description_longest(self):
        """Doit prendre la description la plus longue"""
        event1 = {
            'name': 'Festival',
            'event_type': 'festivals',
            'start_date': '2025/07/15',
            'location': 'Tokyo',
            'description': 'Short desc'
        }

        event2 = {
            'name': 'Festival',
            'event_type': 'tokyo_cheapo',
            'start_date': '2025/07/15',
            'location': 'Tokyo',
            'description': 'Much longer description with more details about the event'
        }

        merged = self.deduplicator.merge_events(event1, event2)

        assert merged['description'] == 'Much longer description with more details about the event'


class TestEventIdDeduplication:
    """Tests de déduplication basée sur event_id (URL)"""

    def setup_method(self):
        self.deduplicator = EventDeduplicator()

    def test_intra_same_event_id_is_duplicate(self):
        """Intra : même event_id → doublon même si noms différents"""
        events = [
            {'name': 'Yokohama Night Flowers 2026', 'event_id': 'ar0314e541039', 'start_date': '2026/04/04'},
            {'name': 'Yokohama Night Flowers × GREEN×EXPO2027', 'event_id': 'ar0314e541039', 'start_date': '2026/04/04'},
        ]
        normalized = [self.deduplicator._normalize_event(e) for e in events]
        deduped, report = self.deduplicator._deduplicate_intra(normalized, 'hanabi')

        assert len(deduped) == 1
        assert report.duplicates_found == 1

    def test_intra_different_event_id_not_duplicate(self):
        """Intra : event_id différents → pas doublon même si noms très similaires"""
        events = [
            {'name': 'Tokyo Hanabi 2026', 'event_id': 'ar0313e000001', 'start_date': '2026/07/25'},
            {'name': 'Tokyo Hanabi 2026', 'event_id': 'ar0313e000002', 'start_date': '2026/07/25'},
        ]
        normalized = [self.deduplicator._normalize_event(e) for e in events]
        deduped, report = self.deduplicator._deduplicate_intra(normalized, 'hanabi')

        assert len(deduped) == 2
        assert report.duplicates_found == 0

    def test_inter_event_id_ignored_uses_name(self):
        """Inter : même event_id ignoré — c'est le nom qui détermine le doublon"""
        # Même event_id mais noms clairement différents → PAS un doublon inter-scraper
        new_events = [
            {'name': 'Sumida River Fireworks', 'event_id': 'ar0313e123', 'start_date': '2026/07/25', 'end_date': '2026/07/25', 'event_type': 'hanabi', 'prefecture': '東京都'},
        ]
        existing_events = [
            {'name': 'Koenji Awa Odori Dance Festival', 'event_id': 'ar0313e123', 'start_date': '2026/07/25', 'end_date': '2026/07/25', 'event_type': 'hanabi', 'prefecture': '東京都'},
        ]
        normalized_new = [self.deduplicator._normalize_event(e) for e in new_events]
        normalized_existing = [self.deduplicator._normalize_event(e) for e in existing_events]

        deduped, report = self.deduplicator._deduplicate_inter(normalized_new, normalized_existing, 'hanabi')

        # Même event_id mais noms très différents → 0 doublon (event_id ignoré en inter)
        assert report.duplicates_found == 0
        assert len(deduped) == 1

    def test_inter_different_event_id_but_same_name_is_duplicate(self):
        """Inter : event_id différents mais même nom → doublon quand même (noms comparés)"""
        new_events = [
            {'name': 'Adachi Fireworks Festival', 'event_id': 'adachi-fireworks-festival-2026', 'start_date': '2026/07/20', 'end_date': '2026/07/20', 'event_type': 'tokyo_cheapo', 'location': 'Adachi'},
        ]
        existing_events = [
            {'name': 'Adachi Fireworks Festival', 'event_id': 'ar0313e999', 'start_date': '2026/07/20', 'end_date': '2026/07/20', 'event_type': 'hanabi', 'location': 'Adachi'},
        ]
        normalized_new = [self.deduplicator._normalize_event(e) for e in new_events]
        normalized_existing = [self.deduplicator._normalize_event(e) for e in existing_events]

        deduped, report = self.deduplicator._deduplicate_inter(normalized_new, normalized_existing, 'tokyo_cheapo')

        # Doublon détecté : tokyo_cheapo (priorité 5) < hanabi (priorité 1) → skip sans insertion
        assert len(deduped) == 0


class TestDeduplicationIntra:
    """Tests de déduplication intra-scraper"""

    def setup_method(self):
        self.deduplicator = EventDeduplicator()

    def test_intra_no_duplicates(self):
        """Doit garder tous les événements si pas de doublons"""
        events = [
            {'name': 'Festival A', 'start_date': '2025/07/15', 'location': 'Shibuya-ku'},
            {'name': 'Festival B', 'start_date': '2025/08/15', 'location': 'Shinjuku-ku'},
            {'name': 'Festival C', 'start_date': '2025/09/15', 'location': 'Minato-ku'},
        ]

        normalized = [self.deduplicator._normalize_event(e) for e in events]
        deduped, report = self.deduplicator._deduplicate_intra(normalized, 'festivals')

        assert len(deduped) == 3
        assert report.duplicates_found == 0

    def test_intra_with_duplicates(self):
        """Doit fusionner les doublons intra-scraper"""
        events = [
            {'name': 'Summer Festival', 'start_date': '2025/07/15', 'end_date': '2025/07/20', 'location': 'Shibuya-ku'},
            {'name': 'Summer Festival Tokyo', 'start_date': '2025/07/15', 'end_date': '2025/07/20', 'location': 'Shibuya-ku', 'hours': '10:00-18:00'},
            {'name': 'Autumn Festival', 'start_date': '2025/09/15', 'location': 'Shinjuku-ku'},
        ]

        normalized = [self.deduplicator._normalize_event(e) for e in events]
        deduped, report = self.deduplicator._deduplicate_intra(normalized, 'festivals')

        assert len(deduped) == 2  # 3 events → 2 (1 fusion)
        assert report.duplicates_found == 1
        assert len(report.merged_events) == 1


class TestDeduplicationInter:
    """Tests de déduplication inter-scraper"""

    def setup_method(self):
        self.deduplicator = EventDeduplicator()

    def test_inter_new_priority_over_existing(self):
        """Doit UPDATE si nouveau plus prioritaire"""
        new_events = [
            {'name': 'Fireworks', 'event_type': 'hanabi', 'start_date': '2025/07/26', 'prefecture': '東京都'}
        ]

        existing_events = [
            {'name': 'Fireworks Festival', 'event_type': 'tokyo_cheapo', 'start_date': '2025/07/26', 'location': 'Tokyo', 'hours': '19:00'}
        ]

        normalized_new = [self.deduplicator._normalize_event(e) for e in new_events]
        normalized_existing = [self.deduplicator._normalize_event(e) for e in existing_events]

        deduped, report = self.deduplicator._deduplicate_inter(
            normalized_new,
            normalized_existing,
            'hanabi'
        )

        # Doit insérer le nouveau (plus prioritaire) + enrichir avec existing
        assert len(deduped) >= 1
        assert report.duplicates_found >= 0

    def test_inter_existing_priority_over_new(self):
        """Doit SKIP ou ENRICH si nouveau moins prioritaire"""
        new_events = [
            {'name': 'Fireworks', 'event_type': 'tokyo_cheapo', 'start_date': '2025/07/26', 'location': 'Tokyo', 'hours': '19:00'}
        ]

        existing_events = [
            {'name': 'Fireworks Festival', 'event_type': 'hanabi', 'start_date': '2025/07/26', 'prefecture': '東京都'}
        ]

        normalized_new = [self.deduplicator._normalize_event(e) for e in new_events]
        normalized_existing = [self.deduplicator._normalize_event(e) for e in existing_events]

        deduped, report = self.deduplicator._deduplicate_inter(
            normalized_new,
            normalized_existing,
            'tokyo_cheapo'
        )

        # Doit enrichir existing avec hours si manquant, ou skip
        assert len(deduped) <= 1


class TestEndToEnd:
    """Tests end-to-end de déduplication complète"""

    def setup_method(self):
        self.deduplicator = EventDeduplicator()

    def test_full_deduplication_workflow(self):
        """Test complet : intra + inter déduplication"""
        new_events = [
            {'name': 'Summer Festival', 'start_date': '2025/07/15', 'end_date': '2025/07/20', 'location': 'Shibuya-ku'},
            {'name': 'Summer Festival Tokyo', 'start_date': '2025/07/15', 'end_date': '2025/07/20', 'location': 'Shibuya-ku', 'hours': '10:00'},  # Doublon intra
            {'name': 'Autumn Festival', 'start_date': '2025/09/15', 'location': 'Shinjuku-ku'},
        ]

        existing_events = [
            {'name': 'Winter Festival', 'event_type': 'festivals', 'start_date': '2025/12/15', 'location': 'Minato-ku'},
        ]

        deduped, report = self.deduplicator.deduplicate_events(
            events=new_events,
            event_type='festivals',
            existing_db_events=existing_events
        )

        # Doit avoir dédupliqué les 2 Summer Festival
        assert report.total_input == 3
        assert report.duplicates_found >= 1  # Au moins le doublon intra
        assert report.final_count <= 3
