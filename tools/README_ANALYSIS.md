# Guide d'Analyse du HTML

## Fichiers disponibles

- `download_html.py` - Télécharge le HTML brut
- `analyze_html.sh` - Analyse automatique basique
- HTML sauvegardé dans `data/html_pages/`

## Structure identifiée

D'après l'analyse, les festivals sont dans des balises **`<h2 class="wp-block-heading">`** avec le format :
```
NOM DU FESTIVAL (DATES)
```

## Commandes utiles

### 1. Trouver tous les titres de festivals
```bash
grep -o '<h2 class="wp-block-heading">[^<]*</h2>' data/html_pages/festivals_mars_2025.html
```

### 2. Extraire juste le texte des titres
```bash
grep -o '<h2 class="wp-block-heading">[^<]*</h2>' data/html_pages/festivals_mars_2025.html | sed 's/<[^>]*>//g'
```

### 3. Trouver le contexte autour d'un festival spécifique
```bash
grep -A 10 -B 2 'MARATHON DE TOKYO' data/html_pages/festivals_mars_2025.html
```

### 4. Chercher les paragraphes après les h2
```bash
grep -A 5 '<h2 class="wp-block-heading">' data/html_pages/festivals_mars_2025.html | grep '<p>'
```

### 5. Compter les festivals
```bash
grep -c '<h2 class="wp-block-heading">' data/html_pages/festivals_mars_2025.html
```

### 6. Chercher les balises Instagram (posts)
```bash
grep -c 'instagram-media' data/html_pages/festivals_mars_2025.html
```

### 7. Extraire une section spécifique
```bash
# Tout entre MARATHON DE TOKYO et IRUGI-JINJA
sed -n '/MARATHON DE TOKYO/,/IRUGI-JINJA/p' data/html_pages/festivals_mars_2025.html
```

### 8. Chercher les liens vers des sites web
```bash
grep -o 'href="http[^"]*"' data/html_pages/festivals_mars_2025.html | head -20
```

### 9. Analyser la structure autour d'un festival
```bash
# Regarder 20 lignes avant et 20 après "MARATHON DE TOKYO"
grep -A 20 -B 20 'MARATHON DE TOKYO' data/html_pages/festivals_mars_2025.html
```

### 10. Filtrer le bruit (éléments de navigation)
```bash
# Tout sauf les h2 contenant "Articles similaires", "Recherche", etc.
grep '<h2 class="wp-block-heading">' data/html_pages/festivals_mars_2025.html | grep -v 'Articles similaires\|Recherche\|Mon Livre'
```

## Observations clés

1. **Titres** : `<h2 class="wp-block-heading">NOM (DATES)</h2>`
2. **Bruit** : Les h2 "Articles similaires", "Recherche", etc. doivent être filtrés
3. **Descriptions** : Probablement dans les `<p>` qui suivent les `<h2>`
4. **Posts Instagram** : Balises `instagram-media` (16 trouvées)
5. **Localisation** : À trouver dans les paragraphes suivant les titres

## Pour analyser plus en profondeur

```bash
# Ouvrir le fichier HTML dans un éditeur
code data/html_pages/festivals_mars_2025.html

# Ou le visualiser avec less
less data/html_pages/festivals_mars_2025.html

# Chercher un pattern spécifique de manière interactive
grep -i 'votre_recherche' data/html_pages/festivals_mars_2025.html | less
```

## Prochaines étapes

Une fois que vous avez identifié la structure exacte :
1. Notez les patterns HTML
2. Mettez à jour `src/scraper_festivals_tokyo.py` avec le bon parsing
3. Testez avec `uv run tests/test_mars_debug.py`
