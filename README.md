# Tokyo Events Scraper 🎌

Scrapers automatiques pour récupérer les événements de Tokyo et région du Kanto avec stockage SQLite :
- **Festivals** depuis [ichiban-japan.com](https://ichiban-japan.com)
- **Expositions** depuis [ichiban-japan.com](https://ichiban-japan.com)
- **Marchés aux puces** depuis [ichiban-japan.com](https://ichiban-japan.com)
- **Feux d'artifice (Hanabi)** depuis [hanabi.walkerplus.com](https://hanabi.walkerplus.com)
- **Tokyo Cheapo Events** depuis [tokyocheapo.com](https://tokyocheapo.com/events/) 🆕

**Stockage** : Base de données SQLite unifiée (`data/tokyo_events.sqlite`)

## 🚀 Installation

```bash
# Cloner le repository
git clone <repository-url>
cd TokyoEvent

# Installer les dépendances
uv pip install -r requirements.txt
```

## 🗺️ Application Web avec Carte Interactive

### Vue d'ensemble

L'application web permet de visualiser tous les événements de Tokyo sur une carte interactive avec filtres en temps réel.

**Fonctionnalités :**
- 🗺️ Carte interactive avec tous les événements géolocalisés (style CartoDB Voyager épuré)
- 🎨 Icônes personnalisées par type (🔥 hanabi, 🎵 festivals, 🎨 expositions, 🏪 marchés)
- 🔍 Filtrage intelligent par type d'événement et période de dates (utilise une logique de chevauchement pour inclure les événements en cours)
- 📍 Popups détaillés avec toutes les informations (nom, dates, lieu, horaires, tarifs, description)
- 📊 Statistiques dynamiques en temps réel (mises à jour selon les filtres appliqués)
- 📋 Liste des événements groupée par catégorie avec compteurs
- 🎯 Clic sur un événement pour zoomer et centrer la carte
- 🗂️ Clustering automatique des marqueurs
- 📅 Filtres par défaut sur la date du jour

### Démarrage Rapide

**Avec Makefile :**
```bash
make web  # Démarrer le serveur
```

**Sans Makefile :**
```bash
uv run scripts/start_web.py

# Ouvrir dans le navigateur
http://localhost:8000
```

**Note :** Les coordonnées GPS sont maintenant extraites **automatiquement lors du scraping**. Plus besoin de script de population séparé !

### API REST

L'application expose également une API REST :

```bash
# Récupérer tous les événements
GET http://localhost:8000/api/events/

# Filtrer par type
GET http://localhost:8000/api/events/?event_type=festivals

# Filtrer par dates
GET http://localhost:8000/api/events/?start_date_from=2025/03/01&start_date_to=2025/03/31

# Statistiques
GET http://localhost:8000/api/events/stats

# Générer carte HTML
GET http://localhost:8000/api/map/generate
```

**Documentation interactive :** [http://localhost:8000/docs](http://localhost:8000/docs)

### Technologies Utilisées

- **Backend :** FastAPI + Uvicorn
- **Carte :** Folium (wrapper Python pour Leaflet.js) avec tuiles CartoDB Voyager
- **Frontend :** Bootstrap 5 + Vanilla JavaScript
- **Icônes :** Font Awesome (icônes personnalisées par type d'événement)
- **Extraction GPS :** Automatique depuis les liens Google Maps (100% de succès)

## 📖 Scraping des Événements

### Mise à Jour Automatique (Recommandé) ⭐

La commande `make update-all` est la méthode **recommandée** pour maintenir votre base de données à jour. Elle met à jour tous les scrapers intelligemment en évitant les doublons :

```bash
# Mise à jour globale de tous les scrapers
make update-all

# Ce que fait cette commande :
# - Tokyo Cheapo    : 5 pages (~120 événements)
# - Festivals       : Mois actuel (skip si déjà scrapé)
# - Expositions     : Mois actuel (skip si déjà scrapé)
# - Marchés         : Tous (skip si déjà scrapé)
# - Hanabi          : 5 prochains mois
# - Nettoyage auto  : Supprime événements >30 jours

# Afficher les statistiques
make stats

# Mode dry-run (simulation)
uv run main.py update-all --dry-run
```

**Fonctionnalités :**
- ✅ Détection intelligente des nouveaux événements
- ✅ Évite les doublons (basé sur nom + date)
- ✅ Nettoyage automatique des événements passés
- ✅ Statistiques avant/après chaque mise à jour
- ✅ Skip automatique si déjà scrapé

### Scraping Manuel (par type)

```bash
# Voir toutes les commandes disponibles
make help

# Scraper tous les événements du mois en cours
make scrape  # Scrappe festivals, expositions, marches, et hanabi automatiquement

# Ou scraper individuellement par type
make scrape-festivals MONTH=mars YEAR=2025
make scrape-expositions MONTH=avril YEAR=2025
make scrape-marches
make scrape-hanabi MONTHS=12
make scrape-tokyo-cheapo  # 5 pages (~120 événements)

# Lancer les tests
make test
```

### Sans Makefile

#### Scraper des festivals

```bash
# Scraper un mois spécifique
uv run main.py festivals mars 2025

# Scraper plusieurs mois
uv run main.py festivals janvier 2025
uv run main.py festivals février 2025
```

#### Scraper des expositions

```bash
uv run main.py expositions avril 2025
```

#### Scraper des marchés aux puces

```bash
# Scrape tous les marchés (pas de paramètre de date)
uv run main.py marches
```

#### Scraper des feux d'artifice (Hanabi)

```bash
# Scrape les hanabi des 6 prochains mois (par défaut)
uv run main.py hanabi

# Scrape les hanabi des 12 prochains mois
uv run main.py hanabi 12
```

## 📂 Structure du Projet

```
TokyoEvent/
├── main.py                            # ⭐ CLI principal
├── Makefile                           # ⭐ Commandes simplifiées
├── requirements.txt                   # Dépendances
├── pytest.ini                         # Configuration tests
│
├── src/                               # Code source
│   ├── database.py                    # ⭐ Gestionnaire SQLite
│   ├── gps_extractor.py               # ⭐ Extraction GPS
│   ├── scraper_festivals_tokyo.py    # Scraper festivals
│   ├── scraper_expositions_tokyo.py  # Scraper expositions
│   ├── scraper_marches_tokyo.py      # Scraper marchés aux puces
│   ├── scraper_hanabi_kanto.py       # Scraper feux d'artifice
│   ├── scraper_tokyo_cheapo.py       # ⭐ Scraper Tokyo Cheapo (🆕)
│   ├── deduplicator.py               # ⭐ Déduplication et fusion d'événements
│   ├── date_utils.py                 # Utilitaires dates japonaises
│   ├── date_utils_fr.py              # Utilitaires dates françaises
│   ├── date_utils_en.py              # ⭐ Utilitaires dates anglaises (🆕)
│   ├── location_utils.py             # Mapping arrondissements
│   └── metadata_extractors.py        # Extraction heures/tarifs
│
├── web/                               # ⭐ Application web
│   ├── main.py                        # Point d'entrée FastAPI
│   ├── config.py                      # Configuration
│   ├── api/                           # Endpoints REST
│   │   ├── events.py                  # API événements
│   │   └── map.py                     # API carte
│   ├── services/                      # Logique métier
│   │   ├── event_service.py           # Service événements
│   │   └── map_service.py             # Service carte Folium
│   ├── models/                        # Modèles Pydantic
│   │   └── schemas.py
│   ├── templates/                     # Templates HTML
│   │   ├── base.html
│   │   └── index.html
│   └── static/                        # Fichiers statiques
│       ├── css/style.css
│       └── js/filters.js
│
├── scripts/                           # ⭐ Scripts utilitaires
│   ├── start_web.py                   # Démarrer serveur web
│   ├── get_current_month.py           # Obtenir mois actuel (français)
│   ├── get_current_year.py            # Obtenir année actuelle
│   ├── remove_duplicates.py           # Supprimer doublons
│   ├── populate_gps_coordinates.py    # Peupler GPS
│   ├── investigate_hanabi_map.py      # Investigation pages map.html hanabi
│   ├── update_hanabi_coords_from_investigation.py  # MAJ coords depuis investigation
│   └── migrate_add_gps_columns.py     # Migration DB
│
│
├── tests/                             # Tests
│   ├── conftest.py                    # ⭐ Fixtures pytest
│   ├── test_database.py               # ⭐ Tests unitaires database (33 tests)
│   ├── compare.py                     # ⭐ Comparaison unifiée (tous types)
│   ├── test_date_utils_fr.py         # Tests unitaires dates
│   ├── test_location_utils.py        # Tests unitaires locations
│   └── test_metadata_extractors.py   # Tests unitaires métadonnées
│
├── data/                              # Données
│   ├── tokyo_events.sqlite            # ⭐ Base de données SQLite
│   └── reference/                     # Données de référence (JSON)
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
- ✅ **Coordonnées GPS** via extraction map.html (100% de couverture)

### Tokyo Cheapo Events 🆕

Scraping événements depuis **tokyocheapo.com** :
- ✅ **Two-stage scraping** (liste + pages de détail)
- ✅ **5 pages** (~120 événements récupérés)
- ✅ **Parsing dates anglaises** (3 variantes supportées)
- ✅ **Catégorisation automatique** (festivals, expositions, marchés, tokyo_cheapo)
- ✅ **Rate limiting** (0.5s entre requêtes)
- ✅ **Extraction GPS** automatique depuis Google Maps (75% de succès)
- ✅ **Détection intelligente** des nouveaux événements
- ✅ **Champs complets** : nom, dates, lieu, description, horaires, tarifs, website, GPS

## 📊 Qualité & Validation

### Tests Automatisés

```bash
# Tests unitaires (104 tests, dont 33 pour la database)
uv run python -m pytest tests/ -v

# Tests de comparaison (tous types: festivals, expositions, hanabi, marches)
uv run tests/compare.py festivals all
uv run tests/compare.py expositions all
uv run tests/compare.py hanabi
uv run tests/compare.py all  # Compare tous les types
```

### Résultats Validés

**Festivals :** 97% parfaits (177/182 événements) - 0 manquants
- Janvier 2025 : 100%
- Février 2025 : 100%
- Mars 2025 : 100%
- Juillet 2025 : 94%
- Octobre 2025 : 100%
- Décembre 2025 : 85%

**Expositions :** 85-88% parfaits
- Décembre 2025 : 88% (23/26)
- Avril 2025 : 85% (17/20)
- Janvier 2025 : 66% (8/12)

**GPS :**
- Festivals/Expositions/Marchés : 94% de succès (Google Maps links)
- Hanabi : 100% de succès (extraction map.html)

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
from src.scraper_tokyo_cheapo import TokyoCheapoScraper

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

# Tokyo Cheapo (🆕)
scraper = TokyoCheapoScraper()
events = scraper.scrape_events(max_pages=5)  # 5 pages (~120 événements)
scraper.save_to_database(events)
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

## 📊 Couverture GPS

L'extraction GPS est **automatique** lors du scraping avec les taux de succès suivants :

| Type | Couverture | Événements |
|------|-----------|-----------|
| **Expositions** | 93.5% ✅ | 29/31 |
| **Marchés** | 90.7% ✅ | 49/54 |
| **Festivals** | 83.7% ⚠️ | 36/43 |
| **Tokyo Cheapo** | 74.6% ⚠️ | 44/59 |
| **Hanabi** | 0.0% ❌ | 0/1 |
| **TOTAL** | **84.0%** | **158/188** |

### Méthodes d'extraction GPS :
1. **JSON Apple Maps** (Tokyo Cheapo) - Extraction depuis `<div component-name="apple-maps">`
2. **Liens Google Maps** (Festivals/Expositions/Marchés) - Pattern `@lat,lng` + résolution liens courts
3. **Map.html** (Hanabi) - Extraction depuis iframes Google Maps

### Événements sans GPS (30) :
- **Événements online/itinérants** : Pas de lieu physique fixe
- **Lieux imprécis** : Seulement un quartier mentionné (ex: "Shibuya")
- **Données manquantes** : Venue non renseigné dans la source

## 🌟 Améliorations Récentes

### v4.5 - Déduplication intelligente + Refonte UI + Catégories (Avril 2026)

- ✅ **Système de déduplication avancé** (`src/deduplicator.py`) : fusion intelligente avec matching fuzzy (rapidfuzz), préfixes communs, chevauchement de dates
- ✅ **Mapping de traduction japonais → anglais** pour normalisation des noms lors de la comparaison
- ✅ **Détection de doublons par préfixe** : "Festival X" matche avec "Festival X 2026"
- ✅ **Refonte des catégories** : système unifié avec groupes et couleurs cohérentes
- ✅ **Refonte UI complète** : thème Tokyo Night + Alpine.js, layout minimaliste épuré
- ✅ **Affichage liste par catégorie** corrigé avec compteurs
- ✅ **Fenêtre de scraping hanabi étendue à 5 mois** (vs 3 auparavant) pour couvrir les événements fin juillet/août

### v4.3 - Scraper Tokyo Cheapo + Système de Mise à Jour Globale (Février 2025)

- ✅ **Nouveau scraper Tokyo Cheapo** (tokyocheapo.com/events/)
- ✅ **Two-stage scraping** : liste + pages de détail pour données complètes
- ✅ **Parsing dates anglaises** avec 3 variantes (single, multi, multi-year)
- ✅ **Catégorisation automatique** : festivals/expositions/marchés/tokyo_cheapo
- ✅ **Extraction GPS 75%** depuis Google Maps links
- ✅ **Système de mise à jour globale** `make update-all`
- ✅ **Détection intelligente** des nouveaux événements (évite doublons)
- ✅ **Skip automatique** si mois déjà scrapé (festivals/expositions/marchés)
- ✅ **Nettoyage automatique** des événements >30 jours
- ✅ **Statistiques détaillées** avant/après chaque mise à jour
- ✅ **Support event_type='tokyo_cheapo'** dans la database

### v4.2 - Améliorations Interface Carte Interactive (Février 2025)

- ✅ **Style de carte amélioré** : CartoDB Voyager pour un rendu épuré et coloré
- ✅ **Icônes personnalisées** : Font Awesome avec icônes spécifiques (🔥 fire, 🎵 music, 🎨 palette, 🏪 store)
- ✅ **Légende déplacée** dans le panneau latéral pour meilleure lisibilité
- ✅ **Statistiques dynamiques** : compteurs mis à jour en temps réel selon les filtres
- ✅ **Liste d'événements** groupée par catégorie avec compteurs
- ✅ **Zoom sur événement** : clic sur un événement dans la liste pour centrer la carte
- ✅ **Filtres par défaut** : date du jour pré-sélectionnée au chargement
- ✅ **Interface épurée** : suppression des statistiques redondantes

### v4.1 - Extraction GPS Hanabi via map.html (Février 2025)

- ✅ **Investigation pages map.html** pour événements hanabi
- ✅ **Extraction GPS à 100%** pour hanabi via Google Maps iframes
- ✅ **Script d'investigation automatique** avec rapport détaillé
- ✅ **Couverture GPS complète** sur tous les feux d'artifice

### v4.0 - Application Web avec Carte Interactive (Février 2025)

- ✅ **Application web FastAPI** avec carte interactive Folium
- ✅ **Extraction GPS automatique** lors du scraping (94% de succès)
- ✅ **Filtrage intelligent par dates** avec logique de chevauchement de périodes
- ✅ **Clustering de marqueurs** pour meilleure visualisation
- ✅ **API REST complète** avec documentation interactive
- ✅ **Commande `make scrape`** pour scraper tous les événements du mois en cours
- ✅ **Amélioration du scraper expositions** (85-88% de précision)
- ✅ **Support dates complexes** sur plusieurs années

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
    event_type TEXT NOT NULL,  -- 'festivals', 'expositions', 'hanabi', 'marches', 'tokyo_cheapo'
    name TEXT NOT NULL,
    start_date TEXT,           -- Format: YYYY/MM/DD
    end_date TEXT,
    location TEXT,             -- Festivals, expositions, marchés, tokyo_cheapo
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
    detail_url TEXT,           -- Hanabi + Tokyo Cheapo
    dates TEXT,                -- JSON array pour marches/hanabi
    latitude REAL,             -- Coordonnées GPS
    longitude REAL,            -- Coordonnées GPS
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
2. Scraper pour autres types d'événements (concerts, théâtre, etc.)
3. Export vers autres formats (Excel, CSV, iCalendar)
4. Amélioration du taux de précision des expositions (actuellement 85-88%)
5. Filtres supplémentaires (tarif, arrondissement, mot-clé)

## 📝 Licence

Usage personnel et éducatif.

## 🙏 Crédits

Sources de données :
- [ichiban-japan.com](https://ichiban-japan.com) - Festivals, expositions, marchés
- [hanabi.walkerplus.com](https://hanabi.walkerplus.com) - Feux d'artifice
- [tokyocheapo.com](https://tokyocheapo.com/events/) - Événements Tokyo Cheapo 🆕

---

**Développé avec ❤️ pour découvrir les événements de Tokyo**
