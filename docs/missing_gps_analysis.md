# Analyse des Événements Sans GPS

## Résumé Exécutif

Investigation de 31 événements sans GPS (16.4% du total) répartis en 3 types :

| Type | Sans GPS | Problème identifié | Solution | GPS récupérables |
|------|----------|-------------------|----------|-----------------|
| Tokyo Cheapo | 15 | Scraper cherchait Google Maps → Apple Maps JSON | Fix tâche 1 (résolu) + adresse imprécise | ~10/15 |
| Festivals | 6 | `google.fr/maps` non reconnu par scraper | Fix 1 ligne de code | ~5/6 |
| Marchés | 6 | `maps.app.goo.gl` (liens courts, pas de coords) | Suivi de redirection ou geocoding | ~4/6 |
| Hanabi | 2 | Source de données à investiguer | À déterminer | Inconnu |
| Expositions | 2 | `maps.app.goo.gl` (même problème marchés) | Fix code | ~1/2 |

**Impact estimé si fixes appliqués** : Couverture GPS → de 83.6% à **~92-95%**

---

## Tokyo Cheapo (15 événements sans GPS)

### Contexte

Le scraper actuel cherchait des liens **Google Maps** (`google.com/maps`), mais Tokyo Cheapo utilise **Apple Maps** (JSON embarqué dans `<div component-name="apple-maps">`). Ce fix a été effectué dans la tâche précédente.

### Événements Analysés

#### 1. UNU Farmers Market
- **URL** : https://tokyocheapo.com/events/unu-farmers-market/
- **GPS trouvé dans apple-maps JSON** : ✅ OUI (lat=35.662312, lng=139.7082801)
- **Raison de l'absence en DB** : Scraper ne parsait pas le JSON apple-maps
- **Catégorie** : D (Bug de scraping, GPS présent mais non extrait)
- **Solution** : Fix apple-maps JSON ✅ (déjà résolu)

#### 2. Shimokitazawa Flea Market
- **URL** : https://tokyocheapo.com/events/shimokitazawa-flea-market/
- **GPS trouvé dans apple-maps JSON** : ✅ OUI (lat=35.663007, lng=139.669419)
- **Raison de l'absence en DB** : Idem
- **Catégorie** : D (Bug de scraping)
- **Solution** : Fix apple-maps JSON ✅ (déjà résolu)

#### 3. Ohi Racecourse Flea Market
- **URL** : https://tokyocheapo.com/events/ohi-racecourse-flea-market/
- **GPS trouvé dans apple-maps JSON** : ✅ OUI (lat=35.593707, lng=139.744775)
- **Catégorie** : D (Bug de scraping)
- **Solution** : Fix apple-maps JSON ✅ (déjà résolu)

#### 4. Tokyo River Clean-Up
- **URL** : https://tokyocheapo.com/events/tokyo-river-clean/
- **GPS trouvé** : ❌ NON (pas de section apple-maps dans HTML)
- **Raison** : Événement de bénévolat en rivière, pas de venue fixe. Seul le quartier "Edogawa" est renseigné.
- **JSON-LD location** : `Place { name: "Edogawa", addressLocality: "Edogawa", addressRegion: "Suburban East Tokyo" }`
- **Catégorie** : B (Événement itinérant/lieu imprécis)
- **Solution** : Geocoding de "Edogawa, Tokyo" → coords approximatives du quartier. Peu précis.

#### 5. Noto Art Line
- **URL** : https://tokyocheapo.com/events/noto-art-line/
- **GPS trouvé** : ❌ NON (pas de section apple-maps)
- **Raison** : Événement artistique itinérant dans le quartier Sugamo, pas de venue unique
- **JSON-LD location** : `Place { name: "Sugamo", addressLocality: "Sugamo" }`
- **Catégorie** : B (Événement itinérant)
- **Solution** : Geocoding du quartier "Sugamo" → approximatif

#### 6. Wi Deh Yah Community Fundraiser
- **URL** : https://tokyocheapo.com/events/wi-deh-yah-community-fundraiser/
- **GPS trouvé** : ❌ NON (pas de section apple-maps)
- **Raison** : Pas d'adresse précise, seulement le quartier "Shibuya"
- **Catégorie** : B (Lieu imprécis)
- **Solution** : Geocoding du quartier Shibuya → approximatif

