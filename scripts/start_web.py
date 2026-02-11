"""
Script pour démarrer le serveur web.

Usage: uv run scripts/start_web.py [--port 8000]
"""

import argparse
import sys
from pathlib import Path
import uvicorn

# Ajouter le dossier parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000, help="Port du serveur")
    parser.add_argument('--host', default="0.0.0.0", help="Host du serveur")
    args = parser.parse_args()

    uvicorn.run(
        "web.main:app",
        host=args.host,
        port=args.port,
        reload=True
    )
