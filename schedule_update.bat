@echo off
REM Script Windows pour mettre à jour automatiquement les événements Tokyo Cheapo
REM À utiliser avec le Planificateur de tâches Windows

cd /d "%~dp0"

echo ========================================
echo Tokyo Events - Mise a jour automatique
echo %date% %time%
echo ========================================

REM Activer l'environnement virtuel et lancer la mise à jour
call .venv\Scripts\activate.bat
python update_events.py --max-pages 5

REM Log le résultat
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Mise a jour terminee avec succes
) else (
    echo [ERROR] Erreur lors de la mise a jour
)

echo ========================================
