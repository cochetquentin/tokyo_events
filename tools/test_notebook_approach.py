import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

from bs4 import BeautifulSoup, Tag
import requests
import unicodedata
from src.scraper_expositions_tokyo import TokyoExpositionScraper

url = "https://ichiban-japan.com/expositions-tokyo-mars-2025/"
header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
res = requests.get(url, headers=header, timeout=10)
soup = BeautifulSoup(res.content, 'html.parser')

scraper = TokyoExpositionScraper()

# Tester le parser simplifié
expositions = scraper._parse_page_simplified(soup, 3, 2025)

print(f"Nombre d'expositions trouvées: {len(expositions)}\n")

# Afficher les 3 premières
for i, expo in enumerate(expositions[:3]):
    print(f"--- EXPOSITION {i+1}: {expo['name'][:50]} ---")
    print(f"  start_date: {expo['start_date']}")
    print(f"  end_date: {expo['end_date']}")
    print(f"  location: {expo['location']}")
    print(f"  description: {expo['description'][:60]}...")
    print()
