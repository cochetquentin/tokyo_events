"""
Script pour migrer les scrapers vers le format start_date/end_date

Modifie:
1. Création du dict: 'dates': dates -> 'start_date': None, 'end_date': None
2. Assignations: festival['dates'] = "..." -> start, end = split... ; festival['start_date'] = start ; festival['end_date'] = end
3. Conditions: if festival['dates'] -> if festival.get('end_date')
4. Affichages: festival.get('dates') -> format_date_range(festival.get('start_date'), festival.get('end_date'))
"""

import re

# Pattern pour remplacer 'dates': dates par 'start_date': None, 'end_date': None dans les dicts
PATTERN_DICT_INIT = re.compile(r"'dates':\s*(\w+),")

# Pattern pour remplacer les assignations festival['dates'] = "YYYY/MM/DD - YYYY/MM/DD"
PATTERN_ASSIGN_RANGE = re.compile(r"(\s+)(\w+)\['dates'\]\s*=\s*f\"(\{annee1\}/\{mois1\}/\{jour1\} - \{annee2\}/\{mois2\}/\{jour2\})\"")
PATTERN_ASSIGN_RANGE2 = re.compile(r"(\s+)(\w+)\['dates'\]\s*=\s*f\"(\{annee\}/\{mois\}/\{jour1\} - \{annee\}/\{mois\}/\{jour2\})\"")
PATTERN_ASSIGN_RANGE3 = re.compile(r"(\s+)(\w+)\['dates'\]\s*=\s*f\"(\{annee\}/\{mois\}/01 - \{annee\}/\{mois\}/\{jour\})\"")
PATTERN_ASSIGN_RANGE4 = re.compile(r"(\s+)(\w+)\['dates'\]\s*=\s*f\"(\{annee\}/\{mois1\}/\{jour1\} - \{annee\}/\{mois2\}/\{jour2\})\"")
PATTERN_ASSIGN_SIMPLE = re.compile(r"(\s+)(\w+)\['dates'\]\s*=\s*f\"(\{annee\}/\{mois\}/\{jour\})\"")

# Pattern pour les assignations depuis _extract_dates_from_paragraph
PATTERN_ASSIGN_FUNC = re.compile(r"(\s+)(\w+)\['dates'\]\s*=\s*(\w+)")

# Pattern pour les conditions
PATTERN_CONDITION = re.compile(r"if\s+(\w+)\['dates'\]")
PATTERN_CONDITION_GET = re.compile(r"if\s+(\w+)\.get\('dates'\)")

# Pattern pour les affichages
PATTERN_DISPLAY_GET = re.compile(r"(\w+)\.get\('dates'\)")
PATTERN_DISPLAY_BRACKETS = re.compile(r"(\w+)\['dates'\]")


