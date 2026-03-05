"""Endpoints API pour les événements."""

from fastapi import APIRouter, Query, BackgroundTasks
from typing import Optional
from web.models.schemas import EventsListResponse, EventFilters
from web.services.event_service import EventService
from datetime import datetime
import uuid
import os

router = APIRouter()
event_service = EventService()

# Système de gestion des mises à jour
update_tasks = {}
last_update_timestamp = None
COOLDOWN_SECONDS = 300  # 5 minutes
LAST_UPDATE_FILE = "data/last_update.txt"


@router.get("/", response_model=EventsListResponse)
async def get_events(
    event_type: Optional[str] = Query(None, pattern="^(festivals|expositions|hanabi|marches|tokyo_cheapo)$"),
    event_types: Optional[str] = Query(None, description="Types d'événements séparés par virgules (ex: hanabi,festivals)"),
    category: Optional[str] = None,
    category_groups: Optional[str] = Query(None, description="Familles de catégories séparées par virgules (ex: culture_arts,nature_outdoor)"),
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
    has_coordinates: bool = Query(True, description="Uniquement événements avec GPS")
):
    """Liste des événements avec filtres."""
    # Parse category_groups et event_types si fournis
    groups_list = category_groups.split(',') if category_groups else None
    types_list = event_types.split(',') if event_types else None

    filters = EventFilters(
        event_type=event_type,
        event_types=types_list,
        category=category,
        category_groups=groups_list,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        has_coordinates=has_coordinates
    )
    return event_service.get_events(filters)


@router.get("/stats")
async def get_stats(
    event_type: Optional[str] = Query(None, pattern="^(festivals|expositions|hanabi|marches|tokyo_cheapo)$"),
    event_types: Optional[str] = Query(None, description="Types d'événements séparés par virgules"),
    category: Optional[str] = None,
    category_groups: Optional[str] = Query(None, description="Familles de catégories séparées par virgules"),
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
    has_coordinates: bool = Query(True, description="Uniquement événements avec GPS")
):
    """Statistiques avec filtres."""
    # Parse category_groups et event_types si fournis
    groups_list = category_groups.split(',') if category_groups else None
    types_list = event_types.split(',') if event_types else None

    filters = EventFilters(
        event_type=event_type,
        event_types=types_list,
        category=category,
        category_groups=groups_list,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        has_coordinates=has_coordinates
    )
    return event_service.get_statistics(filters)


@router.get("/category-groups")
async def get_category_groups():
    """Retourne les métadonnées des familles de catégories."""
    from web.config import CATEGORY_GROUPS
    return CATEGORY_GROUPS


@router.get("/all-categories")
async def get_all_categories():
    """Retourne toutes les catégories unifiées (types + groupes)."""
    from web.config import ALL_CATEGORIES
    return ALL_CATEGORIES


# ============================================================================
# ENDPOINTS DE MISE À JOUR
# ============================================================================

def load_last_update_timestamp():
    """Charge le timestamp de la dernière mise à jour depuis le fichier."""
    global last_update_timestamp
    try:
        if os.path.exists(LAST_UPDATE_FILE):
            with open(LAST_UPDATE_FILE, 'r') as f:
                timestamp_str = f.read().strip()
                last_update_timestamp = datetime.fromisoformat(timestamp_str)
    except Exception as e:
        print(f"Erreur lors du chargement du timestamp: {e}")
        last_update_timestamp = None


def mark_last_update():
    """Enregistre le timestamp actuel comme dernière mise à jour."""
    global last_update_timestamp
    last_update_timestamp = datetime.now()
    try:
        os.makedirs(os.path.dirname(LAST_UPDATE_FILE), exist_ok=True)
        with open(LAST_UPDATE_FILE, 'w') as f:
            f.write(last_update_timestamp.isoformat())
    except Exception as e:
        print(f"Erreur lors de l'enregistrement du timestamp: {e}")


def can_update() -> bool:
    """Vérifie si une mise à jour est autorisée (cooldown expiré)."""
    if last_update_timestamp is None:
        return True
    elapsed = (datetime.now() - last_update_timestamp).total_seconds()
    return elapsed >= COOLDOWN_SECONDS


def get_cooldown_remaining() -> int:
    """Retourne le nombre de secondes restantes avant la prochaine mise à jour."""
    if last_update_timestamp is None:
        return 0
    elapsed = (datetime.now() - last_update_timestamp).total_seconds()
    return max(0, int(COOLDOWN_SECONDS - elapsed))


def run_update_task(task_id: str):
    """Exécute la mise à jour en arrière-plan."""
    try:
        # Importer la fonction de mise à jour
        from main import update_all_events

        # Exécuter la mise à jour
        results = update_all_events(dry_run=False)

        # Mettre à jour le statut de la tâche
        update_tasks[task_id] = {
            "status": "completed",
            "results": results,
            "started_at": update_tasks[task_id]["started_at"],
            "completed_at": datetime.now().isoformat()
        }
    except Exception as e:
        # En cas d'erreur
        update_tasks[task_id] = {
            "status": "error",
            "error": str(e),
            "started_at": update_tasks[task_id]["started_at"],
            "completed_at": datetime.now().isoformat()
        }


@router.get("/update/cooldown")
async def get_cooldown_status():
    """Retourne l'état du cooldown."""
    remaining = get_cooldown_remaining()
    return {
        "cooldown_active": remaining > 0,
        "remaining_seconds": remaining,
        "last_update": last_update_timestamp.isoformat() if last_update_timestamp else None
    }


@router.post("/update")
async def trigger_update(background_tasks: BackgroundTasks):
    """Déclenche une mise à jour globale des événements."""
    # Vérifier le cooldown
    if not can_update():
        return {
            "error": "Cooldown actif",
            "retry_after": get_cooldown_remaining()
        }

    # Générer un ID unique pour la tâche
    task_id = str(uuid.uuid4())

    # Enregistrer la tâche
    update_tasks[task_id] = {
        "status": "running",
        "started_at": datetime.now().isoformat()
    }

    # Marquer le cooldown
    mark_last_update()

    # Lancer la tâche en arrière-plan
    background_tasks.add_task(run_update_task, task_id)

    return {
        "task_id": task_id,
        "status": "started"
    }


@router.get("/update/status/{task_id}")
async def get_update_status(task_id: str):
    """Retourne le statut d'une tâche de mise à jour."""
    if task_id not in update_tasks:
        return {"error": "Tâche inconnue"}

    return update_tasks[task_id]
