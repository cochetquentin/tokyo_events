# Guide d'Utilisation - Scraper de Festivals Tokyo

## Installation

```bash
# Installer les dépendances avec uv
uv pip install -r requirements.txt
```

## Utilisation Rapide

### 1. Script le plus simple - Quick Start

```bash
uv run quick_start.py
```

Ce script scrape les festivals de décembre 2025 et génère automatiquement les fichiers JSON et CSV.

### 2. Script principal - Avec exemples

```bash
uv run scraper_festivals_tokyo.py
```

Le script principal inclut plusieurs exemples :
- Scraping de décembre 2025
- Scraping de plusieurs mois (janvier-mars 2026)

### 3. Utilisation personnalisée

```python
from scraper_festivals_tokyo import TokyoFestivalScraper

# Créer le scraper
scraper = TokyoFestivalScraper()

# Scraper un mois spécifique
festivals = scraper.scrape_festivals(month=6, year=2025)  # Juin 2025

# Sauvegarder les résultats
scraper.save_to_json(festivals, filename="mes_festivals.json")
scraper.save_to_csv(festivals, filename="mes_festivals.csv")
```

## Exemples de Code

### Scraper plusieurs mois

```python
from scraper_festivals_tokyo import TokyoFestivalScraper

scraper = TokyoFestivalScraper()

# Scraper toute l'année 2025
for month in range(1, 13):
    festivals = scraper.scrape_festivals(month=month, year=2025)
    if festivals:
        scraper.save_to_json(festivals)
        scraper.save_to_csv(festivals)
```

### Scraper et filtrer

```python
from scraper_festivals_tokyo import TokyoFestivalScraper

scraper = TokyoFestivalScraper()
festivals = scraper.scrape_festivals(month=12, year=2025)

# Filtrer les festivals gratuits
festivals_gratuits = [
    f for f in festivals
    if f.get('entry_fee') and 'Free' in f['entry_fee']
]

print(f"{len(festivals_gratuits)} festivals gratuits trouvés")
```

### Analyser les données

```python
from scraper_festivals_tokyo import TokyoFestivalScraper
import json

scraper = TokyoFestivalScraper()
festivals = scraper.scrape_festivals(month=5, year=2025)

# Compter les festivals par emplacement
emplacements = {}
for festival in festivals:
    lieu = festival.get('location', 'Non spécifié')
    emplacements[lieu] = emplacements.get(lieu, 0) + 1

print("Festivals par emplacement:")
for lieu, count in sorted(emplacements.items(), key=lambda x: x[1], reverse=True):
    print(f"  {lieu}: {count}")
```

## Format des Données

### JSON
```json
{
  "festivals": [
    {
      "name": "Nom du festival",
      "month": "decembre",
      "year": 2025,
      "dates": "1-25 décembre 2025",
      "location": "Tokyo Skytree",
      "hours": "11am-10pm",
      "entry_fee": "Free",
      "description": "Description du festival...",
      "features": ["Feature 1", "Feature 2"]
    }
  ]
}
```

### CSV
```
name,month,year,dates,location,hours,entry_fee,description,features
Nom du festival,decembre,2025,1-25 décembre 2025,Tokyo Skytree,11am-10pm,Free,Description...,"Feature 1; Feature 2"
```

## Référence des Mois

Le scraper utilise les noms de mois en français :

| Numéro | Nom français |
|--------|--------------|
| 1      | janvier      |
| 2      | fevrier      |
| 3      | mars         |
| 4      | avril        |
| 5      | mai          |
| 6      | juin         |
| 7      | juillet      |
| 8      | aout         |
| 9      | septembre    |
| 10     | octobre      |
| 11     | novembre     |
| 12     | decembre     |

## Gestion des Erreurs

Le scraper gère automatiquement :
- Les pages qui n'existent pas (404) - retourne une liste vide
- Les problèmes de connexion - affiche un message d'erreur
- Les structures HTML différentes - extrait ce qui est possible

## Fichiers Générés

Chaque exécution génère deux fichiers :
- `festivals_tokyo_<mois>_<année>.json` - Format JSON structuré
- `festivals_tokyo_<mois>_<année>.csv` - Format CSV pour Excel/Sheets

## Astuces

1. **Tester plusieurs mois** : Utilisez `test_autre_mois.py` pour voir quels mois sont disponibles
2. **Encodage** : Les fichiers sont en UTF-8 pour supporter les caractères japonais
3. **Rate limiting** : Le scraper attend automatiquement entre les requêtes
4. **Structure des pages** : Certaines pages peuvent avoir des structures différentes, le scraper s'adapte automatiquement

## Dépannage

### Problème d'encodage sous Windows
Le script gère automatiquement l'encodage UTF-8 sous Windows.

### Page non trouvée (404)
Certains mois/années ne sont pas encore publiés sur le site. Essayez un autre mois.

### Aucun festival trouvé
La page existe mais le parsing n'a pas fonctionné. Vérifiez manuellement la page web.

## Contribution

Pour améliorer le parsing :
1. Regardez la structure HTML de la page source
2. Modifiez la méthode `_parse_page()` dans [scraper_festivals_tokyo.py](scraper_festivals_tokyo.py)
3. Testez avec `uv run test_autre_mois.py`
