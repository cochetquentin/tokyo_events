"""
Script pour obtenir l'année actuelle.

Usage: python scripts/get_current_year.py
Output: 2025 (exemple)
"""

from datetime import datetime

if __name__ == "__main__":
    print(datetime.now().year)
