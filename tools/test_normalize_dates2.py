import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

from src.scraper_expositions_tokyo import TokyoExpositionScraper

scraper = TokyoExpositionScraper()

test_cases = [
    "1er mars au 6 juillet 2025",
    "du 1er mars au 6 juillet 2025",
    "18 décembre 2024 au 2 mars 2025",
]

for test in test_cases:
    result = scraper._normalize_dates(test)
    print(f'Input: "{test}"')
    print(f'Result: {result}')
    print()
