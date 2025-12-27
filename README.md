# Tokyo Festivals Scraper 🎌

Scraper automatique pour récupérer les festivals de Tokyo depuis [ichiban-japan.com](https://ichiban-japan.com) pour n'importe quel mois et année.

## Installation

```bash
pip install -r requirements.txt
```

## Démarrage Rapide

```bash
uv run examples/quick_start.py
```

## Utilisation

```python
from scraper_festivals_tokyo import TokyoFestivalScraper

scraper = TokyoFestivalScraper()

# Scraper n'importe quel mois/année
festivals = scraper.scrape_festivals(month=12, year=2025)

# Sauvegarder en JSON et CSV
scraper.save_to_json(festivals, filename="data/mes_festivals.json")
scraper.save_to_csv(festivals, filename="data/mes_festivals.csv")
```

## Structure du Projet

```
TokyoEvent/
├── scraper_festivals_tokyo.py    # Script principal
├── requirements.txt               # Dépendances
│
├── examples/                      # Scripts d'exemple
│   ├── quick_start.py            # Démarrage rapide
│   ├── exemple_utilisation.py    # Exemples avancés
│   └── test_autre_mois.py        # Test multi-mois
│
├── docs/                          # Documentation
│   ├── GUIDE_UTILISATION.md      # Guide complet
│   ├── README_SCRAPER.md         # Doc technique
│   └── README_PROJET.md          # Présentation détaillée
│
└── data/                          # Données générées
    ├── festivals_*.json
    └── festivals_*.csv
```

## Exemples

### Scraper un mois spécifique

```python
scraper = TokyoFestivalScraper()
festivals = scraper.scrape_festivals(month=6, year=2025)  # Juin 2025
```

### Scraper plusieurs mois

```python
for month in range(1, 13):
    festivals = scraper.scrape_festivals(month=month, year=2025)
    scraper.save_to_json(festivals, filename=f"data/festivals_{month}_2025.json")
```

## Documentation

- [Guide d'utilisation](docs/GUIDE_UTILISATION.md) - Exemples détaillés
- [Documentation technique](docs/README_SCRAPER.md) - API et paramètres
- [Présentation du projet](docs/README_PROJET.md) - Vue d'ensemble

## Données Extraites

Chaque festival contient :
- Nom et dates
- Lieu et horaires
- Prix d'entrée
- Description
- Caractéristiques

## Licence

Usage personnel et éducatif.
