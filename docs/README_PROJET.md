# Tokyo Festivals Scraper 🎌

Un scraper automatique pour récupérer les informations des festivals de Tokyo depuis le site [ichiban-japan.com](https://ichiban-japan.com).

## Présentation

Ce projet permet de scraper automatiquement les festivals de Tokyo pour n'importe quel mois et année, et de sauvegarder les données en formats JSON et CSV.

### Fonctionnalités

- Scraping automatique pour n'importe quel mois/année
- Support de tous les mois (janvier à décembre)
- Export en JSON et CSV
- Gestion automatique des erreurs et des pages manquantes
- Encodage UTF-8 pour les caractères japonais
- Compatible Windows, Mac et Linux

## Installation

```bash
# Installer les dépendances
pip install -r requirements.txt
# ou avec uv
uv pip install -r requirements.txt
```

## Démarrage Rapide

```bash
# Méthode la plus simple
uv run quick_start.py
```

Ce script va :
1. Scraper les festivals de décembre 2025
2. Générer `festivals_tokyo_decembre_2025.json`
3. Générer `festivals_tokyo_decembre_2025.csv`

## Utilisation

### Script Simple

```python
from scraper_festivals_tokyo import TokyoFestivalScraper

scraper = TokyoFestivalScraper()

# Scraper un mois
festivals = scraper.scrape_festivals(month=12, year=2025)

# Sauvegarder
scraper.save_to_json(festivals)
scraper.save_to_csv(festivals)
```

### Scraper Plusieurs Mois

Utilisez le script de test fourni :
```bash
uv run test_autre_mois.py
```

Ou créez votre propre script :
```python
for month in range(1, 13):
    festivals = scraper.scrape_festivals(month=month, year=2025)
    scraper.save_to_json(festivals)
```

## Structure du Projet

```
TokyoEvent/
│
├── scraper_festivals_tokyo.py   # Script principal du scraper
├── quick_start.py                # Démarrage rapide
├── exemple_utilisation.py        # Exemples d'utilisation
├── test_autre_mois.py           # Test pour plusieurs mois
│
├── requirements.txt              # Dépendances Python
├── GUIDE_UTILISATION.md         # Guide détaillé
├── README_SCRAPER.md            # Documentation du scraper
│
└── festivals_*.json/csv         # Fichiers générés (ignorés par git)
```

## Format des Données

### Exemple JSON
```json
{
  "festivals": [
    {
      "name": "Tokyo Christmas Market",
      "month": "decembre",
      "year": 2025,
      "dates": "1-25 décembre 2025",
      "location": "Tokyo Skytree",
      "hours": "11am-10pm",
      "entry_fee": "Free",
      "description": "Description...",
      "features": ["Feature 1", "Feature 2"]
    }
  ]
}
```

## Documentation

- [Guide d'utilisation complet](GUIDE_UTILISATION.md) - Exemples détaillés et cas d'usage
- [Documentation du scraper](README_SCRAPER.md) - API et paramètres

## Exemples de Résultats

Le scraper a été testé avec succès sur :
- Janvier 2025 : 21 festivals
- Février 2025 : 22 festivals
- Mars 2025 : 26 festivals
- Avril 2025 : 34 festivals
- Mai 2025 : 50 festivals
- Juin 2025 : 41 festivals
- Décembre 2025 : 21 festivals

## Dépendances

- `requests` - Pour les requêtes HTTP
- `beautifulsoup4` - Pour le parsing HTML
- `lxml` - Parser HTML rapide

## Licence

Projet open-source pour usage personnel et éducatif.

## Contribution

Les améliorations sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Soumettre une Pull Request

## Support

Pour toute question ou problème :
1. Consultez le [Guide d'utilisation](GUIDE_UTILISATION.md)
2. Vérifiez que les dépendances sont installées
3. Testez avec le script `quick_start.py`

## Roadmap

Fonctionnalités futures possibles :
- [ ] Support d'autres villes japonaises
- [ ] Interface graphique (GUI)
- [ ] API REST
- [ ] Notifications pour nouveaux festivals
- [ ] Filtrage avancé par type de festival
- [ ] Export vers d'autres formats (Excel, PDF)

---

Créé avec Python et BeautifulSoup
