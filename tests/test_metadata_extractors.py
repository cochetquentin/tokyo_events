"""
Tests unitaires pour les extracteurs de métadonnées
"""

import pytest
from src.metadata_extractors import extract_hours, extract_fee, extract_access


class TestExtractHours:
    """Tests pour extract_hours()"""

    def test_de_x_a_y(self):
        """Test format 'de Xh à Yh'"""
        assert extract_hours("Ouvert de 11h à 13h30") == "de 11h à 13h30"
        assert extract_hours("De 9h à 17h") == "de 9h à 17h"
        assert extract_hours("de 10h00 à 18h00") == "de 10h00 à 18h00"

    def test_x_hyphen_y(self):
        """Test format 'Xh-Yh'"""
        assert extract_hours("9h-17h") == "9h-17h"
        assert extract_hours("10h30-18h30") == "10h30-18h30"
        assert extract_hours("Horaires : 11h - 19h") == "11h - 19h"

    def test_horaires_prefix(self):
        """Test avec préfixe 'Horaires :'"""
        result = extract_hours("Horaires : 10h-18h tous les jours")
        assert "10h" in result
        assert "18h" in result

    def test_no_hours(self):
        """Test sans horaires"""
        assert extract_hours("Pas d'horaires ici") is None
        assert extract_hours("") is None
        assert extract_hours("Entrée gratuite") is None

    def test_multiple_hours(self):
        """Test avec plusieurs horaires (retourne le premier)"""
        result = extract_hours("de 9h à 12h et de 14h à 18h")
        assert "de 9h à 12h" in result


class TestExtractFee:
    """Tests pour extract_fee()"""

    def test_entree_gratuite(self):
        """Test 'Entrée gratuite'"""
        assert extract_fee("Entrée gratuite") == "Entrée gratuite"
        assert extract_fee("entrée gratuite") == "Entrée gratuite"

    def test_gratuit(self):
        """Test 'Gratuit'"""
        assert extract_fee("Accès gratuit") == "Gratuit"
        assert extract_fee("C'est gratuit") == "Gratuit"

    def test_yens_amount(self):
        """Test montants en yens"""
        result1 = extract_fee("Tarif : 1,500 yens")
        assert "1,500 yens" in result1

        result2 = extract_fee("Prix : 500 yens")
        assert "500 yens" in result2

        result3 = extract_fee("Entrée : 1 000 yens")
        assert result3 is not None

    def test_no_fee(self):
        """Test sans tarif"""
        assert extract_fee("Pas de tarif ici") is None
        assert extract_fee("") is None
        assert extract_fee("de 9h à 17h") is None

    def test_various_formats(self):
        """Test différents formats de montants"""
        assert extract_fee("1500 yens") is not None
        assert extract_fee("2,000 yens") is not None
        assert extract_fee("1 000 yen") is not None  # Singulier


class TestExtractAccess:
    """Tests pour extract_access()"""

    def test_acces_prefix(self):
        """Test avec préfixe 'Accès :'"""
        result = extract_access("Accès : Station Shibuya (ligne JR)")
        assert result == "Station Shibuya (ligne JR)"

    def test_station_mention(self):
        """Test mention de station"""
        result = extract_access("Proche de la station Asakusa")
        assert "station" in result.lower()
        assert "Asakusa" in result

    def test_no_access(self):
        """Test sans info d'accès"""
        assert extract_access("Pas d'accès ici") is None
        assert extract_access("") is None
        assert extract_access("Entrée gratuite") is None

    def test_accent_variations(self):
        """Test variations d'accents"""
        result1 = extract_access("Accès : Station X")
        result2 = extract_access("Acces : Station X")  # Sans accent
        assert result1 is not None or result2 is not None


class TestEdgeCases:
    """Tests des cas limites"""

    def test_none_input(self):
        """Test avec None en entrée"""
        assert extract_hours(None) is None
        assert extract_fee(None) is None
        assert extract_access(None) is None

    def test_mixed_content(self):
        """Test avec contenu mixte"""
        text = "Horaires : de 10h à 18h. Entrée gratuite. Accès : Station Shibuya"
        assert extract_hours(text) is not None
        assert extract_fee(text) == "Entrée gratuite"
        assert extract_access(text) is not None

    def test_case_insensitive(self):
        """Test insensibilité à la casse"""
        assert extract_hours("DE 10H À 18H") is not None
        assert extract_fee("ENTRÉE GRATUITE") == "Entrée gratuite"
        assert extract_access("ACCÈS : STATION X") is not None

    def test_html_entities(self):
        """Test que les fonctions gèrent du texte brut (pas d'entités HTML)"""
        # Ces fonctions reçoivent du texte déjà nettoyé par BeautifulSoup
        result = extract_hours("de 10h à 18h")  # Texte normal
        assert result is not None
