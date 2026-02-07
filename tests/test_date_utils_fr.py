"""
Tests unitaires pour les utilitaires de dates françaises
"""

import pytest
from src.date_utils_fr import (
    expand_complex_dates,
    parse_french_date_range,
    is_complex_date_pattern,
    normalize_french_date,
    MOIS_MAPPING
)


class TestExpandComplexDates:
    """Tests pour expand_complex_dates()"""

    def test_simple_dates_with_commas(self):
        """Test dates simples séparées par virgules"""
        result = expand_complex_dates("1er, 6, 11 février 2026")
        assert result == ["2026/02/01", "2026/02/06", "2026/02/11"]

    def test_ranges_with_commas(self):
        """Test plages de dates séparées par virgules"""
        result = expand_complex_dates("6-8, 13-15 février 2026")
        expected = ["2026/02/06", "2026/02/07", "2026/02/08",
                    "2026/02/13", "2026/02/14", "2026/02/15"]
        assert result == expected

    def test_complex_pattern(self):
        """Test pattern complexe complet"""
        result = expand_complex_dates("1er, 6-8, 11, 13-15, 20-23 et 27-28 février 2026")
        expected = ["2026/02/01", "2026/02/06", "2026/02/07", "2026/02/08", "2026/02/11",
                    "2026/02/13", "2026/02/14", "2026/02/15",
                    "2026/02/20", "2026/02/21", "2026/02/22", "2026/02/23",
                    "2026/02/27", "2026/02/28"]
        assert result == expected

    def test_with_et_keyword(self):
        """Test avec mot-clé 'et'"""
        result = expand_complex_dates("1er et 15 février 2026")
        assert result == ["2026/02/01", "2026/02/15"]

    def test_no_year(self):
        """Test sans année (utilise default_year)"""
        result = expand_complex_dates("1er, 6, 11 février", default_year=2025)
        assert result == ["2025/02/01", "2025/02/06", "2025/02/11"]

    def test_empty_string(self):
        """Test chaîne vide"""
        result = expand_complex_dates("")
        assert result == []

    def test_deduplicate_and_sort(self):
        """Test dédoublonnage et tri"""
        result = expand_complex_dates("11, 6, 1er, 6 février 2026")
        assert result == ["2026/02/01", "2026/02/06", "2026/02/11"]


class TestParseFrenchDateRange:
    """Tests pour parse_french_date_range()"""

    def test_cross_year_range(self):
        """Test plage entre deux années"""
        start, end = parse_french_date_range("Du 31 décembre 2024 au 4 janvier 2025")
        assert start == "2024/12/31"
        assert end == "2025/01/04"

    def test_cross_month_range(self):
        """Test plage entre deux mois (même année)"""
        start, end = parse_french_date_range("Du 8 février au 2 mars 2025")
        assert start == "2025/02/08"
        assert end == "2025/03/02"

    def test_same_month_range(self):
        """Test plage même mois"""
        start, end = parse_french_date_range("Du 1er au 3 janvier 2025")
        assert start == "2025/01/01"
        assert end == "2025/01/03"

    def test_jusqu_au(self):
        """Test 'Jusqu'au'"""
        start, end = parse_french_date_range("Jusqu'au 25 décembre 2025")
        assert start == "2025/12/01"
        assert end == "2025/12/25"

    def test_jusqu_au_with_parentheses(self):
        """Test 'jusqu'au' entre parenthèses"""
        start, end = parse_french_date_range("(jusqu'au 8 janvier 2026)")
        assert start == "2026/01/01"
        assert end == "2026/01/08"

    def test_simple_range_no_du_au(self):
        """Test plage sans 'Du...au'"""
        start, end = parse_french_date_range("1er-25 février 2026")
        assert start == "2026/02/01"
        assert end == "2026/02/25"

    def test_cross_month_no_du_au(self):
        """Test plage entre mois sans 'Du...au'"""
        start, end = parse_french_date_range("30 juin-1er juillet 2025")
        assert start == "2025/06/30"
        assert end == "2025/07/01"

    def test_single_date(self):
        """Test date simple"""
        start, end = parse_french_date_range("3 février 2025")
        assert start == "2025/02/03"
        assert end == "2025/02/03"

    def test_single_date_with_er(self):
        """Test date simple avec 'er'"""
        start, end = parse_french_date_range("1er février 2025")
        assert start == "2025/02/01"
        assert end == "2025/02/01"

    def test_empty_string(self):
        """Test chaîne vide"""
        start, end = parse_french_date_range("")
        assert start is None
        assert end is None

    def test_all_months(self):
        """Test tous les mois"""
        # Tester avec un sous-ensemble (sans doublons)
        months_to_test = [
            ('janvier', '01'), ('février', '02'), ('mars', '03'), ('avril', '04'),
            ('mai', '05'), ('juin', '06'), ('juillet', '07'), ('août', '08'),
            ('septembre', '09'), ('octobre', '10'), ('novembre', '11'), ('décembre', '12')
        ]
        for month_name, month_num in months_to_test:
            start, end = parse_french_date_range(f"15 {month_name} 2025")
            assert start == f"2025/{month_num}/15", f"Failed for {month_name}"
            assert end == f"2025/{month_num}/15", f"Failed for {month_name}"


