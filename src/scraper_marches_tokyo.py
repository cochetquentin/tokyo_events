import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import List, Dict, Optional
import re
import unicodedata

from src.date_utils import split_date_range, format_date_range
from src.date_utils_fr import parse_french_date_range, is_complex_date_pattern, expand_complex_dates
from src.location_utils import normalize_district, extract_location_with_district
from src.metadata_extractors import extract_hours, extract_fee
from src.database import EventDatabase
from src.gps_extractor import GPSExtractor


class TokyoMarcheScraper:
    """
    Scraper pour les marchés aux puces de Tokyo depuis ichiban-japan.com
    """

    # URL fixe pour les marchés aux puces (pas de paramètre mois/année)
    BASE_URL = "https://ichiban-japan.com/marches-aux-puces-tokyo/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_marches(self) -> List[Dict]:
        """
        Scrape tous les marchés aux puces

        Returns:
            Liste de dictionnaires contenant les informations des marchés
        """
        url = self.BASE_URL
        print(f"Scraping: {url}")

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération de la page: {e}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        marches = []

        # Parser le contenu de la page
        marches = self._parse_page(soup)

        print(f"✓ {len(marches)} marchés trouvés")
        return marches

    def _parse_page(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Parse le contenu HTML de la page

        Args:
            soup: Objet BeautifulSoup

        Returns:
            Liste des marchés parsés
        """
        marches = []

        # Mots-clés à filtrer (bruit)
        noise_keywords = ['articles similaires', 'recherche', 'mon livre', 'mes livres', 'jipangu',
                         'articles recommandés', 'annuler la réponse', 'commentaire',
                         'guigui', 'réseaux sociaux', 'régions du japon']

        # Trouver tous les h2 avec class="wp-block-heading"
        h2_elements = soup.find_all('h2', class_='wp-block-heading')

        for h2 in h2_elements:
            # Utiliser separator=' ' pour ajouter des espaces entre les éléments (ex: <sup>)
            title_text = h2.get_text(separator=' ', strip=True)

            # Normaliser Unicode (gère superscripts automatiquement)
            title_text = unicodedata.normalize("NFKC", title_text)

            # Filtrer le bruit
            if any(keyword in title_text.lower() for keyword in noise_keywords):
                continue

            # Les marchés n'ont généralement PAS de dates dans le titre H2
            # Le titre est juste le nom du marché
            name = title_text.strip()

            if not name or len(name) < 3:
                continue

            # Nettoyer les espaces insécables (nbsp) dans le nom
            name = name.replace('\xa0', ' ').replace('&nbsp;', ' ')
            name = re.sub(r'\s+', ' ', name).strip()

            # Créer l'entrée du marché
            marche = {
                'name': name,
                'dates': [],  # Liste de dates individuelles pour marchés
                'start_date': None,
                'end_date': None,
                'location': None,
                'description': '',
                'website': None,
                'googlemap_link': None,
                'hours': None,
                'fee': None
            }

            # Collecter tous les paragraphes et liens suivants
            next_elem = h2.find_next_sibling()
            paragraphs = []
            paragraph_elements = []  # Garder les éléments BeautifulSoup pour extraire les liens

            while next_elem and next_elem.name != 'h2':
                if next_elem.name == 'p':
                    # Utiliser separator=' ' pour ajouter des espaces entre les éléments
                    p_text = next_elem.get_text(separator=' ', strip=True)
                    # Normaliser Unicode
                    p_text = unicodedata.normalize("NFKC", p_text)
                    # Nettoyer les espaces multiples
                    p_text = re.sub(r'\s+', ' ', p_text)
                    p_text = re.sub(r'\s+([,;:.!?])', r'\1', p_text)

                    # Ignorer les embeds Instagram
                    if not ('Une publication partagée par' in p_text or 'instagram' in p_text.lower()):
                        paragraphs.append(p_text)
                        paragraph_elements.append(next_elem)

                next_elem = next_elem.find_next_sibling()

            # Extraire les informations des paragraphes
            if paragraphs:
                # Chercher dans le dernier ou avant-dernier paragraphe (métadonnées)
                for i, p in enumerate(paragraphs):
                    p_elem = paragraph_elements[i]

                    # Chercher dates complexes (pattern spécial pour marchés)
                    # Ex: "1er, 6-8, 11, 13-15, 20-23 et 27-28 février 2026"
                    if is_complex_date_pattern(p):
                        # Utiliser expand_complex_dates pour obtenir toutes les dates individuelles
                        dates_list = expand_complex_dates(p)
                        if dates_list:
                            marche['dates'] = dates_list
                            marche['start_date'] = dates_list[0]
                            marche['end_date'] = dates_list[-1]
                    # Sinon chercher pattern de dates standard
                    elif not marche['start_date']:
                        dates_from_p = self._extract_dates_from_paragraph(p)
                        if dates_from_p:
                            start, end = split_date_range(dates_from_p)
                            marche['start_date'] = start
                            marche['end_date'] = end

                    # Chercher le lieu avec pattern "Lieu :"
                    if not marche['location']:
                        location_from_lieu = self._extract_location_from_lieu_field(p)
                        if location_from_lieu:
                            marche['location'] = normalize_district(location_from_lieu)

                    # Extraire heures et tarifs
                    if not marche['hours']:
                        marche['hours'] = extract_hours(p)
                    if not marche['fee']:
                        marche['fee'] = extract_fee(p)

                    # Extraire les liens du paragraphe
                    marche['website'] = marche['website'] or self._extract_official_url_with_fallback(p_elem)
                    marche['googlemap_link'] = marche['googlemap_link'] or self._extract_googlemap_link(p_elem)

                # Description: prendre les paragraphes descriptifs (pas celui avec "Lieu :")
                description_parts = []
                for p in paragraphs[:2]:
                    if len(p) > 20 and 'Lieu :' not in p and 'Site de l' not in p and 'Du ' not in p:
                        description_parts.append(p)

                if description_parts:
                    marche['description'] = ' '.join(description_parts[:2])

            # Ne garder que les marchés valides
            if marche.get('start_date') or (marche['description'] and len(marche['description']) > 20):
                marches.append(marche)

        return marches

    def _extract_location_from_lieu_field(self, text: str) -> Optional[str]:
        """
        Extrait la localisation spécifiquement du champ "Lieu :" ou "Lieux :"
        """
        match = re.search(r'Lieux?\s*:\s*(.+?)(?:\s+(?:Site|Horaires|Tarif|en un)\s|$)', text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            location = re.sub(r'\s+', ' ', location)
            location = re.sub(r'([^\s])\(', r'\1 (', location)
            return location
        return None

    def _extract_dates_from_paragraph(self, text: str) -> Optional[str]:
        """
        Extrait les dates du paragraphe (formats standard)
        """
        # Utiliser le parser français
        start, end = parse_french_date_range(text)
        if start and end:
            if start == end:
                return start
            return f"{start} - {end}"
        return None

    def _extract_official_url_with_fallback(self, paragraph_elem) -> Optional[str]:
        """
        Extrait l'URL officielle avec hiérarchie de fallback
        """
        if not paragraph_elem:
            return None

        links = paragraph_elem.find_all('a')

        # Priority 1: "Site de l'événement" / "Site officiel"
        for link in links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True).lower()
            if 'site' in link_text and ('événement' in link_text or 'officiel' in link_text):
                if href and href.startswith('http'):
                    return href

        # Priority 2: Lien avec "site" dans le texte
        for link in links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True).lower()
            if 'site' in link_text:
                if href and href.startswith('http'):
                    return href

        # Priority 3: Tout lien HTTP qui n'est pas Google Maps
        for link in links:
            href = link.get('href', '')
            if href.startswith('http') and 'google' not in href and 'goo.gl' not in href:
                return href

        return None

    def _extract_googlemap_link(self, paragraph_elem) -> Optional[str]:
        """
        Extrait le lien Google Maps
        """
        if not paragraph_elem:
            return None

        links = paragraph_elem.find_all('a')
        for link in links:
            href = link.get('href', '')
            if ('google' in href and 'maps' in href) or 'goo.gl' in href or 'maps.app.goo.gl' in href:
                return href

        return None

    def save_to_database(self, marches: List[Dict], db_path: str = None):
        """
        Sauvegarde les marchés dans la base de données SQLite.
        Extrait automatiquement les coordonnées GPS depuis les liens Google Maps.

        Args:
            marches: Liste des marchés
            db_path: Chemin vers la base de données (optionnel, par défaut data/tokyo_events.sqlite)

        Returns:
            int: Nombre de marchés sauvegardés
        """
        if not db_path:
            db_path = "data/tokyo_events.sqlite"

        # Extraire les coordonnées GPS pour chaque marché
        gps_extractor = GPSExtractor()
        gps_success = 0

        for marche in marches:
            if marche.get('googlemap_link'):
                coords = gps_extractor.extract_from_googlemap_link(marche['googlemap_link'])
                if coords:
                    marche['latitude'], marche['longitude'] = coords
                    gps_success += 1

        db = EventDatabase(db_path)
        count = db.insert_events(marches, event_type='marches')

        print(f"✓ {count} marchés sauvegardés dans la base de données {db_path}")
        if gps_success > 0:
            print(f"✓ {gps_success}/{len(marches)} coordonnées GPS extraites automatiquement")
        return count


def main():
    """
    Fonction principale pour utiliser le scraper
    """
    scraper = TokyoMarcheScraper()

    print("=== Scraper de Marchés aux Puces Tokyo ===\n")

    marches = scraper.scrape_marches()

    if marches:
        # Sauvegarder dans la base de données
        scraper.save_to_database(marches)

        # Afficher un aperçu
        print(f"\n=== Aperçu des {min(3, len(marches))} premiers marchés ===")
        for i, marche in enumerate(marches[:3], 1):
            print(f"\n{i}. {marche['name']}")
            if marche.get('dates') and len(marche['dates']) > 0:
                print(f"   Dates ({len(marche['dates'])} occurrences): {', '.join(marche['dates'][:5])}...")
            elif marche.get('start_date'):
                dates_display = format_date_range(marche.get('start_date'), marche.get('end_date'))
                print(f"   Dates: {dates_display}")
            if marche.get('location'):
                print(f"   Lieu: {marche['location']}")
            if marche.get('hours'):
                print(f"   Horaires: {marche['hours']}")


if __name__ == "__main__":
    main()
