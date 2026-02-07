"""
Script pour analyser la structure HTML de JOAN MIRÓ
"""
import sys
import os

# Fix encoding issues on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup

# Lire le HTML téléchargé
with open('data/html_pages/expositions_mars_2025.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Trouver JOAN MIRÓ
h2_elements = soup.find_all('h2', class_='wp-block-heading')
for h2 in h2_elements:
    if 'JOAN MIRÓ' in h2.get_text():
        print('='*80)
        print('H2 TROUVÉ: JOAN MIRÓ')
        print('='*80)
        print(f'H2 text: {h2.get_text()[:100]}')
        print()

        # Analyser les 10 prochains siblings
        print('SIBLINGS SUIVANTS:')
        print('-'*80)
        next_elem = h2.find_next_sibling()
        count = 0
        while next_elem and count < 10:
            print(f'\n{count+1}. <{next_elem.name}>')

            if next_elem.name in ['p', 'blockquote']:
                text = next_elem.get_text(separator=' ', strip=True)
                print(f'   Text (premiers 100 chars): {text[:100]}...')
                print(f'   Has <strong>: {bool(next_elem.find("strong"))}')
                print(f'   Has "Lieu :": {"Lieu :" in text}')
                print(f'   Has "Lieux :": {"Lieux :" in text}')
                print(f'   Longueur totale: {len(text)} caractères')

                # Montrer la structure interne pour blockquote
                if next_elem.name == 'blockquote':
                    print(f'   Structure interne de <blockquote>:')
                    for i, child in enumerate(next_elem.children):
                        if hasattr(child, 'name') and child.name:
                            child_text = child.get_text(strip=True)[:50] if hasattr(child, 'get_text') else ''
                            print(f'      - <{child.name}>: {child_text}...')

            next_elem = next_elem.find_next_sibling()
            count += 1

            # Arrêter si on atteint le prochain h2
            if next_elem and next_elem.name == 'h2':
                print('\n(Arrêt: prochain H2 atteint)')
                break

        break
