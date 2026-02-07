"""
Utilitaires pour parser les dates en français
Gère les formats complexes comme "1er, 6-8, 11, 13-15, 20-23 et 27-28 février 2026"
"""

import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple


# Mapping des mois français vers numéros
MOIS_MAPPING = {
    'janvier': '01', 'février': '02', 'fevrier': '02', 'mars': '03',
    'avril': '04', 'mai': '05', 'juin': '06', 'juillet': '07',
    'août': '08', 'aout': '08', 'septembre': '09', 'octobre': '10',
    'novembre': '11', 'décembre': '12', 'decembre': '12'
}


def expand_complex_dates(date_string: str, default_year: int = None) -> List[str]:
    """
    Expanse les dates complexes en liste de dates individuelles

    Exemples:
        "1er, 6-8, 11, 13-15, 20-23 et 27-28 février 2026"
        → ["2026/02/01", "2026/02/06", "2026/02/07", "2026/02/08", "2026/02/11",
           "2026/02/13", "2026/02/14", "2026/02/15", "2026/02/20", "2026/02/21",
           "2026/02/22", "2026/02/23", "2026/02/27", "2026/02/28"]

    Args:
        date_string: Chaîne de dates complexe
        default_year: Année par défaut si non spécifiée

    Returns:
        Liste de dates au format YYYY/MM/DD, triées
    """
    if not date_string:
        return []

    date_string = date_string.lower().strip()

    # Extraire le mois et l'année
    # Pattern: "... février 2026" ou "... février"
    month_year_match = re.search(r'([a-zéè]+)\s+(\d{4})', date_string)
    if month_year_match:
        month_name = month_year_match.group(1)
        year = month_year_match.group(2)
    else:
        # Chercher juste le mois
        month_match = re.search(r'([a-zéè]+)$', date_string)
        if month_match:
            month_name = month_match.group(1)
            year = str(default_year) if default_year else datetime.now().year
        else:
            return []

    month_num = MOIS_MAPPING.get(month_name)
    if not month_num:
        return []

    # Retirer le mois et l'année de la chaîne pour ne garder que les jours
    days_string = re.sub(rf'\s*{month_name}\s*\d{{4}}?', '', date_string).strip()

    # Nettoyer "er" et "e" après les chiffres
    days_string = re.sub(r'(\d+)(?:er|e)', r'\1', days_string)

    # Liste pour stocker tous les jours
    days = []

    # Séparer par virgules et "et"
    # Remplacer "et" par virgule pour uniformiser
    days_string = days_string.replace(' et ', ', ')

    # Séparer les parties par virgules
    parts = [part.strip() for part in days_string.split(',')]

    for part in parts:
        if not part:
            continue

        # Vérifier si c'est une plage (ex: "6-8", "13-15")
        range_match = re.match(r'(\d+)\s*[-–]\s*(\d+)', part)
        if range_match:
            start_day = int(range_match.group(1))
            end_day = int(range_match.group(2))
            # Ajouter tous les jours de la plage
            for day in range(start_day, end_day + 1):
                days.append(day)
        else:
            # Jour simple
            day_match = re.match(r'(\d+)', part)
            if day_match:
                days.append(int(day_match.group(1)))

    # Convertir en dates formatées et trier
    dates = []
    for day in days:
        day_str = str(day).zfill(2)
        date_formatted = f"{year}/{month_num}/{day_str}"
        dates.append(date_formatted)

    # Retirer les doublons et trier
    dates = sorted(set(dates))

    return dates


