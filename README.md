# Tokyo Events Scraper 🎌

Scrapers automatiques pour récupérer les événements de Tokyo et région du Kanto :
- **Festivals** depuis [ichiban-japan.com](https://ichiban-japan.com)
- **Expositions** depuis [ichiban-japan.com](https://ichiban-japan.com)
- **Marchés aux puces** depuis [ichiban-japan.com](https://ichiban-japan.com)
- **Feux d'artifice (Hanabi)** depuis [hanabi.walkerplus.com](https://hanabi.walkerplus.com)

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
│
├── src/                               # Code source
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
│   ├── compare.py                     # Comparaison ref vs auto
│   ├── compare_hanabi.py              # Tests hanabi
│   ├── test_date_utils_fr.py         # Tests unitaires dates
│   ├── test_location_utils.py        # Tests unitaires locations
│   └── test_metadata_extractors.py   # Tests unitaires métadonnées
│
├── data/                              # Données générées
│   ├── festivals_*.json
│   ├── expositions_*.json
│   ├── marches_tokyo.json
│   ├── hanabi_kanto_*.json
│   └── reference/                     # Données de référence
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
# Tests unitaires (71 tests)
uv run python -m pytest tests/ -v

# Tests de comparaison
uv run tests/compare.py festivals all
uv run tests/compare.py expositions all
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

### Festivals

```python
from src.scraper_festivals_tokyo import TokyoFestivalScraper

scraper = TokyoFestivalScraper()
festivals = scraper.scrape_festivals(month=3, year=2025)

# Sauvegarder
scraper.save_to_json(festivals, "data/festivals_mars_2025.json")
```

### Expositions

```python
from src.scraper_expositions_tokyo import TokyoExpositionScraper

scraper = TokyoExpositionScraper()
expositions = scraper.scrape_expositions(month=4, year=2025)
scraper.save_to_json(expositions)
```

### Marchés aux Puces

```python
from src.scraper_marches_tokyo import TokyoMarcheScraper

scraper = TokyoMarcheScraper()
marches = scraper.scrape_marches()
scraper.save_to_json(marches)
```

### Feux d'Artifice (Hanabi)

```python
from src.scraper_hanabi_kanto import KantoHanabiScraper

scraper = KantoHanabiScraper()
hanabi = scraper.scrape_hanabi(months_ahead=6)
scraper.save_to_json(hanabi, "data/hanabi_kanto_2025.json")
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

### v2.0 - Couverture 97%+

- ✅ **Nouveaux modules** : dates françaises, locations, métadonnées
- ✅ **Scraper marchés** aux puces
- ✅ **Mapping automatique** 40+ quartiers → arrondissements
- ✅ **Support dates complexes** avec virgules et plages multiples
- ✅ **Extraction heures/tarifs** fonctionnelle
- ✅ **71 tests pytest** pour garantir la qualité
- ✅ **97% de couverture** sur festivals (vs 79% avant)

## 🎨 Format des Données

### Festivals & Expositions

```json
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

### Feux d'Artifice (Hanabi)

```json
{
  "name": "Sumida River Fireworks",
  "event_id": "ar0313e123456",
  "dates": ["2025/07/26"],
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

## 🤝 Contribution

Les améliorations sont les bienvenues ! Zones à améliorer :

1. Support d'autres préfectures pour hanabi
2. Scraper pour autres types d'événements
3. Export vers autres formats (Excel, Base de données)
4. Interface web pour visualisation

## 📝 Licence

Usage personnel et éducatif.

## 🙏 Crédits

Sources de données :
- [ichiban-japan.com](https://ichiban-japan.com) - Festivals, expositions, marchés
- [hanabi.walkerplus.com](https://hanabi.walkerplus.com) - Feux d'artifice

---

**Développé avec ❤️ pour découvrir les événements de Tokyo**
