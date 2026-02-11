.PHONY: help install test web populate-gps scrape-festivals scrape-expositions scrape-marches scrape-hanabi clean

help:
	@echo "Commandes disponibles:"
	@echo "  make install          - Installer les dependances"
	@echo "  make test            - Executer les tests"
	@echo "  make web             - Demarrer l'application web"
	@echo "  make populate-gps    - Peupler les coordonnees GPS"
	@echo "  make scrape-festivals - Scraper festivals (ex: make scrape-festivals MONTH=mars YEAR=2025)"
	@echo "  make scrape-expositions - Scraper expositions"
	@echo "  make scrape-marches  - Scraper marches aux puces"
	@echo "  make scrape-hanabi   - Scraper feux d'artifice"
	@echo "  make clean           - Nettoyer les fichiers temporaires"

install:
	uv pip install -r requirements.txt

test:
	uv run python -m pytest tests/ -v

web:
	uv run scripts/start_web.py

populate-gps:
	uv run scripts/populate_gps_coordinates.py

scrape-festivals:
	@if [ -z "$(MONTH)" ] || [ -z "$(YEAR)" ]; then \
		echo "Usage: make scrape-festivals MONTH=mars YEAR=2025"; \
		exit 1; \
	fi
	uv run main.py festivals $(MONTH) $(YEAR)

scrape-expositions:
	@if [ -z "$(MONTH)" ] || [ -z "$(YEAR)" ]; then \
		echo "Usage: make scrape-expositions MONTH=avril YEAR=2025"; \
		exit 1; \
	fi
	uv run main.py expositions $(MONTH) $(YEAR)

scrape-marches:
	uv run main.py marches

scrape-hanabi:
	uv run main.py hanabi $(MONTHS)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
