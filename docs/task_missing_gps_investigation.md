# Task: Investigation des Événements Sans Coordonnées GPS

## 📋 Contexte du Projet

Nous avons un scraper d'événements Tokyo avec une base de données SQLite. Après amélioration de l'extraction GPS, nous avons une bonne couverture globale mais **25-30% des événements n'ont toujours pas de coordonnées GPS**.

## 📊 État Actuel de la Couverture GPS

```
Type                 Total      Avec GPS   Sans GPS   % GPS
------------------------------------------------------------
expositions          31         29         2          93.5%  ✅
festivals            42         36         6          85.7%  ✅
marches              55         49         6          89.1%  ✅
tokyo_cheapo         59         44         15         74.6%  ⚠️
hanabi               2          0          2          0.0%   ❌
------------------------------------------------------------
TOTAL                189        158        31         83.6%
```

**Problème** : Il reste **31 événements** (16.4%) sans coordonnées GPS, ce qui les rend invisibles sur la carte interactive.

## 🎯 Objectif de la Tâche

**Investiguer pourquoi certains événements spécifiques n'ont pas de coordonnées GPS et trouver des solutions pour les récupérer.**

## 🔍 Événements à Investiguer

### A. Tokyo Cheapo (15 événements sans GPS)

Exemples d'événements Tokyo Cheapo **SANS** GPS à investiguer :

1. **UNU Farmers Market** - https://tokyocheapo.com/events/unu-farmers-market/
2. **Shimokitazawa Flea Market** - https://tokyocheapo.com/events/shimokitazawa-flea-market/
3. **Weekend Comedy at TCB** - https://tokyocheapo.com/events/weekend-comedy-at-tcb/
4. **Ohi Racecourse Flea Market** - https://tokyocheapo.com/events/ohi-racecourse-flea-market/
5. **Hanazono Shrine Antique Market** - https://tokyocheapo.com/events/hanazono-shrine-antique-market/

**Questions à répondre** :
- [ ] Ces événements ont-ils une section `<div component-name="apple-maps">` ?
- [ ] Si oui, le JSON contient-il `lat` et `lng` ?
- [ ] Si non, pourquoi ? (événement online ? lieu non précis ? autre raison ?)
- [ ] Y a-t-il une adresse textuelle qu'on pourrait geocoder ?
- [ ] Y a-t-il un pattern commun entre les événements sans GPS ?

### B. Festivals (6 événements sans GPS)

Exemples d'événements Festivals **SANS** GPS à investiguer :

1. Chercher dans la base de données les 6 festivals sans GPS
2. Visiter leurs pages sur ichiban-japan.com
3. Vérifier s'ils ont des liens Google Maps dans le HTML

**Questions à répondre** :
- [ ] Les pages ont-elles un lien Google Maps ?
- [ ] Si oui, est-il dans un format non reconnu par notre extracteur ?
- [ ] Si non, y a-t-il une adresse textuelle complète ?
- [ ] Les GPS sont-ils dans un iframe ou un format spécial ?

### C. Hanabi (2 événements sans GPS - 0%)

**PRIORITAIRE** : Les événements Hanabi n'ont AUCUN GPS malgré le script d'extraction map.html.

**Questions à répondre** :
- [ ] Quels sont les 2 événements Hanabi dans la base ?
- [ ] Ont-ils des pages map.html comme les autres hanabi ?
- [ ] Le script `investigate_hanabi_map.py` fonctionne-t-il sur ces événements ?
- [ ] Y a-t-il un problème avec leurs URLs ou IDs ?

## 🛠️ Outils et Méthodes à Utiliser

### 1. Analyser la Base de Données

Utilisez cette requête SQLite pour identifier les événements sans GPS :

```sql
-- Tokyo Cheapo sans GPS
SELECT id, name, location, detail_url
FROM events
WHERE event_type = 'tokyo_cheapo'
  AND (latitude IS NULL OR longitude IS NULL)
LIMIT 10;

-- Festivals sans GPS
SELECT id, name, location, website, googlemap_link
FROM events
WHERE event_type = 'festivals'
  AND (latitude IS NULL OR longitude IS NULL);

-- Hanabi sans GPS
SELECT id, name, event_id, detail_url
FROM events
WHERE event_type = 'hanabi'
  AND (latitude IS NULL OR longitude IS NULL);
```

### 2. Visiter les Pages

Pour chaque événement sans GPS :
1. Copier l'URL (detail_url ou website)
2. Ouvrir dans Chrome
3. Inspecter avec DevTools
4. Chercher :
   - JSON embarqué (Tokyo Cheapo)
   - Liens Google Maps (Festivals)
   - Iframes de cartes
   - Données structurées JSON-LD
   - Balises `<script>` avec coordonnées

### 3. Identifier les Patterns

Grouper les événements sans GPS par catégories :
- **Catégorie A** : Événements online (pas de lieu physique)
- **Catégorie B** : Événements itinérants (plusieurs lieux ou lieu changeant)
- **Catégorie C** : Événements avec lieu mais pas de GPS dans le HTML
- **Catégorie D** : Erreur de scraping (GPS présent mais non extrait)

## 📝 Livrables Attendus

### 1. Rapport d'Investigation (Markdown)

Créez un fichier `docs/missing_gps_analysis.md` avec :

