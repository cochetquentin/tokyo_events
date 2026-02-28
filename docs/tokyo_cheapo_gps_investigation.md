# Investigation GPS Tokyo Cheapo

## Résumé Exécutif

**✅ Les coordonnées GPS sont TROUVABLES** sur les pages de détail Tokyo Cheapo. Elles sont stockées dans un bloc JSON embarqué directement dans le HTML source (accessible par BeautifulSoup sans JavaScript). La source est un élément `<script type="application/json">` à l'intérieur d'un `<div component-name="apple-maps">`.

**Problème identifié** : Le scraper actuel cherche des liens **Google Maps** (`google.com/maps`), mais Tokyo Cheapo utilise **Apple Maps** (MapKit JS). Les coordonnées GPS ne sont pas dans les liens mais dans le JSON embarqué.

**Couverture attendue** : ~70-85% des événements avec la nouvelle méthode (contre 1.7% actuellement).

---

## Méthode d'Investigation

Pages visitées :
1. https://tokyocheapo.com/events/ (page liste)
2. https://tokyocheapo.com/events/roppongi-crossing-2025-what-passes-is-time-we-are-eternal/ (musée, venue précis)
3. https://tokyocheapo.com/events/shimokitazawa-flea-market/ (marché en plein air)
4. https://tokyocheapo.com/events/matsuda-cherry-blossom-festival/ (festival dans un parc)
5. https://tokyocheapo.com/events/unu-farmers-market/ (marché universitaire)
6. https://tokyocheapo.com/events/tokyo-river-clean/ (événement sans adresse précise)
7. https://tokyocheapo.com/events/ohi-racecourse-flea-market/ (hippodrome)
8. https://tokyocheapo.com/events/nagatoro-fire-festival/ (festival extérieur)

Outils : Chrome DevTools, JavaScript DOM analysis, fetch() pour vérification HTML brut.

---

## Résultats

### Liens Google Maps

- **Présents** : NON (Google Maps)
- **Carte utilisée** : Apple Maps (MapKit JS)
- **Lien visible** : "Open with Maps" (lien Apple Maps, dans `.section--map__map-link a`)
- **Important** : Le lien Apple Maps n'est PAS une source fiable pour l'extraction GPS directe. Utiliser le JSON embarqué à la place.

---

### Source GPS Principale : JSON Embarqué dans le HTML ✅

**C'est la méthode recommandée.** Les coordonnées GPS sont dans le HTML source initial (pas générées par JavaScript).

**Structure HTML** :
```html
<section id="map" class="section--map section-block section--map--event section-block--large">
  <div async-component="1" id="map" delay="1200" component-name="apple-maps">
    <script type="application/json">{
      "heading": "<h3>Location Map:<\/h3>",
      "lat": "35.663006829689216",
      "lng": "139.66941913883585",
      "zoom": 17,
      "dispaddr": "2-33-12 Kitazawa, Setagaya-ku, Tokyo",
      "addr": "2-33-12 Kitazawa, Setagaya-ku, Tokyo",
      "tel": "",
      "min_zoom": 7,
      "max_zoom": 21,
      "title": "Shimokita Senrogai Open Space",
      "locations": [
        [
          "Shimokita Senrogai Open Space",
          "35.663006829689216",
          "139.66941913883585",
          "2-33-12 Kitazawa, Setagaya-ku, Tokyo",
          "2-33-12 Kitazawa, Setagaya-ku, Tokyo",
          "",
          "https://cdn.cheapoguides.com/.../marker-icon.png",
          2,
          "https://maps.apple.com/?..."
        ]
      ],
      "tokenId": "...",
      "jsFile": "...",
      "cssFile": "..."
    }</script>
  </div>
</section>
```

**Sélecteurs CSS valides (tous équivalents)** :
- `[component-name="apple-maps"] script[type="application/json"]`
- `#map[async-component] script[type="application/json"]`
- `.section--map script[type="application/json"]`

