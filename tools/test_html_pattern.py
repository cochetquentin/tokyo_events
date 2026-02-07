"""
Script de test pour valider le pattern HTML des pages d'expositions
Pattern observé: H2 → embed (iframe/div/figure) → p (description) → p (métadonnées)
"""

import sys
import os

# Fix encoding issues on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
import requests
import re


def analyze_exposition_structure(url):
    """
    Analyse la structure HTML d'une page d'exposition
    pour valider le pattern observé
    """
    print(f"📥 Analyse de: {url}\n")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

    soup = BeautifulSoup(response.content, 'html.parser')
    h2_elements = soup.find_all('h2', class_='wp-block-heading')

    # Filtrer le bruit
    noise_keywords = ['articles similaires', 'recherche', 'mon livre', 'jipangu']
    valid_h2s = []

    for h2 in h2_elements:
        title = h2.get_text(separator=' ', strip=True)
        if not any(keyword in title.lower() for keyword in noise_keywords):
            valid_h2s.append(h2)

    print(f"✅ Trouvé {len(valid_h2s)} expositions valides\n")
    print("="*80)

    # Analyser les 5 premières expositions pour voir le pattern
    pattern_matches = 0
    pattern_variations = []

    for i, h2 in enumerate(valid_h2s[:5], 1):
        title = h2.get_text(separator=' ', strip=True)
        print(f"\n{i}. {title[:60]}...")
        print("-" * 80)

        # Analyser les 5 prochains siblings
        siblings = []
        next_elem = h2.find_next_sibling()
        count = 0

        while next_elem and next_elem.name != 'h2' and count < 5:
            if next_elem.name in ['p', 'figure', 'div', 'iframe', 'script']:
                siblings.append({
                    'tag': next_elem.name,
                    'class': next_elem.get('class', []),
                    'text_preview': next_elem.get_text(strip=True)[:50] if next_elem.name == 'p' else '(media)',
                    'has_strong': bool(next_elem.find('strong')) if next_elem.name == 'p' else False,
                    'has_lieu': 'Lieu' in next_elem.get_text() if next_elem.name == 'p' else False
                })
                count += 1
            next_elem = next_elem.find_next_sibling()

        # Afficher la structure
        for j, sib in enumerate(siblings, 1):
            strong_marker = " [HAS <strong>]" if sib['has_strong'] else ""
            lieu_marker = " [HAS 'Lieu']" if sib['has_lieu'] else ""
            print(f"   {j}. <{sib['tag']}>{strong_marker}{lieu_marker}")
            if sib['tag'] == 'p':
                print(f"      → {sib['text_preview']}...")

        # Vérifier si ça matche le pattern: embed → p → p(metadata)
        is_pattern_match = False
        if len(siblings) >= 3:
            # Pattern attendu: premier élément = embed, puis p (description), puis p (metadata avec Lieu)
            first_is_embed = siblings[0]['tag'] in ['figure', 'div', 'iframe', 'script']
            second_is_p = siblings[1]['tag'] == 'p'
            third_is_p_meta = siblings[2]['tag'] == 'p' and siblings[2]['has_lieu']

            if first_is_embed and second_is_p and third_is_p_meta:
                is_pattern_match = True
                pattern_matches += 1
                print(f"   ✅ MATCHE LE PATTERN: embed → p(description) → p(metadata)")
            else:
                variation = f"{siblings[0]['tag']} → {siblings[1]['tag']} → {siblings[2]['tag'] if len(siblings) > 2 else 'END'}"
                pattern_variations.append(variation)
                print(f"   ⚠️  VARIATION: {variation}")
        else:
            print(f"   ⚠️  Pas assez d'éléments ({len(siblings)})")

    print("\n" + "="*80)
    print(f"\n📊 RÉSUMÉ (sur {min(5, len(valid_h2s))} expositions analysées):")
    print(f"   • Matches du pattern: {pattern_matches}/{min(5, len(valid_h2s))}")

    if pattern_variations:
        print(f"\n   • Variations observées:")
        for var in set(pattern_variations):
            count = pattern_variations.count(var)
            print(f"      - {var} (x{count})")

    # Conclusion
    if pattern_matches >= 4:
        print(f"\n✅ CONCLUSION: Le pattern est FIABLE (≥80% de matches)")
        print(f"   → Recommandation: Utiliser le pattern simplifié")
        return True
    else:
        print(f"\n⚠️  CONCLUSION: Le pattern est VARIABLE (<80% de matches)")
        print(f"   → Recommandation: Garder la logique actuelle flexible")
        return False


if __name__ == "__main__":
    # Tester sur plusieurs mois pour valider la consistance
    test_urls = [
        ("Mars 2025", "https://ichiban-japan.com/expositions-tokyo-mars-2025/"),
        ("Avril 2025", "https://ichiban-japan.com/expositions-tokyo-avril-2025/"),
        ("Mai 2025", "https://ichiban-japan.com/expositions-tokyo-mai-2025/"),
    ]

    print("="*80)
    print("TEST DE VALIDATION DU PATTERN HTML DES EXPOSITIONS")
    print("="*80)

    results = []
    for name, url in test_urls:
        print(f"\n\n{'#'*80}")
        print(f"# {name}")
        print(f"{'#'*80}\n")

        is_reliable = analyze_exposition_structure(url)
        results.append((name, is_reliable))

        # Pause entre les requêtes
        import time
        time.sleep(2)

    # Résumé final
    print("\n\n" + "="*80)
    print("RÉSUMÉ GLOBAL")
    print("="*80)

    reliable_count = sum(1 for _, reliable in results if reliable)
    print(f"\nPages avec pattern fiable: {reliable_count}/{len(results)}\n")

    for name, reliable in results:
        status = "✅ FIABLE" if reliable else "⚠️  VARIABLE"
        print(f"   {status} - {name}")

    if reliable_count == len(results):
        print(f"\n🎯 RECOMMANDATION FINALE: Refonte avec pattern simplifié recommandée")
    elif reliable_count >= len(results) * 0.7:
        print(f"\n💡 RECOMMANDATION FINALE: Pattern partiellement fiable, envisager refonte avec fallback")
    else:
        print(f"\n⚠️  RECOMMANDATION FINALE: Garder la logique actuelle (pattern trop variable)")
