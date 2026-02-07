"""
Utilitaires pour la gestion des dates
"""

from typing import Tuple, Optional
import re
from datetime import datetime


def parse_japanese_dates(dates_text: str, default_year: int = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse Japanese date formats to YYYY/MM/DD (legacy function for compatibility)

    This function returns only start_date and end_date.
    For full date list, use parse_japanese_dates_list()

    Args:
        dates_text: Japanese date string
        default_year: Year to use if not present in text (defaults to current year)

    Returns:
        Tuple (start_date, end_date) in YYYY/MM/DD format
    """
    dates_list = parse_japanese_dates_list(dates_text, default_year)

    if not dates_list:
        return None, None

    return dates_list[0], dates_list[-1]


def parse_japanese_dates_list(dates_text: str, default_year: int = None) -> list:
    """
    Parse Japanese date formats to a list of individual dates in YYYY/MM/DD format

    Handles various Japanese date formats:
    - Single date: "2026年1月17日(土)" → ["2026/01/17"]
    - Multiple dates: "1月17日(土)・24日(土)・31日(土)" → ["2026/01/17", "2026/01/24", "2026/01/31"]
    - Mixed months: "2026年1月17日・24日・31日、2月7日・14日" → ["2026/01/17", "2026/01/24", "2026/01/31", "2026/02/07", "2026/02/14"]
    - Date range: "7月26日～8月2日" → ["2026/07/26", "2026/08/02"] (only start and end)
    - Complex: "2025年12/24・31、2026年1/24・31、2/7・14・21・28、3/21" → full list

    Args:
        dates_text: Japanese date string
        default_year: Year to use if not present in text (defaults to current year)

    Returns:
        List of dates in YYYY/MM/DD format, sorted chronologically
    """
    if not dates_text:
        return []

    if default_year is None:
        default_year = datetime.now().year

    # Remove day of week markers: (土), (日), (月), (火), (水), (木), (金)
    cleaned_text = re.sub(r'\([月火水木金土日]\)', '', dates_text)

    dates = []
    current_year = default_year

    # Extract year if present
    year_match = re.search(r'(\d{4})年', cleaned_text)
    if year_match:
        current_year = int(year_match.group(1))

    # Pattern 1: Range with tilde "7月26日～8月2日" (only extract start and end)
    range_match = re.search(r'(\d{1,2})月(\d{1,2})日[～〜](\d{1,2})月(\d{1,2})日', cleaned_text)
    if range_match:
        start_month = int(range_match.group(1))
        start_day = int(range_match.group(2))
        end_month = int(range_match.group(3))
        end_day = int(range_match.group(4))

        # Handle cross-year
        start_year = current_year
        end_year = current_year
        if end_month < start_month:
            end_year = current_year + 1

        dates.append(f"{start_year}/{start_month:02d}/{start_day:02d}")
        dates.append(f"{end_year}/{end_month:02d}/{end_day:02d}")
        return sorted(set(dates))

    # Pattern 2: Multiple days in same month with ・ separator
    # "1月17日(土)・24日(土)・31日(土)" → all days in January
    # This pattern appears before commas, so process the full text first

    # Find all occurrences of month+day followed by just days with ・
    # Example: "1月17日・24日・31日" should give us all three days in month 1

    # Strategy: Find month, then find all following day numbers until we hit another month or comma
    parts = re.split(r'[、,]', cleaned_text)

    current_month = None

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Check if part has a year
        year_in_part = re.search(r'(\d{4})年', part)
        if year_in_part:
            current_year = int(year_in_part.group(1))

        # Pattern A: "1月17日・24日・31日" - month followed by multiple days
        # First extract the month
        month_match = re.search(r'(\d{1,2})月', part)
        if month_match:
            current_month = int(month_match.group(1))

            # Now find ALL day numbers in this part (including the first one)
            day_matches = re.findall(r'(\d{1,2})日', part)
            for day_str in day_matches:
                day = int(day_str)
                date_str = f"{current_year}/{current_month:02d}/{day:02d}"
                if date_str not in dates:  # Avoid duplicates
                    dates.append(date_str)
            continue

        # Pattern B: slash format "1/24・31" or "1/24"
        slash_match = re.search(r'(\d{1,2})/(\d{1,2})', part)
        if slash_match:
            current_month = int(slash_match.group(1))
            first_day = int(slash_match.group(2))
            dates.append(f"{current_year}/{current_month:02d}/{first_day:02d}")

            # Find additional days with ・
            additional_days = re.findall(r'・(\d{1,2})', part)
            for day_str in additional_days:
                day = int(day_str)
                dates.append(f"{current_year}/{current_month:02d}/{day:02d}")
            continue

        # Pattern C: just days "24・31" (no month marker, use current month)
        if current_month and '日' in part:
            day_matches = re.findall(r'(\d{1,2})日', part)
            for day_str in day_matches:
                day = int(day_str)
                dates.append(f"{current_year}/{current_month:02d}/{day:02d}")

    # If no dates found with complex parsing, try simple pattern
    if not dates:
        # Simple pattern: all "月日" occurrences
        all_matches = re.findall(r'(\d{1,2})月(\d{1,2})日', cleaned_text)
        for month_str, day_str in all_matches:
            month = int(month_str)
            day = int(day_str)
            dates.append(f"{current_year}/{month:02d}/{day:02d}")

    # Remove duplicates and sort
    dates = sorted(set(dates))
    return dates


def split_date_range(date_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Split une date au format "2024/10/09 - 2025/01/13" ou "2025/01/13"

    Args:
        date_str: Date au format "YYYY/MM/DD - YYYY/MM/DD" ou "YYYY/MM/DD"

    Returns:
        tuple: (start_date, end_date) ou (date, date) si date simple
               ou (None, None) si date invalide
    """
    if not date_str:
        return None, None

    # Plage de dates
    if ' - ' in date_str:
        parts = date_str.split(' - ')
        return parts[0].strip(), parts[1].strip()
    else:
        # Date simple (start_date et end_date identiques)
        single_date = date_str.strip()
        return single_date, single_date


def format_date_range(start_date: Optional[str], end_date: Optional[str]) -> Optional[str]:
    """
    Formate une plage de dates au format "YYYY/MM/DD - YYYY/MM/DD"

    Args:
        start_date: Date de début ou None
        end_date: Date de fin

    Returns:
        str: Date formatée ou None
    """
    if not end_date:
        return None

    if start_date and start_date != end_date:
        return f"{start_date} - {end_date}"
    else:
        return end_date
