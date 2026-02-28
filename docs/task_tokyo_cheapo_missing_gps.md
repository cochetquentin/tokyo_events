# Task: Investigation des 15 Événements Tokyo Cheapo Sans Coordonnées GPS

## 📋 Contexte

Après l'amélioration de l'extraction GPS pour Tokyo Cheapo (passage de 1.7% à 74.6% de couverture), il reste **15 événements (25.4%)** sans coordonnées GPS. Ces événements ne sont donc pas visibles sur la carte interactive.

**Méthode d'extraction actuelle** :
- ✅ Extraction du JSON Apple Maps : `<div component-name="apple-maps"><script type="application/json">` avec `lat` et `lng`
- ✅ Fallback Google Maps : liens `google.com/maps`
- ✅ GPSExtractor pour extraire GPS depuis URLs Google Maps

**Problème** : Malgré ces méthodes, 15 événements n'ont toujours pas de GPS.

## 📊 Statistiques Actuelles

```
Tokyo Cheapo GPS Coverage: 44/59 (74.6%)
Événements SANS GPS: 15 (25.4%)
```

## 🎯 Objectif de la Tâche

**Investiguer les 15 événements Tokyo Cheapo listés ci-dessous pour comprendre pourquoi ils n'ont pas de GPS et proposer des solutions concrètes.**

## 🔍 Liste Complète des 15 Événements Sans GPS

