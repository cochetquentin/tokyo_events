# Guide de Mise à Jour Automatique des Événements

## 📋 Vue d'ensemble

Ce guide explique comment utiliser le système de mise à jour automatique pour les événements Tokyo Cheapo.

## 🚀 Utilisation

### 1. Mise à jour manuelle (recommandé pour tester)

```bash
# Mise à jour complète (toutes les pages)
cd "d:\Perso\Algo\Perso\TokyoEvent"
PYTHONPATH=. uv run update_events.py

# Mise à jour limitée (3 pages seulement)
PYTHONPATH=. uv run update_events.py --max-pages 3

# Simulation sans sauvegarde (dry-run)
PYTHONPATH=. uv run update_events.py --dry-run

# Voir les statistiques uniquement
PYTHONPATH=. uv run update_events.py --stats

# Mise à jour sans nettoyer les vieux événements
PYTHONPATH=. uv run update_events.py --no-clean
```

### 2. Statistiques de la base de données

```bash
# Afficher l'état actuel
PYTHONPATH=. uv run update_events.py --stats
```

Affiche :
- Total événements
- Événements futurs vs passés
- Répartition par type (festivals, expositions, marches, tokyo_cheapo)
- Dernière mise à jour

### 3. Voir les événements Tokyo Cheapo

```bash
# Afficher tous les événements tokyo_cheapo
uv run view_tokyo_cheapo.py
```

## ⚙️ Fonctionnalités du script de mise à jour

### Détection intelligente des nouveaux événements

Le script :
1. ✅ Récupère les événements existants de la base
2. ✅ Scrappe les événements du site Tokyo Cheapo
3. ✅ Compare et identifie **uniquement les nouveaux**
4. ✅ Sauvegarde seulement les nouveaux événements
5. ✅ Évite les doublons (basé sur nom + date)

### Nettoyage automatique

- 🧹 Supprime automatiquement les événements passés depuis **plus de 30 jours**
- 📊 Garde l'historique récent pour référence
- ⚡ Optimise la taille de la base de données

### Statistiques détaillées

Affiche avant/après chaque mise à jour :
- Nombre total d'événements
- Événements futurs/passés
- Répartition par type
- Nombre de nouveaux événements ajoutés
- Nombre d'événements nettoyés

## 🤖 Automatisation

### Option 1 : Tâche planifiée Windows

1. **Ouvrir le Planificateur de tâches**
   - Appuyez sur `Win + R`
   - Tapez `taskschd.msc`
   - Entrée

2. **Créer une tâche**
   - Clic droit → "Créer une tâche de base"
   - Nom : "Mise à jour événements Tokyo"
   - Déclencheur : Quotidien à 8h00 (par exemple)

3. **Action**
   - Programme : `d:\Perso\Algo\Perso\TokyoEvent\schedule_update.bat`
   - Démarrer dans : `d:\Perso\Algo\Perso\TokyoEvent`

4. **Options**
   - ✅ Exécuter même si l'utilisateur n'est pas connecté
   - ✅ Exécuter avec les autorisations maximales

### Option 2 : Script manuel avec log

```bash
# Créer un fichier de log horodaté
cd "d:\Perso\Algo\Perso\TokyoEvent"
PYTHONPATH=. uv run update_events.py > logs/update_$(date +%Y%m%d_%H%M%S).log 2>&1
```

### Option 3 : Cron job (Linux/Mac)

```bash
# Ajouter au crontab (exécution quotidienne à 8h)
0 8 * * * cd /path/to/TokyoEvent && PYTHONPATH=. uv run update_events.py >> logs/update.log 2>&1
```

## 📊 Exemple de sortie

```
================================================================================
🔄 MISE À JOUR DES ÉVÉNEMENTS TOKYO CHEAPO
================================================================================

📊 État de la base de données AVANT mise à jour:
   Total événements        : 161
   Événements futurs       : 145
   Événements passés       : 16

   Par type:
      - expositions        :   73
      - festivals          :   34
      - hanabi             :    2
      - marches            :   27
      - tokyo_cheapo       :   25

🔍 Récupération des événements existants...
   ✓ 161 événements déjà en base

🕷️  Scraping des événements (max_pages=all)...
📄 Detected 5 pages to scrape
  Page 1/5: 24 events
  Page 2/5: 24 events
  ...
   ✓ 120 événements scrapés

🆕 Identification des nouveaux événements...
   ✓ 15 nouveaux événements détectés

📝 Aperçu des nouveaux événements:
   1. Cherry Blossom Night Illumination
      📅 2026/03/20
      📍 Chidorigafuchi
   2. Spring Art Exhibition
      📅 2026/03/15
      📍 Roppongi
   ...

💾 Sauvegarde des nouveaux événements...
   ✓ 15 événements sauvegardés

🧹 Nettoyage des événements passés (>30 jours)...
   ✓ 8 événements supprimés

================================================================================
✅ MISE À JOUR TERMINÉE
================================================================================
   Événements scrapés      : 120
   Nouveaux événements     : 15
   Événements sauvegardés  : 15
   Événements nettoyés     : 8
   Différence totale       : +7
```

## 🔧 Configuration

### Modifier la fréquence de nettoyage

Dans `update_events.py`, ligne ~150 :

```python
cleaned = self.clean_old_events(days_old=30)  # Changer 30 par le nombre de jours souhaité
```

### Modifier le nombre de pages scrapées

```bash
# Scraper seulement 3 pages (rapide, ~72 événements)
PYTHONPATH=. uv run update_events.py --max-pages 3

# Scraper toutes les pages (~120 événements)
PYTHONPATH=. uv run update_events.py
```

## 📈 Performance

- **Scraping complet (5 pages)** : ~60-70 secondes
- **Scraping partiel (3 pages)** : ~40-45 secondes
- **Statistiques uniquement** : < 1 seconde
- **Dry-run** : ~60 secondes (scraping) + 0 (pas de sauvegarde)

## 🛠️ Dépannage

### Erreur "No module named 'src'"

```bash
# Assurez-vous d'utiliser PYTHONPATH=.
PYTHONPATH=. uv run update_events.py
```

### Erreur d'encodage (emojis)

Le script gère automatiquement l'encodage UTF-8 sur Windows.

### Base de données verrouillée

Si la base est utilisée par une autre application :
```bash
# Attendre ou fermer l'autre application
# Ou utiliser --dry-run pour tester sans toucher à la base
PYTHONPATH=. uv run update_events.py --dry-run
```

## 💡 Bonnes pratiques

1. **Tester d'abord avec --dry-run**
   ```bash
   PYTHONPATH=. uv run update_events.py --dry-run
   ```

2. **Vérifier les statistiques avant/après**
   ```bash
   PYTHONPATH=. uv run update_events.py --stats
   ```

3. **Limiter les pages pour les tests**
   ```bash
   PYTHONPATH=. uv run update_events.py --max-pages 2
   ```

4. **Logger les mises à jour**
   ```bash
   PYTHONPATH=. uv run update_events.py > logs/update.log 2>&1
   ```

5. **Automatiser de manière intelligente**
   - 1x par jour suffit (événements ne changent pas si souvent)
   - Préférer la nuit ou tôt le matin (moins de charge serveur)
   - Limiter à 3-5 pages si mise à jour fréquente

## 📝 Notes

- Les événements sont identifiés par leur **nom + date de début**
- Un même événement avec une date différente sera considéré comme nouveau
- Le nettoyage des vieux événements est **optionnel** (--no-clean)
- Les événements sont catégorisés automatiquement (festivals, expositions, marches, tokyo_cheapo)
