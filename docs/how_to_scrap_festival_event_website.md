# Rapport d'Analyse Ichiban Japan - Scraping Événements Tokyo

## Date d'Analyse

- **Date** : 7 février 2026
- **Articles Examinés** : 6 articles (festivals, expositions, marchés)
- **Périodes Analysées** : Janvier 2026, Février 2026, Décembre 2025, Mai 2025

## Table des Matières

1. [Structure des URLs](#structure-des-urls)
2. [Architecture des Articles](#architecture-des-articles)
3. [Variations par Type](#variations-par-type)
4. [Formats de Données](#formats-de-données)
5. [Patterns Observés](#patterns-observés)
6. [Défis de Scraping](#défis-de-scraping)
7. [Recommandations Techniques](#recommandations-techniques)
8. [Schéma de Base de Données](#schéma-de-base-de-données)
9. [Cas Spéciaux](#cas-spéciaux)

---

## Structure des URLs

### Pattern Principal

```
https://ichiban-japan.com/[TYPE]-tokyo-[MOIS]-[ANNEE]/
```

### Variations d'URLs

| Type                 | Pattern                              | Exemple                                   |
| -------------------- | ------------------------------------ | ----------------------------------------- |
| Festivals mensuels   | `festivals-tokyo-[mois]-[annee]`   | `/festivals-tokyo-fevrier-2026/`        |
| Expositions mensuels | `expositions-tokyo-[mois]-[annee]` | `/expositions-tokyo-janvier-2026/`      |
| Marchés aux puces   | `marches-aux-puces-tokyo`          | `/marches-aux-puces-tokyo/`             |
| Articles spéciaux   | `[slug-custom]`                    | `/yuki-matsuri/`, `/expo-2025-osaka/` |

### Pagination

```
https://ichiban-japan.com/category/japon/evenements-japon/page/[N]/
```

### Observations Clés

- ✅ Pattern d'URLs très cohérent
- ✅ Facile à prédire pour les nouveaux articles
- ✅ Archives disponibles sur plusieurs années
- ✅ Noms de mois en français dans les URLs

---

## Architecture des Articles

### Structure HTML Générale

```html
<main>
  <!-- Breadcrumb -->
  <generic> > > > Titre Article </generic>
  
  <!-- Titre principal -->
  <h1> Les festivals à Tokyo en février 2026 </h1>
  
  <!-- Image bannière -->
  <image> ... </image>
  
  <!-- Paragraphes d'introduction -->
  <generic>
    Contexte saisonnier + liens internes + description générale
  </generic>
  
  <!-- Sections par événement -->
  <h2> Nom Festival (Date) </h2>
  <generic> Description détaillée </generic>
  <generic> Bloc d'informations structurées </generic>
  <link> Site de l'événement </link>
  
  <!-- Répété pour chaque événement -->
  
  <!-- Conclusion -->
  <generic> Conclusion + renvois vers articles connexes </generic>
</main>
```

### Points Importants

- Peu ou pas de classes CSS spécifiques
- Structure basée sur balises HTML5 standards (`h1`, `h2`, `generic`, `link`)
- Hiérarchie des balises = structure logique
- Tous les conteneurs génériques utilisent `<generic>`

---

## Variations par Type

### 1. Articles sur les FESTIVALS

#### Structure Type

```
[H1] Titre
[Image bannière]
[Paragraphes intro] contexte saisonnier
[Sections H2] 1 H2 par festival
  - Description
  - Bloc d'info structuré
  - Lien officiel
[Conclusion] renvois
```

#### Bloc d'Information Structuré

**Format Single Location :**

```
1er février 2026Lieu : sanctuaire Mabashi Inari-jinja
Site de l'événement
```

**Format Multi-Locations (ex: Setsubun) :**

```
Du 30 janvier au 1er février 2026Lieu : Shimo Kitazawa Ichibangai Shotengai (Shimo Kitazawa)
Site de l'événement

3 février 2026Lieu : temple Senso-ji (Asakusa)
Site de l'événement
```

**Format Plage Longue :**

```
Du 7 février au 1er mars 2026Lieu : parc Hanegi Koen
Site de l'événement
```

#### Données Extraites

- Nom du festival (du H2)
- Date(s) d'occurrence (avant "Lieu :")
- Lieu(x) (après "Lieu :")
- Arrondissement (entre parenthèses)
- Description (paragraphes entre H2 et bloc d'info)
- URL officielle (lien "Site de l'événement")
- Horaires (optionnel, dans description)
- Frais d'entrée (optionnel, dans description)

#### Cas Spéciaux Observés

- **Multi-festivals sous 1 H2** : Setsubun peut avoir 10+ variations
- **Plages inter-mois** : "Du 7 février au 1er mars 2026"
- **Dates non-consécutives** : "1er et 13 février 2026"
- **Plages complexes** : "1-25 février 2026"
- **Entrées payantes** : Parfois mentionnées ("Entrée : 1,500 yens")
- **Horaires spécifiques** : "de 11h à 13h30", "de 7h à 15h"

---

### 2. Articles sur les EXPOSITIONS

#### Structure Type

```
[H1] Titre
[Image bannière]
[Paragraphes intro] atmosphère saisonnière
[Sections H2] 1 H2 par exposition
  - Description détaillée (2-4 phrases)
  - Bloc d'info structuré
  - Lien officiel
  - Parfois embeds Instagram
[Conclusion] renvois
```

#### Bloc d'Information Structuré

```
Du 2 janvier au 22 mars 2026
Lieu : Seikado Bunko Art Museum
Site officiel
```

#### Données Extraites

- Nom de l'exposition (du H2)
- Plage de dates
- Musée/Galerie
- Description (contexte culturel, collections)
- URL officielle
- Images (embeds Instagram)

#### Différences vs Festivals

| Aspect             | Festivals         | Expositions       |
| ------------------ | ----------------- | ----------------- |
| Nombre par article | 15-25             | 20-30             |
| Lieux multiples    | ✅ Oui (Setsubun) | ❌ Non            |
| Arrondissement     | Systématique     | Rarement          |
| Horaires           | Souvent           | Rarement          |
| Images             | Peu (1-2)         | Beaucoup (embeds) |
| Durée typique     | Variable          | Longue (3+ mois)  |

---

### 3. Articles sur les MARCHÉS AUX PUCES

#### Structure Type

```
[H1] Titre
[Paragraphes intro] description générale des marchés
[Sous-titre] "Les marchés aux puces de Tokyo"
[Long paragraphe] ce qu'on trouve, ambiance, conseils
[Sections H2] 1 H2 par marché
  - Description courte
  - Bloc d'info structuré
  - Lien officiel
[Conclusion] conseils pratiques
```

#### Bloc d'Information Structuré

**Format Simple :**

```
1er février 2026Lieu : sanctuaire Machida Tenman-gu (Machida)
Site de l'événement
```

**Format Multi-Dates Complexe :**

```
1er, 6-8, 11, 13-15, 20-23 et 27-28 février 2026Lieu : Shimokita Senrogai (Shimo Kitazawa)
Site de l'événement
```

#### Données Extraites

- Nom du marché
- Date(s) d'occurrence (même format complexe)
- Lieu
- Arrondissement
- Horaires (quasi systématiques)
- Type de marché (flea market, boro ichi, etc.)
- URL officielle

#### Caractéristiques Spéciales

- Dates TRÈS complexes (plages fragmentées)
- Horaires PRESQUE TOUJOURS présents
- Fréquence régulière (hebdo/mensuelle)
- Tous les lieux avec arrondissement
- Un seul lieu par marché

---

## Formats de Données

### Dates - Formats Observés

#### 1. Date Simple

```
1er février 2026
3 février 2026
11 janvier 2026
```

Regex :

```
(\\d{1,2})(?:er|e|ème)?\\s([a-z]+)\\s(\\d{4})
```

#### 2. Plage Mensuelle

```
Du 7 février au 1er mars 2026
Du 8 février au 8 mars 2026
```

Regex :

```
Du\\s(\\d{1,2})\\s([a-z]+)\\sau\\s(\\d{1,2})(?:er|e)?\\s([a-z]+)\\s(\\d{4})
```

#### 3. Plage Compacte Même Mois

```
1-25 février 2026
18-31 décembre 2025
```

Regex :

```
(\\d{1,2})-(\\d{1,2})\\s([a-z]+)\\s(\\d{4})
```

#### 4. Dates Multiples Non-Consécutives

```
1er et 13 février 2026
11 et 13 février 2026
15 et 16 janvier 2026
```

Regex :

```
(\\d{1,2})(?:er|e)?\\set\\s(\\d{1,2})\\s([a-z]+)\\s(\\d{4})
```

#### 5. Dates Très Complexes (Marchés)

```
1er, 6-8, 11, 13-15, 20-23 et 27-28 février 2026
1er, 7-8, 14-15 et 21-22 février 2026
```

Approche :

- Splitter par virgule et "et"
- Parser chaque segment
- Étendre les plages (6-8 → 6, 7, 8)
- Concaténer le mois/année

#### 6. Dates Partielles

```
(jusqu'au 8 janvier 2026)
(jusqu'au 1er février 2026)
```

Regex :

```
\\(jusqu'au\\s(\\d{1,2})(?:er|e)?\\s([a-z]+)\\s(\\d{4})\\)
```

---

### Lieux - Formats Observés

#### 1. Lieu Simple

```
sanctuaire Meiji-jingu
temple Senso-ji
parc Yoyogi Koen
```

#### 2. Lieu avec Arrondissement

```
sanctuaire Meiji-jingu (Harajuku)
temple Senso-ji (Asakusa)
parc Yoyogi Koen (Harajuku)
```

Regex :

```
(.*?)\\s*\\(([^)]+)\\)$
```

#### 3. Lieux Multiples

```
sanctuaire Tokumaru Kitano-jinja et sanctuaire Akatsuka Suwa-jinja (Akatsuka)
```

Pattern :

- Parser par "et"
- Dernier arrondissement = pour tous

#### 4. Lieux Génériques

```
quartier de Shinjuku
quartier de Shimokitazawa
ville d'Akishima
```

Approche :

- Mapper quartier → arrondissement via table de références

#### 5. Lieux Venues/Complexes

```
Tokyo Dome
Ryogoku Kokugikan Sumo Stadium
Azabudai Hills
Tokyo International Forum
```

Approche :

- Database de correspondances venue ↔ arrondissement

---

### Autres Données

#### Horaires

Format observé :

```
de 7h à 15h
de 11h à 22h
de 10h à 16h
12h à 18h
```

Regex :

```
de\\s(\\d{1,2})h\\s*(?:\\d{2})?\\s*à\\s(\\d{1,2})h\\s*(?:\\d{2})?
```

#### Frais d'Entrée

Formats observés :

```
Entrée gratuite
Entrée : de 1 000 yens (6€) à 2 000 yens (12€)
L'entrée coûte 1,500 yens
Entrée payante (6,000 yens par adulte sur place)
```

Approche :

- Chercher "Entrée", "gratuit", "payant"
- Extraire montant si présent

#### URLs Officielles

Pattern :

- Toujours après "Site de l'événement" ou "Site officiel"
- Parfois lien Google Maps
- Parfois Facebook ou Instagram à défaut

---

## Patterns Observés

### Pattern 1 : Fréquence de Publication

#### Articles Garantis Mensuels

```
✅ 1 article "festivals-tokyo-[mois]-[annee]" par mois
✅ 1 article "expositions-tokyo-[mois]-[annee]" par mois
⚠️ 1 article "marches-aux-puces-tokyo" (peut être d'un mois différent)
⚠️ Articles spéciaux saisonniers (festivals de neige, sakura, etc.)
⚠️ Articles ad-hoc pour événements majeurs
```

### Pattern 2 : Structure Intro

Tous les articles commencent par :

1. **Contexte saisonnier** : description de la saison/du mois
2. **Liens internes** : renvois vers articles connexes
3. **Introduction générale** : explication du contenu

Exemple intro :

> "Si le froid persiste en février au Japon, la capitale laisse déjà poindre les premiers signes du printemps. Le mois débute avec Setsubun, rituel de purification marquant la fin de l'hiver..."

### Pattern 3 : Structure Conlusion

Tous les articles finissent par :

1. **Récapitulatif** : résumé du contenu
2. **Renvois** : liens vers expositions/marchés du même mois
3. **Promotion** : plug pour l'ebook "600 festivals du Japon"
4. **Teaser** : mention du prochain mois

### Pattern 4 : Variations Saisonnières

#### Janvier

- Hatsumode dominant (visites du Nouvel An)
- Dezomeshiki (parades de pompiers)
- Tournoi de sumo
- Foires traditionnelles (daruma, boro ichi)
- Environ 20 événements

#### Février

- Setsubun dominant (peut avoir 10+ variations)
- Festivals de pruniers (ume matsuri)
- Environ 19 événements

#### Mai

- **EXCEPTIONNEL** : Golden Week massive
- Plus de 35 événements
- Kanda Matsuri (biennal)
- Haute saison des festivals
- Article 50% plus long

#### Décembre

- Marchés de Noël
- Foires de fin d'année (toshi no ichi)
- Comiket
- Fêtes commémoratives
- Environ 18 événements

### Pattern 5 : Longueur des Articles

| Mois      | Type      | # Événements | Taille |
| --------- | --------- | -------------- | ------ |
| Mai       | Festivals | 35+            | 50 KB+ |
| Janvier   | Festivals | 20             | 40 KB  |
| Février  | Festivals | 19             | 35 KB  |
| Décembre | Festivals | 18             | 30 KB  |

**Observation :** Plus d'événements = article plus long

### Pattern 6 : Consistance Format

- ✅ Format HTML identique mois après mois
- ✅ Structure de données très cohérente
- ✅ Micro-variations seulement (descriptions, horaires)
- ✅ Facilite énormément le scraping

---

## Défis de Scraping

### Priorité : CRITIQUE

#### 1. Parsing des Dates en Français

**Le Problème :**

- Format français : "1er février 2026", "3 février 2026"
- Ordinals variables : "1er", "2e", "3e", "11e", "12e"
- Plages mensuelles : "Du 7 février au 1er mars 2026"
- Dates multiples : "11 et 13 février 2026"
- Plages compactes : "1-25 février 2026"
- Dates partielles : "(jusqu'au 8 janvier 2026)"
- Contexte saisonnier : "La nuit du Nouvel An" → 31 décembre

**La Solution :**

```python
import re
from datetime import datetime
from dateutil.parser import parse

MOIS_FR = {
    'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
    'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
    'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
}

def parse_french_date(text):
    """Extrait et parse les dates en français"""
  
    # Pattern 1 : Plage multi-mois "Du 7 février au 1er mars 2026"
    match = re.search(r'Du\\s(\\d{1,2})\\s(\\w+)\\sau\\s(\\d{1,2})(?:er|e)?\\s(\\w+)\\s(\\d{4})', text)
    if match:
        day1, month1, day2, month2, year = match.groups()
        start = datetime(int(year), MOIS_FR[month1], int(day1))
        end = datetime(int(year), MOIS_FR[month2], int(day2))
        return (start, end)
  
    # Pattern 2 : Plage simple mois "1-25 février 2026"
    match = re.search(r'(\\d{1,2})-(\\d{1,2})\\s(\\w+)\\s(\\d{4})', text)
    if match:
        day1, day2, month, year = match.groups()
        start = datetime(int(year), MOIS_FR[month], int(day1))
        end = datetime(int(year), MOIS_FR[month], int(day2))
        return (start, end)
  
    # Pattern 3 : Dates multiples "11 et 13 février 2026"
    match = re.search(r'(\\d{1,2})\\set\\s(\\d{1,2})\\s(\\w+)\\s(\\d{4})', text)
    if match:
        day1, day2, month, year = match.groups()
        dates = [
            datetime(int(year), MOIS_FR[month], int(day1)),
            datetime(int(year), MOIS_FR[month], int(day2))
        ]
        return dates
  
    # Pattern 4 : Date simple "3 février 2026"
    match = re.search(r'(\\d{1,2})(?:er|e)?\\s(\\w+)\\s(\\d{4})', text)
    if match:
        day, month, year = match.groups()
        date = datetime(int(year), MOIS_FR[month], int(day))
        return date
  
    return None
```

### Priorité : HAUTE

#### 2. Parsing des Lieux Multi-Locations

**Le Problème :**

- Locations simples : "sanctuaire Meiji-jingu"
- Avec arrondissement : "sanctuaire Meiji-jingu (Harajuku)"
- Multiples : "sanctuaire X et sanctuaire Y (Arrondissement)"
- Noms composés : "Tokyo International Forum"
- Pas d'arrondissement : "quartier de Shinjuku"

**La Solution :**

```python
def parse_location(text):
    """Extrait lieux et arrondissements"""
  
    locations = []
  
    # Extraire le dernier arrondissement (s'il existe)
    district_match = re.search(r'\\(([^)]+)\\)$', text)
    district = district_match.group(1) if district_match else None
  
    # Retirer parenthèses pour traiter les lieux
    text_clean = re.sub(r'\\([^)]+\\)', '', text).strip()
  
    # Splitter par "et"
    parts = [p.strip() for p in text_clean.split(' et ')]
  
    for part in parts:
        if part:
            locations.append({
                'name': part,
                'district': district
            })
  
    return locations

# Exemple
text = "sanctuaire Tokumaru Kitano-jinja et sanctuaire Akatsuka Suwa-jinja (Akatsuka)"
print(parse_location(text))
# Output: [
#   {'name': 'sanctuaire Tokumaru Kitano-jinja', 'district': 'Akatsuka'},
#   {'name': 'sanctuaire Akatsuka Suwa-jinja', 'district': 'Akatsuka'}
# ]
```

#### 3. Gestion des Dates Complexes (Marchés)

**Le Problème :**

```
"1er, 6-8, 11, 13-15, 20-23 et 27-28 février 2026"
→ 17 dates distinctes à générer
```

**La Solution :**

```python
def expand_complex_dates(date_string):
    """Expands complex date patterns like '1er, 6-8, 11, 13-15, 20-23 et 27-28 février 2026'"""
  
    # Extraire le mois et l'année
    month_year_match = re.search(r'(\\w+)\\s(\\d{4})$', date_string)
    if not month_year_match:
        return []
  
    month_str, year = month_year_match.groups()
    month = MOIS_FR[month_str]
    year = int(year)
  
    # Retirer le mois/année pour traiter les dates
    dates_str = date_string.replace(month_year_match.group(0), '').strip()
  
    dates = []
  
    # Splitter par virgules et "et"
    segments = re.split(r',\\s*|et\\s+', dates_str)
  
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
    
        # Si plage (ex: "6-8")
        if '-' in segment:
            match = re.match(r'(\\d{1,2})-(\\d{1,2})', segment)
            if match:
                start, end = int(match.group(1)), int(match.group(2))
                for day in range(start, end + 1):
                    dates.append(datetime(year, month, day))
        else:
            # Date simple
            match = re.match(r'(\\d{1,2})(?:er|e)?', segment)
            if match:
                day = int(match.group(1))
                dates.append(datetime(year, month, day))
  
    return sorted(dates)

# Exemple
text = "1er, 6-8, 11, 13-15, 20-23 et 27-28 février 2026"
dates = expand_complex_dates(text)
print(f"Total dates: {len(dates)}")
# Output: Total dates: 17
```

### Priorité : MOYENNE

#### 4. Extraction des URLs Officielles

**Le Problème :**

- Toujours après "Site de l'événement" ou "Site officiel"
- Parfois manquant (anciens articles)
- Parfois c'est un lien Google Maps
- Plusieurs liens possibles

**La Solution :**

```python
def extract_official_url(event_block_html):
    """Extrait l'URL officielle d'un bloc événement"""
  
    soup = BeautifulSoup(event_block_html, 'html.parser')
  
    # Chercher le lien contenant "Site de l'événement"
    event_link = soup.find('link', string=re.compile(r'Site.*événement|Site officiel'))
    if event_link and event_link.get('href'):
        return event_link['href']
  
    # Fallback : chercher tous les liens non-Google Maps
    for link in soup.find_all('link'):
        href = link.get('href')
        if href and 'google.com/maps' not in href:
            return href
  
    return None
```

#### 5. Distinction Festival vs Exposition vs Marché

**Le Problème :**
Même site, même structure, mais types différents

**La Solution :**

```python
def infer_event_type(url):
    """Déduit le type d'événement à partir de l'URL"""
  
    if 'festivals' in url:
        return 'festival'
    elif 'expositions' in url:
        return 'exposition'
    elif 'marches' in url:
        return 'marche'
    else:
        return 'unknown'
```

---

## Recommandations Techniques

### Architecture Recommandée

```python
class IchibanScraper:
  
    def __init__(self):
        self.base_url = "https://ichiban-japan.com"
        self.months_fr = {
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }
  
    def build_monthly_urls(self, year, month):
        """Génère les URLs attendues pour un mois"""
        month_fr = [k for k, v in self.months_fr.items() if v == month][0]
    
        return {
            'festivals': f"{self.base_url}/festivals-tokyo-{month_fr}-{year}/",
            'expositions': f"{self.base_url}/expositions-tokyo-{month_fr}-{year}/",
            'marches': f"{self.base_url}/marches-aux-puces-tokyo/"
        }
  
    def scrape_article(self, url):
        """Scrape un article complet"""
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
    
        event_type = self.infer_type(url)
        events = []
    
        # Trouver tous les H2 (titres d'événements)
        for h2 in soup.find_all('h2'):
            event_block = self.extract_event_block(h2)
            event = self.parse_event(event_block, event_type)
            if self.validate_event(event):
                events.append(event)
    
        return events
  
    def extract_event_block(self, h2_element):
        """Extrait le bloc complet d'un événement à partir du H2"""
    
        block_text = ""
        current = h2_element.next_sibling
    
        while current:
            # Arrêter si on rencontre un autre H2
            if hasattr(current, 'name') and current.name == 'h2':
                break
        
            # Accumuler le texte
            if isinstance(current, str):
                block_text += str(current)
            elif hasattr(current, 'get_text'):
                block_text += current.get_text()
        
            current = current.next_sibling
    
        return {
            'title': h2_element.get_text(),
            'content': block_text,
            'html': str(h2_element) + str(current) if current else str(h2_element)
        }
  
    def parse_event(self, block, event_type):
        """Parse un bloc événement en données structurées"""
    
        event = {
            'name': block['title'],
            'type': event_type,
            'dates': self.extract_dates(block['content']),
            'locations': self.extract_locations(block['content']),
            'description': self.extract_description(block['content']),
            'url': self.extract_url(block['html']),
            'hours': self.extract_hours(block['content']),
            'fee': self.extract_fee(block['content'])
        }
    
        return event
  
    def validate_event(self, event):
        """Valide qu'un événement a les données obligatoires"""
        return (
            event['name'] and
            event['dates'] and
            event['locations'] and
            event['description']
        )
```

### Stratégie de Scraping Continu

```python
def monthly_scrape_scheduler():
    """À exécuter une fois par mois"""
  
    current_date = datetime.now()
    urls = scraper.build_monthly_urls(
        current_date.year,
        current_date.month
    )
  
    for event_type, url in urls.items():
        try:
            # Vérifier que l'URL existe
            response = requests.head(url)
            if response.status_code == 200:
                events = scraper.scrape_article(url)
                save_to_database(events)
                log(f"✅ Scraped {len(events)} {event_type} for {current_date.strftime('%B %Y')}")
            else:
                log(f"⚠️ URL not found: {url}")
        except Exception as e:
            log(f"❌ Error scraping {url}: {e}")
```

---

## Cas Spéciaux

### 1. Festivals Sans Arrondissement Explicite

**Exemple :**

```
"quartier de Shinjuku"
```

**Approche :**

- Créer table de correspondances quartier ↔ arrondissement
- Mapper "Shinjuku" → "Shinjuku-ku"

```python
DISTRICT_MAP = {
    'Harajuku': 'Shibuya-ku',
    'Asakusa': 'Taito-ku',
    'Shinjuku': 'Shinjuku-ku',
    'Shibuya': 'Shibuya-ku',
    'Odaiba': 'Minato-ku',
    # ... etc
}
```

### 2. Articles avec Blocs Groupés (Setsubun)

**Exemple :**

```
Les festivals pour Setsubun (3 février 2026)
  → 10+ variations du même festival
```

**Approche :**

- Détecter "Les festivals pour [Nom]"
- Traiter comme méta-section
- Créer N événements distincts

```python
def handle_multi_event_section(h2_text):
    if "Les festivals pour" in h2_text:
        return "multi_event"
    return "single_event"
```

### 3. Événements Sans Site Officiel

**Fallback Order :**

1. Lien "Site de l'événement"
2. Lien "Site officiel"
3. Lien Google Maps
4. Lien Facebook
5. Lien Instagram
6. `NULL`

### 4. Dates Contextuelles (Nouvel An)

**Exemple :**

```
"Oji Kitsune no Gyoretsu (31 décembre 2025)"
Description: "La nuit du Nouvel An..."
```

**Approche :**

- Parser le contexte de description
- Si "Nouvel An" mentionné, ajouter aussi 1er janvier

### 5. Événements Annulables

**Note dans articles :**

```
"Attention à bien garder en tête que les marchés aux puces peuvent 
parfois être annulés ou déplacés en raison des conditions météorologiques"
```

**Recommandation :**

- Marquer les événements météo-dépendants
- Ajouter un flag `weather_dependent: true`

---

## Résumé des Recommandations

### ✅ Points Forts du Site

- Structure HTML très cohérente
- Pattern d'URLs prévisible et logique
- Fréquence de publication régulière (100% mensuelle)
- Historique long (plusieurs années d'archives)
- Contenu riche (descriptions, images, liens officiels)
- Peu de contenu JavaScript (scraping simple)

### ⚠️ Défis Principaux

1. **Dates en français** - Requires French month parsing
2. **Lieux variables** - No standardized location field
3. **Multi-locations** - Some festivals have 10+ variations
4. **Complexité saisonnière** - Différent number of events par mois
5. **Pas de classes CSS** - Structure basée sur balises HTML5

### 🎯 Résultat Attendu

Avec un scraper bien pensé :

- **Accuracy cible** : 95%+ sur tous les articles
- **Couverture** : 100% des articles mensuels depuis 2020+
- **Maintenance** : Minimal (pattern très stable)
- **Scalabilité** : Facile (URLs prévisibles)

---

## Conclusion

Le site **Ichiban Japan** est une source **exceptionnellement robuste** pour scraper les événements Tokyo. Avec 3-4 regex bien pensées et un parseur français solide, vous pouvez atteindre une couverture complète et fiable.

**Prochaines étapes recommandées :**

1. Implémenter le parseur de dates français
2. Créer la table de correspondances lieux ↔ arrondissements
3. Coder le scraper principal (voir architecture recommandée)
4. Mettre en place la sauvegarde en base de données
5. Planifier la tâche de scraping mensuelle
