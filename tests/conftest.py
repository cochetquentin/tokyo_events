"""
Configuration pytest et fixtures pour les tests.

Ce module fournit des fixtures réutilisables pour les tests,
notamment pour les bases de données et les données de test.
"""

import pytest
from src.database import EventDatabase


@pytest.fixture
def in_memory_db():
    """
    Fixture pour base de données en mémoire (tests unitaires).

    Crée une base de données SQLite en mémoire (:memory:) pour chaque test.
    Très rapide et isolé - chaque test a sa propre BD vierge.
    Pas de cleanup nécessaire - la BD disparaît après le test.

    Returns:
        EventDatabase: Instance de base de données en mémoire
    """
    return EventDatabase(":memory:")


@pytest.fixture
def temp_db(tmp_path):
    """
    Fixture pour base de données temporaire sur disque (tests d'intégration).

    Crée un fichier SQLite temporaire dans le répertoire tmp_path.
    Pytest nettoie automatiquement tmp_path après le test.

    Args:
        tmp_path: Répertoire temporaire fourni par pytest

    Returns:
        EventDatabase: Instance de base de données fichier temporaire
    """
    db_path = tmp_path / "test_events.sqlite"
    return EventDatabase(str(db_path))


@pytest.fixture
def sample_festivals():
    """
    Fixture avec des données de test pour festivals.

    Returns:
        List[Dict]: Liste de festivals de test
    """
    return [
        {
            'name': 'Setsubun Festival',
            'start_date': '2025/02/03',
            'end_date': '2025/02/03',
            'location': 'Temple Senso-ji (Taito-ku)',
            'description': 'Festival traditionnel de printemps',
            'website': 'https://www.senso-ji.jp/',
            'googlemap_link': 'https://maps.google.com/?q=Senso-ji',
            'hours': 'de 10h à 17h',
            'fee': 'Entrée gratuite'
        },
        {
            'name': 'Plum Blossom Festival',
            'start_date': '2025/02/10',
            'end_date': '2025/03/10',
            'location': 'Parc Koishikawa Korakuen (Bunkyo-ku)',
            'description': 'Festival des fleurs de prunier',
            'website': 'https://www.tokyo-park.or.jp/park/format/index030.html',
            'googlemap_link': 'https://maps.google.com/?q=Koishikawa+Korakuen',
            'hours': 'de 9h à 17h',
            'fee': '300 yens'
        },
        {
            'name': 'Hina Matsuri',
            'start_date': '2025/03/03',
            'end_date': '2025/03/03',
            'location': 'Temple Hie Jinja (Chiyoda-ku)',
            'description': 'Fête des poupées',
            'website': None,
            'googlemap_link': None,
            'hours': None,
            'fee': 'Entrée gratuite'
        }
    ]


@pytest.fixture
def sample_expositions():
    """
    Fixture avec des données de test pour expositions.

    Returns:
        List[Dict]: Liste d'expositions de test
    """
    return [
        {
            'name': 'Exposition Art Moderne',
            'start_date': '2025/03/01',
            'end_date': '2025/04/30',
            'location': 'Musée National d\'Art Moderne (Chiyoda-ku)',
            'description': 'Collection permanente et expositions temporaires',
            'website': 'https://www.momat.go.jp/',
            'googlemap_link': 'https://maps.google.com/?q=MOMAT',
            'hours': 'de 10h à 17h (fermé lundi)',
            'fee': '500 yens'
        }
    ]


@pytest.fixture
def sample_hanabi():
    """
    Fixture avec des données de test pour hanabi (feux d'artifice).

    Inclut le champ 'dates' (liste) et les champs spécifiques hanabi.

    Returns:
        List[Dict]: Liste de hanabi de test
    """
    return [
        {
            'name': 'Tokyo Bay Fireworks',
            'event_id': 'ar0313e999999',
            'dates': ['2026/07/15', '2026/07/22', '2026/07/29'],
            'start_date': '2026/07/15',
            'end_date': '2026/07/29',
            'prefecture': '東京都',
            'city': '台東区',
            'venue': 'Sumida River',
            'description': 'Grand feu d\'artifice estival au-dessus de la rivière Sumida',
            'start_time': '19:00',
            'fireworks_count': '20,000発',
            'detail_url': 'https://hanabi.walkerplus.com/detail/ar0313e999999/',
            'googlemap_link': 'https://maps.google.com/?q=Sumida+River',
            'website': None,
            'hours': None,
            'fee': None
        },
        {
            'name': 'Edogawa Fireworks',
            'event_id': 'ar0313e888888',
            'dates': ['2026/08/05'],
            'start_date': '2026/08/05',
            'end_date': '2026/08/05',
            'prefecture': '東京都',
            'city': '江戸川区',
            'venue': 'Edogawa River',
            'description': 'Feu d\'artifice d\'Edogawa',
            'start_time': '19:30',
            'fireworks_count': '14,000発',
            'detail_url': 'https://hanabi.walkerplus.com/detail/ar0313e888888/',
            'googlemap_link': None,
            'website': None,
            'hours': None,
            'fee': None
        }
    ]


@pytest.fixture
def sample_marches():
    """
    Fixture avec des données de test pour marchés aux puces.

    Inclut le champ 'dates' (liste) pour les dates multiples.

    Returns:
        List[Dict]: Liste de marchés de test
    """
    return [
        {
            'name': 'Marché Arai Yakushi',
            'dates': ['2026/02/01', '2026/02/08', '2026/02/15', '2026/02/22'],
            'start_date': '2026/02/01',
            'end_date': '2026/02/22',
            'location': 'Temple Arai Yakushi (Nakano-ku)',
            'description': 'Marché aux puces mensuel',
            'website': 'https://ichiban-japan.com/marches-aux-puces-tokyo/',
            'googlemap_link': 'https://maps.google.com/?q=Arai+Yakushi',
            'hours': 'de 6h à 15h',
            'fee': 'Entrée gratuite'
        }
    ]
