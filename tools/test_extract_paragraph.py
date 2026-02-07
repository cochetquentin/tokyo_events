import sys
import io

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

from src.scraper_expositions_tokyo import TokyoExpositionScraper

scraper = TokyoExpositionScraper()

test_text = "Joan Miró Du 1ᵉʳ mars au 6 juillet 2025 Lieu : musée d'art métropolitain de Tokyo Site officiel"

result = scraper._extract_dates_from_paragraph(test_text)
print(f'Input: {test_text}')
print(f'Result: {result}')
