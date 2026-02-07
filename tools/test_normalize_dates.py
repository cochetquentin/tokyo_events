import sys
sys.path.insert(0, '.')

from src.scraper_expositions_tokyo import TokyoExpositionScraper

scraper = TokyoExpositionScraper()

test_cases = [
    "DU 1er MARS AU 6 JUILLET 2025",
    "JUSQU'AU 23 MARS 2025",
    "JUSQU'AU 26 MARS 2025",
    "JUSQU'AU 6 JUIN 2025"
]

for test in test_cases:
    result = scraper._normalize_dates(test)
    print(f'Input: {test}')
    print(f'Result: {result}')
    print()
