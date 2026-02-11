# Tokyo Events Scraper 🎌

Scrapers automatiques pour récupérer les événements de Tokyo et région du Kanto avec stockage SQLite :
- **Festivals** depuis [ichiban-japan.com](https://ichiban-japan.com)
- **Expositions** depuis [ichiban-japan.com](https://ichiban-japan.com)
- **Marchés aux puces** depuis [ichiban-japan.com](https://ichiban-japan.com)
- **Feux d'artifice (Hanabi)** depuis [hanabi.walkerplus.com](https://hanabi.walkerplus.com)

**Stockage** : Base de données SQLite unifiée (`data/tokyo_events.sqlite`)

## 🚀 Installation

```bash
# Cloner le repository
git clone <repository-url>
cd TokyoEvent

# Installer les dépendances
uv pip install -r requirements.txt
```

## 📖 Démarrage Rapide

### Scraper des festivals

```bash
# Scraper un mois spécifique
uv run scrape.py festivals mars 2025

# Scraper plusieurs mois
uv run scrape.py festivals janvier 2025
uv run scrape.py festivals février 2025
```

### Scraper des expositions

```bash
uv run scrape.py expositions avril 2025
```

### Scraper des marchés aux puces

```bash
# Scrape tous les marchés (pas de paramètre de date)
uv run scrape.py marches
```

### Scraper des feux d'artifice (Hanabi)

```bash
# Scrape les hanabi des 6 prochains mois (par défaut)
uv run scrape.py hanabi

# Scrape les hanabi des 12 prochains mois
uv run scrape.py hanabi 12
```

## 📂 Structure du Projet

```
TokyoEvent/
├── scrape.py                          # CLI principal
├── requirements.txt                   # Dépendances
├── pytest.ini                         # Configuration tests
├── test_sqlite.py                     # Script de test SQLite
│
├── src/                               # Code source
│   ├── database.py                    # ⭐ Gestionnaire SQLite
│   ├── scraper_festivals_tokyo.py    # Scraper festivals
│   ├── scraper_expositions_tokyo.py  # Scraper expositions
│   ├── scraper_marches_tokyo.py      # Scraper marchés aux puces
│   ├── scraper_hanabi_kanto.py       # Scraper feux d'artifice
│   ├── date_utils.py                 # Utilitaires dates japonaises
│   ├── date_utils_fr.py              # Utilitaires dates françaises
│   ├── location_utils.py             # Mapping arrondissements
│   └── metadata_extractors.py        # Extraction heures/tarifs
│
├── tests/                             # Tests
│   ├── conftest.py                    # ⭐ Fixtures pytest
│   ├── test_database.py               # ⭐ Tests unitaires database (33 tests)
│   ├── compare.py                     # Comparaison ref vs auto
│   ├── compare_hanabi.py              # Tests hanabi
│   ├── test_date_utils_fr.py         # Tests unitaires dates
│   ├── test_location_utils.py        # Tests unitaires locations
│   └── test_metadata_extractors.py   # Tests unitaires métadonnées
│
├── data/                              # Données
│   ├── tokyo_events.sqlite            # ⭐ Base de données SQLite
│   └── reference/                     # Données de référence (JSON)
│
├── docs/                              # Documentation
│   ├── GUIDE_UTILISATION.md
│   ├── README_SCRAPER.md
│   ├── README_PROJET.md
│   ├── how_to_scrap_festival_event_website.md
│   └── how_to_scrap_hanabi_website.md
│
└── tools/                             # Scripts utilitaires
    └── update_references_districts.py
```

## 🎯 Fonctionnalités

### Festivals & Expositions

Extraction complète avec :
- ✅ **Nom et dates** (formats français complexes supportés)
- ✅ **Lieu avec arrondissement** (mapping automatique de 40+ quartiers)
- ✅ **Description** détaillée
- ✅ **Horaires** (extraction automatique)
- ✅ **Tarifs** (gratuit/montant en yens)
- ✅ **Site officiel** (hiérarchie de fallback intelligente)
- ✅ **Lien Google Maps**

### Marchés aux Puces

Support des **dates complexes** :
```
"1er, 6-8, 11, 13-15, 20-23 et 27-28 février 2026"
→ 17 dates individuelles extraites
```

### Feux d'Artifice (Hanabi)

Scraping région **Kanto** (7 préfectures) :
- ✅ **13 champs** extraits par événement
- ✅ **Dates multiples** (liste complète des occurrences)
- ✅ **Horaires de début**
- ✅ **Nombre de feux d'artifice**
- ✅ **Préfecture et ville**
- ✅ **Lieu détaillé**
- ✅ **Double parsing** (JSON-LD + HTML)

## 📊 Qualité & Validation

### Tests Automatisés

```bash
# Tests unitaires (104 tests, dont 33 pour la database)
uv run python -m pytest tests/ -v

# Tests de comparaison
uv run tests/compare.py festivals all
uv run tests/compare.py expositions all

# Test SQLite complet
uv run python test_sqlite.py
```

### Résultats Validés

**Festivals :** 97% parfaits (177/182 événements) - 0 manquants
- Janvier 2025 : 100%
- Février 2025 : 100%
- Mars 2025 : 100%
- Juillet 2025 : 94%
- Octobre 2025 : 100%
- Décembre 2025 : 85%

## 💻 Utilisation en Python

### Scraper et Sauvegarder dans SQLite

```python
from src.scraper_festivals_tokyo import TokyoFestivalScraper

scraper = TokyoFestivalScraper()
festivals = scraper.scrape_festivals(month=3, year=2025)

# Sauvegarder dans SQLite
scraper.save_to_database(festivals)
```

### Requêter la Base de Données

```python
from src.database import EventDatabase

db = EventDatabase()

# Compter les événements
print(f"Total: {db.count_events()}")
print(f"Festivals: {db.count_events('festivals')}")

# Récupérer des événements avec filtres
festivals_mars = db.get_events(
    event_type='festivals',
    start_date_from='2025/03/01',
    start_date_to='2025/03/31'
)

# Filtrer par lieu
events_taito = db.get_events(
    event_type='festivals',
    location='Taito'
)

# Afficher
for event in festivals_mars[:3]:
    print(f"{event['name']} - {event['start_date']}")
```

### Autres Scrapers

```python
from src.scraper_expositions_tokyo import TokyoExpositionScraper
from src.scraper_marches_tokyo import TokyoMarcheScraper
from src.scraper_hanabi_kanto import KantoHanabiScraper

# Expositions
scraper = TokyoExpositionScraper()
expositions = scraper.scrape_expositions(month=4, year=2025)
scraper.save_to_database(expositions)

# Marchés
scraper = TokyoMarcheScraper()
marches = scraper.scrape_marches()
scraper.save_to_database(marches)

# Hanabi
scraper = KantoHanabiScraper()
hanabi = scraper.scrape_hanabi(months_ahead=6)
scraper.save_to_database(hanabi)
```

## 🔧 Utilitaires

### Mapping Arrondissements

```python
from src.location_utils import normalize_district

location = "parc Ueno Koen"
# → "parc Ueno Koen (Taito-ku)"
```

### Parsing Dates Françaises Complexes

```python
from src.date_utils_fr import expand_complex_dates

dates = expand_complex_dates("1er, 6-8, 11 février 2026")
# → ["2026/02/01", "2026/02/06", "2026/02/07", "2026/02/08", "2026/02/11"]
```

### Extraction Métadonnées

```python
from src.metadata_extractors import extract_hours, extract_fee

text = "Ouvert de 10h à 18h. Entrée gratuite."
hours = extract_hours(text)  # → "de 10h à 18h"
fee = extract_fee(text)      # → "Entrée gratuite"
```

## 📖 Documentation

- [Guide d'utilisation](docs/GUIDE_UTILISATION.md) - Exemples détaillés
- [Documentation technique](docs/README_SCRAPER.md) - API et paramètres
- [Présentation du projet](docs/README_PROJET.md) - Vue d'ensemble
- [Analyse site festivals](docs/how_to_scrap_festival_event_website.md) - Patterns HTML
- [Analyse site hanabi](docs/how_to_scrap_hanabi_website.md) - Architecture scraper

## 🌟 Améliorations Récentes

### v3.0 - Migration SQLite (Février 2025)

- ✅ **Base de données SQLite** unifiée pour tous les événements
- ✅ **Table unique** avec support 4 types d'événements
- ✅ **Déduplication automatique** via clé composite unique
- ✅ **Stratégie UPSERT** (INSERT OR REPLACE) pour mises à jour
- ✅ **33 tests unitaires** pour la database
- ✅ **API de requêtage** avec filtres (type, dates, lieu)
- ✅ **Support champs JSON** pour dates multiples (hanabi/marches)
- ✅ **104 tests pytest** au total

### v2.0 - Couverture 97%+

- ✅ **Nouveaux modules** : dates françaises, locations, métadonnées
- ✅ **Scraper marchés** aux puces
- ✅ **Mapping automatique** 40+ quartiers → arrondissements
- ✅ **Support dates complexes** avec virgules et plages multiples
- ✅ **Extraction heures/tarifs** fonctionnelle
- ✅ **97% de couverture** sur festivals (vs 79% avant)

## 🎨 Format des Données

### Base de Données SQLite

**Table** : `events` (table unifiée)

**Schéma** :
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,  -- 'festivals', 'expositions', 'hanabi', 'marches'
    name TEXT NOT NULL,
    start_date TEXT,           -- Format: YYYY/MM/DD
    end_date TEXT,
    location TEXT,             -- Festivals, expositions, marchés
    prefecture TEXT,           -- Hanabi uniquement
    city TEXT,                 -- Hanabi uniquement
    venue TEXT,                -- Hanabi uniquement
    description TEXT,
    website TEXT,
    googlemap_link TEXT,
    hours TEXT,
    fee TEXT,
    event_id TEXT,             -- Hanabi uniquement
    start_time TEXT,           -- Hanabi uniquement
    fireworks_count TEXT,      -- Hanabi uniquement
    detail_url TEXT,           -- Hanabi uniquement
    dates TEXT,                -- JSON array pour marches/hanabi
    created_at TEXT,
    updated_at TEXT,

    -- Clé unique composite pour éviter doublons
    UNIQUE(event_type, name, start_date, location)
);
```

### Exemples de Données

**Festivals** :
```python
{
  "name": "Setsubun Matsuri",
  "start_date": "2025/02/02",
  "end_date": "2025/02/03",
  "location": "temple Senso-ji (Taito-ku)",
  "description": "Festival traditionnel...",
  "hours": "de 10h à 16h",
  "fee": "Entrée gratuite",
  "website": "https://...",
  "googlemap_link": "https://maps.google.com/..."
}
```

**Hanabi** :
```python
{
  "name": "Sumida River Fireworks",
  "event_id": "ar0313e123456",
  "dates": ["2025/07/26"],  # JSON array
  "start_date": "2025/07/26",
  "end_date": "2025/07/26",
  "prefecture": "東京都",
  "city": "台東区・墨田区",
  "venue": "Sumida River",
  "start_time": "19:00",
  "fireworks_count": "約20,000発",
  "description": "...",
  "detail_url": "https://...",
  "googlemap_link": "https://..."
}
```

## 🗄️ Base de Données SQLite

### Architecture

- **Table unifiée** `events` pour tous les types
- **Clé primaire** auto-incrémentée (`id`)
- **Clé unique composite** : `(event_type, name, start_date, location)`
- **Déduplication** automatique via `INSERT OR REPLACE`
- **Champs type-spécifiques** :
  - Hanabi : `prefecture`, `city`, `venue`, `event_id`, `start_time`, `fireworks_count`, `detail_url`
  - Autres : `location`, `hours`, `fee`
- **JSON** pour champs `dates` (liste de dates multiples)

### Requêtes Utiles

```python
from src.database import EventDatabase

db = EventDatabase()

# Stats globales
print(f"Total événements: {db.count_events()}")

# Par type
for event_type in ['festivals', 'expositions', 'hanabi', 'marches']:
    count = db.count_events(event_type)
    print(f"{event_type}: {count}")

# Événements de février
events = db.get_events(
    start_date_from='2025/02/01',
    start_date_to='2025/02/28'
)

# Événements gratuits
all_events = db.get_events()
free_events = [e for e in all_events if e.get('fee') and 'gratuit' in e['fee'].lower()]
```

## 🤝 Contribution

Les améliorations sont les bienvenues ! Zones à améliorer :

1. Support d'autres préfectures pour hanabi
2. Scraper pour autres types d'événements
3. Export vers autres formats (Excel, CSV)
4. Interface web pour visualisation
5. API REST pour accéder aux données

## 📝 Licence

Usage personnel et éducatif.

## 🙏 Crédits

Sources de données :
- [ichiban-japan.com](https://ichiban-japan.com) - Festivals, expositions, marchés
- [hanabi.walkerplus.com](https://hanabi.walkerplus.com) - Feux d'artifice

---

**Développé avec ❤️ pour découvrir les événements de Tokyo**
