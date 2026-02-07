"""
Utilitaires pour gérer les locations et arrondissements de Tokyo
"""

import re
from typing import Optional


# Mapping des quartiers vers arrondissements (ku)
DISTRICT_MAP = {
    # Arrondissements centraux
    'Harajuku': 'Shibuya-ku',
    'Omotesando': 'Shibuya-ku',
    'Shibuya': 'Shibuya-ku',
    'Shinjuku': 'Shinjuku-ku',
    'Kabukicho': 'Shinjuku-ku',
    'Asakusa': 'Taito-ku',
    'Ueno': 'Taito-ku',
    'Akihabara': 'Chiyoda-ku',
    'Ginza': 'Chuo-ku',
    'Nihonbashi': 'Chuo-ku',
    'Tsukiji': 'Chuo-ku',
    'Roppongi': 'Minato-ku',
    'Akasaka': 'Minato-ku',
    'Odaiba': 'Minato-ku',
    'Azabu': 'Minato-ku',

    # Arrondissements est
    'Ryogoku': 'Sumida-ku',
    'Kinshicho': 'Sumida-ku',
    'Kameido': 'Koto-ku',
    'Kiba': 'Koto-ku',
    'Toyosu': 'Koto-ku',

    # Arrondissements ouest
    'Ikebukuro': 'Toshima-ku',
    'Mejiro': 'Toshima-ku',
    'Nakano': 'Nakano-ku',
    'Koenji': 'Suginami-ku',
    'Ogikubo': 'Suginami-ku',
    'Kichijoji': 'Musashino-shi',

    # Arrondissements sud
    'Meguro': 'Meguro-ku',
    'Ebisu': 'Shibuya-ku',
    'Gotanda': 'Shinagawa-ku',
    'Shinagawa': 'Shinagawa-ku',
    'Osaki': 'Shinagawa-ku',

    # Arrondissements nord
    'Komagome': 'Bunkyo-ku',
    'Hongo': 'Bunkyo-ku',
    'Yanaka': 'Taito-ku',
    'Nippori': 'Arakawa-ku',
    'Tabata': 'Kita-ku',
    'Akabane': 'Kita-ku',
    'Jujo': 'Kita-ku',

    # Périphérie
    'Chofu': 'Chofu-shi',
    'Tachikawa': 'Tachikawa-shi',
    'Machida': 'Machida-shi',
    'Hachioji': 'Hachioji-shi',
}


def normalize_district(location: str) -> str:
    """
    Ajoute l'arrondissement si manquant en utilisant le mapping

    Args:
        location: Nom du lieu (ex: "parc Yoyogi Koen (Harajuku)")

    Returns:
        Location avec arrondissement si possible (ex: "parc Yoyogi Koen (Shibuya-ku)")

    Examples:
        >>> normalize_district("temple Senso-ji (Asakusa)")
        'temple Senso-ji (Taito-ku)'
        >>> normalize_district("sanctuaire Meiji-jingu (Harajuku)")
        'sanctuaire Meiji-jingu (Shibuya-ku)'
    """
    if not location:
        return location

    # Si déjà un arrondissement (-ku ou -shi), ne rien changer
    if re.search(r'-(?:ku|shi)\b', location, re.IGNORECASE):
        return location

    # Chercher un quartier dans le mapping
    for quartier, arrondissement in DISTRICT_MAP.items():
        # Chercher le quartier (case-insensitive)
        if re.search(rf'\b{re.escape(quartier)}\b', location, re.IGNORECASE):
            # Remplacer le quartier par l'arrondissement dans les parenthèses
            location = re.sub(
                rf'\({re.escape(quartier)}\)',
                f'({arrondissement})',
                location,
                flags=re.IGNORECASE
            )
            # Ou ajouter entre parenthèses si pas déjà présent
            if '(' not in location:
                location = f"{location} ({arrondissement})"
            return location

    return location


def extract_location_with_district(text: str) -> Optional[str]:
    """
    Extrait la location et ajoute l'arrondissement si manquant

    Args:
        text: Texte contenant potentiellement une location

    Returns:
        Location normalisée avec arrondissement
    """
    if not text:
        return None

    # Pattern 1: "Lieu :" ou "Lieux :"
    match = re.search(r'Lieux?\s*:\s*(.+?)(?:\s+(?:Site|Horaires|Tarif|en un)\s|$)', text, re.IGNORECASE)
    if match:
        location = match.group(1).strip()
        # Nettoyer
        location = re.sub(r'\s+', ' ', location)
        location = re.sub(r'([^\s])\(', r'\1 (', location)
        # Normaliser l'arrondissement
        return normalize_district(location)

    # Pattern 2: Lieux avec préposition (parc, temple, etc.)
    match = re.search(
        r'(?:au|à|dans le|dans l\')\s+(parc|temple|sanctuaire|jardin|quartier|station|mont|siège|musée|galerie|centre|espace)\s+([A-Za-zÀ-ÿ\-\s]+?)(?:\s+\([^)]+\))?',
        text,
        re.IGNORECASE
    )
    if match:
        location = match.group(1) + ' ' + match.group(2).strip()
        # Ajouter parenthèses si présentes
        paren_match = re.search(r'\([^)]+\)', match.group(0))
        if paren_match:
            location += ' ' + paren_match.group(0)
        return normalize_district(location)

    return None


def parse_multiple_locations(location_text: str) -> list:
    """
    Parse les locations multiples séparées par "et"

    Args:
        location_text: Texte avec plusieurs locations

    Returns:
        Liste de locations individuelles

    Examples:
        >>> parse_multiple_locations("temple X et temple Y (Shibuya-ku)")
        ['temple X (Shibuya-ku)', 'temple Y (Shibuya-ku)']
    """
    if not location_text:
        return []

    # Extraire l'arrondissement s'il est en fin (entre parenthèses)
    arrondissement = None
    arr_match = re.search(r'\(([^)]*-(?:ku|shi))\)\s*$', location_text, re.IGNORECASE)
    if arr_match:
        arrondissement = arr_match.group(1)
        # Retirer l'arrondissement du texte
        location_text = re.sub(r'\s*\([^)]*-(?:ku|shi)\)\s*$', '', location_text, flags=re.IGNORECASE)

    # Séparer par "et"
    if ' et ' not in location_text.lower():
        # Une seule location
        if arrondissement:
            return [f"{location_text.strip()} ({arrondissement})"]
        return [location_text.strip()]

    # Multiples locations
    parts = re.split(r'\s+et\s+', location_text, flags=re.IGNORECASE)
    locations = []

    for part in parts:
        part = part.strip()
        if part:
            # Ajouter l'arrondissement à chaque location
            if arrondissement:
                locations.append(f"{part} ({arrondissement})")
            else:
                locations.append(part)

    return locations