**Structure JSON** :
| Champ | Type | Description |
|-------|------|-------------|
| `lat` | string | Latitude (ex: "35.660373") |
| `lng` | string | Longitude (ex: "139.729230") |
| `title` | string | Nom du lieu/venue |
| `addr` | string | Adresse complète |
| `dispaddr` | string | Adresse affichée (= addr en général) |
| `tel` | string | Téléphone du lieu |
| `zoom` | int/string | Niveau de zoom de la carte |
| `locations` | array | Tableau de lieux (multi-venues possibles) |

**Structure de `locations[i]`** :
```
[0] name      → Nom du lieu
[1] lat       → Latitude (string)
[2] lng       → Longitude (string)
[3] addr      → Adresse complète
[4] dispaddr  → Adresse affichée
[5] tel       → Téléphone
[6] icon_url  → URL icône marqueur
[7] index     → Index interne
[8] map_link  → Lien Apple Maps
```

---

### Cartes Intégrées

- **Type de carte** : Apple Maps via MapKit JS (PAS Google Maps, PAS Leaflet, PAS Mapbox)
- **Localisation** : `<div async-component="1" component-name="apple-maps">` dans `<section class="section--map">`
- **Mode de chargement** : La carte est rendue côté client par JavaScript, mais les **données GPS sont déjà dans le HTML source**
- **Accessible par BeautifulSoup** : ✅ OUI - confirmé par fetch() du HTML brut

---

### Données Structurées JSON-LD

- **Format** : JSON-LD (Schema.org)
- **Types présents** : Event, Article, WebPage, WebSite, Organization
- **GPS dans JSON-LD** : ❌ NON - le JSON-LD de type `Event` contient l'adresse textuelle mais PAS de coordonnées GPS

**JSON-LD Event (extrait)** :
```json
{
  "@type": "Event",
  "name": "Shimokitazawa Flea Market",
  "location": [{
    "@type": "Place",
    "name": "Shimokitazawa",
    "address": {
      "@type": "PostalAddress",
      "addressCountry": "Japan",
      "addressLocality": "Shimokitazawa",
      "addressRegion": "Western Tokyo"
    }
  }]
}
```

Le JSON-LD Event peut servir de **fallback** pour récupérer l'adresse textuelle quand le JSON apple-maps est absent.

---

### Adresses Textuelles

- **Localisation** : Section `.section--info-box--event` avec éléments `.section--info-box__attribute`
- **Champs disponibles** : Venue (lien), Area, Access (stations métro), Dates, Entry, Categories

**HTML exemple** :
```html
<div class="section--info-box__attribute">
  <div class="section--info-box__label">Venue</div>
  <div class="section--info-box__value">
    <a href="https://tokyocheapo.com/place/shimokita-senrogai-open-space/">
      Shimokita Senrogai Open Space
    </a>
  </div>
</div>
<div class="section--info-box__attribute">
  <div class="section--info-box__label">Area</div>
  <div class="section--info-box__value">
    <a href="...">Shimokitazawa</a>
  </div>
</div>
```

**Sélecteur BeautifulSoup pour le venue** :
```python
# Venue name
venue_label = soup.find('div', class_='section--info-box__label', string='Venue')
if venue_label:
    venue_value = venue_label.find_next_sibling('div', class_='section--info-box__value')
    venue_name = venue_value.get_text(strip=True)
```

---

### Quand les GPS sont Absents

Les GPS ne sont **pas disponibles** quand l'événement n'a pas d'adresse précise :
- Pas de section `.section--map` dans le HTML
- Le JSON-LD `location` ne contient qu'un quartier (ex: "Edogawa") sans adresse de rue
- Exemple : Tokyo River Clean-Up → location = "Edogawa" (bénévolat dans une rivière, pas de lieu fixe)
- Cause : Ces événements n'ont pas de venue assigné dans le CMS

---

## Exemples Testés

### 1. Roppongi Crossing 2025 (Musée)
- **URL** : https://tokyocheapo.com/events/roppongi-crossing-2025-what-passes-is-time-we-are-eternal/
- **GPS trouvé** : ✅ Oui
- **lat** : 35.660373, **lng** : 139.729230
- **Venue** : Mori Art Museum, Roppongi Hills Mori Tower, 6-10-1 Roppongi, Minato-ku, Tokyo

