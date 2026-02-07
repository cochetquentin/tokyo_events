"""
Script pour mettre à jour les fichiers de référence avec les arrondissements
"""

import json
import sys
import os
import io
from pathlib import Path

# Fix encoding on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Ajouter le chemin parent pour importer les modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.location_utils import normalize_district


def update_reference_file(filepath):
    """
    Met à jour un fichier de référence en ajoutant les arrondissements aux locations

    Args:
        filepath: Chemin du fichier de référence
    """
    print(f"Traitement de {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Déterminer le type (festivals ou expositions)
    if 'festivals' in data:
        items = data['festivals']
        item_type = 'festivals'
    elif 'expositions' in data:
        items = data['expositions']
        item_type = 'expositions'
    else:
        print(f"  ⚠️ Type inconnu, skip")
        return

    updated_count = 0

    for item in items:
        if item.get('location'):
            original_location = item['location']
            normalized_location = normalize_district(original_location)

            # Si la normalisation a ajouté un arrondissement
            if normalized_location != original_location:
                item['location'] = normalized_location
                updated_count += 1
                print(f"  ✓ {item['name'][:50]}")
                print(f"    {original_location} → {normalized_location}")

    # Sauvegarder le fichier mis à jour
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  ✅ {updated_count}/{len(items)} {item_type} mis à jour\n")
    return updated_count


def main():
    """Fonction principale"""
    reference_dir = Path('data/reference')

    if not reference_dir.exists():
        print("❌ Dossier data/reference/ non trouvé")
        return

    # Trouver tous les fichiers de référence
    reference_files = list(reference_dir.glob('*_reference.json'))

    if not reference_files:
        print("❌ Aucun fichier de référence trouvé")
        return

    print(f"📂 {len(reference_files)} fichiers de référence trouvés\n")
    print("="*60)

    total_updated = 0

    for ref_file in sorted(reference_files):
        updated = update_reference_file(ref_file)
        total_updated += updated

    print("="*60)
    print(f"✅ Terminé ! {total_updated} locations mises à jour au total")


if __name__ == "__main__":
    main()
