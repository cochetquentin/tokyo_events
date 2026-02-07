import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

from bs4 import BeautifulSoup, Tag
import requests

url = "https://ichiban-japan.com/expositions-tokyo-mars-2025/"
header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
res = requests.get(url, headers=header, timeout=10)
soup = BeautifulSoup(res.content, 'html.parser')

entry_content = soup.find('div', class_='entry-content')

sections = []
current_section = []

for elem in entry_content.children:
    if not isinstance(elem, Tag):
        continue

    if elem.name == "div" and "crp_related" in (elem.get("class") or []):
        break

    if elem.name == "h2":
        if current_section:
            sections.append(current_section)
        current_section = [elem]
    else:
        if current_section:
            current_section.append(elem)

if current_section:
    sections.append(current_section)

# Afficher toutes les sections
print(f"Nombre de sections: {len(sections)}\n")

for k, section in enumerate(sections[:5]):  # Premières 5 sections
    print("="*80)
    print(f"SECTION {k} (len={len(section)}):")
    print("="*80)
    print(f"Titre: {section[0].get_text(strip=True)[:60]}...")
    print(f"Elements:")
    for i, elem in enumerate(section):
        text = elem.get_text(separator=' ', strip=True)[:60]
        print(f"  [{i}] <{elem.name}>: {text}...")
    print()