### 2. Shimokitazawa Flea Market (Marché en plein air)
- **URL** : https://tokyocheapo.com/events/shimokitazawa-flea-market/
- **GPS trouvé** : ✅ Oui
- **lat** : 35.663006829689216, **lng** : 139.66941913883585
- **Venue** : Shimokita Senrogai Open Space, 2-33-12 Kitazawa, Setagaya-ku, Tokyo

### 3. Matsuda Cherry Blossom Festival (Festival dans un parc)
- **URL** : https://tokyocheapo.com/events/matsuda-cherry-blossom-festival/
- **GPS trouvé** : ✅ Oui
- **lat** : 35.35105618817873, **lng** : 139.1375249999872
- **Venue** : Nishihirabatake Park, 2951 Matsudasoryo, Matsuda, Ashigarakami District, Kanagawa

### 4. UNU Farmers Market (Marché universitaire)
- **URL** : https://tokyocheapo.com/events/unu-farmers-market/
- **GPS trouvé** : ✅ Oui
- **lat** : 35.662312, **lng** : 139.7082801
- **Venue** : United Nations University, 5-chōme-53-70 Jingūmae, Shibuya City

### 5. Tokyo River Clean-Up (Événement sans lieu précis)
- **URL** : https://tokyocheapo.com/events/tokyo-river-clean/
- **GPS trouvé** : ❌ Non
- **Raison** : Événement de bénévolat sans venue fixe, seul quartier "Edogawa" disponible
- **Fallback** : Adresse textuelle dans JSON-LD → "Edogawa"

### 6. Ohi Racecourse Flea Market (Hippodrome)
- **URL** : https://tokyocheapo.com/events/ohi-racecourse-flea-market/
- **GPS trouvé** : ✅ Oui
- **lat** : 35.5937070, **lng** : 139.7447750
- **Venue** : Oi Racecourse, 140-0012 Tokyo, Shinagawa, Katsushima

### 7. Nagatoro Fire Festival (Festival extérieur)
- **URL** : https://tokyocheapo.com/events/nagatoro-fire-festival/
- **GPS trouvé** : ✅ Oui
- **lat** : 36.09130456030866, **lng** : 139.10225198650747
- **Venue** : Hodosan Ropeway, 〒369-1305, 1766-1 Nagatoro, Chichibu District, Saitama

---

## Recommandations

### Méthode Principale : Parser le JSON apple-maps

Le JSON est dans le HTML initial → BeautifulSoup peut le lire sans Selenium.

**Sélecteur BeautifulSoup (recommandé)** :
```python
map_div = soup.find('div', {'component-name': 'apple-maps'})
# ou alternatifs :
map_div = soup.find('div', attrs={'component-name': 'apple-maps'})
map_div = soup.select_one('[component-name="apple-maps"]')
```

---

## Code Proposé

### Modification de `scraper_tokyo_cheapo.py`

