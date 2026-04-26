"""
Utilitaires pour extraire les métadonnées des événements (horaires, tarifs, etc.)
"""

import re
from typing import Optional


def extract_hours(text: str) -> Optional[str]:
    """
    Extrait les horaires d'un texte

    Args:
        text: Texte contenant potentiellement des horaires

    Returns:
        Chaîne des horaires ou None

    Examples:
        >>> extract_hours("Ouvert de 11h à 13h30")
        'de 11h à 13h30'
        >>> extract_hours("Horaires : 9h-17h")
        '9h-17h'
    """
    if not text:
        return None

    # Pattern 1: "de Xh à Yh" ou "de XhMM à YhMM"
    match = re.search(r'de\s+(\d{1,2})h\s*(\d{2})?\s*à\s+(\d{1,2})h\s*(\d{2})?', text, re.IGNORECASE)
    if match:
        return match.group(0).lower()

    # Pattern 2: "Xh-Yh" ou "XhMM-YhMM"
    match = re.search(r'(\d{1,2})h\s*(\d{2})?\s*[-–]\s*(\d{1,2})h\s*(\d{2})?', text, re.IGNORECASE)
    if match:
        return match.group(0)

    # Pattern 3: "Horaires : X" (capturer ce qui suit)
    match = re.search(r'horaires?\s*:\s*([^\n,\.]+)', text, re.IGNORECASE)
    if match:
        hours = match.group(1).strip()
        # Vérifier que ça contient bien des heures (au moins un chiffre suivi de 'h')
        if re.search(r'\d+h', hours):
            return hours

    return None


def extract_fee(text: str) -> Optional[str]:
    """
    Extrait le tarif/frais d'entrée d'un texte

    Args:
        text: Texte contenant potentiellement un tarif

    Returns:
        Chaîne du tarif ou None

    Examples:
        >>> extract_fee("Entrée gratuite")
        'Entrée gratuite'
        >>> extract_fee("Tarif : 1,500 yens")
        '1,500 yens'
    """
    if not text:
        return None

    # Pattern 1: Entrée gratuite
    if re.search(r'entr[ée]e\s+gratuite', text, re.IGNORECASE):
        return "Entrée gratuite"

    # Pattern 2: Gratuit
    if re.search(r'\bgratuit\b', text, re.IGNORECASE):
        return "Gratuit"

    # Pattern 3: Montant en yens (format: "1,500 yens", "1500 yens", "1 500 yens")
    # Chercher après "Tarif :", "Entrée :", "Prix :"
    match = re.search(r'(?:tarif|entr[ée]e|prix)\s*:\s*([^\n\.]+)', text, re.IGNORECASE)
    if match:
        fee_text = match.group(1).strip()
        # Vérifier que ça contient un montant
        if re.search(r'\d', fee_text):
            return fee_text

    # Pattern 4: Montant en yens (sans préfixe)
    match = re.search(r'(\d[\d\s,]*\s*yens?)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


def extract_access(text: str) -> Optional[str]:
    """
    Extrait les informations d'accès (transports, stations)

    Args:
        text: Texte contenant potentiellement des infos d'accès

    Returns:
        Chaîne d'accès ou None

    Examples:
        >>> extract_access("Accès : Station Shibuya (ligne JR)")
        'Station Shibuya (ligne JR)'
    """
    if not text:
        return None

    # Pattern 1: "Accès :" suivi du texte
    match = re.search(r'acc[èe]s\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern 2: Mention de station
    match = re.search(r'(station\s+[A-Za-z\-\s]+(?:\([^)]+\))?)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None