def parse_french_date_range(date_string: str, default_year: int = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse une plage de dates en français

    Exemples:
        "Du 31 décembre 2024 au 4 janvier 2025" → ("2024/12/31", "2025/01/04")
        "Du 1er au 3 janvier 2025" → ("2025/01/01", "2025/01/03")
        "3 février 2025" → ("2025/02/03", "2025/02/03")

    Args:
        date_string: Chaîne de dates
        default_year: Année par défaut

    Returns:
        Tuple (start_date, end_date) au format YYYY/MM/DD
    """
    if not date_string:
        return None, None

    date_string = date_string.lower().strip()

    # Nettoyer les espaces multiples
    date_string = re.sub(r'\s+', ' ', date_string)

    # Pattern 1: "Du X mois1 année1 au Y mois2 année2" (cross-year)
    match = re.search(
        r'du\s+(\d{1,2})(?:\s*er)?\s+([a-zéè]+)\s+(\d{4})\s+au\s+(\d{1,2})(?:\s*er)?\s+([a-zéè]+)\s+(\d{4})',
        date_string
    )
    if match:
        jour1 = match.group(1).zfill(2)
        mois1 = MOIS_MAPPING.get(match.group(2), '??')
        annee1 = match.group(3)
        jour2 = match.group(4).zfill(2)
        mois2 = MOIS_MAPPING.get(match.group(5), '??')
        annee2 = match.group(6)
        return f"{annee1}/{mois1}/{jour1}", f"{annee2}/{mois2}/{jour2}"

    # Pattern 2: "Du X mois1 au Y mois2 année" (cross-month, same year)
    match = re.search(
        r'du\s+(\d{1,2})(?:\s*er)?\s+([a-zéè]+)\s+au\s+(\d{1,2})(?:\s*er)?\s+([a-zéè]+)\s+(\d{4})',
        date_string
    )
    if match:
        jour1 = match.group(1).zfill(2)
        mois1 = MOIS_MAPPING.get(match.group(2), '??')
        jour2 = match.group(3).zfill(2)
        mois2 = MOIS_MAPPING.get(match.group(4), '??')
        annee = match.group(5)
        return f"{annee}/{mois1}/{jour1}", f"{annee}/{mois2}/{jour2}"

    # Pattern 3: "Du X au Y mois année" (same month)
    match = re.search(
        r'du\s+(\d{1,2})(?:\s*er)?\s+au\s+(\d{1,2})(?:\s*er)?\s+([a-zéè]+)\s+(\d{4})',
        date_string
    )
    if match:
        jour1 = match.group(1).zfill(2)
        jour2 = match.group(2).zfill(2)
        mois = MOIS_MAPPING.get(match.group(3), '??')
        annee = match.group(4)
        return f"{annee}/{mois}/{jour1}", f"{annee}/{mois}/{jour2}"

    # Pattern 4: "Jusqu'au X mois année"
    match = re.search(r'jusqu[\'\'\u2019]?au\s+(\d{1,2})(?:\s*er)?\s+([a-zéè]+)\s+(\d{4})', date_string)
    if match:
        jour = match.group(1).zfill(2)
        mois = MOIS_MAPPING.get(match.group(2), '??')
        annee = match.group(3)
        # Jusqu'au = du 1er au X
        return f"{annee}/{mois}/01", f"{annee}/{mois}/{jour}"

    # Pattern 5: "(jusqu'au X mois année)" - avec parenthèses
    match = re.search(r'\(jusqu[\'\'\u2019]?au\s+(\d{1,2})(?:\s*er)?\s+([a-zéè]+)\s+(\d{4})\)', date_string)
    if match:
        jour = match.group(1).zfill(2)
        mois = MOIS_MAPPING.get(match.group(2), '??')
        annee = match.group(3)
        return f"{annee}/{mois}/01", f"{annee}/{mois}/{jour}"

    # Pattern 6: "X-Y mois année" (range without "du...au")
    match = re.search(r'(\d{1,2})(?:\s*er)?\s*[-–]\s*(\d{1,2})(?:\s*er)?\s+([a-zéè]+)\s+(\d{4})', date_string)
    if match:
        jour1 = match.group(1).zfill(2)
        jour2 = match.group(2).zfill(2)
        mois = MOIS_MAPPING.get(match.group(3), '??')
        annee = match.group(4)
        return f"{annee}/{mois}/{jour1}", f"{annee}/{mois}/{jour2}"

    # Pattern 7: "X mois1-Y mois2 année" (cross-month without "du...au")
    match = re.search(r'(\d{1,2})(?:\s*er)?\s+([a-zéè]+)\s*[-–]\s*(\d{1,2})(?:\s*er)?\s+([a-zéè]+)\s+(\d{4})', date_string)
    if match:
        jour1 = match.group(1).zfill(2)
        mois1 = MOIS_MAPPING.get(match.group(2), '??')
        jour2 = match.group(3).zfill(2)
        mois2 = MOIS_MAPPING.get(match.group(4), '??')
        annee = match.group(5)
        if mois1 != '??':
            return f"{annee}/{mois1}/{jour1}", f"{annee}/{mois2}/{jour2}"

    # Pattern 8: "X mois année" (single date)
    match = re.search(r'(\d{1,2})(?:\s*er)?\s+([a-zéè]+)\s+(\d{4})', date_string)
    if match:
        jour = match.group(1).zfill(2)
        mois = MOIS_MAPPING.get(match.group(2), '??')
        annee = match.group(3)
        single_date = f"{annee}/{mois}/{jour}"
        return single_date, single_date

    return None, None


def is_complex_date_pattern(date_string: str) -> bool:
    """
    Vérifie si la chaîne de dates contient un pattern complexe
    (virgules, "et", multiples ranges)

    Args:
        date_string: Chaîne à vérifier

    Returns:
        True si pattern complexe détecté
    """
    if not date_string:
        return False

    # Contient des virgules ou "et" → pattern complexe
    if ',' in date_string or ' et ' in date_string.lower():
        return True

    return False


def normalize_french_date(date_string: str, default_year: int = None) -> str:
    """
    Normalise une date française au format YYYY/MM/DD - YYYY/MM/DD

    Args:
        date_string: Date en français
        default_year: Année par défaut

    Returns:
        Date normalisée
    """
    if not date_string:
        return None

    # Vérifier si c'est un pattern complexe
    if is_complex_date_pattern(date_string):
        # Pour les patterns complexes, retourner juste la première et dernière date
        dates = expand_complex_dates(date_string, default_year)
        if dates:
            return f"{dates[0]} - {dates[-1]}"
        return None

    # Sinon, utiliser le parser de plage standard
    start, end = parse_french_date_range(date_string, default_year)
    if start and end:
        if start == end:
            return start
        return f"{start} - {end}"

    return None