```python
import json

def scrape_detail_page(self, url: str, soup) -> dict:
    """Extrait les données complètes depuis une page de détail Tokyo Cheapo."""
    
    event = {}
    lat, lon = None, None
    
    # ============================================================
    # MÉTHODE PRINCIPALE : JSON apple-maps (dans le HTML source)
    # Accessible par BeautifulSoup sans JavaScript/Selenium
    # ============================================================
    
    # Cherche le div avec component-name="apple-maps"
    map_div = soup.find('div', {'component-name': 'apple-maps'})
    
    if map_div:
        # Cherche le script JSON à l'intérieur
        json_script = map_div.find('script', {'type': 'application/json'})
        
        if json_script and json_script.string:
            try:
                map_data = json.loads(json_script.string)
                
                # Extraction des coordonnées GPS
                lat_str = map_data.get('lat')
                lon_str = map_data.get('lng')
                
                if lat_str and lon_str:
                    lat = float(lat_str)
                    lon = float(lon_str)
                
                # Extraction bonus : venue et adresse
                if not event.get('venue_name'):
                    event['venue_name'] = map_data.get('title', '')
                if not event.get('address'):
                    event['address'] = map_data.get('addr', '')
                if not event.get('telephone'):
                    event['telephone'] = map_data.get('tel', '')
                
                # Si plusieurs lieux (locations array), on peut les itérer
                # locations[i] = [name, lat, lng, addr, dispaddr, tel, icon, index, map_link]
                
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"[WARN] Erreur parsing JSON map pour {url}: {e}")
    
    # ============================================================
    # FALLBACK 1 : JSON-LD Schema.org Event
    # Donne l'adresse textuelle mais PAS les GPS
    # Utile pour récupérer venue_name et address quand pas de carte
    # ============================================================
    if not lat or not event.get('venue_name'):
        for script in soup.find_all('script', {'type': 'application/ld+json'}):
            try:
                ld_data = json.loads(script.string)
                if ld_data.get('@type') == 'Event':
                    locations = ld_data.get('location', [])
                    if locations and isinstance(locations, list):
                        place = locations[0]
                        if not event.get('venue_name'):
                            event['venue_name'] = place.get('name', '')
                        if not event.get('address'):
                            addr_obj = place.get('address', {})
                            parts = [
                                addr_obj.get('streetAddress', ''),
                                addr_obj.get('addressLocality', ''),
                                addr_obj.get('addressRegion', ''),
                                addr_obj.get('addressCountry', '')
                            ]
                            event['address'] = ', '.join(p for p in parts if p)
                    break
            except (json.JSONDecodeError, TypeError, AttributeError):
                continue
    
    # ============================================================
    # FALLBACK 2 : Ancien code (liens Google Maps)
    # Gardé pour compatibilité, mais normalement inutile
    # car le site n'utilise PAS Google Maps
    # ============================================================
    if not lat:
        map_links = soup.find_all('a', href=True)
        for link in map_links:
            href = link['href']
            if 'google.com/maps' in href or 'maps.google.com' in href:
                gps_extractor = GPSExtractor()
                extracted_lat, extracted_lon = gps_extractor.extract_from_google_maps_url(href)
                if extracted_lat:
                    lat = extracted_lat
                    lon = extracted_lon
                    break
    
    # Assignation finale des coordonnées GPS
    event['latitude'] = lat
    event['longitude'] = lon
    
    return event
```

---

## Notes Techniques

1. **BeautifulSoup compatible** : Le JSON est dans le HTML initial, pas généré dynamiquement. Confirmé par XMLHttpRequest sur le HTML brut.

2. **Coordonnées en string** : Les lat/lng sont des strings dans le JSON (`"35.663006"`), pas des floats. Convertir avec `float()`.

3. **Disponibilité** : La section `.section--map` n'apparaît que si l'événement a un venue avec adresse précise. Si elle est absente, pas de GPS possible par cette méthode.

4. **Apple Maps vs Google Maps** : Le site a migré de Google Maps vers Apple Maps MapKit JS. L'ancien code cherchant `google.com/maps` ne fonctionne donc plus.

5. **Multi-venues** : Certains événements pourraient avoir plusieurs lieux dans `locations[]`. Utiliser `data['lat']` / `data['lng']` pour le lieu principal.

6. **Rate limiting** : Garder le rate limit de 0.5s entre requêtes pour respecter le site.

---

## Couverture GPS Estimée

| Catégorie | GPS attendu | Raison |
|-----------|-------------|--------|
| Musées, salles, venues | ✅ ~95% | Toujours une adresse précise |
| Marchés, festivals avec lieu fixe | ✅ ~90% | Venue assigné |
| Événements en plein air (parc) | ✅ ~85% | Généralement un parc avec adresse |
| Bénévolat, événements itinérants | ❌ ~20% | Pas de venue fixe |
| Événements "Online" | ❌ 0% | Pas de lieu physique |

**Estimation globale** : **~75-85%** de couverture GPS pour les événements Tokyo Cheapo (contre 1.7% actuellement).
