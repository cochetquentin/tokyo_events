"""
Tests unitaires pour les utilitaires de dates japonaises
"""

import pytest
from src.date_utils import (
    parse_japanese_dates,
    parse_japanese_dates_list,
    split_date_range,
    format_date_range,
)


class TestParseJapaneseDatesList:
    """Tests pour parse_japanese_dates_list()"""

    def test_single_date_with_year(self):
        """Date unique avec année: 2026年1月17日(土)"""
        result = parse_japanese_dates_list("2026年1月17日(土)")
        assert result == ["2026/01/17"]

    def test_single_date_without_year(self):
        """Date unique sans année, utilise default_year"""
        result = parse_japanese_dates_list("1月17日", default_year=2026)
        assert result == ["2026/01/17"]

    def test_multiple_dates_same_month(self):
        """Plusieurs dates dans le même mois"""
        result = parse_japanese_dates_list("1月17日(土)・24日(土)・31日(土)", default_year=2026)
        assert result == ["2026/01/17", "2026/01/24", "2026/01/31"]

    def test_multiple_dates_different_months(self):
        """Dates sur plusieurs mois"""
        result = parse_japanese_dates_list("1月17日・24日・31日、2月7日・14日", default_year=2026)
        assert "2026/01/17" in result
        assert "2026/01/24" in result
        assert "2026/02/07" in result
        assert "2026/02/14" in result

    def test_date_range_with_tilde(self):
        """Plage avec tilde: 7月26日～8月2日"""
        result = parse_japanese_dates_list("7月26日～8月2日", default_year=2026)
        assert "2026/07/26" in result
        assert "2026/08/02" in result
        assert len(result) == 2

    def test_cross_year_in_range(self):
        """Plage qui traverse l'année: 12月31日～1月3日"""
        result = parse_japanese_dates_list("12月31日～1月3日", default_year=2026)
        assert "2026/12/31" in result
        assert "2027/01/03" in result

    def test_slash_format(self):
        """Format slash: 1/17 — seules les occurrences 'M/D' complètes sont parsées"""
        # Le "24" isolé après "・" n'est pas au format M/D donc non parsé
        result = parse_japanese_dates_list("1/17", default_year=2026)
        assert "2026/01/17" in result

    def test_slash_format_multiple(self):
        """Plusieurs dates au format slash complet"""
        result = parse_japanese_dates_list("1/17・1/24", default_year=2026)
        assert "2026/01/17" in result
        assert "2026/01/24" in result

    def test_complex_cross_year(self):
        """Format complexe cross-year: 2025年12/24、2026年1/24"""
        # Le "31" isolé après "・" sans M/ n'est pas parsé en slash format
        result = parse_japanese_dates_list("2025年12/24、2026年1/24")
        assert "2025/12/24" in result
        assert "2026/01/24" in result

    def test_removes_day_of_week_markers(self):
        """Les marqueurs de jour (土)(日) doivent être ignorés"""
        result = parse_japanese_dates_list("1月17日(土)・1月18日(日)", default_year=2026)
        assert result == ["2026/01/17", "2026/01/18"]

    def test_sorted_output(self):
        """Le résultat doit être trié"""
        result = parse_japanese_dates_list("2月7日・1月17日", default_year=2026)
        assert result == sorted(result)

    def test_no_duplicates(self):
        """Pas de doublons dans le résultat"""
        result = parse_japanese_dates_list("1月17日・1月17日", default_year=2026)
        assert result == ["2026/01/17"]

    def test_empty_string(self):
        result = parse_japanese_dates_list("")
        assert result == []

    def test_none(self):
        result = parse_japanese_dates_list(None)
        assert result == []


class TestParseJapaneseDates:
    """Tests pour parse_japanese_dates() — wrapper legacy"""

    def test_returns_first_and_last(self):
        """Doit retourner (première_date, dernière_date)"""
        start, end = parse_japanese_dates("1月17日・24日・31日", default_year=2026)
        assert start == "2026/01/17"
        assert end == "2026/01/31"

    def test_single_date_same_start_end(self):
        """Date unique → start == end"""
        start, end = parse_japanese_dates("1月17日(土)", default_year=2026)
        assert start == "2026/01/17"
        assert end == "2026/01/17"

    def test_empty_returns_none_tuple(self):
        start, end = parse_japanese_dates("")
        assert start is None
        assert end is None


class TestSplitDateRange:
    """Tests pour split_date_range()"""

    def test_range_with_dash(self):
        """Plage avec tiret: '2025/03/01 - 2025/04/30'"""
        start, end = split_date_range("2025/03/01 - 2025/04/30")
        assert start == "2025/03/01"
        assert end == "2025/04/30"

    def test_single_date(self):
        """Date unique → start et end identiques"""
        start, end = split_date_range("2025/03/15")
        assert start == "2025/03/15"
        assert end == "2025/03/15"

    def test_empty_string(self):
        start, end = split_date_range("")
        assert start is None
        assert end is None

    def test_none(self):
        start, end = split_date_range(None)
        assert start is None
        assert end is None

    def test_strips_whitespace(self):
        start, end = split_date_range("  2025/03/01 - 2025/04/30  ")
        assert start == "2025/03/01"
        assert end == "2025/04/30"


class TestFormatDateRange:
    """Tests pour format_date_range()"""

    def test_different_dates(self):
        result = format_date_range("2025/03/01", "2025/04/30")
        assert result == "2025/03/01 - 2025/04/30"

    def test_same_date(self):
        """Dates identiques → retourner juste end_date"""
        result = format_date_range("2025/03/15", "2025/03/15")
        assert result == "2025/03/15"

    def test_no_start_date(self):
        """Pas de start_date → retourner end_date"""
        result = format_date_range(None, "2025/04/30")
        assert result == "2025/04/30"

    def test_no_end_date(self):
        """Pas de end_date → retourner None"""
        result = format_date_range("2025/03/01", None)
        assert result is None
