#!/bin/bash
# Script d'analyse du HTML téléchargé

HTML_FILE="data/html_pages/festivals_mars_2025.html"

echo "==============================================="
echo "ANALYSE DU HTML - Mars 2025"
echo "==============================================="

# Vérifier que le fichier existe
if [ ! -f "$HTML_FILE" ]; then
    echo "❌ Fichier non trouvé: $HTML_FILE"
    echo "💡 Exécutez d'abord: uv run tools/download_html.py"
    exit 1
fi

echo ""
echo "📊 Informations générales:"
echo "  Taille: $(wc -c < "$HTML_FILE") octets"
echo "  Lignes: $(wc -l < "$HTML_FILE")"
echo ""

# Rechercher les titres h2, h3, h4
echo "🔍 Recherche des titres (h2, h3, h4):"
echo "  H2: $(grep -c '<h2' "$HTML_FILE")"
echo "  H3: $(grep -c '<h3' "$HTML_FILE")"
echo "  H4: $(grep -c '<h4' "$HTML_FILE")"
echo ""

# Rechercher les noms en MAJUSCULES (pattern des festivals)
echo "🎌 Premiers titres trouvés (10 premiers):"
grep -o '<h[234][^>]*>[^<]*</h[234]>' "$HTML_FILE" | head -20 | nl
echo ""

# Rechercher les classes courantes
echo "📦 Classes CSS les plus fréquentes:"
grep -o 'class="[^"]*"' "$HTML_FILE" | sort | uniq -c | sort -rn | head -15
echo ""

# Rechercher les éléments article
echo "📰 Éléments <article>:"
echo "  Nombre: $(grep -c '<article' "$HTML_FILE")"
echo ""

# Rechercher les sections
echo "📂 Éléments <section>:"
echo "  Nombre: $(grep -c '<section' "$HTML_FILE")"
echo ""

# Rechercher les div avec id ou class contenant "festival", "event", "content"
echo "🎯 Divs potentiellement intéressantes (id/class avec 'festival', 'event', 'content', 'entry'):"
grep -i 'class="[^"]*\(festival\|event\|content\|entry\|post\)[^"]*"' "$HTML_FILE" | head -10
echo ""

echo "==============================================="
echo "💡 Pour plus d'analyses, utilisez:"
echo "   grep 'pattern' $HTML_FILE"
echo "   grep -A 5 'pattern' $HTML_FILE  # 5 lignes après"
echo "   grep -B 5 'pattern' $HTML_FILE  # 5 lignes avant"
echo "==============================================="
