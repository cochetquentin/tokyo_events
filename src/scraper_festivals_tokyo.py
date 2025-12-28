import requests
from bs4 import BeautifulSoup
import json
import csv
from datetime import datetime
from typing import List, Dict, Optional
import re
import sys

# Fix encoding issues on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class TokyoFestivalScraper:
    """
    Scraper pour les festivals de Tokyo depuis ichiban-japan.com
    """

    BASE_URL = "https://ichiban-japan.com/festivals-tokyo-{month}-{year}/"

    MONTHS_FR = {
        1: "janvier", 2: "fevrier", 3: "mars", 4: "avril",
        5: "mai", 6: "juin", 7: "juillet", 8: "aout",
        9: "septembre", 10: "octobre", 11: "novembre", 12: "decembre"
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_url(self, month: int, year: int) -> str:
        """
        Génère l'URL pour un mois et une année donnés

        Args:
            month: Numéro du mois (1-12)
            year: Année (ex: 2025)

        Returns:
            URL complète
        """
        month_name = self.MONTHS_FR.get(month)
        if not month_name:
            raise ValueError(f"Mois invalide: {month}. Doit être entre 1 et 12.")

        return self.BASE_URL.format(month=month_name, year=year)

    def scrape_festivals(self, month: int, year: int) -> List[Dict]:
        """
        Scrape les festivals pour un mois et une année donnés

        Args:
            month: Numéro du mois (1-12)
            year: Année

        Returns:
            Liste de dictionnaires contenant les informations des festivals
        """
        url = self.get_url(month, year)
        print(f"Scraping: {url}")

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération de la page: {e}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        festivals = []

        # Parser le contenu de la page
        festivals = self._parse_page(soup, month, year)

        print(f"✓ {len(festivals)} festivals trouvés pour {self.MONTHS_FR[month]} {year}")
        return festivals

    def _parse_page(self, soup: BeautifulSoup, month: int, year: int) -> List[Dict]:
        """
        Parse le contenu HTML de la page

        Args:
            soup: Objet BeautifulSoup
            month: Mois
            year: Année

        Returns:
            Liste des festivals parsés
        """
        festivals = []

        # Mots-clés à filtrer (bruit)
        # Note: Ne pas filtrer "les festivals dédiés" car utilisé pour les sous-festivals (ex: cerisiers)
        noise_keywords = ['articles similaires', 'recherche', 'mon livre', 'mes livres', 'jipangu',
                         'articles recommandés', 'annuler la réponse', 'commentaire',
                         'guigui', 'réseaux sociaux', 'régions du japon', 'encyclopédie des matsuri',
                         'la nuit du nouvel an prend vie']

        # Trouver tous les h2 avec class="wp-block-heading"
        h2_elements = soup.find_all('h2', class_='wp-block-heading')

        for h2 in h2_elements:
            # Utiliser separator=' ' pour ajouter des espaces entre les éléments (ex: <sup>)
            title_text = h2.get_text(separator=' ', strip=True)

            # Filtrer le bruit
            if any(keyword in title_text.lower() for keyword in noise_keywords):
                continue

            # Séparer le nom des dates
            # Format: "NOM DU FESTIVAL (DATES)"
            name, dates = self._split_name_and_dates(title_text)

            if not name:
                continue

            # Nettoyer les espaces insécables (nbsp) dans le nom
            name = name.replace('\xa0', ' ').replace('&nbsp;', ' ')
            name = re.sub(r'\s+', ' ', name).strip()

            # Créer l'entrée du festival
            festival = {
                'name': name,
                'dates': dates,
                'location': None,
                'description': '',
                'website': None,
                'googlemap_link': None
            }

            # Collecter tous les paragraphes et liens suivants
            next_elem = h2.find_next_sibling()
            paragraphs = []
            paragraph_elements = []  # Garder les éléments BeautifulSoup pour extraire les liens

            while next_elem and next_elem.name != 'h2':
                if next_elem.name == 'p':
                    # Utiliser separator=' ' pour ajouter des espaces entre les éléments
                    p_text = next_elem.get_text(separator=' ', strip=True)
                    # Nettoyer les espaces multiples et espaces avant ponctuation
                    p_text = re.sub(r'\s+', ' ', p_text)
                    p_text = re.sub(r'\s+([,;:.!?])', r'\1', p_text)

                    # Ignorer les embeds Instagram
                    if not ('Une publication partagée par' in p_text or 'instagram' in p_text.lower()):
                        paragraphs.append(p_text)
                        paragraph_elements.append(next_elem)

                next_elem = next_elem.find_next_sibling()

            # Détecter automatiquement si ce h2 contient des sous-festivals
            # Pattern: plusieurs paragraphes consécutifs commençant par <strong>Nom</strong>
            # Ex: "LES FESTIVALS POUR HATSUMODE", "LES FESTIVALS POUR SETSUBUN", "Marchés de Noël"
            sub_festivals = self._extract_sub_festivals(paragraph_elements, dates, month, year)
            if sub_festivals and len(sub_festivals) >= 3:  # Au moins 3 sous-festivals pour confirmer le pattern
                festivals.extend(sub_festivals)
                continue  # Ne pas ajouter le h2 parent, seulement les sous-festivals

            # Extraire les informations des paragraphes
            if paragraphs:
                # Chercher d'abord dans le paragraphe 2 (qui contient souvent "Lieu :" et dates complètes)
                if len(paragraphs) >= 2:
                    p2 = paragraphs[1]
                    p2_elem = paragraph_elements[1]

                    # Chercher le lieu avec pattern "Lieu :"
                    location_from_lieu = self._extract_location_from_lieu_field(p2)
                    if location_from_lieu:
                        festival['location'] = location_from_lieu

                    # Chercher dates complètes "Du X au Y"
                    dates_from_p2 = self._extract_dates_from_paragraph(p2)
                    if dates_from_p2 and len(dates_from_p2) > len(dates or ''):
                        festival['dates'] = dates_from_p2

                    # Extraire les liens du paragraphe 2
                    links = p2_elem.find_all('a')
                    for link in links:
                        href = link.get('href', '')
                        link_text = link.get_text(strip=True).lower()

                        # Google Maps link (format long ou court: google.*/maps ou goo.gl)
                        if ('google' in href and 'maps' in href) or 'goo.gl' in href:
                            festival['googlemap_link'] = href
                        # Website (sur "Site de l'événement")
                        elif 'site' in link_text:
                            festival['website'] = href
                        # Sinon, si c'est un lien http et pas Google Maps, c'est probablement le website
                        elif 'http' in href and 'google' not in href and 'goo.gl' not in href and not festival['website']:
                            festival['website'] = href

                # Si pas trouvé de lieu, chercher dans tous les paragraphes
                if not festival['location']:
                    for p in paragraphs:
                        location = self._extract_location(p)
                        if location:
                            festival['location'] = location
                            break

                # Description: prendre les paragraphes descriptifs (pas celui avec "Lieu :")
                description_parts = []
                for p in paragraphs[:2]:
                    if len(p) > 20 and 'Lieu :' not in p and 'Site de l' not in p:
                        description_parts.append(p)

                if description_parts:
                    festival['description'] = ' '.join(description_parts[:2])

            # Ne garder que les festivals valides (qui ont au moins des dates ou une description)
            if festival['dates'] or (festival['description'] and len(festival['description']) > 20):
                festivals.append(festival)

        return festivals

    def _extract_sub_festivals(self, paragraph_elements, parent_dates, month, year) -> List[Dict]:
        """
        Extrait les sous-festivals des paragraphes <strong>
        Utilisé pour les cas comme "Les marchés de Noël" qui contiennent plusieurs festivals

        Args:
            paragraph_elements: Liste des éléments <p> BeautifulSoup
            parent_dates: Dates du h2 parent
            month: Mois
            year: Année

        Returns:
            Liste des sous-festivals extraits
        """
        sub_festivals = []

        for p_elem in paragraph_elements:
            # Chercher les paragraphes qui commencent par <strong>
            first_strong = p_elem.find('strong')
            if not first_strong:
                continue

            # Le nom peut être dans un ou plusieurs <strong>
            # Trois formats possibles:
            # Format A: <strong>Nom</strong><br>Date... (Setsubun)
            # Format B: <strong>Nom<br></strong>Date... (Cerisiers)
            # Format C: <strong>Nom1</strong> <strong>Nom2</strong><br>Date... (Kanda Myojin Hatsumode)

            # Détecter le format en vérifiant si <br> est dans le premier <strong>
            br_in_strong = first_strong.find('br')

            if br_in_strong:
                # Format B: <strong>Nom<br></strong>
                # Extraire uniquement le texte avant le <br>
                name_parts = []
                for sub_child in first_strong.children:
                    if sub_child.name == 'br':
                        break
                    if isinstance(sub_child, str):
                        text = sub_child.strip()
                        if text:
                            name_parts.append(text)
                    elif hasattr(sub_child, 'get_text'):
                        # Tag imbriqué (ex: <em>, <strong>)
                        name_parts.append(sub_child.get_text(separator=' ', strip=True))
                name = ' '.join(name_parts)
            else:
                # Format A ou C: <strong>Nom</strong> [<strong>Suite</strong>]<br>...
                # Collecter tous les <strong> avant le premier <br> au niveau racine
                name_parts = []
                for child in p_elem.children:
                    if child.name == 'br':
                        break
                    if child.name == 'strong':
                        name_parts.append(child.get_text(separator=' ', strip=True))
                    elif isinstance(child, str):
                        # Ignorer le texte entre les <strong> (espaces)
                        pass
                name = ' '.join(name_parts)

            # Nettoyer les espaces insécables (nbsp) dans le nom
            name = name.replace('\xa0', ' ').replace('&nbsp;', ' ')
            name = re.sub(r'\s+', ' ', name).strip()

            # Ignorer si c'est juste un mot simple, vide, ou du texte générique
            if len(name) < 5:
                continue

            # Filtrer un seul mot en minuscules (probablement un paragraphe d'intro)
            # Ex: "hatsumode" seul n'est pas un nom de festival
            if ' ' not in name and name.islower():
                continue

            # Filtrer les textes génériques qui ne sont pas des noms de festivals
            # Caractéristiques des paragraphes d'introduction:
            # - Très longs (>100 caractères)
            # - Contiennent certains mots clés
            if len(name) > 100:
                continue

            generic_keywords = ['quelques marchés', 'voici une liste', 'dans différents endroits', 'le mois de']
            if any(keyword in name.lower() for keyword in generic_keywords):
                continue

            if name.lower().startswith('des ') or name.lower().startswith('la magie'):
                continue

            # Créer l'entrée du festival
            festival = {
                'name': name,
                'dates': None,
                'location': None,
                'description': '',
                'website': None,
                'googlemap_link': None
            }

            # Extraire le HTML brut pour parser plus finement
            p_html = str(p_elem)

            # Extraire le texte complet du paragraphe avec <br> comme séparateur
            full_text = p_elem.get_text(separator=' ', strip=True)

            # Mapping des mois
            mois_mapping = {
                'janvier': '01', 'février': '02', 'fevrier': '02', 'mars': '03',
                'avril': '04', 'mai': '05', 'juin': '06', 'juillet': '07',
                'août': '08', 'aout': '08', 'septembre': '09', 'octobre': '10',
                'novembre': '11', 'décembre': '12', 'decembre': '12'
            }

            # Chercher les dates (plusieurs formats possibles)
            # Format 1: "Du 31 décembre 2024 au 4 janvier 2025" (plage entre deux années)
            # Note: (?:\s*er)? pour gérer "1 er" avec espace (à cause de <sup>)
            dates_match = re.search(r'Du\s+(\d{1,2})(?:\s*er)?\s+(\w+)\s+(\d{4})\s+au\s+(\d{1,2})(?:\s*er)?\s+(\w+)\s+(\d{4})', full_text, re.IGNORECASE)
            if dates_match:
                jour1 = dates_match.group(1).zfill(2)
                mois1 = mois_mapping.get(dates_match.group(2).lower(), '??')
                annee1 = dates_match.group(3)
                jour2 = dates_match.group(4).zfill(2)
                mois2 = mois_mapping.get(dates_match.group(5).lower(), '??')
                annee2 = dates_match.group(6)
                festival['dates'] = f"{annee1}/{mois1}/{jour1} - {annee2}/{mois2}/{jour2}"

            # Format 1b: "Du 1er au 3 janvier 2025" (même mois et année)
            if not festival['dates']:
                dates_match = re.search(r'Du\s+(\d{1,2})(?:\s*er)?\s+au\s+(\d{1,2})(?:\s*er)?\s+(\w+)\s+(\d{4})', full_text, re.IGNORECASE)
                if dates_match:
                    jour1 = dates_match.group(1).zfill(2)
                    jour2 = dates_match.group(2).zfill(2)
                    mois = mois_mapping.get(dates_match.group(3).lower(), '??')
                    annee = dates_match.group(4)
                    festival['dates'] = f"{annee}/{mois}/{jour1} - {annee}/{mois}/{jour2}"

            # Format 2: "Jusqu'au 25 décembre 2025"
            if not festival['dates']:
                dates_match = re.search(r'Jusqu[\'\'\u2019]?au\s+(\d{1,2})\s+(\w+)\s+(\d{4})', full_text, re.IGNORECASE)
                if dates_match:
                    jour = dates_match.group(1).zfill(2)
                    mois = mois_mapping.get(dates_match.group(2).lower(), '??')
                    annee = dates_match.group(3)
                    # Format: du 1er au 25 décembre
                    festival['dates'] = f"{annee}/{mois}/01 - {annee}/{mois}/{jour}"

            # Format 3: Date simple "2 février 2025" ou "Du 31 janvier au 2 février 2025"
            if not festival['dates']:
                # D'abord chercher les plages "Du X au Y"
                dates_match = re.search(r'Du\s+(\d{1,2})(?:\s*er)?\s+(\w+)\s+au\s+(\d{1,2})\s+(\w+)\s+(\d{4})', full_text, re.IGNORECASE)
                if dates_match:
                    jour1 = dates_match.group(1).zfill(2)
                    mois1 = mois_mapping.get(dates_match.group(2).lower(), '??')
                    jour2 = dates_match.group(3).zfill(2)
                    mois2 = mois_mapping.get(dates_match.group(4).lower(), '??')
                    annee = dates_match.group(5)
                    festival['dates'] = f"{annee}/{mois1}/{jour1} - {annee}/{mois2}/{jour2}"
                else:
                    # Sinon chercher une date simple "2 février 2025"
                    dates_match = re.search(r'(\d{1,2})(?:\s*er)?\s+(\w+)\s+(\d{4})', full_text, re.IGNORECASE)
                    if dates_match:
                        jour = dates_match.group(1).zfill(2)
                        mois = mois_mapping.get(dates_match.group(2).lower(), '??')
                        annee = dates_match.group(3)
                        festival['dates'] = f"{annee}/{mois}/{jour}"

            # Chercher le lieu : il est dans un lien après "Lieu :"
            # Il peut y avoir plusieurs liens, prendre le premier non-vide
            lieu_section = re.search(r'Lieu\s*:(.+?)(?:<br|Site)', p_html, re.IGNORECASE | re.DOTALL)
            if lieu_section:
                lieu_html = lieu_section.group(1)
                # Extraire tous les liens
                lieu_links = re.findall(r'<a[^>]*>([^<]*)</a>', lieu_html)
                for link_text in lieu_links:
                    if link_text.strip():
                        location = link_text.strip()
                        # Nettoyer les entités HTML
                        location = location.replace('&rsquo;', "'")
                        festival['location'] = location
                        break

            # Extraire la description : après "Site de l'événement"
            # Format 1: ...Site de l'événement</a><br/>DESCRIPTION<br/>Entrée... (marchés de Noël)
            # Format 2: ...Site de l'événement</a><br/>DESCRIPTION</p> (hatsumode)
            desc_pattern = re.search(r'v.nement</a><br/>(.+?)(?:<br/>Entr|</p>)', p_html, re.IGNORECASE | re.DOTALL)
            if desc_pattern:
                description = desc_pattern.group(1).strip()
                # Nettoyer les balises HTML sans ajouter d'espaces (pour éviter "hatsumode ," au lieu de "hatsumode,")
                description = re.sub(r'<[^>]+>', '', description)
                # Nettoyer les entités HTML
                description = description.replace('&rsquo;', "'").replace('&nbsp;', ' ')
                description = description.replace('&#8230;', '...').replace('&eacute;', 'é')
                description = description.replace('&egrave;', 'è').replace('&agrave;', 'à')
                description = description.replace('&ccedil;', 'ç')
                # Nettoyer les espaces multiples
                description = re.sub(r'\s+', ' ', description).strip()
                if len(description) > 20:
                    festival['description'] = description

            # Extraire les liens
            links = p_elem.find_all('a')
            for link in links:
                href = link.get('href', '')
                link_text = link.get_text(strip=True).lower()

                # Google Maps
                if ('google' in href and 'maps' in href) or 'goo.gl' in href or 'maps.app.goo.gl' in href:
                    festival['googlemap_link'] = href
                # Website (sur "Site de l'événement")
                elif 'site' in link_text or 'événement' in link_text:
                    festival['website'] = href

            sub_festivals.append(festival)

        return sub_festivals

    def _split_name_and_dates(self, title_text: str) -> tuple:
        """
        Sépare le nom du festival des dates dans le titre
        Format attendu: "NOM DU FESTIVAL (DATES)"

        Args:
            title_text: Texte du titre complet

        Returns:
            Tuple (name, dates) - dates normalisées au format YYYY/MM/DD
        """
        # Pattern pour extraire nom et dates entre parenthèses
        match = re.match(r'^(.+?)\s*\(([^)]+)\)\s*$', title_text)

        if match:
            name = match.group(1).strip()
            dates_raw = match.group(2).strip()
            # Normaliser les dates
            dates = self._normalize_dates(dates_raw)
            return name, dates

        # Si pas de parenthèses, tout est le nom
        return title_text.strip(), None

    def _normalize_dates(self, dates_text: str) -> str:
        """
        Normalise le format des dates pour correspondre au format de référence
        Convertit "9 MARS 2025" en "2025/03/09"
        Convertit "3-4 MARS 2025" en "2025/03/03 - 2025/03/04"

        Args:
            dates_text: Texte des dates brut (ex: "9 MARS 2025", "3-4 MARS 2025")

        Returns:
            Dates normalisées au format YYYY/MM/DD
        """
        if not dates_text:
            return None

        # Mapping des mois français vers numéros
        mois_mapping = {
            'janvier': '01', 'février': '02', 'fevrier': '02', 'mars': '03',
            'avril': '04', 'mai': '05', 'juin': '06', 'juillet': '07',
            'août': '08', 'aout': '08', 'septembre': '09', 'octobre': '10',
            'novembre': '11', 'décembre': '12', 'decembre': '12'
        }

        dates_lower = dates_text.lower()

        # Nettoyer les espaces multiples causés par separator=' ' dans get_text()
        # Ex: "1 ER -2 MARS" → "1 ER-2 MARS"
        dates_lower = re.sub(r'\s+', ' ', dates_lower).strip()

        # Pattern spécial: "31 décembre 2024-1 er janvier 2025" (plage entre deux années)
        # Note: \s* pour "er" séparé par <sup>
        match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})\s*[-–]\s*(\d{1,2})\s*(?:er|e)?\s+(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour1 = match.group(1).zfill(2)
            mois1 = mois_mapping.get(match.group(2), '??')
            annee1 = match.group(3)
            jour2 = match.group(4).zfill(2)
            mois2 = mois_mapping.get(match.group(5), '??')
            annee2 = match.group(6)
            return f"{annee1}/{mois1}/{jour1} - {annee2}/{mois2}/{jour2}"

        # Pattern spécial: "30 juin-1er juillet 2025" (plage entre deux mois, même année)
        # Note: le mois1 doit être un vrai mois (au moins 3 lettres), pas "er"
        match = re.search(r'(\d{1,2})\s+(\w{3,})\s*[-–]\s*(\d{1,2})(?:er|e)?\s+(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour1 = match.group(1).zfill(2)
            mois1 = mois_mapping.get(match.group(2), '??')
            jour2 = match.group(3).zfill(2)
            mois2 = mois_mapping.get(match.group(4), '??')
            annee = match.group(5)
            # Vérifier que mois1 est un vrai mois (pas "er")
            if mois1 != '??':
                return f"{annee}/{mois1}/{jour1} - {annee}/{mois2}/{jour2}"

        # Pattern 0: "X ER-Y MOIS ANNÉE" avec espaces optionnels (1 er-2 mars 2025, 1er-2mars 2025)
        # Note: \s* avant et après "er" pour gérer <sup>
        match = re.search(r'(\d{1,2})\s*(?:er|e)?\s*[-–]\s*(\d{1,2})\s+(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour1 = match.group(1).zfill(2)
            jour2 = match.group(2).zfill(2)
            mois = mois_mapping.get(match.group(3), '??')
            annee = match.group(4)
            return f"{annee}/{mois}/{jour1} - {annee}/{mois}/{jour2}"

        # Pattern 0b: "XERMOIS ANNÉE" sans espaces (1ermars 2025)
        match = re.search(r'(\d{1,2})(?:er|e)(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour = match.group(1).zfill(2)
            mois = mois_mapping.get(match.group(2), '??')
            annee = match.group(3)
            return f"{annee}/{mois}/{jour}"

        # Pattern 1: "JUSQU'AU X MOIS ANNÉE"
        match = re.search(r'jusqu[\'\']?au\s+(\d{1,2})\s+(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour = match.group(1).zfill(2)
            mois = mois_mapping.get(match.group(2), '??')
            annee = match.group(3)
            return f"{annee}/{mois}/{jour}"

        # Pattern 2: "X-Y MOIS ANNÉE" (plage de dates)
        match = re.search(r'(\d{1,2})\s*[-–]\s*(\d{1,2})\s+(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour1 = match.group(1).zfill(2)
            jour2 = match.group(2).zfill(2)
            mois = mois_mapping.get(match.group(3), '??')
            annee = match.group(4)
            return f"{annee}/{mois}/{jour1} - {annee}/{mois}/{jour2}"

        # Pattern 3: "X ER MOIS ANNÉE" (date simple avec espaces optionnels)
        # Note: \s* avant "er" pour gérer <sup>
        match = re.search(r'(\d{1,2})\s*(?:er|e)?\s+(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour = match.group(1).zfill(2)
            mois = mois_mapping.get(match.group(2), '??')
            annee = match.group(3)
            return f"{annee}/{mois}/{jour}"

        # Pattern 5: "X MOIS-Y MOIS ANNÉE" (plage entre mois)
        match = re.search(r'(\d{1,2})\s+(\w+)\s*[-–]\s*(\d{1,2})?\s*(\w+)?\s+(\d{4})', dates_lower)
        if match:
            jour1 = match.group(1).zfill(2)
            mois1 = mois_mapping.get(match.group(2), '??')
            jour2 = match.group(3)
            mois2_str = match.group(4)
            annee = match.group(5)

            if jour2 and mois2_str:
                jour2 = jour2.zfill(2)
                mois2 = mois_mapping.get(mois2_str, '??')
                return f"{annee}/{mois1}/{jour1} - {annee}/{mois2}/{jour2}"

        # Si aucun pattern ne matche, retourner tel quel
        return dates_text

    def _extract_location_from_lieu_field(self, text: str) -> Optional[str]:
        """
        Extrait la localisation spécifiquement du champ "Lieu :"
        C'est la source la plus fiable pour le lieu

        Args:
            text: Texte à analyser

        Returns:
            Localisation extraite ou None
        """
        match = re.search(r'Lieu\s*:\s*(.+?)(?:\s+(?:Site|Horaires|Tarif|en un|et )|$)', text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            # Nettoyer les espaces multiples
            location = re.sub(r'\s+', ' ', location)
            # Ajouter espace avant parenthèse si manquant
            location = re.sub(r'([^\s])\(', r'\1 (', location)
            # Supprimer les parenthèses si la localisation est assez courte
            if len(location) < 100:
                base_match = re.match(r'^([^(]+)', location)
                if base_match:
                    base_loc = base_match.group(1).strip()
                    if len(base_loc) >= 10:
                        location = base_loc
            return location
        return None

    def _extract_dates_from_paragraph(self, text: str) -> Optional[str]:
        """
        Extrait les dates du paragraphe info (format "Du X au Y" ou "Du X Y au Z W")

        Args:
            text: Texte du paragraphe

        Returns:
            Dates normalisées ou None
        """
        # Mapping des mois
        mois_mapping = {
            'janvier': '01', 'février': '02', 'fevrier': '02', 'mars': '03',
            'avril': '04', 'mai': '05', 'juin': '06', 'juillet': '07',
            'août': '08', 'aout': '08', 'septembre': '09', 'octobre': '10',
            'novembre': '11', 'décembre': '12', 'decembre': '12'
        }

        # Pattern "Du 8 février au 2 mars 2025"
        match = re.search(r'Du\s+(\d{1,2})\s+(\w+)\s+au\s+(\d{1,2})\s+(\w+)\s+(\d{4})', text, re.IGNORECASE)
        if match:
            jour1 = match.group(1).zfill(2)
            mois1 = mois_mapping.get(match.group(2).lower(), '??')
            jour2 = match.group(3).zfill(2)
            mois2 = mois_mapping.get(match.group(4).lower(), '??')
            annee = match.group(5)
            return f"{annee}/{mois1}/{jour1} - {annee}/{mois2}/{jour2}"

        # Pattern "Du X au Y mois année" (même mois)
        match = re.search(r'Du\s+(\d{1,2})\s+au\s+(\d{1,2})\s+(\w+)\s+(\d{4})', text, re.IGNORECASE)
        if match:
            jour1 = match.group(1).zfill(2)
            jour2 = match.group(2).zfill(2)
            mois = mois_mapping.get(match.group(3).lower(), '??')
            annee = match.group(4)
            return f"{annee}/{mois}/{jour1} - {annee}/{mois}/{jour2}"

        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """
        Extrait la localisation d'un texte
        Cherche des patterns comme "à [lieu]", "au [lieu]", "Lieu :[lieu]", etc.

        Args:
            text: Texte à analyser

        Returns:
            Localisation extraite ou None
        """
        # Pattern 0: Format "Lieu :" ou "Lieu:" (le plus fiable)
        match = re.search(r'Lieu\s*:\s*(.+?)(?:\s+(?:Site|Horaires|Tarif|en un|et )|$)', text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            # Nettoyer les espaces multiples
            location = re.sub(r'\s+', ' ', location)
            # Ajouter espace avant parenthèse si manquant
            location = re.sub(r'([^\s])\(', r'\1 (', location)
            # Supprimer les parenthèses si la localisation est assez courte (moins de 50 chars)
            # et qu'elles ne semblent pas essentielles
            if len(location) < 60:
                # Garder seulement la partie avant les parenthèses si c'est redondant
                base_match = re.match(r'^([^(]+)', location)
                if base_match:
                    base_loc = base_match.group(1).strip()
                    # Si la base est suffisante (contient parc/temple/etc), l'utiliser
                    if len(base_loc) >= 10:
                        location = base_loc
            return location

        # Pattern 1: Lieux avec préposition et parenthèses (ex: "au parc Yoyogi Koen (Harajuku)")
        match = re.search(r'(?:au|à|dans le|dans l\')\s+(parc|temple|sanctuaire|jardin|quartier|station|mont|siège)\s+([A-Za-z\-\s]+?)(?:\s+\([^)]+\))?(?=[,\.]|$)', text, re.IGNORECASE)
        if match:
            location = match.group(1) + ' ' + match.group(2).strip()
            # Ajouter les parenthèses si présentes
            paren_match = re.search(r'\([^)]+\)', match.group(0))
            if paren_match:
                location += ' ' + paren_match.group(0)
            return location

        # Pattern 2: Lieux directs avec nom propre (ex: "parc Akatsuka Tameike Koen")
        match = re.search(r'(parc|temple|sanctuaire|jardin|quartier|station|mont|siège)\s+([A-Z][A-Za-z\-\s]+?)(?:\s+\([^)]+\))?(?=[,\.]|$)', text)
        if match:
            location = match.group(1) + ' ' + match.group(2).strip()
            # Ajouter les parenthèses si présentes
            paren_match = re.search(r'\([^)]+\)', match.group(0))
            if paren_match:
                location += ' ' + paren_match.group(0)
            return location

        # Pattern 3: Lieux avec "départ" (ex: "départ au siège du gouvernement")
        match = re.search(r'départ\s+(?:au|à)\s+([^,\.]+?)(?:\s+\([^)]+\))?(?=[,\.]|$)', text, re.IGNORECASE)
        if match:
            return 'départ ' + match.group(1).strip()

        return None

    def _extract_dates(self, text: str) -> Optional[str]:
        """Extrait les dates d'un texte"""
        # Liste de tous les mois en anglais et français
        mois = '|'.join([
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'janvier', 'février', 'fevrier', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'aout', 'septembre', 'octobre', 'novembre', 'décembre', 'decembre'
        ])

        # Pattern pour les dates (ex: "December 1-25, 2025" ou "3-7 décembre")
        date_patterns = [
            rf'({mois})\s+\d{{1,2}}[-–]\d{{1,2}},?\s+\d{{4}}',
            rf'\d{{1,2}}[-–]\d{{1,2}}\s+({mois})\s+\d{{4}}',
            rf'({mois})\s+\d{{1,2}},?\s+\d{{4}}',
            rf'\d{{1,2}}\s+({mois})\s+\d{{4}}',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def save_to_json(self, festivals: List[Dict], filename: str = None):
        """
        Sauvegarde les festivals en JSON

        Args:
            festivals: Liste des festivals
            filename: Nom du fichier (optionnel)
        """
        if not filename:
            # Chercher le premier festival avec month et year définis
            month = 'unknown'
            year = 'unknown'
            for festival in festivals:
                if festival.get('month') and festival.get('year'):
                    month = festival['month']
                    year = festival['year']
                    break

            # Créer le dossier data s'il n'existe pas
            import os
            os.makedirs('data', exist_ok=True)
            filename = f"data/festivals_tokyo_{month}_{year}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({'festivals': festivals}, f, ensure_ascii=False, indent=2)

        print(f"✓ Données sauvegardées dans {filename}")



def main():
    """
    Fonction principale pour utiliser le scraper
    """
    scraper = TokyoFestivalScraper()

    # Exemple d'utilisation
    print("=== Scraper de Festivals Tokyo ===\n")

    # Scraper décembre 2025
    festivals = scraper.scrape_festivals(month=12, year=2025)

    if festivals:
        # Sauvegarder en JSON
        scraper.save_to_json(festivals)

        # Sauvegarder en CSV
        scraper.save_to_csv(festivals)

        # Afficher un aperçu
        print(f"\n=== Aperçu des {len(festivals)} premiers festivals ===")
        for i, festival in enumerate(festivals[:3], 1):
            print(f"\n{i}. {festival['name']}")
            if festival.get('dates'):
                print(f"   Dates: {festival['dates']}")
            if festival.get('location'):
                print(f"   Lieu: {festival['location']}")

    # Exemple: scraper plusieurs mois
    print("\n\n=== Scraper plusieurs mois ===")
    for month in [1, 2, 3]:  # Janvier, Février, Mars 2026
        try:
            festivals = scraper.scrape_festivals(month=month, year=2026)
            if festivals:
                scraper.save_to_json(festivals)
                scraper.save_to_csv(festivals)
        except Exception as e:
            print(f"Erreur pour le mois {month}/2026: {e}")


if __name__ == "__main__":
    main()