#### 7. Bad Bunny Live in Tokyo 2026
- **URL** : https://tokyocheapo.com/events/bad-bunny-live-tokyo/
- **GPS trouvé** : ❌ NON (pas de section apple-maps, location JSON-LD vide)
- **Raison** : Venue non encore assigné dans le CMS au moment du scraping
- **JSON-LD location** : [] (liste vide)
- **Catégorie** : A (Venue manquant dans la source)
- **Solution** : Rescrap après mise à jour du site, ou chercher manuellement

#### 8. Weekend Comedy at TCB
- **URL originale** : https://tokyocheapo.com/events/weekend-comedy-at-tcb/ → **404 Not Found**
- **Raison** : Page supprimée ou URL invalide dans la DB
- **Catégorie** : A (Événement expiré/supprimé)
- **Solution** : Supprimer de la DB ou marquer comme inactif

#### 9. Hanazono Shrine Antique Market (URL erronée)
- **URL originale** : https://tokyocheapo.com/events/hanazono-shrine-antique-market/ → **404**
- **URL correcte** : https://tokyocheapo.com/events/hanazono-antique-market/ ✅
- **GPS** : ✅ OUI via apple-maps JSON (lat=35.693555, lng=139.705168)
- **Catégorie** : D (URL incorrecte dans la DB)
- **Solution** : Corriger l'URL dans la DB

### Patterns Identifiés (Tokyo Cheapo)

| Catégorie | Nb estimé | Description | Solution |
|-----------|-----------|-------------|----------|
| D - Bug scraping (apple-maps) | ~8-10 | GPS présent dans JSON, non parsé | Fix apple-maps JSON ✅ résolu |
| B - Lieu imprécis (quartier) | ~3-4 | Pas d'adresse de rue, juste un quartier | Geocoding quartier (approximatif) |
| A - Venue manquant/expiré | ~2-3 | URL 404, location vide, événement online | Pas de solution directe |
| D - URL incorrecte en DB | ~1 | URL 404 mais événement existe avec URL différente | Corriger URL en DB |

---

## Festivals (6 événements sans GPS)

### Problème Identifié : `google.fr/maps` non reconnu

Les articles ichiban-japan.com pour les festivals contiennent des liens Google Maps sous **deux formats** :

1. **`google.fr/maps`** (9-11 par article) — contient les coordonnées dans l'URL
2. **`maps.app.goo.gl`** (12-13 par article) — lien court, nécessite suivi de redirection

Le scraper actuel cherche uniquement `google.com/maps` et `maps.google.com`.  
**Résultat** : les liens `google.fr/maps` sont ignorés.

### Exemple de Liens Google.fr/maps

```
https://www.google.fr/maps/place/Sanctuaire+Oji-Inari/@35.7541848,139.7536183,17z/data=...
→ lat=35.7541848, lng=139.7536183 ✅

https://www.google.fr/maps/place/Zōjō-ji/@35.6574833,139.7457179,17z/data=...
→ lat=35.6574833, lng=139.7457179 ✅
```

### Fix Proposé : Ajouter `google.fr/maps` à la détection

```python
# Dans scraper_festivals.py (ou GPSExtractor) - chercher aussi google.fr/maps

map_links = soup.find_all('a', href=True)
for link in map_links:
    href = link['href']
    # CORRECTION : ajouter 'google.fr/maps' à la liste
    if ('google.com/maps' in href or 'maps.google.com' in href or
        'google.fr/maps' in href or  # ← NOUVEAU
        'maps.app.goo.gl' in href):   # ← NOUVEAU (voir section marchés)
        googlemap_link = href
        break
```

### Couverture GPS attendue après fix

- Festivals avec `google.fr/maps` → GPS récupérable via regex `@lat,lng` ✅
- Festivals avec `maps.app.goo.gl` → voir section ci-dessous

### Événements Festivals Sans GPS (estimé)

Exemple du mois de février 2026 (article ichiban-japan.com) :
- Hatsuuma Matsuri → `maps.app.goo.gl` → pas de GPS direct
- Kobai Matsuri → `google.fr/maps` → GPS dispo si scraper fixé
- Setagaya Ume Matsuri → `google.fr/maps` → GPS dispo si fixé
- Bunkyo Ume Matsuri → `google.fr/maps` → GPS dispo si fixé
- Irugi-jinja Reitaisai → `google.fr/maps` → GPS dispo si fixé
- Meiji-jingu → `maps.app.goo.gl` → pas de GPS direct

---

## Marchés (6 événements sans GPS)

### Problème Identifié : `maps.app.goo.gl` sans coordonnées