### 1. **Bad Bunny Live in Tokyo 2026**
- **Location**: N/A
- **URL**: ⚠️ `None` (pas d'URL de détail enregistrée)
- **Hypothèse**: Événement concert → probablement un lieu spécifique

### 2. **Candlelight Concert: A Tribute to Joe Hisaishi (Studio Ghibli)**
- **Location**: Shinagawa
- **URL**: ⚠️ `None`
- **Hypothèse**: Concert dans une salle à Shinagawa

### 3. **Candlelight Concert: Magical Movie Soundtracks**
- **Location**: Ginza
- **URL**: ⚠️ `None`
- **Hypothèse**: Concert dans une salle à Ginza

### 4. **Fuchū Citizens' Cherry Blossom Festival**
- **Location**: Fuchu
- **URL**: ⚠️ `None`
- **Hypothèse**: Festival de cerisiers → parc ou lieu public

### 5. **Harumeki Early Blooming Cherry Blossom Festival**
- **Location**: Minami-Ashigara
- **URL**: ⚠️ `None`
- **Hypothèse**: Festival de cerisiers → hors Tokyo

### 6. **Kotatsu Boat in Nagatoro**
- **Location**: Chichibu
- **URL**: ⚠️ `None`
- **Hypothèse**: Activité bateau → point de départ spécifique

### 7. **Kyōdo-no-Mori Plum Blossom Festival**
- **Location**: Fuchu
- **URL**: ⚠️ `None`
- **Hypothèse**: Festival de pruniers → parc Kyōdo-no-Mori

### 8. **Noto Art Line**
- **Location**: Sugamo
- **URL**: ⚠️ `None`
- **Hypothèse**: Exposition art → galerie ou musée

### 9. **Shinagawa Yakiimo Terrace**
- **Location**: Shinagawa
- **URL**: ⚠️ `None`
- **Hypothèse**: Événement food → terrasse spécifique

### 10. **Takao Baigo Plum Village Festival**
- **Location**: Hachiōji
- **URL**: ⚠️ `None`
- **Hypothèse**: Festival de pruniers → village Takao Baigo

### 11. **Tokyo Anime Award Festival 2026**
- **Location**: Ikebukuro
- **URL**: ⚠️ `None`
- **Hypothèse**: Festival anime → centre de convention

### 12. **Tokyo Creative Salon 2026**
- **Location**: Ginza
- **URL**: ⚠️ `None`
- **Hypothèse**: Salon créatif → salle ou galerie

### 13. **Tokyo River Clean-Up**
- **Location**: Edogawa
- **URL**: ⚠️ `None`
- **Hypothèse**: ⚠️ Événement itinérant → plusieurs points de rencontre possibles (pas de GPS unique)

### 14. **Wi Deh Yah Community Fundraiser**
- **Location**: Shibuya
- **URL**: ⚠️ `None`
- **Hypothèse**: Événement fundraiser → salle communautaire

### 15. **Yokohama America-Yama Rooftop Illuminations**
- **Location**: Yokohama
- **URL**: ⚠️ `None`
- **Hypothèse**: Illuminations → rooftop America-Yama à Yokohama

## ⚠️ Observation Critique

**TOUS les événements sans GPS ont `detail_url = None`** dans la base de données !

Cela signifie que :
1. ❌ Le scraper n'a pas enregistré l'URL de la page de détail
2. ❌ Le scraper n'a donc jamais visité la page de détail pour extraire le GPS
3. ⚠️ Problème probable dans `_scrape_detail_page()` ou dans l'enregistrement de `detail_url`

## 🔍 Questions d'Investigation

### A. Vérifier la Base de Données

**SQL à exécuter** :
```sql
-- Vérifier si les événements ont bien un detail_url NULL
SELECT id, name, location, detail_url, latitude, longitude
FROM events
WHERE event_type = 'tokyo_cheapo'
  AND (latitude IS NULL OR longitude IS NULL);

-- Comparer avec les événements qui ONT un GPS
SELECT id, name, location, detail_url, latitude, longitude
FROM events
WHERE event_type = 'tokyo_cheapo'
  AND latitude IS NOT NULL
LIMIT 5;
```

### B. Chercher les URLs Manuellement

Pour chaque événement, chercher sur tokyocheapo.com :

**Étapes** :
1. Aller sur https://tokyocheapo.com/events/
2. Chercher le nom de l'événement (ex: "Bad Bunny Live in Tokyo")
3. Noter l'URL de la page de détail
4. Inspecter le HTML de la page :
   - Y a-t-il un `<div component-name="apple-maps">` ?
   - Y a-t-il un `<script type="application/json">` avec `lat` et `lng` ?
   - Y a-t-il un lien Google Maps ?
   - Y a-t-il une adresse textuelle qu'on pourrait geocoder ?

### C. Identifier les Patterns

Après investigation de 5-10 événements, catégoriser :

#### **Catégorie A** : Événement sans lieu fixe / itinérant
- Exemple potentiel : "Tokyo River Clean-Up"
- Solution : ❌ Pas de GPS unique possible

#### **Catégorie B** : Événement avec lieu mais page sans GPS dans HTML
- Exemple potentiel : événements "Candlelight Concert"
- Solution : 🔧 Geocoding depuis l'adresse textuelle (location + nom du lieu)

#### **Catégorie C** : Bug de scraping - `detail_url` non enregistrée
- Exemple potentiel : TOUS les événements listés
- Solution : 🐛 Corriger le scraper pour enregistrer `detail_url` systématiquement

#### **Catégorie D** : GPS présent dans HTML mais non extrait
- Solution : 🔧 Améliorer les sélecteurs CSS/XPath

## 🛠️ Méthode d'Investigation Recommandée

### Étape 1 : Vérifier la Base de Données (5 min)
```bash
# Vérifier si detail_url est vraiment NULL pour tous
sqlite3 data/tokyo_events.sqlite "SELECT name, detail_url FROM events WHERE event_type='tokyo_cheapo' AND latitude IS NULL LIMIT 15;"
```

### Étape 2 : Chercher 5 Événements Manuellement (15-20 min)

Choisir 5 événements variés :
1. **Bad Bunny Live in Tokyo 2026** (concert)
2. **Tokyo River Clean-Up** (itinérant probable)
3. **Fuchū Citizens' Cherry Blossom Festival** (festival parc)
4. **Noto Art Line** (exposition)
5. **Yokohama America-Yama Rooftop Illuminations** (illuminations)

Pour chacun :
- Chercher l'URL sur tokyocheapo.com
- Ouvrir DevTools (F12) → Inspector
- Chercher `<div component-name="apple-maps">`
- Copier le JSON s'il existe
- Noter si c'est un événement online/itinérant/avec lieu fixe

### Étape 3 : Analyser le Scraper (10 min)

Lire `src/scraper_tokyo_cheapo.py` et vérifier :
- Comment est extraite `detail_url` dans la liste des événements ?
- Y a-t-il un bug qui empêche l'enregistrement de `detail_url` ?
- Le scraper visite-t-il TOUTES les pages de détail ou seulement certaines ?

### Étape 4 : Catégoriser (5 min)

Basé sur les 5 événements testés, déterminer la distribution :
- X% sont Catégorie A (pas de GPS possible)
- Y% sont Catégorie B (geocoding nécessaire)
- Z% sont Catégorie C (bug scraping)
- W% sont Catégorie D (GPS présent mais non extrait)

## 📝 Livrable Attendu

Créer un fichier `docs/tokyo_cheapo_missing_gps_analysis.md` avec :

```markdown
# Analyse des 15 Événements Tokyo Cheapo Sans GPS

## Résumé Exécutif

[% d'événements analysés, cause principale identifiée, solutions proposées]

## Investigation des Événements (échantillon)

### 1. Bad Bunny Live in Tokyo 2026
- **URL trouvée** : https://tokyocheapo.com/events/...
- **GPS dans HTML** : Oui/Non
- **JSON Apple Maps présent** : Oui/Non
- **Coordonnées extraites** :
  ```json
  {
    "lat": "35.xxxxx",
    "lng": "139.xxxxx",
    "title": "Venue Name"
  }
  ```
- **Catégorie** : A/B/C/D
- **Solution proposée** : [description]

### 2. [Autre événement]
...

## Patterns Identifiés

### Cause Principale (80% des cas)
[Description de la cause principale]

**Preuve** :
- [Liste d'observations]

### Solutions Proposées

#### Solution 1 : Corriger l'enregistrement de `detail_url`

**Fichier** : `src/scraper_tokyo_cheapo.py`

**Problème** :
```python
# Code actuel qui ne sauvegarde pas detail_url
```

**Solution** :
```python
# Code corrigé pour sauvegarder detail_url systématiquement
detail_data['detail_url'] = detail_url  # Ajouter cette ligne
```

#### Solution 2 : Geocoding pour événements sans GPS dans HTML

**Cas d'usage** : Événements avec `location` textuelle mais pas de JSON Apple Maps

**Code proposé** :
```python
from geopy.geocoders import Nominatim

def geocode_from_location(location_text: str) -> tuple:
    """Geocode une adresse textuelle en (lat, lon)"""
    geolocator = Nominatim(user_agent="tokyo-events")
    location = geolocator.geocode(f"{location_text}, Tokyo, Japan")
    if location:
        return (location.latitude, location.longitude)
    return (None, None)
```

#### Solution 3 : [Autre solution si applicable]

## Répartition par Catégorie

| Catégorie | Nombre | % | Solution |
|-----------|--------|---|----------|
| A - Itinérant | X | X% | ❌ Pas de GPS unique |
| B - Geocoding | Y | Y% | 🔧 Ajouter geocoding |
| C - Bug scraping | Z | Z% | 🐛 Corriger le code |
| D - GPS non extrait | W | W% | 🔧 Améliorer extraction |

## Événements Sans Solution

[Liste des événements qui ne peuvent pas avoir de GPS avec justification]

## Recommandations

### Action Immédiate (Haute Priorité)
1. [Correction à faire dans le scraper]

### Action Court Terme (Après correction)
1. [Re-scraper les événements concernés]

### Action Long Terme (Optionnel)
1. [Ajouter geocoding pour cas limites]
```

## ✅ Critères de Succès

**Mission réussie si** :
1. ✅ Vous avez investigué **au moins 5 événements** manuellement sur tokyocheapo.com
2. ✅ Vous avez identifié la **cause principale** (bug scraping, pas de GPS dans HTML, etc.)
3. ✅ Vous avez proposé des **solutions concrètes avec code** (si bug de scraping)
4. ✅ Vous avez catégorisé les événements (A/B/C/D)
5. ✅ Vous avez documenté les **URLs réelles** des événements testés

## 🔧 Outils Disponibles

### 1. DevTools Chrome
- F12 → Inspector
- Ctrl+F pour chercher "apple-maps"
- Onglet Network pour voir les requêtes

### 2. SQLite
```bash
sqlite3 data/tokyo_events.sqlite
```

### 3. Python pour Tests
```python
# Tester l'extraction GPS sur une URL spécifique
from src.scraper_tokyo_cheapo import TokyoCheapoScraper

scraper = TokyoCheapoScraper()
detail_url = "https://tokyocheapo.com/events/bad-bunny-live-tokyo-2026/"
detail_data = scraper._scrape_detail_page(detail_url)
print(f"Latitude: {detail_data.get('latitude')}")
print(f"Longitude: {detail_data.get('longitude')}")
```

## 📚 Contexte Technique

### Scraper Actuel

**Fichier** : `src/scraper_tokyo_cheapo.py`

**Méthode d'extraction GPS** (lignes ~401-430) :
```python
# Extract GPS coordinates from Apple Maps JSON (Primary method)
map_div = soup.find('div', {'component-name': 'apple-maps'})
if map_div:
    json_script = map_div.find('script', {'type': 'application/json'})
    if json_script and json_script.string:
        try:
            map_data = json.loads(json_script.string)
            lat_str = map_data.get('lat')
            lng_str = map_data.get('lng')

            if lat_str and lng_str:
                detail_data['latitude'] = float(lat_str)
                detail_data['longitude'] = float(lng_str)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"      ⚠️ Error parsing Apple Maps JSON: {e}")
```

### Base de Données

**Schéma events** :
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    location TEXT,
    detail_url TEXT,  -- ⚠️ NULL pour les 15 événements sans GPS
    latitude REAL,    -- NULL = pas de GPS
    longitude REAL,   -- NULL = pas de GPS
    ...
);
```

## 🚀 Après l'Investigation

**Si bug de scraping identifié** :
1. Corriger le code dans `src/scraper_tokyo_cheapo.py`
2. Re-scraper les événements concernés
3. Vérifier la nouvelle couverture GPS

**Si geocoding nécessaire** :
1. Choisir le service (Nominatim gratuit vs Google Maps payant)
2. Implémenter la fonction de geocoding
3. Appliquer sur les événements avec `location` mais sans GPS

**Si événements sans GPS légitime** :
1. Documenter pourquoi (itinérant, online, etc.)
2. Accepter la limitation de couverture

---

**Merci pour votre aide ! 🙏**

**Objectif** : Comprendre et résoudre les 15 événements Tokyo Cheapo sans GPS pour atteindre **>90% de couverture GPS**.
