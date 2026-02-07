"""
Script pour convertir le format des dates dans les fichiers JSON
Convertit "dates": "2024/10/09 - 2025/01/13"
en "start_date": "2024/10/09", "end_date": "2025/01/13"

Usage: uv run tools/convert_dates_format.py
"""

import json
import os
import sys
from pathlib import Path

# Fix encoding issues on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def split_date(date_str):
    """
    Split une date au format "2024/10/09 - 2025/01/13" ou "2025/01/13"

    Returns:
        tuple: (start_date, end_date) ou (date, date) si pas de plage
    """
    if not date_str:
        return None, None

    # Plage de dates
    if ' - ' in date_str:
        parts = date_str.split(' - ')
        return parts[0].strip(), parts[1].strip()
    else:
        # Date simple (pas de plage)
        return date_str.strip(), date_str.strip()


def convert_file(filepath, item_type):
    """
    Convertit un fichier JSON au nouveau format

    Args:
        filepath: Chemin du fichier JSON
        item_type: 'festivals' ou 'expositions'
    """
    print(f"\n📄 Conversion de {filepath}")

    # Lire le fichier
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data.get(item_type, [])
    converted_count = 0
    missing_start_count = 0

    # Convertir chaque item
    for item in items:
        if 'dates' in item:
            date_str = item['dates']
            start_date, end_date = split_date(date_str)

            # Remplacer 'dates' par 'start_date' et 'end_date'
            del item['dates']
            item['start_date'] = start_date
            item['end_date'] = end_date

            converted_count += 1

            # Détecter si start_date manque (même que end_date = pas de vraie plage)
            if start_date == end_date and date_str and ' - ' not in date_str:
                missing_start_count += 1
                print(f"  ⚠️  {item['name']}: pas de date de début (seule end_date: {end_date})")

    # Sauvegarder
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  ✅ {converted_count} items convertis")
    if missing_start_count > 0:
        print(f"  ⚠️  {missing_start_count} items sans date de début")

    return converted_count, missing_start_count


def main():
    """Convertit tous les fichiers JSON dans data/ et data/reference/"""

    print("=" * 60)
    print("CONVERSION DU FORMAT DES DATES")
    print("=" * 60)

    total_converted = 0
    total_missing_start = 0

    # Chercher tous les fichiers JSON
    files_to_convert = []

    # Fichiers de référence
    ref_dir = Path('data/reference')
    if ref_dir.exists():
        files_to_convert.extend([
            (f, 'festivals') for f in ref_dir.glob('festivals_*_reference.json')
        ])
        files_to_convert.extend([
            (f, 'expositions') for f in ref_dir.glob('expositions_*_reference.json')
        ])

    # Fichiers scrapés
    data_dir = Path('data')
    if data_dir.exists():
        files_to_convert.extend([
            (f, 'festivals') for f in data_dir.glob('festivals_*.json')
            if 'reference' not in f.name
        ])
        files_to_convert.extend([
            (f, 'expositions') for f in data_dir.glob('expositions_*.json')
            if 'reference' not in f.name
        ])

    if not files_to_convert:
        print("\n❌ Aucun fichier JSON trouvé")
        return

    print(f"\n📂 {len(files_to_convert)} fichiers trouvés\n")

    # Convertir chaque fichier
    for filepath, item_type in files_to_convert:
        converted, missing = convert_file(str(filepath), item_type)
        total_converted += converted
        total_missing_start += missing

    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"✅ Total items convertis: {total_converted}")
    print(f"⚠️  Total items sans date de début: {total_missing_start}")
    print("=" * 60)


if __name__ == "__main__":
    main()