L'article ichiban-japan.com sur les marchés aux puces utilise **uniquement** des liens courts `maps.app.goo.gl` (14 liens, 0 lien google.com/maps ou google.fr/maps).

Ces URLs courtes **ne contiennent pas de coordonnées** dans l'URL — elles redirigent vers une URL Google Maps avec les coords, mais nécessitent une requête HTTP supplémentaire (HEAD request pour suivre la redirection).

**Exemple** :
```
https://maps.app.goo.gl/SCZsK1Fgignhbx9z8
→ Redirige vers → https://www.google.com/maps/place/Shimokita+Senrogai/@35.663...,139.669...
```

### Solution : Suivi de Redirection pour `maps.app.goo.gl`

```python
import requests
import re

def resolve_short_maps_url(short_url: str) -> tuple:
    """Résout un lien maps.app.goo.gl et retourne (lat, lon)."""
    try:
        # HEAD request avec suivi de redirection
        response = requests.head(
            short_url,
            allow_redirects=True,
            timeout=5,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        final_url = response.url
        
        # Extraire les coords de l'URL finale
        coord_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        if coord_match:
            return float(coord_match.group(1)), float(coord_match.group(2))
        
        # Alternative : chercher dans les paramètres ?q=lat,lng
        q_match = re.search(r'[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        if q_match:
            return float(q_match.group(1)), float(q_match.group(2))
            
    except Exception as e:
        print(f"Erreur résolution {short_url}: {e}")
    
    return None, None

# Utilisation dans le scraper
for link in soup.find_all('a', href=True):
    href = link['href']
    if 'maps.app.goo.gl' in href:
        lat, lon = resolve_short_maps_url(href)
        if lat:
            event['latitude'] = lat
            event['longitude'] = lon
            break
```

**Note** : Cette solution nécessite des requêtes HTTP supplémentaires (1 par lien court). Avec rate limiting 0.5s, c'est raisonnable.

---

## Hanabi (2 événements sans GPS)

### Investigation

Le scraper hanabi utilise un script `investigate_hanabi_map.py` et des fichiers `map.html`. Sans accès à la base de données SQLite, les 2 événements hanabi spécifiques ne peuvent pas être identifiés précisément.

### Problèmes Possibles

**Hypothèse A** : L'URL de la page map.html est incorrecte dans la DB
- Vérifier avec : `SELECT id, name, venue, detail_url FROM events WHERE event_type='hanabi' AND latitude IS NULL;`

**Hypothèse B** : La page map.html a changé de structure
- Chercher si la structure HTML du widget de carte a été modifiée

**Hypothèse C** : Les événements hanabi sont de type "Online" ou sans lieu fixe
- Certains feux d'artifice n'ont pas de lieu précis, seulement une rivière ou un quartier

### Action Recommandée

```sql
-- Identifier les 2 hanabi sans GPS
SELECT id, name, venue, detail_url, event_id
FROM events
WHERE event_type = 'hanabi'
  AND (latitude IS NULL OR longitude IS NULL);
```

Puis visiter manuellement chaque `detail_url` pour vérifier si elle est accessible et si elle contient des données GPS.

---

## Recommandations Globales

### Fix 1 : Ajouter `google.fr/maps` au GPSExtractor (PRIORITAIRE)

**Impact** : Festivals 85.7% → ~95%+ de GPS

```python
# Dans src/gps_extractor.py ou dans le scraper des festivals
# Modifier la condition de détection des liens Maps

# AVANT (actuel) :
if 'google.com/maps' in href or 'maps.google.com' in href:
    googlemap_link = href
    break

# APRÈS (corrigé) :
if ('google.com/maps' in href or 'maps.google.com' in href or
    'google.fr/maps' in href):  # ← Ajouter cette ligne
    googlemap_link = href
    break
```

### Fix 2 : Résoudre les liens `maps.app.goo.gl` (IMPORTANT)

**Impact** : Marchés 89.1% → ~95%+ | Festivals amélioration supplémentaire

```python
# Dans src/gps_extractor.py, ajouter une méthode
import requests, re

def extract_from_short_url(self, short_url: str) -> tuple:
    """Résout maps.app.goo.gl et extrait les coordonnées."""
    try:
        resp = requests.head(short_url, allow_redirects=True, 
                            timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        final_url = resp.url
        
        coord_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        if coord_match:
            return float(coord_match.group(1)), float(coord_match.group(2))
    except:
        pass
    return None, None

# Dans extract_from_google_maps_url, appeler si c'est un lien court :
def extract_from_google_maps_url(self, url: str) -> tuple:
    if 'maps.app.goo.gl' in url or 'goo.gl/maps' in url:
        return self.extract_from_short_url(url)
    # ... reste du code existant
```

