# RAPPORT D'ANALYSE DE SCRAPING
## Site: hanabi.walkerplus.com/list/ar0300/ (Région 関東)

---

## 1. STRUCTURE GÉNÉRALE DU SITE

**URL cible:** `https://hanabi.walkerplus.com/list/ar0300/`

**Points importants:**
- ✅ Les données sont **chargées côté serveur (SSR)** - Pas de JavaScript requis pour le contenu principal
- ✅ Pas de pagination observable - Tous les éléments semblent chargés sur une seule page
- ✅ Structure HTML claire et prévisible avec des éléments génériques `<generic>`
- ✅ Les données des feux d'artifice sont organisées par **préfecture** (都道府県)
- ⚠️ Les données sont récupérables facilement sans JavaScript lourd

---

## 2. ORGANISATION DES DONNÉES PAR RÉGION (関東)

**Préfectures incluses dans ar0300 (関東):**
- 東京都 (Tokyo) - ar0313
- 神奈川県 (Kanagawa) - ar0314
- 千葉県 (Chiba) - ar0312
- 埼玉県 (Saitama) - ar0311
- 群馬県 (Gunma) - ar0310
- 栃木県 (Tochigi) - ar0309
- 茨城県 (Ibaraki) - ar0308

**Observation:** Chaque événement a un URL unique avec format: `/detail/[region_code][event_id]/`

---

## 3. STRUCTURE HTML DES LISTES (À SCRAPER)

**Architecture générale:**
```html
<main>
  <region>
    <list>  <!-- Liste par préfecture -->
      <listitem>
        <heading>東京都</heading>
        <list>  <!-- Cartes d'événements -->
          <listitem>
            <link href="/detail/ar0313e335967/">
              <image>...</image>
              <generic>稲城市</generic>  <!-- Localisation -->
              <generic>よみうりランド 花火＆大迫力噴水ショー</generic>  <!-- Titre -->
              <generic>2026年1月17日(土)・24日(土)...</generic>  <!-- Dates -->
            </link>
          </listitem>
          <!-- Plus de cartes... -->
        </list>
      </listitem>
    </list>
  </region>
</main>
```

---

## 4. DONNÉES EXTRAIBLES PER ÉVÉNEMENT

**Depuis la liste principale (list view):**
- ✅ **Titre** (name): `<generic>` contenant le nom de l'événement
- ✅ **Localisation** (location): `<generic>` avec ville/arrondissement
- ✅ **Dates** (dates): `<generic>` avec format "2026年1月17日(土)・24日(土)・31日(土)..."
- ✅ **URL détail** (detail_url): `<link href="/detail/[code]/"`
- ✅ **Image** (thumbnail): `<image src=...>`
- ✅ **Code région** (region_code): Extrait de l'URL `/list/ar0[XXX]/`
- ✅ **Code événement** (event_id): Extrait de `/detail/ar0313e335967/` → `ar0313e335967`

**Depuis la page de détail (/detail/...):**
- ✅ **Heure de début** (start_time): Page de détail → "19:15～19:25"
- ✅ **Nombre de feux d'artifice** (fireworks_count): Page détail data.html → "1日1200発×5日間で、延べ6000発"
- ✅ **Statut** (status): "中止", "非開催", ou données normales
- ✅ **Adresse complète** (full_address): Page détail
- ✅ **Accès/Transport** (access_info): Page détail
- ✅ **Parking** (parking): Page détail
- ✅ **Contact** (contact): Page détail
- ✅ **Site officiel** (official_website): Page détail

---

## 5. STRUCTURE DES SÉLECTEURS CSS/XPATH

**Pour la liste principale:**

| Données | Sélecteur | Type | Exemple |
|---------|-----------|------|---------|
| Toutes les cartes | `main li > a[href*="/detail/"]` ou `li:has(a[href*="/detail/"])` | XPath | Pour boucler sur les événements |
| Titre | `.closest('li')` puis `generic` (texte long) | Texte | "よみうりランド 花火＆大迫力噴水ショー" |
| Localisation | `.closest('li')` puis `generic` (texte court) | Texte | "稲城市" |
| Dates | `.closest('li')` puis `generic:contains("年")` | Texte | "2026年1月17日(土)..." |
| URL détail | `a[href*="/detail/"]` → `href` | Attribut | "/detail/ar0313e335967/" |
| Image | `img[src*="..."]` | Attribut | URL de l'image |

---

## 6. ARCHITECTURE DE SCRAPING RECOMMANDÉE

**Approche hybride en 2 étapes:**

### **Étape 1: Scraper la liste (Requests + BeautifulSoup)**
```python
# Pseudo-code
1. GET https://hanabi.walkerplus.com/list/ar0300/
2. Parser avec BeautifulSoup
3. Trouver toutes les <li> contenant les liens "/detail/"
4. Extraire: titre, localisation, dates, event_id
5. Constituer la liste des URLs détail pour étape 2
```

