# Scraper de Festivals Tokyo 🎌

Scraper automatique pour récupérer les informations des festivals de Tokyo depuis [ichiban-japan.com](https://ichiban-japan.com).

## Installation

1. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

### Utilisation basique

```python
from scraper_festivals_tokyo import TokyoFestivalScraper

# Créer une instance du scraper
scraper = TokyoFestivalScraper()

# Scraper les festivals de décembre 2025
festivals = scraper.scrape_festivals(month=12, year=2025)

# Sauvegarder en JSON
scraper.save_to_json(festivals)

# Sauvegarder en CSV
scraper.save_to_csv(festivals)
```

### Scraper plusieurs mois

```python
scraper = TokyoFestivalScraper()

# Scraper de janvier à juin 2026
for month in range(1, 7):
    festivals = scraper.scrape_festivals(month=month, year=2026)
    scraper.save_to_json(festivals)
    scraper.save_to_csv(festivals)
```

### Scraper toute une année

```python
scraper = TokyoFestivalScraper()
year = 2025
tous_festivals = []

for month in range(1, 13):
    festivals = scraper.scrape_festivals(month=month, year=year)
    tous_festivals.extend(festivals)

# Sauvegarder tous les festivals
scraper.save_to_json(tous_festivals, filename=f"festivals_{year}_complet.json")
```

## Exécution rapide

Lancez simplement le script principal :
```bash
python scraper_festivals_tokyo.py
```

Ou utilisez les exemples :
```bash
python exemple_utilisation.py
```

## Paramètres

### `scrape_festivals(month, year)`
- `month` : Numéro du mois (1-12)
- `year` : Année (ex: 2025)

### `save_to_json(festivals, filename=None)`
- `festivals` : Liste des festivals à sauvegarder
- `filename` : Nom du fichier (optionnel, auto-généré si non spécifié)

### `save_to_csv(festivals, filename=None)`
- `festivals` : Liste des festivals à sauvegarder
- `filename` : Nom du fichier (optionnel, auto-généré si non spécifié)

## Format des données

Chaque festival contient les informations suivantes :
- `name` : Nom du festival
- `month` : Mois (en français)
- `year` : Année
- `dates` : Dates du festival
- `location` : Lieu
- `hours` : Horaires d'ouverture
- `entry_fee` : Prix d'entrée
- `description` : Description
- `features` : Liste des caractéristiques/attractions

## Mois disponibles

Le scraper supporte tous les mois en français :
- janvier, février, mars, avril, mai, juin
- juillet, août, septembre, octobre, novembre, décembre

## Exemples de fichiers générés

### JSON
```json
{
  "festivals": [
    {
      "name": "Tokyo Christmas Market",
      "month": "decembre",
      "year": 2025,
      "dates": "December 1-25, 2025",
      "location": "Tokyo Skytree",
      "hours": "11am-10pm",
      "entry_fee": "Free",
      "features": ["Gingerbread house", "Mulled wine"]
    }
  ]
}
```

### CSV
```
name,month,year,dates,location,hours,entry_fee,description,features
Tokyo Christmas Market,decembre,2025,December 1-25 2025,Tokyo Skytree,11am-10pm,Free,...
```

## Notes

- Le scraper attend quelques secondes entre chaque requête pour ne pas surcharger le serveur
- Si une page n'existe pas pour un mois/année donné, le scraper retourne une liste vide
- Les fichiers sont sauvegardés avec l'encodage UTF-8 pour supporter les caractères japonais

## Licence

Utilisation libre pour un usage personnel et éducatif.