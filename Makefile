.PHONY: help install test web scrape scrape-festivals scrape-expositions scrape-marches scrape-hanabi scrape-tokyo-cheapo update-all stats clean

help:
	@echo "Commandes disponibles:"
	@echo "  make install          - Installer les dependances"
	@echo "  make test            - Executer les tests"
	@echo "  make web             - Demarrer l'application web"
	@echo "  make scrape          - Scraper tous les evenements du mois en cours"
	@echo "  make scrape-festivals - Scraper festivals (ex: make scrape-festivals MONTH=mars YEAR=2025)"
	@echo "  make scrape-expositions - Scraper expositions"
	@echo "  make scrape-marches  - Scraper marches aux puces"
	@echo "  make scrape-hanabi   - Scraper feux d'artifice"
	@echo "  make scrape-tokyo-cheapo - Scraper Tokyo Cheapo (toutes les pages)"
	@echo ""
	@echo "Mise a jour automatique (recommande):"
	@echo "  make update-all      - Mettre a jour TOUS les scrapers intelligemment"
	@echo "                         (festivals/expos/marches: mois actuel si nouveau)"
	@echo "                         (hanabi: 3 prochains mois)"
	@echo "                         (tokyo cheapo: 5 pages)"
	@echo "  make stats           - Afficher les statistiques de la base de donnees"
	@echo ""
	@echo "  make clean           - Nettoyer les fichiers temporaires"
	@echo ""
	@echo "Note: Les coordonnees GPS sont automatiquement extraites pendant le scraping"

install:
	uv pip install -r requirements.txt

test:
	uv run python -m pytest tests/ -v

web:
	uv run scripts/start_web.py

scrape:
	@MONTH=$$(uv run python scripts/get_current_month.py) && \
	YEAR=$$(uv run python scripts/get_current_year.py) && \
	echo "Scraping du mois en cours: $$MONTH $$YEAR" && \
	echo "" && \
	echo "==> Scraping festivals..." && \
	uv run main.py festivals $$MONTH $$YEAR && \
	echo "" && \
	echo "==> Scraping expositions..." && \
	uv run main.py expositions $$MONTH $$YEAR && \
	echo "" && \
	echo "==> Scraping marches..." && \
	uv run main.py marches && \
	echo "" && \
	echo "==> Scraping hanabi (2 mois)..." && \
	uv run main.py hanabi 2 && \
	echo "" && \
	echo "✓ Scraping termine!"

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

scrape-tokyo-cheapo:
	@echo "Scraping Tokyo Cheapo events (toutes les pages)..."
	PYTHONPATH=. uv run src/scraper_tokyo_cheapo.py

update-all:
	uv run main.py update-all

stats:
	uv run main.py stats

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
