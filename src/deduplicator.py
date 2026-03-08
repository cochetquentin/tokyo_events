"""
Module de déduplication et fusion intelligente d'événements.

Responsabilités :
- Normalisation de noms, dates, lieux
- Calcul de similarité fuzzy (rapidfuzz)
- Détection de doublons intra-scraper et inter-scraper
- Fusion intelligente avec priorités et enrichissement
- Génération de rapports de déduplication
"""

import re
import unicodedata
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from rapidfuzz import fuzz
from datetime import datetime


@dataclass
class DeduplicationReport:
    """Rapport de déduplication avec statistiques et détails des fusions"""
    total_input: int
    duplicates_found: int
    merged_events: List[Dict] = field(default_factory=list)
    final_count: int = 0
    enrichment_stats: Dict[str, int] = field(default_factory=dict)


class EventDeduplicator:
    """
    Gestionnaire de déduplication et fusion d'événements.

    Utilise la normalisation fuzzy et des priorités de sources pour :
    - Détecter les doublons entre événements
    - Fusionner intelligemment en préservant les données prioritaires
    - Enrichir avec les champs manquants (hours, fee, etc.)
    """

    # Priorités des sources (1 = plus prioritaire)
    SOURCE_PRIORITY = {
        'hanabi': 1,
        'festivals': 2,
        'expositions': 3,
        'marches': 4,
        'tokyo_cheapo': 5
    }

    # Mapping de traduction japonais → anglais (mot à mot)
    TRANSLATION_MAP = {
        # Événements
        'matsuri': 'festival',
        'taikai': 'tournament',
        'marche': 'market',

        # Feux d'artifice
        'hanabi': 'fireworks',

        # Fleurs
        'sakura': 'cherry',
        'ume': 'plum',
        'momiji': 'maple',
        'ajisai': 'hydrangea',
        'tsubaki': 'camellia',

        # Termes naturels
        'yozakura': 'nightcherry',  # Nuit + cerisier (mot composé)
        'koyo': 'foliage',
        'koen': 'park',

        # Termes génériques
        'festival': 'festival',  # Garder tel quel
        'blossom': 'blossom',
        'exhibition': 'exhibition',
        'market': 'market',
    }

    # Champs JAMAIS écrasés lors de la fusion
    PROTECTED_FIELDS = [
        'name', 'event_type', 'start_date', 'end_date',
        'location', 'prefecture', 'city', 'venue'
    ]

    # Champs enrichissables (prendre secondary si primary vide)
    ENRICHABLE_FIELDS = [
        'description', 'website', 'googlemap_link',
        'latitude', 'longitude', 'hours', 'fee',
        'category', 'dates', 'event_id', 'start_time',
        'fireworks_count', 'detail_url'
    ]

    def deduplicate_events(
        self,
        events: List[Dict],
        event_type: str,
        existing_db_events: List[Dict]
    ) -> Tuple[List[Dict], DeduplicationReport]:
        """
        Déduplique les événements en 2 passes :
        1. Intra-scraper : dédupliquer events entre eux
        2. Inter-scraper : comparer avec existing_db_events

        Args:
            events: Nouveaux événements à dédupliquer
            event_type: Type de la source (hanabi, festivals, etc.)
            existing_db_events: Événements déjà en DB

        Returns:
            Tuple (événements dédupliqués, rapport)
        """
        if not events:
            return [], DeduplicationReport(total_input=0, duplicates_found=0, final_count=0)

        # Normaliser tous les événements
        normalized_new = [self._normalize_event(e) for e in events]
        normalized_existing = [self._normalize_event(e) for e in existing_db_events]

        # PASSE 1 : Intra-scraper (doublons dans events)
        deduped_new, intra_report = self._deduplicate_intra(normalized_new, event_type)

        # PASSE 2 : Inter-scraper (comparer avec DB existante)
        final_events, inter_report = self._deduplicate_inter(
            deduped_new,
            normalized_existing,
            event_type
        )

        # Fusionner les rapports
        total_report = self._merge_reports(intra_report, inter_report, len(events))

        return final_events, total_report

    def _normalize_event(self, event: Dict) -> Dict:
        """
        Ajoute des champs normalisés pour comparaison.

        Args:
            event: Événement à normaliser

        Returns:
            Copie de l'événement avec champs _norm_*
        """
        normalized = event.copy()

        # Normaliser le nom
        normalized['_norm_name'] = self._normalize_name(event['name'])

        # Normaliser la localisation (gérer les 2 formats)
        if event.get('location'):
            normalized['_norm_location'] = self._normalize_location(
                location=event['location']
            )
        else:
            # Hanabi : construire depuis prefecture/city/venue
            normalized['_norm_location'] = self._normalize_location(
                prefecture=event.get('prefecture', ''),
                city=event.get('city', ''),
                venue=event.get('venue', '')
            )

        return normalized

    def _normalize_name(self, name: str) -> str:
        """
        Normalise un nom pour comparaison fuzzy.

        Étapes :
        1. Minuscules
        2. Supprimer accents
        3. Supprimer ponctuation
        4. Normaliser espaces
        5. Traduire termes japonais courants → anglais

        Args:
            name: Nom à normaliser

        Returns:
            Nom normalisé et traduit
        """
        if not name:
            return ""

        # Minuscules
        text = name.lower()

        # Supprimer accents (NFD decomposition)
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')

        # Supprimer ponctuation (garder alphanumériques, espaces, caractères japonais)
        text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', ' ', text)

        # Normaliser espaces (multiples → single, strip)
        text = re.sub(r'\s+', ' ', text).strip()

        # Traduire termes japonais courants
        words = text.split()
        translated_words = []
        for word in words:
            # Chercher traduction exacte ou conserver le mot original
            translated_words.append(self.TRANSLATION_MAP.get(word, word))
        text = ' '.join(translated_words)

        return text

    def _normalize_location(
        self,
        location: str = "",
        prefecture: str = "",
        city: str = "",
        venue: str = ""
    ) -> str:
        """
        Normalise une localisation pour comparaison.

        Gère 2 formats :
        - Format simple : location="Shibuya-ku"
        - Format hanabi : prefecture="東京都", city="渋谷区", venue="Yoyogi Park"

        Args:
            location: Location directe (festivals/expositions/marches)
            prefecture: Préfecture (hanabi)
            city: Ville (hanabi)
            venue: Lieu spécifique (hanabi)

        Returns:
            Location normalisée
        """
        # Construire location unifiée
        if location:
            text = location
        else:
            # Hanabi : construire depuis prefecture/city/venue
            parts = [venue, city, prefecture]
            text = ', '.join(p for p in parts if p)

        if not text:
            return ""

        # Minuscules
        text = text.lower()

        # Supprimer accents
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')

        # Supprimer ponctuation (garder alphanumériques, espaces, caractères japonais)
        text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', ' ', text)

        # Normaliser espaces
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calcule la similarité entre 2 chaînes (0-100%).

        Utilise rapidfuzz pour performance optimale.

        Args:
            str1: Première chaîne
            str2: Deuxième chaîne

        Returns:
            Score de similarité (0-100)
        """
        if not str1 or not str2:
            return 0.0

        return fuzz.ratio(str1, str2)

    def _dates_match(self, date1: Optional[str], date2: Optional[str]) -> bool:
        """
        Vérifie si 2 dates sont identiques.

        Args:
            date1: Date 1 (format YYYY/MM/DD)
            date2: Date 2 (format YYYY/MM/DD)

        Returns:
            True si identiques
        """
        if not date1 or not date2:
            return False

        return date1 == date2

    def _dates_overlap(
        self,
        start1: Optional[str],
        end1: Optional[str],
        start2: Optional[str],
        end2: Optional[str]
    ) -> bool:
        """
        Vérifie si 2 périodes se chevauchent.

        Args:
            start1, end1: Période 1
            start2, end2: Période 2

        Returns:
            True si chevauchement
        """
        if not start1 or not start2:
            return False

        # Utiliser end = start si end manquant
        end1 = end1 or start1
        end2 = end2 or start2

        # Chevauchement : start1 <= end2 ET start2 <= end1
        return start1 <= end2 and start2 <= end1

    def _are_duplicates(
        self,
        event1: Dict,
        event2: Dict,
        threshold: float = 0.80
    ) -> Tuple[bool, str]:
        """
        Détermine si 2 événements sont des doublons.

        Utilise 2 niveaux de critères :
        1. Critères stricts : dates exactes + similarité 80%
        2. Critères assouplis : dates chevauchantes + similarité 90%

        Args:
            event1: Premier événement (normalisé)
            event2: Deuxième événement (normalisé)
            threshold: Seuil de similarité (default: 0.80)

        Returns:
            Tuple (is_duplicate, reason)
        """
        # Edge case : événements sans dates
        if not event1.get('start_date') or not event2.get('start_date'):
            return False, "Missing dates - skipping comparison"

        # Vérifier les dates
        dates_match_strict = (
            self._dates_match(event1.get('start_date'), event2.get('start_date')) and
            self._dates_match(event1.get('end_date'), event2.get('end_date'))
        )

        dates_overlap = self._dates_overlap(
            event1.get('start_date'), event1.get('end_date'),
            event2.get('start_date'), event2.get('end_date')
        )

        # Calculer similarités
        name_sim = self._calculate_similarity(
            event1.get('_norm_name', ''),
            event2.get('_norm_name', '')
        )

        loc_sim = self._calculate_similarity(
            event1.get('_norm_location', ''),
            event2.get('_norm_location', '')
        )

        # Détection de préfixes (ex: "Roppongi Crossing" vs "Roppongi Crossing 2025: ...")
        name1 = event1.get('_norm_name', '')
        name2 = event2.get('_norm_name', '')

        # Préfixe exact (un nom complet est préfixe de l'autre)
        is_exact_prefix = (name1.startswith(name2) or name2.startswith(name1)) and min(len(name1), len(name2)) >= 10

        # Préfixe commun (les deux noms partagent un préfixe significatif)
        # Ex: "Yoshino Baigo Ume Matsuri" vs "Yoshino Baigo Plum Blossom Festival"
        common_prefix_len = 0
        for c1, c2 in zip(name1, name2):
            if c1 == c2:
                common_prefix_len += 1
            else:
                break
        has_common_prefix = common_prefix_len >= 15  # Au moins 15 caractères communs (environ 3 mots)

        # Critères stricts
        if dates_match_strict and name_sim >= (threshold * 100) and loc_sim >= (threshold * 100):
            return True, f"Strict match (name:{name_sim:.0f}%, loc:{loc_sim:.0f}%)"

        # Critères préfixe exact (threshold location très bas car le nom préfixe est déjà une forte indication)
        # Ex: "Roppongi Crossing" (Roppongi) vs "Roppongi Crossing 2025: ..." (Mori Art Museum)
        if dates_match_strict and is_exact_prefix:
            return True, f"Prefix match (shorter is prefix of longer, loc:{loc_sim:.0f}%)"

        # Critères préfixe commun (noms bilingues ou variantes avec même début significatif)
        # Ex: "Yoshino Baigo Ume Matsuri" vs "Yoshino Baigo Plum Blossom Festival"
        if dates_match_strict and has_common_prefix:
            return True, f"Common prefix match ({common_prefix_len} chars common, loc:{loc_sim:.0f}%)"

        # Critères assouplis (threshold augmenté pour compenser)
        if dates_overlap and name_sim >= 85 and loc_sim >= 75:
            return True, f"Overlap match (name:{name_sim:.0f}%, loc:{loc_sim:.0f}%)"

        return False, ""

    def merge_events(self, primary: Dict, secondary: Dict) -> Dict:
        """
        Fusionne 2 événements en gardant le primaire et en enrichissant.

        Règles :
        - Champs PROTECTED_FIELDS : jamais écrasés
        - Champs ENRICHABLE_FIELDS : prendre secondary si primary vide
        - Description : prendre la plus longue

        Args:
            primary: Événement prioritaire
            secondary: Événement à fusionner

        Returns:
            Événement fusionné
        """
        merged = primary.copy()
        enriched_fields = []

        # Enrichir avec les champs manquants
        for field in self.ENRICHABLE_FIELDS:
            # Si primary n'a pas le champ mais secondary l'a
            if not merged.get(field) and secondary.get(field):
                merged[field] = secondary[field]
                enriched_fields.append(field)

        # Cas spécial : description (prendre la plus longue si différentes)
        if merged.get('description') and secondary.get('description'):
            if (merged['description'] != secondary['description'] and
                len(secondary['description']) > len(merged['description'])):
                merged['description'] = secondary['description']
                if 'description' not in enriched_fields:
                    enriched_fields.append('description')

        # Stocker les champs enrichis pour reporting
        if enriched_fields:
            merged['_enriched_fields'] = enriched_fields

        return merged

    def _get_source_priority(self, event_type: str) -> int:
        """
        Retourne la priorité d'une source (1 = plus prioritaire).

        Args:
            event_type: Type de source

        Returns:
            Priorité (1-5)
        """
        return self.SOURCE_PRIORITY.get(event_type, 99)

    def _deduplicate_intra(
        self,
        events: List[Dict],
        event_type: str
    ) -> Tuple[List[Dict], DeduplicationReport]:
        """
        Déduplique les événements entre eux (intra-scraper).

        Args:
            events: Événements normalisés
            event_type: Type de source

        Returns:
            Tuple (événements dédupliqués, rapport)
        """
        if not events:
            return [], DeduplicationReport(total_input=0, duplicates_found=0, final_count=0)

        deduped = []
        merged_events = []
        enrichment_counts = {}

        for i, event in enumerate(events):
            # Chercher si doublon avec événements déjà traités
            is_duplicate = False

            for j, existing in enumerate(deduped):
                is_dup, reason = self._are_duplicates(event, existing)

                if is_dup:
                    # Fusionner (garder le premier trouvé comme primaire)
                    merged = self.merge_events(existing, event)
                    deduped[j] = merged

                    # Logger la fusion
                    merged_events.append({
                        'primary_name': existing['name'],
                        'secondary_name': event['name'],
                        'reason': reason,
                        'enriched_fields': merged.get('_enriched_fields', [])
                    })

                    # Compter enrichissements
                    for field in merged.get('_enriched_fields', []):
                        enrichment_counts[field] = enrichment_counts.get(field, 0) + 1

                    is_duplicate = True
                    break

            # Si pas doublon, ajouter
            if not is_duplicate:
                deduped.append(event)

        report = DeduplicationReport(
            total_input=len(events),
            duplicates_found=len(events) - len(deduped),
            merged_events=merged_events,
            final_count=len(deduped),
            enrichment_stats=enrichment_counts
        )

        return deduped, report

    def _deduplicate_inter(
        self,
        new_events: List[Dict],
        existing_events: List[Dict],
        event_type: str
    ) -> Tuple[List[Dict], DeduplicationReport]:
        """
        Déduplique par rapport aux événements déjà en DB (inter-scraper).

        Logique :
        - Nouveau plus prioritaire → UPDATE (garder nouveau)
        - Nouveau moins prioritaire → SKIP ou ENRICH seulement
        - Même priorité → Enrichir champs manquants

        Args:
            new_events: Nouveaux événements normalisés
            existing_events: Événements DB normalisés
            event_type: Type de la source des nouveaux

        Returns:
            Tuple (événements à insérer, rapport)
        """
        if not new_events:
            return [], DeduplicationReport(total_input=0, duplicates_found=0, final_count=0)

        to_insert = []
        merged_events = []
        enrichment_counts = {}
        new_priority = self._get_source_priority(event_type)

        for new_event in new_events:
            # Chercher si doublon avec DB
            found_duplicate = False

            for existing in existing_events:
                is_dup, reason = self._are_duplicates(new_event, existing)

                if is_dup:
                    existing_priority = self._get_source_priority(existing.get('event_type', ''))

                    # Nouveau plus prioritaire → UPDATE (via INSERT OR REPLACE)
                    if new_priority < existing_priority:
                        merged = self.merge_events(new_event, existing)
                        to_insert.append(merged)

                        merged_events.append({
                            'primary_name': new_event['name'],
                            'secondary_name': existing['name'],
                            'reason': f"{reason} - UPDATE (new priority {new_priority} > existing {existing_priority})",
                            'enriched_fields': merged.get('_enriched_fields', [])
                        })

                    # Nouveau moins prioritaire → Enrichir seulement si champs manquants
                    elif new_priority > existing_priority:
                        merged = self.merge_events(existing, new_event)

                        # Seulement insérer si enrichissement effectif
                        if merged.get('_enriched_fields'):
                            to_insert.append(merged)

                            merged_events.append({
                                'primary_name': existing['name'],
                                'secondary_name': new_event['name'],
                                'reason': f"{reason} - ENRICH only (existing priority {existing_priority} > new {new_priority})",
                                'enriched_fields': merged.get('_enriched_fields', [])
                            })

                            # Compter enrichissements
                            for field in merged.get('_enriched_fields', []):
                                enrichment_counts[field] = enrichment_counts.get(field, 0) + 1
                        # Sinon SKIP

                    # Même priorité → Enrichir champs manquants
                    else:
                        merged = self.merge_events(existing, new_event)

                        if merged.get('_enriched_fields'):
                            to_insert.append(merged)

                            merged_events.append({
                                'primary_name': existing['name'],
                                'secondary_name': new_event['name'],
                                'reason': f"{reason} - ENRICH (same priority {new_priority})",
                                'enriched_fields': merged.get('_enriched_fields', [])
                            })

                            for field in merged.get('_enriched_fields', []):
                                enrichment_counts[field] = enrichment_counts.get(field, 0) + 1

                    found_duplicate = True
                    break

            # Si pas doublon, ajouter
            if not found_duplicate:
                to_insert.append(new_event)

        report = DeduplicationReport(
            total_input=len(new_events),
            duplicates_found=len(merged_events),
            merged_events=merged_events,
            final_count=len(to_insert),
            enrichment_stats=enrichment_counts
        )

        return to_insert, report

    def _merge_reports(
        self,
        intra_report: DeduplicationReport,
        inter_report: DeduplicationReport,
        total_input: int
    ) -> DeduplicationReport:
        """
        Fusionne les rapports intra et inter.

        Args:
            intra_report: Rapport déduplication intra-scraper
            inter_report: Rapport déduplication inter-scraper
            total_input: Nombre total d'événements en entrée

        Returns:
            Rapport fusionné
        """
        merged_events = intra_report.merged_events + inter_report.merged_events

        # Fusionner les stats d'enrichissement
        enrichment_stats = intra_report.enrichment_stats.copy()
        for field, count in inter_report.enrichment_stats.items():
            enrichment_stats[field] = enrichment_stats.get(field, 0) + count

        return DeduplicationReport(
            total_input=total_input,
            duplicates_found=intra_report.duplicates_found + inter_report.duplicates_found,
            merged_events=merged_events,
            final_count=inter_report.final_count,
            enrichment_stats=enrichment_stats
        )