class TestIsComplexDatePattern:
    """Tests pour is_complex_date_pattern()"""

    def test_with_commas(self):
        """Test détection avec virgules"""
        assert is_complex_date_pattern("1er, 6, 11 février 2026") is True

    def test_with_et(self):
        """Test détection avec 'et'"""
        assert is_complex_date_pattern("1er et 15 février 2026") is True

    def test_simple_range(self):
        """Test pattern simple (pas complexe)"""
        assert is_complex_date_pattern("Du 1er au 3 janvier 2025") is False

    def test_single_date(self):
        """Test date simple (pas complexe)"""
        assert is_complex_date_pattern("3 février 2025") is False

    def test_empty_string(self):
        """Test chaîne vide"""
        assert is_complex_date_pattern("") is False


class TestNormalizeFrenchDate:
    """Tests pour normalize_french_date()"""

    def test_complex_pattern_returns_first_last(self):
        """Test que les patterns complexes retournent première-dernière date"""
        result = normalize_french_date("1er, 6-8, 11 février 2026")
        assert result == "2026/02/01 - 2026/02/11"

    def test_simple_range(self):
        """Test plage simple"""
        result = normalize_french_date("Du 1er au 3 janvier 2025")
        assert result == "2025/01/01 - 2025/01/03"

    def test_single_date(self):
        """Test date simple sans plage"""
        result = normalize_french_date("3 février 2025")
        assert result == "2025/02/03"

    def test_empty_string(self):
        """Test chaîne vide"""
        result = normalize_french_date("")
        assert result is None


class TestEdgeCases:
    """Tests des cas limites"""

    def test_accents_in_month_names(self):
        """Test accents dans les noms de mois"""
        start, end = parse_french_date_range("15 février 2025")
        assert start == "2025/02/15"

        start, end = parse_french_date_range("15 fevrier 2025")  # Sans accent
        assert start == "2025/02/15"

    def test_december_to_january(self):
        """Test transition décembre-janvier"""
        start, end = parse_french_date_range("Du 31 décembre 2025 au 1er janvier 2026")
        assert start == "2025/12/31"
        assert end == "2026/01/01"

    def test_leap_year_february(self):
        """Test février année bissextile"""
        result = expand_complex_dates("27-29 février 2024")  # 2024 est bissextile
        assert "2024/02/29" in result

    def test_different_apostrophes(self):
        """Test différents types d'apostrophes"""
        # Apostrophe droite
        start1, end1 = parse_french_date_range("Jusqu'au 8 janvier 2026")
        # Apostrophe typographique
        start2, end2 = parse_french_date_range("Jusqu'au 8 janvier 2026")
        assert start1 == start2
        assert end1 == end2

    def test_whitespace_variations(self):
        """Test variations d'espaces"""
        start1, end1 = parse_french_date_range("Du 1er au 3 janvier 2025")
        start2, end2 = parse_french_date_range("Du  1er  au  3  janvier  2025")  # Espaces multiples
        assert start1 == start2
        assert end1 == end2
