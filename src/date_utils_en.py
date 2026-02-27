"""
Utilitaires pour la gestion des dates en anglais (Tokyo Cheapo)
"""

from typing import Tuple, Optional
import re
from datetime import datetime


# Mapping des mois anglais vers numéros
MONTHS_EN = {
    'jan': '01', 'january': '01',
    'feb': '02', 'february': '02',
    'mar': '03', 'march': '03',
    'apr': '04', 'april': '04',
    'may': '05',
    'jun': '06', 'june': '06',
    'jul': '07', 'july': '07',
    'aug': '08', 'august': '08',
    'sep': '09', 'september': '09',
    'oct': '10', 'october': '10',
    'nov': '11', 'november': '11',
    'dec': '12', 'december': '12'
}


def parse_english_date(date_str: str, default_year: int = None) -> Optional[str]:
    """
    Parse une date en anglais vers le format YYYY/MM/DD

    Formats supportés:
    - "Feb 28" → "2026/02/28" (utilise default_year)
    - "Mar 1 2026" → "2026/03/01" (année explicite)
    - "March 1" → "2026/03/01"

    Args:
        date_str: Date en anglais (ex: "Feb 28", "Mar 1 2026")
        default_year: Année à utiliser si non présente (défaut: année courante)

    Returns:
        Date au format YYYY/MM/DD ou None si parsing échoue
    """
    if not date_str:
        return None

    if not default_year:
        default_year = datetime.now().year

    # Nettoyer la chaîne
    date_str = date_str.strip()

    # Pattern: "Month Day Year" ou "Month Day"
    # Ex: "Mar 1 2026" ou "Feb 28"
    pattern = r'([A-Za-z]+)\s+(\d{1,2})(?:\s+(\d{4}))?'
    match = re.match(pattern, date_str)

    if not match:
        return None

    month_name = match.group(1).lower()
    day = match.group(2).zfill(2)
    year = match.group(3) if match.group(3) else str(default_year)

    # Convertir le mois
    month = MONTHS_EN.get(month_name)
    if not month:
        return None

    return f"{year}/{month}/{day}"


def parse_english_date_range(start_str: str, end_str: str, current_year: int = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse une plage de dates en anglais avec inférence d'année

    Gère les cas:
    - Même année: "Feb 28" - "Mar 1" (même année)
    - Années différentes: "Nov 17" - "Mar 1 2026" (années qui se chevauchent)

    Logique d'inférence:
    - Si end_date a une année explicite, l'utiliser
    - Si start_month > end_month, start_year = end_year - 1
    - Sinon, même année

    Args:
        start_str: Date de début (ex: "Feb 28", "Nov 17")
        end_str: Date de fin (ex: "Mar 1", "Mar 1 2026")
        current_year: Année de référence (défaut: année courante)

    Returns:
        Tuple (start_date, end_date) au format YYYY/MM/DD
    """
    if not current_year:
        current_year = datetime.now().year

    # Parser la date de fin d'abord (elle peut avoir l'année explicite)
    end_date = parse_english_date(end_str, current_year)
    if not end_date:
        return None, None

    # Extraire l'année de la date de fin
    end_year = int(end_date.split('/')[0])
    end_month = int(end_date.split('/')[1])

    # Parser la date de début
    # D'abord essayer avec l'année de fin
    start_date = parse_english_date(start_str, end_year)
    if not start_date:
        return None, None

    start_month = int(start_date.split('/')[1])

    # Si le mois de début > mois de fin, la date de début est l'année précédente
    # Ex: Nov 17 - Mar 1 2026 → Nov 2025 - Mar 2026
    if start_month > end_month:
        start_date = parse_english_date(start_str, end_year - 1)

    return start_date, end_date


def infer_year_from_month(month: int, current_date: datetime = None) -> int:
    """
    Infère l'année pour un mois donné basé sur la date courante

    Logique:
    - Si le mois est avant le mois courant de plus de 2 mois, c'est probablement l'année prochaine
    - Sinon, c'est l'année courante

    Args:
        month: Numéro du mois (1-12)
        current_date: Date de référence (défaut: date actuelle)

    Returns:
        Année inférée
    """
    if not current_date:
        current_date = datetime.now()

    current_month = current_date.month
    current_year = current_date.year

    # Si l'événement est dans le passé de plus de 2 mois, c'est probablement l'année prochaine
    if month < current_month - 2:
        return current_year + 1
    else:
        return current_year


def parse_single_date_components(day_text: str, date_num: str, current_year: int = None) -> Optional[str]:
    """
    Parse une date depuis ses composants séparés (format Tokyo Cheapo single date)

    Ex:
    - day_text = "Sun, Mar" → extrait "Mar"
    - date_num = "01"
    - → "2026/03/01"

    Args:
        day_text: Texte contenant le jour de semaine et mois (ex: "Sun, Mar")
        date_num: Numéro du jour (ex: "01", "15")
        current_year: Année de référence (défaut: année courante)

    Returns:
        Date au format YYYY/MM/DD ou None si parsing échoue
    """
    if not day_text or not date_num:
        return None

    if not current_year:
        current_year = datetime.now().year

    # Extraire le mois du day_text (après la virgule)
    # Ex: "Sun, Mar" → "Mar"
    parts = day_text.split(',')
    if len(parts) < 2:
        # Essayer sans virgule: "Mar" directement
        month_name = day_text.strip().split()[-1]
    else:
        month_name = parts[1].strip()

    # Convertir le mois
    month = MONTHS_EN.get(month_name.lower())
    if not month:
        return None

    # Inférer l'année basée sur le mois
    year = infer_year_from_month(int(month), datetime.now())

    # Formater le jour
    day = date_num.zfill(2)

    return f"{year}/{month}/{day}"
