import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup

url = 'https://tokyocheapo.com/events/'
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
soup = BeautifulSoup(response.content, 'html.parser')

nav = soup.select_one('nav.post-nav')
if nav:
    page_links = nav.select('.post-page a')
    page_numbers = [int(a.text.strip()) for a in page_links if a.text.strip().isdigit()]
    max_page = max(page_numbers) if page_numbers else 1

    print(f'Pagination detectee :')
    print(f'   Nombre total de pages : {max_page}')
    print(f'   Evenements par page : ~24')
    print(f'   Evenements totaux estimes : ~{max_page * 24}')
    print()
    print(f'Pages disponibles : {sorted(set(page_numbers))}')
else:
    print('Aucune pagination trouvee')