```markdown
# Analyse des Événements Sans GPS

## Résumé Exécutif
[% d'événements analysés, solutions trouvées, limitations identifiées]

## Tokyo Cheapo (15 événements)

### Événements Analysés

#### 1. UNU Farmers Market
- **URL** : https://...
- **GPS trouvé** : Oui/Non
- **Raison de l'absence** : [description]
- **Solution proposée** : [code ou méthode]
- **Catégorie** : A/B/C/D

#### 2. [Autre événement]
...

### Patterns Identifiés

- X événements sont de **Catégorie A** (online) → Pas de solution
- Y événements sont de **Catégorie C** (lieu mais pas de GPS) → Solution : [décrire]
- Z événements sont de **Catégorie D** (erreur scraping) → Solution : [corriger code]

### Solutions Proposées

#### Pour Catégorie C : Geocoding depuis adresse
```python
# Code pour extraire adresse et geocoder
```

#### Pour Catégorie D : Améliorer l'extraction
```python
# Code pour corriger le scraper
```

## Festivals (6 événements)

[Même structure]

## Hanabi (2 événements)

[Même structure]

## Recommandations Globales

### Solutions Immédiates (Code)
1. [Liste des corrections de code à faire]

### Solutions Long Terme (Geocoding)
1. [Si on doit utiliser une API de geocoding]
2. [Coût estimé, complexité, alternatives]

### Événements Sans Solution
[Liste des événements qui ne peuvent pas avoir de GPS et pourquoi]
```

### 2. Code de Correction (si applicable)

Si vous trouvez des patterns ou bugs dans l'extraction actuelle, proposez :
- Code Python pour corriger le scraper
- Sélecteurs CSS/XPath alternatifs
- Nouvelles sources de données GPS

### 3. Liste d'Événements par Catégorie

```markdown
## Événements par Catégorie

### Catégorie A - Online/Pas de lieu physique (pas de solution)
- Weekend Comedy at TCB (online)
- [autres...]

### Catégorie B - Itinérants (geocoding possible sur lieu principal)
- [événements...]

### Catégorie C - Lieu mais pas de GPS dans HTML (geocoding nécessaire)
- [événements...]

### Catégorie D - GPS présent mais non extrait (corriger le code)
- [événements...]
```

## 🔧 Exemples de Solutions

### Solution 1 : Extraction Améliorée

Si le GPS est dans le HTML mais pas extrait correctement :

```python
# Exemple : chercher dans un autre sélecteur
map_div = soup.find('div', class_='map-container')
if map_div and map_div.get('data-lat'):
    lat = float(map_div['data-lat'])
    lon = float(map_div['data-lng'])
```

### Solution 2 : Geocoding depuis Adresse

Si seule l'adresse est disponible :

```python
# Option 1 : Nominatim (gratuit, limité)
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="tokyo-events")
location = geolocator.geocode("2-33-12 Kitazawa, Setagaya-ku, Tokyo, Japan")
if location:
    lat = location.latitude
    lon = location.longitude

# Option 2 : Google Geocoding API (payant, précis)
# Nécessite une clé API
```

### Solution 3 : Extraction depuis Venue Pages

Si Tokyo Cheapo a une page venue séparée avec GPS :

```python
# Extraire l'URL du venue
venue_link = soup.find('a', href=lambda x: x and '/place/' in x)
if venue_link:
    venue_url = venue_link['href']
    # Scraper la page venue pour GPS
```

## ⚠️ Points d'Attention

1. **Vérifier 5-10 événements par type** (pas besoin de tous les analyser)
2. **Identifier les patterns** (si 80% sont online, pas besoin d'analyser chacun)
3. **Prioriser les solutions simples** (correction de code > geocoding > API payante)
4. **Documenter clairement** ce qui est impossible vs ce qui nécessite du travail

## 📚 Contexte Technique Additionnel

### Notre Stack Actuel

**Extraction GPS existante** :
- Tokyo Cheapo : JSON Apple Maps (`<div component-name="apple-maps">`)
- Festivals/Expositions/Marchés : Liens Google Maps + GPSExtractor
- Hanabi : Script `investigate_hanabi_map.py` + extraction map.html

**Limitations** :
- ❌ Pas de JavaScript execution (BeautifulSoup uniquement)
- ❌ Pas de geocoding actuellement (pourrait être ajouté)
- ✅ Peut parser JSON, HTML, iframes

### Base de Données

**Schéma events** :
```sql
latitude REAL,      -- NULL = pas de GPS
longitude REAL,     -- NULL = pas de GPS
location TEXT,      -- Texte du lieu (ex: "Shibuya")
googlemap_link TEXT,-- Lien Google Maps (peut être NULL)
detail_url TEXT,    -- URL de la page de détail
venue TEXT,         -- Nom du venue (Hanabi uniquement)
```

## ✅ Critères de Succès

**Mission réussie si** :
1. Vous avez analysé **5-10 événements de chaque type** sans GPS
2. Vous avez identifié les **patterns principaux** (online, itinérants, bug, etc.)
3. Vous avez proposé des **solutions concrètes** avec code (si possible)
4. Vous avez documenté les **limitations** (événements impossibles à géolocaliser)
5. Votre rapport permet de **prioriser** les améliorations

## 🚀 Prochaines Étapes (après votre investigation)

**Si solutions trouvées** :
1. Corriger le code des scrapers
2. Ajouter geocoding si nécessaire
3. Re-scraper les événements concernés
4. Vérifier la nouvelle couverture GPS

**Si geocoding nécessaire** :
1. Évaluer le coût (nombre d'événements × coût par requête)
2. Choisir le service (Nominatim gratuit vs Google Maps payant)
3. Implémenter avec rate limiting
4. Stocker les résultats pour éviter re-geocoding

---

**Merci pour votre aide ! 🙏**

**Objectif** : Atteindre **>90% de couverture GPS** pour une carte interactive complète.
