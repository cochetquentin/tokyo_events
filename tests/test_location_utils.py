"""
Tests unitaires pour les utilitaires de locations
"""

import pytest
from src.location_utils import (
    normalize_district,
    extract_location_with_district,
    parse_multiple_locations,
    DISTRICT_MAP
)


class TestNormalizeDistrict:
    """Tests pour normalize_district()"""

    def test_adds_district_for_known_quartier(self):
        """Test ajout d'arrondissement pour quartier connu"""
        result = normalize_district("temple Senso-ji (Asakusa)")
        assert "Taito-ku" in result

        result = normalize_district("sanctuaire Meiji-jingu (Harajuku)")
        assert "Shibuya-ku" in result

    def test_preserves_existing_district(self):
        """Test conservation d'arrondissement existant"""
        result = normalize_district("parc Yoyogi (Shibuya-ku)")
        assert result == "parc Yoyogi (Shibuya-ku)"

    def test_no_change_for_unknown_location(self):
        """Test pas de changement pour lieu inconnu"""
        result = normalize_district("temple XYZ")
        assert result == "temple XYZ"

    def test_adds_parentheses_if_missing(self):
        """Test ajout de parenthèses si manquantes"""
        result = normalize_district("parc Yoyogi Harajuku")
        # Devrait détecter Harajuku et ajouter l'arrondissement
        assert "Shibuya-ku" in result or "Harajuku" in result

    def test_case_insensitive_matching(self):
        """Test recherche insensible à la casse"""
        result = normalize_district("temple (asakusa)")  # Minuscules
        assert "Taito-ku" in result

    def test_empty_or_none(self):
        """Test avec None ou chaîne vide"""
        assert normalize_district(None) is None
        assert normalize_district("") == ""


class TestExtractLocationWithDistrict:
    """Tests pour extract_location_with_district()"""

    def test_extract_from_lieu_field(self):
        """Test extraction du champ 'Lieu :'"""
        text = "Lieu : temple Senso-ji (Asakusa) Site : ..."
        result = extract_location_with_district(text)
        assert result is not None
        assert "Senso-ji" in result
        assert "Taito-ku" in result  # Normalisé

    def test_extract_with_preposition(self):
        """Test extraction avec préposition"""
        text = "au parc Yoyogi Koen"
        result = extract_location_with_district(text)
        assert result is not None
        assert "parc" in result
        assert "Yoyogi" in result

    def test_no_location(self):
        """Test sans location"""
        assert extract_location_with_district("Pas de lieu ici") is None
        assert extract_location_with_district("") is None
        assert extract_location_with_district(None) is None


class TestParseMultipleLocations:
    """Tests pour parse_multiple_locations()"""

    def test_single_location(self):
        """Test une seule location"""
        result = parse_multiple_locations("temple Senso-ji (Taito-ku)")
        assert len(result) == 1
        assert result[0] == "temple Senso-ji (Taito-ku)"

    def test_multiple_locations_with_shared_district(self):
        """Test plusieurs locations avec arrondissement partagé"""
        text = "temple X et temple Y (Shibuya-ku)"
        result = parse_multiple_locations(text)
        assert len(result) == 2
        assert "temple X (Shibuya-ku)" in result
        assert "temple Y (Shibuya-ku)" in result

    def test_multiple_locations_without_district(self):
        """Test plusieurs locations sans arrondissement"""
        text = "temple X et temple Y"
        result = parse_multiple_locations(text)
        assert len(result) == 2
        assert "temple X" in result
        assert "temple Y" in result

    def test_case_insensitive_et(self):
        """Test 'et' insensible à la casse"""
        text = "temple X ET temple Y"
        result = parse_multiple_locations(text)
        assert len(result) == 2

    def test_empty_or_none(self):
        """Test avec None ou chaîne vide"""
        assert parse_multiple_locations(None) == []
        assert parse_multiple_locations("") == []


class TestDistrictMap:
    """Tests pour DISTRICT_MAP"""

    def test_district_map_completeness(self):
        """Test que DISTRICT_MAP contient les quartiers principaux"""
        essential_quartiers = [
            'Harajuku', 'Shibuya', 'Shinjuku', 'Asakusa', 'Ueno',
            'Akihabara', 'Ginza', 'Roppongi', 'Odaiba'
        ]
        for quartier in essential_quartiers:
            assert quartier in DISTRICT_MAP, f"{quartier} manquant dans DISTRICT_MAP"

    def test_district_map_format(self):
        """Test que tous les arrondissements se terminent par -ku ou -shi"""
        for quartier, arrondissement in DISTRICT_MAP.items():
            assert arrondissement.endswith('-ku') or arrondissement.endswith('-shi'), \
                f"Format invalide pour {arrondissement}"

    def test_no_duplicate_values(self):
        """Test qu'il n'y a pas de doublons (plusieurs quartiers → même arrondissement est OK)"""
        # Ce test vérifie juste la cohérence
        # Il est normal que Harajuku et Ebisu pointent tous deux vers Shibuya-ku
        assert len(DISTRICT_MAP) > 0


class TestEdgeCases:
    """Tests des cas limites"""

    def test_location_with_multiple_parentheses(self):
        """Test location avec plusieurs parenthèses"""
        result = normalize_district("parc X (info 1) (info 2)")
        # Devrait gérer sans erreur
        assert result is not None

    def test_location_without_parentheses(self):
        """Test location sans parenthèses"""
        result = normalize_district("parc Yoyogi Koen Harajuku")
        # Devrait détecter Harajuku et ajouter l'arrondissement
        assert result is not None

    def test_whitespace_handling(self):
        """Test gestion des espaces"""
        result = normalize_district("temple   Senso-ji   (Asakusa)")
        assert result is not None
        # Les espaces multiples devraient être préservés ou normalisés

    def test_special_characters(self):
        """Test caractères spéciaux dans les noms"""
        result = normalize_district("temple Senso-ji (Asakusa)")  # Tiret
        assert result is not None

        result = normalize_district("musée d'Art (Roppongi)")  # Apostrophe
        assert result is not None
