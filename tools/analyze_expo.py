import sys
import requests
from bs4 import BeautifulSoup

if len(sys.argv) != 3:
    print("Usage: python analyze_expo.py <url> <exposition_name_keyword>")
    sys.exit(1)

url = sys.argv[1]
keyword = sys.argv[2].upper()

response = requests.get(url, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')

# Trouver l'exposition
h2_tags = soup.find_all('h2')
for h2 in h2_tags:
    if keyword in h2.get_text().upper():
        print('='*80)
        print('H2 TROUVÉ:', h2.get_text()[:80])
        print('='*80)
        print('H2 text:', h2.get_text())
        print('\nSIBLINGS SUIVANTS:')
        print('-'*80)

        next_elem = h2.find_next_sibling()
        count = 1
        while next_elem and count <= 10:
            print(f'\n{count}. <{next_elem.name}>')
            text = next_elem.get_text(separator=' ', strip=True)
            print(f'   Text (premiers 100 chars): {text[:100]}...')
            print(f'   Has <strong>: {bool(next_elem.find("strong"))}')
            print(f'   Has "Lieu :": {"Lieu :" in text}')
            print(f'   Has "Lieux :": {"Lieux :" in text}')
            print(f'   Longueur totale: {len(text)} caractères')

            if next_elem.name == 'h2':
                print('\n(Arrêt: prochain H2 atteint)')
                break

            next_elem = next_elem.find_next_sibling()
            count += 1
        break
