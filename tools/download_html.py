"""
Script pour télécharger le HTML brut des pages de festivals
Utile pour analyser la structure sans faire trop de requêtes
"""

import sys
import os

# Fix encoding issues on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from datetime import datetime


def download_page(page_type, month, year):
    """
    Télécharge le HTML d'une page de festival ou exposition

    Args:
        page_type: Type de page ("festivals" ou "expositions")
        month: Numéro du mois (1-12)
        year: Année
    """

    MONTHS_FR = {
        1: "janvier", 2: "fevrier", 3: "mars", 4: "avril",
        5: "mai", 6: "juin", 7: "juillet", 8: "aout",
        9: "septembre", 10: "octobre", 11: "novembre", 12: "decembre"
    }

    month_name = MONTHS_FR.get(month)
    if not month_name:
        print(f"❌ Mois invalide: {month}")
        return

    # Construire l'URL
    url = f"https://ichiban-japan.com/{page_type}-tokyo-{month_name}-{year}/"

    print(f"📥 Téléchargement de: {url}")

    try:
        # Faire la requête avec User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Créer le dossier html_pages s'il n'existe pas
        output_dir = "data/html_pages"
        os.makedirs(output_dir, exist_ok=True)

        # Nom du fichier
        filename = f"{output_dir}/{page_type}_{month_name}_{year}.html"

        # Sauvegarder le HTML
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)

        print(f"✅ HTML sauvegardé dans: {filename}")
        print(f"📊 Taille: {len(response.text)} caractères")

        return filename

    except requests.RequestException as e:
        print(f"❌ Erreur lors du téléchargement: {e}")
        return None


def download_festival_page(month, year):
    """
    Télécharge le HTML d'une page de festival

    Args:
        month: Numéro du mois (1-12)
        year: Année
    """
    return download_page("festivals", month, year)


def download_exposition_page(month, year):
    """
    Télécharge le HTML d'une page d'exposition

    Args:
        month: Numéro du mois (1-12)
        year: Année
    """
    return download_page("expositions", month, year)


def download_multiple_months(months_list):
    """
    Télécharge plusieurs mois

    Args:
        months_list: Liste de tuples (month, year)
    """
    print("="*60)
    print("TÉLÉCHARGEMENT DES PAGES HTML")
    print("="*60)

    results = []

    for month, year in months_list:
        print()
        filename = download_festival_page(month, year)
        if filename:
            results.append(filename)

    print("\n" + "="*60)
    print(f"✅ {len(results)} pages téléchargées avec succès")
    print("="*60)

    return results


if __name__ == "__main__":
    if len(sys.argv) not in [3, 4]:
        print("Usage: uv run tools/download_html.py [type] <mois> <année>")
        print("  type: festivals ou expositions (par défaut: festivals)")
        print("Exemples:")
        print("  uv run tools/download_html.py mars 2025")
        print("  uv run tools/download_html.py festivals mars 2025")
        print("  uv run tools/download_html.py expositions mars 2025")
        sys.exit(1)

    # Déterminer le type et les arguments
    if len(sys.argv) == 4:
        page_type = sys.argv[1].lower()
        month_name = sys.argv[2].lower()
        year_str = sys.argv[3]
    else:
        page_type = "festivals"  # Par défaut
        month_name = sys.argv[1].lower()
        year_str = sys.argv[2]

    # Valider le type
    if page_type not in ["festivals", "expositions"]:
        print(f"❌ Type invalide: {page_type}")
        print("Type valides: festivals, expositions")
        sys.exit(1)

    # Valider l'année
    try:
        year = int(year_str)
    except ValueError:
        print(f"❌ Année invalide: {year_str}")
        sys.exit(1)

    # Mapping des mois
    months = {
        'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12
    }

    month_num = months.get(month_name)
    if not month_num:
        print(f"❌ Mois invalide: {month_name}")
        print(f"Mois valides: {', '.join(months.keys())}")
        sys.exit(1)

    print(f"\n🎯 Téléchargement {page_type} de {month_name} {year}...\n")
    download_page(page_type, month_num, year)