def migrate_file(filepath):
    """Migre un fichier scraper vers le format start_date/end_date"""
    print(f"\n📄 Migration de {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. Remplacer les imports
    if "from typing import List, Dict, Optional" in content:
        # Ajouter l'import de date_utils après les imports
        import_section = content.find("import sys")
        if import_section != -1:
            # Trouver la fin des imports
            next_class = content.find("\n\nclass", import_section)
            if next_class != -1:
                # Insérer l'import avant la classe
                content = content[:next_class] + "\nfrom src.date_utils import split_date_range, format_date_range\n" + content[next_class:]

    # 2. Remplacer 'dates': dates dans les dict par 'start_date': None, 'end_date': None
    def replace_dict_init(match):
        indent = match.group(0)[:-len(match.group(1))-3]  # Garder l'indentation
        var_name = match.group(1)
        if var_name == 'dates':
            # C'est la création initiale
            return f"'start_date': None,\n{indent}'end_date': None,"
        else:
            # C'est une assignation depuis une variable (comme parent_dates)
            return f"'start_date': None,\n{indent}'end_date': None,"

    content = PATTERN_DICT_INIT.sub(replace_dict_init, content)

    # 3. Remplacer les assignations de plages de dates
    def replace_assign_range(match):
        indent = match.group(1)
        var = match.group(2)
        date_expr = match.group(3)

        # Extraire les composants
        if 'annee1' in date_expr:
            # Format: {annee1}/{mois1}/{jour1} - {annee2}/{mois2}/{jour2}
            return (f"{indent}{var}['start_date'] = f\"{{annee1}}/{{mois1}}/{{jour1}}\"\n"
                   f"{indent}{var}['end_date'] = f\"{{annee2}}/{{mois2}}/{{jour2}}\"")
        elif '{jour1}' in date_expr:
            # Format: {annee}/{mois}/{jour1} - {annee}/{mois}/{jour2}
            return (f"{indent}{var}['start_date'] = f\"{{annee}}/{{mois}}/{{jour1}}\"\n"
                   f"{indent}{var}['end_date'] = f\"{{annee}}/{{mois}}/{{jour2}}\"")
        elif '/01 -' in date_expr:
            # Format: {annee}/{mois}/01 - {annee}/{mois}/{jour}
            return (f"{indent}{var}['start_date'] = f\"{{annee}}/{{mois}}/01\"\n"
                   f"{indent}{var}['end_date'] = f\"{{annee}}/{{mois}}/{{jour}}\"")
        elif 'mois1' in date_expr:
            # Format: {annee}/{mois1}/{jour1} - {annee}/{mois2}/{jour2}
            return (f"{indent}{var}['start_date'] = f\"{{annee}}/{{mois1}}/{{jour1}}\"\n"
                   f"{indent}{var}['end_date'] = f\"{{annee}}/{{mois2}}/{{jour2}}\"")

    content = PATTERN_ASSIGN_RANGE.sub(replace_assign_range, content)
    content = PATTERN_ASSIGN_RANGE2.sub(replace_assign_range, content)
    content = PATTERN_ASSIGN_RANGE3.sub(replace_assign_range, content)
    content = PATTERN_ASSIGN_RANGE4.sub(replace_assign_range, content)

    # Remplacer les assignations simples (date unique = end_date seulement)
    def replace_assign_simple(match):
        indent = match.group(1)
        var = match.group(2)
        return f"{indent}{var}['end_date'] = f\"{{annee}}/{{mois}}/{{jour}}\""

    content = PATTERN_ASSIGN_SIMPLE.sub(replace_assign_simple, content)

    # 4. Remplacer les assignations depuis fonctions (dates_from_p2, etc.)
    def replace_assign_func(match):
        indent = match.group(1)
        var = match.group(2)
        func_call = match.group(3)
        return (f"{indent}dates_result = {func_call}\n"
               f"{indent}if dates_result:\n"
               f"{indent}    start, end = split_date_range(dates_result)\n"
               f"{indent}    {var}['start_date'] = start\n"
               f"{indent}    {var}['end_date'] = end")

    content = PATTERN_ASSIGN_FUNC.sub(replace_assign_func, content)

    # 5. Remplacer les conditions
    content = PATTERN_CONDITION.sub(r"if \1.get('end_date')", content)
    content = PATTERN_CONDITION_GET.sub(r"if \1.get('end_date')", content)

    # 6. Remplacer les affichages
    content = PATTERN_DISPLAY_GET.sub(r"format_date_range(\1.get('start_date'), \1.get('end_date'))", content)
    # Ne pas remplacer les brackets dans les assignations
    # Seulement dans les print/format
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if ('print' in line or 'f"' in line or "f'" in line) and "['dates']" in line:
            line = PATTERN_DISPLAY_BRACKETS.sub(r"format_date_range(\1.get('start_date'), \1.get('end_date'))", line)
        new_lines.append(line)
    content = '\n'.join(new_lines)

    # Vérifier si des changements ont été faits
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Fichier migré avec succès")
        return True
    else:
        print(f"  ℹ️  Aucun changement nécessaire")
        return False


def main():
    """Migre les scrapers"""
    print("=" * 60)
    print("MIGRATION DES SCRAPERS VERS start_date/end_date")
    print("=" * 60)

    files = [
        'src/scraper_festivals_tokyo.py',
        'src/scraper_expositions_tokyo.py'
    ]

    migrated_count = 0
    for filepath in files:
        if migrate_file(filepath):
            migrated_count += 1

    print("\n" + "=" * 60)
    print(f"✅ {migrated_count}/{len(files)} fichiers migrés")
    print("=" * 60)


if __name__ == "__main__":
    main()
