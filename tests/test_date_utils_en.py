"""
Tests unitaires pour les utilitaires de dates anglaises (Tokyo Cheapo)
"""

import pytest
from datetime import datetime
from src.date_utils_en import (
    parse_english_date,
    parse_english_date_range,
    infer_year_from_month,
    parse_single_date_components,
)


class TestParseEnglishDate:
    """Tests pour parse_english_date()"""

    def test_month_day(self):
        """Format 'Feb 28' avec default_year"""
        result = parse_english_date("Feb 28", default_year=2026)
        assert result == "2026/02/28"

    def test_month_day_year(self):
        """Format 'Mar 1 2026' avec année explicite"""
        result = parse_english_date("Mar 1 2026")
        assert result == "2026/03/01"

    def test_full_month_name(self):
        """Format 'March 1' avec nom complet"""
        result = parse_english_date("March 1", default_year=2026)
        assert result == "2026/03/01"

    def test_day_zero_padded(self):
        """Jour doit être zero-padded"""
        result = parse_english_date("Jan 5", default_year=2026)
        assert result == "2026/01/05"

    def test_all_months(self):
        """Tous les mois doivent être supportés"""
        months = [
            ("Jan", "01"), ("Feb", "02"), ("Mar", "03"), ("Apr", "04"),
            ("May", "05"), ("Jun", "06"), ("Jul", "07"), ("Aug", "08"),
            ("Sep", "09"), ("Oct", "10"), ("Nov", "11"), ("Dec", "12"),
        ]
        for abbr, num in months:
            result = parse_english_date(f"{abbr} 15", default_year=2026)
            assert result == f"2026/{num}/15", f"Failed for {abbr}"

    def test_empty_string(self):
        result = parse_english_date("")
        assert result is None

    def test_none(self):
        result = parse_english_date(None)
        assert result is None

    def test_invalid_month(self):
        result = parse_english_date("Xyz 15", default_year=2026)
        assert result is None

    def test_explicit_year_overrides_default(self):
        """L'année explicite dans la chaîne prime sur default_year"""
        result = parse_english_date("Mar 1 2027", default_year=2026)
        assert result == "2027/03/01"


class TestParseEnglishDateRange:
    """Tests pour parse_english_date_range()"""

    def test_same_year_range(self):
        """Plage sur la même année"""
        start, end = parse_english_date_range("Feb 28", "Mar 15", current_year=2026)
        assert start == "2026/02/28"
        assert end == "2026/03/15"

    def test_cross_year_range(self):
        """Plage qui traverse l'année (Nov → Mar)"""
        start, end = parse_english_date_range("Nov 17", "Mar 1 2026", current_year=2026)
        assert start == "2025/11/17"
        assert end == "2026/03/01"

    def test_end_with_explicit_year(self):
        """Date de fin avec année explicite"""
        start, end = parse_english_date_range("Dec 25", "Jan 5 2026", current_year=2026)
        assert start == "2025/12/25"
        assert end == "2026/01/05"

    def test_same_month_range(self):
        """Plage dans le même mois"""
        start, end = parse_english_date_range("Mar 1", "Mar 31", current_year=2026)
        assert start == "2026/03/01"
        assert end == "2026/03/31"

    def test_invalid_start(self):
        start, end = parse_english_date_range("", "Mar 1", current_year=2026)
        assert start is None
        assert end is None

    def test_invalid_end(self):
        start, end = parse_english_date_range("Feb 1", "", current_year=2026)
        assert start is None
        assert end is None


class TestInferYearFromMonth:
    """Tests pour infer_year_from_month()"""

    def test_current_month_returns_current_year(self):
        ref = datetime(2026, 4, 15)
        assert infer_year_from_month(4, ref) == 2026

    def test_future_month_returns_current_year(self):
        ref = datetime(2026, 4, 15)
        assert infer_year_from_month(7, ref) == 2026

    def test_recent_past_month_returns_current_year(self):
        """Mois 2 mois en arrière → même année"""
        ref = datetime(2026, 4, 15)
        assert infer_year_from_month(2, ref) == 2026

    def test_old_past_month_returns_next_year(self):
        """Mois de plus de 2 mois en arrière → année suivante"""
        ref = datetime(2026, 4, 15)
        assert infer_year_from_month(1, ref) == 2027


class TestParseSingleDateComponents:
    """Tests pour parse_single_date_components()"""

    def test_day_text_with_comma(self):
        """Format 'Sun, Mar' + '01'"""
        result = parse_single_date_components("Sun, Mar", "01", current_year=2026)
        assert result is not None
        assert "/03/01" in result

    def test_day_text_without_comma(self):
        """Format 'Mar' + '15'"""
        result = parse_single_date_components("Mar", "15", current_year=2026)
        assert result is not None
        assert "/03/15" in result

    def test_empty_day_text(self):
        result = parse_single_date_components("", "01", current_year=2026)
        assert result is None

    def test_empty_date_num(self):
        result = parse_single_date_components("Sun, Mar", "", current_year=2026)
        assert result is None

    def test_invalid_month(self):
        result = parse_single_date_components("Sun, Xyz", "01", current_year=2026)
        assert result is None