### **Étape 2: Scraper les détails (Requests + BeautifulSoup)**
```python
# Pseudo-code
1. Pour chaque événement trouvé en étape 1
2. GET https://hanabi.walkerplus.com/detail/[event_id]/
3. Extraire les infos principales (heure, description)
4. GET https://hanabi.walkerplus.com/detail/[event_id]/data.html
5. Extraire les détails (nombre de feux, accès, parking, etc.)
6. Sauvegarder dans la base de données
```

---

## 7. CONSIDÉRATIONS IMPORTANTES

**Rate Limiting:**
- ⚠️ Robots.txt existe mais le sitemap est accessible → respecter un délai entre les requêtes (0.5-1s minimum)
- La page ne semble pas avoir de protection CAPTCHA visible

**Pagination et Chargement Dynamique:**
- ✅ Pas de pagination observable → tout est sur une seule page
- ✅ Pas de "load more" button
- ✅ Pas de chargement asynchrone (AJAX) pour le contenu initial
- ⚠️ Vérifier le sitemap pour une liste complète: `https://hanabi.walkerplus.com/sitemap.xml`

**Particularités des données:**
- Les dates peuvent avoir plusieurs formats: "2025年7月26日(土)" ou "2026年1月17日(土)・24日(土)・31日(土)..."
- Le statut "中止" (annulé) ou "非開催" peut apparaître dans le titre
- Certains événements n'ont pas d'images (placeholder possible)
- Les URLs détail suivent un pattern: `/detail/[region_code][event_id]/`

**Cookies et Headers:**
- ✅ Pas d'authentification requise
- ✅ Pas de cookies de session critiques
- ⚠️ User-Agent recommandé pour éviter les blocages

---

## 8. EXEMPLE DE DONNÉES À EXTRAIRE

**Événement type (liste):**
```json
{
  "title": "よみうりランド 花火＆大迫力噴水ショー",
  "location": "稲城市",
  "prefecture": "東京都",
  "dates_raw": "2026年1月17日(土)・24日(土)・31日(土)、2月7日(土)・14日(土)",
  "event_id": "ar0313e335967",
  "region_code": "ar0313",
  "url": "/detail/ar0313e335967/",
  "thumbnail": "https://...",
  "status": "scheduled"
}
```

**Événement type (détail):**
```json
{
  "title": "よみうりランド 花火＆大迫力噴水ショー",
  "fireworks_count": "1日1200発×5日間で、延べ6000発",
  "start_time": "19:15",
  "end_time": "19:25",
  "duration_minutes": 10,
  "venue": "よみうりランド",
  "prefecture": "東京都",
  "city": "稲城市",
  "full_address": "...",
  "access_info": "【電車】京王電鉄京王よみうりランド駅...",
  "parking": "2000台普通車",
  "parking_fee": "平日1500円、土日祝2000円",
  "contact": "044-966-1111",
  "official_site": "https://...",
  "weather_rainy_day_policy": "荒天時は翌日に順延、翌日も荒天の場合は中止",
  "paid_seats": false,
  "food_stalls": true
}
```

---

## 9. POINTS DE VIGILANCE POUR LE CODE

1. **Parsing des dates:** Format variable (単一 vs 複数 dates) → regex flexible
2. **Extraction du code région:** À partir de l'URL (ar0300 = 関東 / ar0313 = 東京都)
3. **Gestion des statuts:** Vérifier la présence de "中止", "非開催", "開催予定"
4. **URLs relatives:** Les URLs dans le HTML sont relatives (`/detail/...`) → ajouter le domaine
5. **Encoding:** Page en UTF-8, bien gérer les caractères japonais
6. **Timeouts:** Certaines pages peuvent être lentes → définir des timeouts appropriés (10s minimum)

---

## 10. TÂCHES RECOMMANDÉES POUR LE SCRIPT

1. ✅ Créer une fonction pour parser la liste `/list/ar0300/`
2. ✅ Créer une fonction pour scraper les détails `/detail/[id]/`
3. ✅ Créer une fonction pour parser les dates (regex pour géométrie variable)
4. ✅ Implémenter une sauvegarde en base de données (SQLite ou JSON)
5. ✅ Ajouter un système de log et de gestion d'erreurs
6. ✅ Respecter les délais entre requêtes (0.5-1s minimum)
7. ✅ Ajouter un système de cache pour éviter les requêtes redondantes
8. ✅ Gérer les cas "en annulé" vs "prévu" vs "à confirmer"

---

## RÉSUMÉ EXÉCUTIF

- **Difficultés:** Basse ⭐ (structure HTML claire, pas de JavaScript lourd)
- **Temps d'exécution estimé:** 30-40s pour ~40-50 feux d'artifice (avec délais respectés)
- **Volume de données:** ~40-50 événements par région
- **Maintenance:** Faible (structure stable, pattern URLs cohérent)
- **Légalité:** Respecter robots.txt et limiter les requêtes (0.5-1s entre requêtes)