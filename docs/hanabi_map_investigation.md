# Investigation: Hanabi Map.html Pages for Coordinate Extraction

**Date:** 2026-02-15 01:23:17
**Objectif:** Analyser si les pages `/map.html` des événements hanabi contiennent des données de coordonnées géographiques exploitables.

## Résumé Exécutif

- **Événements testés:** 2
- **Pages map.html existantes:** 2/2 (100.0%)
- **Coordonnées trouvées:** 2/2 (100.0% des pages existantes)
- **Correspondance avec coords existantes:** 0/2

## Méthodes d'Extraction Détectées

- **google_maps_iframe**: 2 occurrences

## Résultats Détaillés


### Without Coords

#### 横浜ナイトフラワーズ2025

- **Event ID:** `ar0314e541039`
- **Coordonnées existantes:** Aucune
- **Page map.html:** ✅ Existe
- **Coordonnées trouvées:** (35.45753, 139.642916)
- **Méthodes d'extraction:** google_maps_iframe

#### よみうりランド 花火＆大迫力噴水ショー

- **Event ID:** `ar0313e335967`
- **Coordonnées existantes:** Aucune
- **Page map.html:** ✅ Existe
- **Coordonnées trouvées:** (35.62494, 139.517534)
- **Méthodes d'extraction:** google_maps_iframe


## Recommandations

### ✅ Implémentation Recommandée

Les pages map.html contiennent des coordonnées exploitables. Il est recommandé d'intégrer cette extraction dans le scraper.

**Actions suggérées:**
1. Ajouter une méthode `_scrape_map_page()` dans `src/scraper_hanabi_kanto.py`
2. Appeler cette méthode pendant l'enrichissement des détails
3. Utiliser les méthodes d'extraction suivantes (par ordre de fiabilité):
   - google_maps_iframe

4. Comparer avec les coordonnées existantes (Google Maps links) pour validation
5. Mettre à jour la base de données avec les nouvelles coordonnées

**Impact estimé:** +2/2 événements avec coordonnées (100.0% d'amélioration)