### Fix 3 : Corriger les URLs incorrectes en DB

Certains événements ont une URL 404 en DB (ex: `hanazono-shrine-antique-market` au lieu de `hanazono-antique-market`). Un re-scraping complet résoudrait ce problème.

### Solution Long Terme : Geocoding pour les Événements sans Adresse

Pour les événements avec seulement un quartier (Catégorie B) :

```python
from geopy.geocoders import Nominatim

def geocode_ward(ward_name: str, city: str = "Tokyo", country: str = "Japan") -> tuple:
    """Géocode un quartier/arrondissement de Tokyo."""
    geolocator = Nominatim(user_agent="tokyo-events-scraper/1.0")
    
    query = f"{ward_name}, {city}, {country}"
    try:
        location = geolocator.geocode(query, timeout=5)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Erreur geocoding {query}: {e}")
    
    return None, None

# Exemple d'utilisation
lat, lon = geocode_ward("Edogawa")  # → coords du quartier Edogawa
lat, lon = geocode_ward("Sugamo")   # → coords du quartier Sugamo
```

**Attention** : Ces coordonnées sont au centre du quartier, pas du lieu exact de l'événement. Acceptable pour une carte générale, mais pas précis.

**Coût** : Nominatim est **gratuit** (open source, OpenStreetMap). Limite : 1 requête/seconde. Pour 10-15 événements → quelques secondes.

---

## Événements par Catégorie

### Catégorie A — Venue manquant/expiré (pas de solution directe)
- Weekend Comedy at TCB → URL 404, événement probablement terminé
- Bad Bunny Live in Tokyo → Location vide dans le CMS au moment du scraping
- Hanabi #1 et #2 → À investiguer avec accès à la DB

### Catégorie B — Lieu imprécis/itinérant (geocoding quartier possible)
- Tokyo River Clean-Up → "Edogawa" (rivière, pas de lieu fixe)
- Noto Art Line → "Sugamo" (événement itinérant dans le quartier)
- Wi Deh Yah Community Fundraiser → "Shibuya" (lieu non précisé)
- ~2-3 autres Tokyo Cheapo sans venue précis

### Catégorie C — GPS dans la source mais lien court (fix requis)
- ~4-6 marchés aux puces → `maps.app.goo.gl`
- ~1-2 festivals → `maps.app.goo.gl`
- ~1 exposition → `maps.app.goo.gl` (ex: Tokiwaso Manga Museum)

### Catégorie D — Bug de scraping (fix simple)
- ~8-10 Tokyo Cheapo → JSON apple-maps non parsé ✅ résolu
- ~4-5 Festivals → `google.fr/maps` non reconnu ← fix urgent
- 1 Tokyo Cheapo → URL incorrecte en DB

---

## Impact des Fixes Estimé

| Fix | Effort | Événements récupérés | Nouvelle couverture |
|-----|--------|---------------------|---------------------|
| Fix 1 : google.fr/maps | 1 ligne de code | +4-5 festivals | 87% → ~95% |
| Fix 2 : maps.app.goo.gl | ~10 lignes + HTTP req | +4-6 marchés, +1-2 festivals | ~95% → ~97% |
| Fix 3 : URLs incorrectes DB | Re-scraping | +1-2 events | marginal |
| Geocoding quartiers | ~20 lignes + Nominatim | +3-5 events (approx) | ~97% → ~98% |
| **Total estimé** | | **~13-18 événements** | **83.6% → ~95-98%** |

---

## Résumé Exécutif Détaillé

**Problèmes identifiés** (par ordre d'importance) :
1. **Bug Catégorie D** (résolu) : scraper cherchait Google Maps au lieu du JSON apple-maps sur Tokyo Cheapo
2. **Bug Catégorie D** (urgent) : `google.fr/maps` non reconnu → affecte ~5 festivals
3. **Bug Catégorie C** (important) : `maps.app.goo.gl` sans suivi de redirection → affecte ~7 marchés/festivals
4. **Limitation Catégorie B** (faible priorité) : événements sans adresse précise → geocoding approximatif
5. **Catégorie A** (non solvable) : URL 404, venues manquants → ~3-5 événements

**Recommandation principale** : Fix #1 (google.fr/maps) est trivial (1 ligne) et récupère ~5 festivals immédiatement.
