import requests
from bs4 import BeautifulSoup, Tag
import json
import csv
from datetime import datetime
from typing import List, Dict, Optional
import re
import sys
import unicodedata

from src.date_utils import split_date_range, format_date_range
from src.date_utils_fr import parse_french_date_range, is_complex_date_pattern, expand_complex_dates
from src.location_utils import normalize_district, extract_location_with_district
from src.metadata_extractors import extract_hours, extract_fee
from src.database import EventDatabase
from src.gps_extractor import GPSExtractor


class TokyoExpositionScraper:
    """
    Scraper pour les expositions de Tokyo depuis ichiban-japan.com
    """

    BASE_URL = "https://ichiban-japan.com/expositions-tokyo-{month}-{year}/"

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

    def scrape_expositions(self, month: int, year: int) -> List[Dict]:
        """
        Scrape les expositions pour un mois et une année donnés

        Args:
            month: Numéro du mois (1-12)
            year: Année

        Returns:
            Liste de dictionnaires contenant les informations des expositions
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
        expositions = []

        # Parser le contenu de la page
        expositions = self._parse_page(soup, month, year)

        print(f"✓ {len(expositions)} expositions trouvées pour {self.MONTHS_FR[month]} {year}")
        return expositions

    def _parse_page(self, soup: BeautifulSoup, month: int, year: int) -> List[Dict]:
        """
        Parse le contenu HTML de la page
        Utilise une approche simplifiée basée sur le pattern HTML consistant

        Args:
            soup: Objet BeautifulSoup
            month: Mois
            year: Année

        Returns:
            Liste des expositions parsées
        """
        # Tenter d'abord le parsing simplifié (version corrigée)
        try:
            expositions = self._parse_page_simplified(soup, month, year)
            if expositions:  # Si réussi, retourner
                return expositions
        except Exception as e:
            print(f"⚠️ Fallback vers parsing classique: {e}")

        # Sinon, fallback vers l'ancienne méthode
        return self._parse_page_legacy(soup, month, year)

    def _parse_page_simplified(self, soup: BeautifulSoup, month: int, year: int) -> List[Dict]:
        """
        Parser simplifié basé sur découpage en sections (approche notebook)
        Chaque section = H2 + éléments suivants jusqu'au prochain H2

        Args:
            soup: Objet BeautifulSoup
            month: Mois
            year: Année

        Returns:
            Liste des expositions parsées
        """
        expositions = []

        # Trouver le conteneur principal
        entry_content = soup.find('div', class_='entry-content')
        if not entry_content:
            return []

        # Découper en sections
        sections = []
        current_section = []

        for elem in entry_content.children:
            if not isinstance(elem, Tag):
                continue

            # Arrêter au bloc "crp_related"
            if elem.name == "div" and "crp_related" in (elem.get("class") or []):
                break

            if elem.name == "h2":
                if current_section:
                    sections.append(current_section)
                current_section = [elem]
            else:
                if current_section:
                    current_section.append(elem)

        if current_section:
            sections.append(current_section)

        # Parser chaque section
        for k, section in enumerate(sections):
            if len(section) < 2:
                continue

            # H2 = titre
            h2 = section[0]
            title = h2.get_text(separator=' ', strip=True)

            if self._is_noise(title):
                continue

            name, _ = self._split_name_and_dates(title)
            if not name:
                continue

            # Trouver les paragraphes <p> (exclure les <div> et <figure>)
            paragraphs = [elem for elem in section[1:] if isinstance(elem, Tag) and elem.name == 'p']

            if len(paragraphs) == 0:
                # Aucun paragraphe, skip
                continue
            elif len(paragraphs) == 1:
                # Un seul paragraphe : description ET métadonnées combinées
                description_elem = paragraphs[0]
                metadata_elem = paragraphs[0]
            else:
                # Deux paragraphes ou plus : premier = description, deuxième = métadonnées
                description_elem = paragraphs[0]
                metadata_elem = paragraphs[1]

            # Extraire description
            description = self._clean_description(description_elem.get_text(separator=' ', strip=True))

            # Extraire métadonnées avec normalisation Unicode (gère automatiquement les superscripts)
            metadata_text = metadata_elem.get_text(separator=' ', strip=True)
            metadata_text = unicodedata.normalize("NFKC", metadata_text).lower()

            # Parser dates et lieu
            start_date, end_date, location = None, None, None

            if 'du' in metadata_text and 'lieu :' in metadata_text:
                try:
                    # Split par "lieu :" pour séparer dates et lieu
                    parts = metadata_text.split('lieu :', 1)

                    if len(parts) == 2:
                        dates_part = parts[0].strip()
                        location_raw = parts[1].strip()

                        # Extraire dates - passer la chaîne complète avec "du" à _normalize_dates
                        dates_normalized = self._normalize_dates(dates_part)
                        if dates_normalized:
                            start_date, end_date = split_date_range(dates_normalized)

                        # Extraire lieu (avant "site" si présent)
                        # Restaurer la casse du lieu depuis l'élément original (pas lowercase)
                        location_original = metadata_elem.get_text(separator=' ', strip=True)
                        if 'Lieu :' in location_original or 'Lieux :' in location_original:
                            lieu_match = re.search(r'Lieux?\s*:\s*(.+?)(?:\s+(?:Site|$))', location_original, re.IGNORECASE)
                            if lieu_match:
                                location = lieu_match.group(1).strip()
                except:
                    pass

            # Extraire liens
            links = metadata_elem.find_all('a')
            website, googlemap_link = None, None

            for link in links:
                href = link.get('href', '')
                link_text = link.get_text(strip=True).lower()

                if ('google' in href and 'maps' in href) or 'goo.gl' in href or 'maps.app.goo.gl' in href:
                    googlemap_link = href
                elif 'site' in link_text or 'officiel' in link_text:
                    website = href
                elif not website and href.startswith('http') and 'google' not in href:
                    website = href

            # Créer exposition
            exposition = {
                'name': name,
                'start_date': start_date,
                'end_date': end_date,
                'location': normalize_district(location) if location else None,
                'description': description,
                'website': website,
                'googlemap_link': googlemap_link,
                'hours': extract_hours(metadata_text),
                'fee': extract_fee(metadata_text)
            }

            if self._is_valid_exposition(exposition):
                expositions.append(exposition)

        return expositions

    def _parse_page_legacy(self, soup: BeautifulSoup, month: int, year: int) -> List[Dict]:
        """
        Ancienne méthode de parsing (fallback)

        Args:
            soup: Objet BeautifulSoup
            month: Mois
            year: Année

        Returns:
            Liste des expositions parsées
        """
        expositions = []

        # Mots-clés à filtrer (bruit)
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
            # Format: "NOM DE L'EXPOSITION (DATES)"
            name, dates = self._split_name_and_dates(title_text)

            if not name:
                continue

            # Nettoyer les espaces insécables (nbsp) dans le nom
            name = name.replace('\xa0', ' ').replace('&nbsp;', ' ')
            name = re.sub(r'\s+', ' ', name).strip()

            # Créer l'entrée de l'exposition
            start_date, end_date = split_date_range(dates) if dates else (None, None)
            exposition = {
                'name': name,
                'start_date': start_date,
                'end_date': end_date,
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
                    # Nettoyer les espaces multiples et espaces avant ponctuation
                    p_text = re.sub(r'\s+', ' ', p_text)
                    p_text = re.sub(r'\s+([,;:.!?])', r'\1', p_text)

                    # Ignorer les embeds Instagram
                    if not ('Une publication partagée par' in p_text or 'instagram' in p_text.lower()):
                        paragraphs.append(p_text)
                        paragraph_elements.append(next_elem)

                next_elem = next_elem.find_next_sibling()

            # Détecter automatiquement si ce h2 contient des sous-expositions
            # Pattern: plusieurs paragraphes consécutifs commençant par <strong>Nom</strong>
            sub_expositions = self._extract_sub_expositions(paragraph_elements, dates, month, year)
            if sub_expositions and len(sub_expositions) >= 3:  # Au moins 3 sous-expositions pour confirmer le pattern
                expositions.extend(sub_expositions)
                continue  # Ne pas ajouter le h2 parent, seulement les sous-expositions

            # Extraire les informations des paragraphes
            if paragraphs:
                # Chercher dans le dernier paragraphe qui contient souvent les métadonnées ("Lieu :", dates, liens)
                # Parfois c'est le paragraphe 2, parfois c'est le paragraphe 1 unique
                meta_paragraph = None
                meta_paragraph_elem = None

                # Chercher le paragraphe contenant "Lieu :" ou "Du "
                for i, p in enumerate(paragraphs):
                    if 'Lieu' in p or 'Du ' in p or 'Site' in p:
                        meta_paragraph = p
                        meta_paragraph_elem = paragraph_elements[i]
                        break

                # Si trouvé, extraire les métadonnées
                if meta_paragraph:
                    # Chercher le lieu avec pattern "Lieu :"
                    location_from_lieu = self._extract_location_from_lieu_field(meta_paragraph)
                    if location_from_lieu:
                        exposition['location'] = normalize_district(location_from_lieu)

                    # Chercher dates complètes "Du X au Y"
                    # Toujours donner la priorité au paragraphe de métadonnées car il contient les dates les plus complètes
                    dates_from_meta = self._extract_dates_from_paragraph(meta_paragraph)
                    if dates_from_meta:
                        start, end = split_date_range(dates_from_meta)
                        exposition['start_date'] = start
                        exposition['end_date'] = end

                    # Extraire heures et tarifs
                    exposition['hours'] = extract_hours(meta_paragraph)
                    exposition['fee'] = extract_fee(meta_paragraph)

                    # Extraire les liens avec hiérarchie de fallback
                    exposition['website'] = self._extract_official_url_with_fallback(meta_paragraph_elem)
                    exposition['googlemap_link'] = self._extract_googlemap_link(meta_paragraph_elem)

                # Si pas trouvé de lieu, chercher dans tous les paragraphes
                if not exposition['location']:
                    for p in paragraphs:
                        location = self._extract_location(p)
                        if location:
                            exposition['location'] = normalize_district(location)
                            break

                # Si pas trouvé d'heures/tarifs, chercher dans tous les paragraphes
                if not exposition['hours'] or not exposition['fee']:
                    for p in paragraphs:
                        if not exposition['hours']:
                            exposition['hours'] = extract_hours(p)
                        if not exposition['fee']:
                            exposition['fee'] = extract_fee(p)

                # Description: extraire le texte descriptif avant les métadonnées
                # Si le paragraphe de métadonnées contient aussi la description (séparée par <br><br>),
                # extraire uniquement la partie descriptive
                if meta_paragraph and len(paragraphs) == 1:
                    # Cas où tout est dans un seul paragraphe
                    # Extraire la partie avant les métadonnées (avant le nom répété "Toyohara Kunichika Du...")
                    # Chercher "Du X" qui marque le début des dates
                    desc_match = re.search(r'^(.+?)\s+Du\s+\d', meta_paragraph)
                    if desc_match:
                        desc = desc_match.group(1).strip()
                        # Retirer le nom en double à la fin si présent
                        # Le nom peut être présent à la fin de la description (ex: "... XIXe siècle. Toyohara Kunichika")
                        desc_words = desc.split()
                        if len(desc_words) > 10:
                            # Vérifier si les derniers mots ressemblent au nom de l'exposition
                            # En retirant les mots qui pourraient être le nom répété
                            cleaned_desc = desc
                            # Pattern pour retirer le nom répété à la fin (capitale + mots)
                            cleaned_desc = re.sub(r'\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s*$', '', cleaned_desc)
                            # Nettoyer les espaces multiples causés par get_text(separator=' ')
                            # D'abord nettoyer espaces multiples
                            cleaned_desc = re.sub(r'\s+', ' ', cleaned_desc).strip()
                            # Corriger "l' ukiyo-e" → "l'ukiyo-e" (apostrophe droite et typographique)
                            cleaned_desc = re.sub(r"([ldjmnts])\s*['\u2019]\s+", r"\1'", cleaned_desc)
                            if len(cleaned_desc) > 50:
                                exposition['description'] = cleaned_desc
                            elif len(desc) > 50:
                                # Nettoyer aussi desc si on l'utilise
                                desc = re.sub(r'\s+', ' ', desc).strip()
                                desc = re.sub(r"([ldjmnts])\s*['\u2019]\s+", r"\1'", desc)
                                exposition['description'] = desc
                else:
                    # Cas classique: description dans un paragraphe séparé
                    description_parts = []
                    for p in paragraphs:
                        # Prendre les paragraphes qui ne contiennent pas de métadonnées
                        if p != meta_paragraph and len(p) > 50:
                            # Nettoyer les espaces multiples causés par get_text(separator=' ')
                            # D'abord nettoyer espaces multiples
                            p_cleaned = re.sub(r'\s+', ' ', p).strip()
                            # Corriger "l' ukiyo-e" → "l'ukiyo-e" (apostrophe droite et typographique)
                            p_cleaned = re.sub(r"([ldjmnts])\s*['\u2019]\s+", r"\1'", p_cleaned)
                            description_parts.append(p_cleaned)
                            break  # Prendre seulement le premier paragraphe descriptif

                    if description_parts:
                        exposition['description'] = description_parts[0]

            # Ne garder que les expositions valides (qui ont au moins des dates ou une description)
            if exposition.get('end_date') or (exposition['description'] and len(exposition['description']) > 20):
                expositions.append(exposition)

        return expositions

    def _extract_sub_expositions(self, paragraph_elements, parent_dates, month, year) -> List[Dict]:
        """
        Extrait les sous-expositions des paragraphes <strong>
        Utilisé pour les cas qui contiennent plusieurs expositions groupées

        Args:
            paragraph_elements: Liste des éléments <p> BeautifulSoup
            parent_dates: Dates du h2 parent
            month: Mois
            year: Année

        Returns:
            Liste des sous-expositions extraites
        """
        sub_expositions = []

        for p_elem in paragraph_elements:
            # Chercher les paragraphes qui COMMENCENT par <strong>
            # (pas juste qui contiennent un <strong> quelque part)
            first_child = None
            for child in p_elem.children:
                if isinstance(child, str):
                    # Si c'est du texte, vérifier qu'il est vide (espaces)
                    if child.strip():
                        # Texte non vide avant le <strong> → pas une sous-exposition
                        break
                elif child.name == 'strong':
                    first_child = child
                    break
                else:
                    # Autre tag avant <strong> → pas une sous-exposition
                    break

            if not first_child:
                continue

            first_strong = first_child

            # Le nom peut être dans un ou plusieurs <strong>
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

            # Filtrer un seul mot en minuscules
            if ' ' not in name and name.islower():
                continue

            # Filtrer les textes génériques qui ne sont pas des noms d'expositions
            if len(name) > 100:
                continue

            generic_keywords = ['quelques marchés', 'voici une liste', 'dans différents endroits', 'le mois de']
            if any(keyword in name.lower() for keyword in generic_keywords):
                continue

            if name.lower().startswith('des ') or name.lower().startswith('la magie'):
                continue

            # Créer l'entrée de l'exposition
            exposition = {
                'name': name,
                'start_date': None,
                'end_date': None,
                'location': None,
                'description': '',
                'website': None,
                'googlemap_link': None,
                'hours': None,
                'fee': None
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
            dates_match = re.search(r'Du\s+(\d{1,2})(?:\s*er)?\s+(\w+)\s+(\d{4})\s+au\s+(\d{1,2})(?:\s*er)?\s+(\w+)\s+(\d{4})', full_text, re.IGNORECASE)
            if dates_match:
                jour1 = dates_match.group(1).zfill(2)
                mois1 = mois_mapping.get(dates_match.group(2).lower(), '??')
                annee1 = dates_match.group(3)
                jour2 = dates_match.group(4).zfill(2)
                mois2 = mois_mapping.get(dates_match.group(5).lower(), '??')
                annee2 = dates_match.group(6)
                exposition['start_date'] = f"{annee1}/{mois1}/{jour1}"
                exposition['end_date'] = f"{annee2}/{mois2}/{jour2}"

            # Format 1b: "Du 1er au 3 janvier 2025" (même mois et année)
            if not exposition.get('end_date'):
                dates_match = re.search(r'Du\s+(\d{1,2})(?:\s*er)?\s+au\s+(\d{1,2})(?:\s*er)?\s+(\w+)\s+(\d{4})', full_text, re.IGNORECASE)
                if dates_match:
                    jour1 = dates_match.group(1).zfill(2)
                    jour2 = dates_match.group(2).zfill(2)
                    mois = mois_mapping.get(dates_match.group(3).lower(), '??')
                    annee = dates_match.group(4)
                    exposition['start_date'] = f"{annee}/{mois}/{jour1}"
                    exposition['end_date'] = f"{annee}/{mois}/{jour2}"

            # Format 2: "Jusqu'au 25 décembre 2025"
            if not exposition.get('end_date'):
                dates_match = re.search(r'Jusqu[\'\'\u2019]?au\s+(\d{1,2})\s+(\w+)\s+(\d{4})', full_text, re.IGNORECASE)
                if dates_match:
                    jour = dates_match.group(1).zfill(2)
                    mois = mois_mapping.get(dates_match.group(2).lower(), '??')
                    annee = dates_match.group(3)
                    # Format: du 1er au 25 décembre
                    exposition['start_date'] = f"{annee}/{mois}/01"
                    exposition['end_date'] = f"{annee}/{mois}/{jour}"

            # Format 3: Date simple "2 février 2025" ou "Du 31 janvier au 2 février 2025"
            if not exposition.get('end_date'):
                # D'abord chercher les plages "Du X au Y"
                dates_match = re.search(r'Du\s+(\d{1,2})(?:\s*er)?\s+(\w+)\s+au\s+(\d{1,2})\s+(\w+)\s+(\d{4})', full_text, re.IGNORECASE)
                if dates_match:
                    jour1 = dates_match.group(1).zfill(2)
                    mois1 = mois_mapping.get(dates_match.group(2).lower(), '??')
                    jour2 = dates_match.group(3).zfill(2)
                    mois2 = mois_mapping.get(dates_match.group(4).lower(), '??')
                    annee = dates_match.group(5)
                    exposition['start_date'] = f"{annee}/{mois1}/{jour1}"
                    exposition['end_date'] = f"{annee}/{mois2}/{jour2}"
                else:
                    # Sinon chercher une date simple "2 février 2025"
                    dates_match = re.search(r'(\d{1,2})(?:\s*er)?\s+(\w+)\s+(\d{4})', full_text, re.IGNORECASE)
                    if dates_match:
                        jour = dates_match.group(1).zfill(2)
                        mois = mois_mapping.get(dates_match.group(2).lower(), '??')
                        annee = dates_match.group(3)
                        single_date = f"{annee}/{mois}/{jour}"
                        exposition['start_date'] = single_date
                        exposition['end_date'] = single_date

            # Chercher le lieu : il est dans un lien après "Lieu :"
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
                        exposition['location'] = normalize_district(location)
                        break

            # Extraire la description : après "Site de l'événement" ou "Site de l'exposition"
            desc_pattern = re.search(r'v.nement</a><br/>(.+?)(?:<br/>Entr|</p>)', p_html, re.IGNORECASE | re.DOTALL)
            if not desc_pattern:
                desc_pattern = re.search(r'exposition</a><br/>(.+?)(?:<br/>Entr|</p>)', p_html, re.IGNORECASE | re.DOTALL)

            if desc_pattern:
                description = desc_pattern.group(1).strip()
                # Nettoyer les balises HTML
                description = re.sub(r'<[^>]+>', '', description)
                # Nettoyer les entités HTML
                description = description.replace('&rsquo;', "'").replace('&nbsp;', ' ')
                description = description.replace('&#8230;', '...').replace('&eacute;', 'é')
                description = description.replace('&egrave;', 'è').replace('&agrave;', 'à')
                description = description.replace('&ccedil;', 'ç')
                # Nettoyer les espaces multiples
                description = re.sub(r'\s+', ' ', description).strip()
                if len(description) > 20:
                    exposition['description'] = description

            # Extraire heures et tarifs
            exposition['hours'] = extract_hours(full_text)
            exposition['fee'] = extract_fee(full_text)

            # Extraire les liens avec hiérarchie de fallback
            exposition['website'] = self._extract_official_url_with_fallback(p_elem)
            exposition['googlemap_link'] = self._extract_googlemap_link(p_elem)

            sub_expositions.append(exposition)

        return sub_expositions

    def _is_noise(self, text: str) -> bool:
        """
        Vérifie si un texte est du bruit (à filtrer)

        Args:
            text: Texte à vérifier

        Returns:
            True si c'est du bruit, False sinon
        """
        noise_keywords = ['articles similaires', 'recherche', 'mon livre', 'mes livres', 'jipangu',
                         'articles recommandés', 'annuler la réponse', 'commentaire',
                         'guigui', 'réseaux sociaux', 'régions du japon', 'encyclopédie des matsuri',
                         'la nuit du nouvel an prend vie']

        return any(keyword in text.lower() for keyword in noise_keywords)

    def _clean_description(self, text: str) -> str:
        """
        Nettoie le texte de description

        Args:
            text: Texte brut

        Returns:
            Texte nettoyé
        """
        # Nettoyer les espaces insécables (nbsp) et espaces multiples
        text = text.replace('\xa0', ' ').replace('&nbsp;', ' ')
        text = re.sub(r'\s+', ' ', text).strip()

        # Corriger "l' ukiyo-e" → "l'ukiyo-e" (apostrophe droite et typographique)
        text = re.sub(r"([ldjmnts])\s*['\u2019]\s+", r"\1'", text)

        # Supprimer les espaces avant virgules, deux-points et points
        text = re.sub(r'\s+([,:.])', r'\1', text)

        return text

    def _extract_metadata_from_paragraph(self, p_elem) -> dict:
        """
        Extrait toutes les métadonnées d'un paragraphe structuré

        Args:
            p_elem: Élément BeautifulSoup du paragraphe

        Returns:
            Dictionnaire avec start_date, end_date, location, website, googlemap_link
        """
        text = p_elem.get_text(separator=' ', strip=True)
        metadata = {}

        # Dates (priorité au texte complet avec "Du X au Y")
        dates = self._extract_dates_from_paragraph(text)
        if dates:
            start, end = split_date_range(dates)
            metadata['start_date'] = start
            metadata['end_date'] = end

        # Lieu
        location = self._extract_location_from_lieu_field(text)
        if location:
            # Ne pas tronquer - garder le nom complet
            location = re.sub(r'\s+', ' ', location)  # Normaliser les espaces
            metadata['location'] = location

        # Liens (website et Google Maps)
        links = p_elem.find_all('a')
        googlemap_candidates = []
        website_candidates = []

        for link in links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True).lower()

            # Google Maps
            if ('google' in href and 'maps' in href) or 'goo.gl' in href or 'maps.app.goo.gl' in href:
                googlemap_candidates.append(href)
            # Website (explicite)
            elif 'site' in link_text or 'officiel' in link_text or 'official' in link_text:
                website_candidates.append(href)
            # Website (fallback: tout lien HTTP qui n'est pas Google)
            elif href.startswith('http') and 'google' not in href:
                website_candidates.append(href)

        # Assigner les meilleurs candidats
        if googlemap_candidates:
            metadata['googlemap_link'] = googlemap_candidates[0]
        if website_candidates:
            metadata['website'] = website_candidates[0]

        return metadata

    def _is_valid_exposition(self, exposition: dict) -> bool:
        """
        Vérifie si une exposition est valide (critères minimums)

        Args:
            exposition: Dictionnaire de l'exposition

        Returns:
            True si valide, False sinon
        """
        # Critères:
        # - Doit avoir au moins end_date OU une description >20 caractères
        has_end_date = exposition.get('end_date') is not None
        has_description = exposition.get('description') and len(exposition.get('description', '')) > 20

        return has_end_date or has_description

    def _split_name_and_dates(self, title_text: str) -> tuple:
        """
        Sépare le nom de l'exposition des dates dans le titre
        Format attendu: "NOM DE L'EXPOSITION (DATES)"

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

        # Nettoyer les espaces multiples
        dates_lower = re.sub(r'\s+', ' ', dates_lower).strip()

        # Pattern spécial: "du 16 décembre 2025 au 8 février 2026" (DU...AU entre deux années)
        # Support "1 er février" avec espace et "1erfévrier" sans espace
        match = re.search(r'du\s+(\d{1,2})\s*(?:er|e)?\s+(\w+)\s+(\d{4})\s+au\s+(\d{1,2})\s*(?:er|e)?\s+(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour1 = match.group(1).zfill(2)
            mois1 = mois_mapping.get(match.group(2), '??')
            annee1 = match.group(3)
            jour2 = match.group(4).zfill(2)
            mois2 = mois_mapping.get(match.group(5), '??')
            annee2 = match.group(6)
            if mois1 != '??':
                return f"{annee1}/{mois1}/{jour1} - {annee2}/{mois2}/{jour2}"

        # Pattern spécial: "31 décembre 2024-1 er janvier 2025" (plage entre deux années)
        match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})\s*[-–]\s*(\d{1,2})\s*(?:er|e)?\s+(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour1 = match.group(1).zfill(2)
            mois1 = mois_mapping.get(match.group(2), '??')
            annee1 = match.group(3)
            jour2 = match.group(4).zfill(2)
            mois2 = mois_mapping.get(match.group(5), '??')
            annee2 = match.group(6)
            return f"{annee1}/{mois1}/{jour1} - {annee2}/{mois2}/{jour2}"

        # Pattern spécial: "du 5 au 26 janvier 2025" (DU X AU Y même mois, sans "er")
        match = re.search(r'du\s+(\d{1,2})\s+au\s+(\d{1,2})\s+(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour1 = match.group(1).zfill(2)
            jour2 = match.group(2).zfill(2)
            mois = mois_mapping.get(match.group(3), '??')
            annee = match.group(4)
            if mois != '??':
                return f"{annee}/{mois}/{jour1} - {annee}/{mois}/{jour2}"

        # Pattern spécial: "DU 1er MARS AU 6 JUILLET 2025" (format avec DU...AU même année)
        # Support "1 er février" avec espace et "1erfévrier" sans espace
        match = re.search(r'du\s+(\d{1,2})\s*(?:er|e)?\s+(\w+)\s+au\s+(\d{1,2})\s*(?:er|e)?\s+(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour1 = match.group(1).zfill(2)
            mois1 = mois_mapping.get(match.group(2), '??')
            jour2 = match.group(3).zfill(2)
            mois2 = mois_mapping.get(match.group(4), '??')
            annee = match.group(5)
            # Vérifier que mois1 est un vrai mois
            if mois1 != '??':
                return f"{annee}/{mois1}/{jour1} - {annee}/{mois2}/{jour2}"

        # Pattern spécial: "30 juin-1er juillet 2025" ou "1er février-26 mars 2025" (plage entre deux mois, même année)
        # Support pour "er" après le premier chiffre (1er, 2e, etc.)
        match = re.search(r'(\d{1,2})(?:er|e)?\s+(\w+)\s*[-–]\s*(\d{1,2})(?:er|e)?\s+(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour1 = match.group(1).zfill(2)
            mois1 = mois_mapping.get(match.group(2), '??')
            jour2 = match.group(3).zfill(2)
            mois2 = mois_mapping.get(match.group(4), '??')
            annee = match.group(5)
            # Vérifier que mois1 est un vrai mois
            if mois1 != '??':
                return f"{annee}/{mois1}/{jour1} - {annee}/{mois2}/{jour2}"

        # Pattern 0: "X ER-Y MOIS ANNÉE" avec espaces optionnels
        match = re.search(r'(\d{1,2})\s*(?:er|e)?\s*[-–]\s*(\d{1,2})\s+(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour1 = match.group(1).zfill(2)
            jour2 = match.group(2).zfill(2)
            mois = mois_mapping.get(match.group(3), '??')
            annee = match.group(4)
            return f"{annee}/{mois}/{jour1} - {annee}/{mois}/{jour2}"

        # Pattern 0b: "XERMOIS ANNÉE" sans espaces
        match = re.search(r'(\d{1,2})(?:er|e)(\w+)\s+(\d{4})', dates_lower)
        if match:
            jour = match.group(1).zfill(2)
            mois = mois_mapping.get(match.group(2), '??')
            annee = match.group(3)
            return f"{annee}/{mois}/{jour}"

        # Pattern 1: "JUSQU'AU X MOIS ANNÉE"
        match = re.search(r'jusqu[\'\'\u2019]?au\s+(\d{1,2})\s+(\w+)\s+(\d{4})', dates_lower)
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
        Extrait la localisation spécifiquement du champ "Lieu :" ou "Lieux :"
        C'est la source la plus fiable pour le lieu

        Args:
            text: Texte à analyser

        Returns:
            Localisation extraite ou None
        """
        # Supporter à la fois "Lieu :" (singulier) et "Lieux :" (pluriel)
        # Ne pas s'arrêter sur "et" qui fait partie du nom du lieu
        match = re.search(r'Lieux?\s*:\s*(.+?)(?:\s+(?:Site|Horaires|Tarif|en un)\s|$)', text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            # Nettoyer les espaces multiples
            location = re.sub(r'\s+', ' ', location)
            # Ajouter espace avant parenthèse si manquant
            location = re.sub(r'([^\s])\(', r'\1 (', location)
            # Ne plus tronquer - garder le nom complet avec parenthèses
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
        # Normaliser les superscripts "ᵉʳ" en "er" (causé par <sup>er</sup>)
        text = text.replace('ᵉʳ', 'er').replace('ᵉ', 'e')

        # Mapping des mois
        mois_mapping = {
            'janvier': '01', 'février': '02', 'fevrier': '02', 'mars': '03',
            'avril': '04', 'mai': '05', 'juin': '06', 'juillet': '07',
            'août': '08', 'aout': '08', 'septembre': '09', 'octobre': '10',
            'novembre': '11', 'décembre': '12', 'decembre': '12'
        }

        # Pattern "Du 9 octobre 2024 au 13 janvier 2025" ou "Du 1er novembre 2024 au 2 février 2025" (deux années différentes)
        # Support "Du 1 er février" avec espace avant "er" (causé par <sup>er</sup>)
        match = re.search(r'Du\s+(\d{1,2})(?:\s*(?:er|e))?\s+(\w+)\s+(\d{4})\s+au\s+(\d{1,2})(?:\s*(?:er|e))?\s+(\w+)\s+(\d{4})', text, re.IGNORECASE)
        if match:
            jour1 = match.group(1).zfill(2)
            mois1 = mois_mapping.get(match.group(2).lower(), '??')
            annee1 = match.group(3)
            jour2 = match.group(4).zfill(2)
            mois2 = mois_mapping.get(match.group(5).lower(), '??')
            annee2 = match.group(6)
            return f"{annee1}/{mois1}/{jour1} - {annee2}/{mois2}/{jour2}"

        # Pattern "Du 8 février au 2 mars 2025" ou "Du 1er février au 26 mars 2025" (même année)
        # Support "Du 1 er février" avec espace avant "er" (causé par <sup>er</sup>)
        match = re.search(r'Du\s+(\d{1,2})(?:\s*(?:er|e))?\s+(\w+)\s+au\s+(\d{1,2})(?:\s*(?:er|e))?\s+(\w+)\s+(\d{4})', text, re.IGNORECASE)
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
        Cherche des patterns comme "à [lieu]", "au [lieu]", "Lieu :[lieu]", "Lieux :[lieux]", etc.

        Args:
            text: Texte à analyser

        Returns:
            Localisation extraite ou None
        """
        # Pattern 0: Format "Lieu :" / "Lieux :" (le plus fiable)
        # Ne pas s'arrêter sur "et" qui fait partie du nom du lieu
        match = re.search(r'Lieux?\s*:\s*(.+?)(?:\s+(?:Site|Horaires|Tarif|en un)\s|$)', text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            # Nettoyer les espaces multiples
            location = re.sub(r'\s+', ' ', location)
            # Ajouter espace avant parenthèse si manquant
            location = re.sub(r'([^\s])\(', r'\1 (', location)
            # Supprimer les parenthèses si la localisation est assez courte
            if len(location) < 60:
                base_match = re.match(r'^([^(]+)', location)
                if base_match:
                    base_loc = base_match.group(1).strip()
                    if len(base_loc) >= 10:
                        location = base_loc
            return location

        # Pattern 1: Lieux avec préposition (musée, galerie, etc.)
        match = re.search(r'(?:au|à|dans le|dans l\')\s+(musée|musee|galerie|parc|temple|sanctuaire|jardin|centre|espace)\s+([A-Za-z\-\s]+?)(?:\s+\([^)]+\))?(?=[,\.]|$)', text, re.IGNORECASE)
        if match:
            location = match.group(1) + ' ' + match.group(2).strip()
            # Ajouter les parenthèses si présentes
            paren_match = re.search(r'\([^)]+\)', match.group(0))
            if paren_match:
                location += ' ' + paren_match.group(0)
            return location

        # Pattern 2: Lieux directs avec nom propre
        match = re.search(r'(musée|musee|galerie|parc|temple|sanctuaire|jardin|centre|espace)\s+([A-Z][A-Za-z\-\s]+?)(?:\s+\([^)]+\))?(?=[,\.]|$)', text)
        if match:
            location = match.group(1) + ' ' + match.group(2).strip()
            # Ajouter les parenthèses si présentes
            paren_match = re.search(r'\([^)]+\)', match.group(0))
            if paren_match:
                location += ' ' + paren_match.group(0)
            return location

        return None

    def _extract_official_url_with_fallback(self, paragraph_elem) -> Optional[str]:
        """
        Extrait l'URL officielle avec hiérarchie de fallback

        Priority:
        1. "Site de l'événement" / "Site officiel" / "Site de l'exposition"
        2. Lien avec "site" dans le texte
        3. Lien HTTP non-Google Maps

        Args:
            paragraph_elem: Élément BeautifulSoup du paragraphe

        Returns:
            URL officielle ou None
        """
        if not paragraph_elem:
            return None

        links = paragraph_elem.find_all('a')

        # Priority 1: "Site de l'événement", "Site officiel", "Site de l'exposition"
        for link in links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True).lower()
            if 'site' in link_text and ('événement' in link_text or 'officiel' in link_text or 'exposition' in link_text):
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

        Args:
            paragraph_elem: Élément BeautifulSoup du paragraphe

        Returns:
            Lien Google Maps ou None
        """
        if not paragraph_elem:
            return None

        links = paragraph_elem.find_all('a')
        for link in links:
            href = link.get('href', '')
            # Google Maps (formats: google.*/maps, goo.gl, maps.app.goo.gl)
            if ('google' in href and 'maps' in href) or 'goo.gl' in href or 'maps.app.goo.gl' in href:
                return href

        return None

    def save_to_database(self, expositions: List[Dict], db_path: str = None):
        """
        Sauvegarde les expositions dans la base de données SQLite.
        Extrait automatiquement les coordonnées GPS depuis les liens Google Maps.

        Args:
            expositions: Liste des expositions
            db_path: Chemin vers la base de données (optionnel, par défaut data/tokyo_events.sqlite)

        Returns:
            int: Nombre d'expositions sauvegardées
        """
        if not db_path:
            db_path = "data/tokyo_events.sqlite"

        # Extraire les coordonnées GPS pour chaque exposition
        gps_extractor = GPSExtractor()
        gps_success = 0

        for exposition in expositions:
            if exposition.get('googlemap_link'):
                coords = gps_extractor.extract_from_googlemap_link(exposition['googlemap_link'])
                if coords:
                    exposition['latitude'], exposition['longitude'] = coords
                    gps_success += 1

        db = EventDatabase(db_path)
        count = db.insert_events(expositions, event_type='expositions')

        print(f"✓ {count} expositions sauvegardées dans la base de données {db_path}")
        if gps_success > 0:
            print(f"✓ {gps_success}/{len(expositions)} coordonnées GPS extraites automatiquement")
        return count


def main():
    """
    Fonction principale pour utiliser le scraper
    """
    scraper = TokyoExpositionScraper()

    # Exemple d'utilisation
    print("=== Scraper d'Expositions Tokyo ===\n")

    # Scraper janvier 2026
    expositions = scraper.scrape_expositions(month=1, year=2026)

    if expositions:
        # Sauvegarder dans la base de données
        scraper.save_to_database(expositions)

        # Afficher un aperçu
        print(f"\n=== Aperçu des {min(3, len(expositions))} premières expositions ===")
        for i, exposition in enumerate(expositions[:3], 1):
            print(f"\n{i}. {exposition['name']}")
            dates_display = format_date_range(exposition.get('start_date'), exposition.get('end_date'))
            if dates_display:
                print(f"   Dates: {dates_display}")
            if exposition.get('location'):
                print(f"   Lieu: {exposition['location']}")

    # Exemple: scraper plusieurs mois
    print("\n\n=== Scraper plusieurs mois ===")
    for month in [1, 2, 3]:  # Janvier, Février, Mars 2026
        try:
            expositions = scraper.scrape_expositions(month=month, year=2026)
            if expositions:
                scraper.save_to_database(expositions)
        except Exception as e:
            print(f"Erreur pour le mois {month}/2026: {e}")


if __name__ == "__main__":
    main()
