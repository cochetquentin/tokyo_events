"""
Test d'intégration de la déduplication avec de vrais événements
"""
from src.database import EventDatabase
from src.deduplicator import EventDeduplicator

# Événements de test simulant différents scrapers
hanabi_events = [
    {
        'name': 'Sumida River Fireworks',
        'start_date': '2025/07/26',
        'end_date': '2025/07/26',
        'prefecture': '東京都',
        'city': '墨田区',
        'venue': 'Sumida River'
    }
]

tokyo_cheapo_events = [
    {
        'name': 'Sumida River Fireworks',  # Nom identique (normalisé)
        'start_date': '2025/07/26',
        'end_date': '2025/07/26',
        'location': 'Sumida-ku Tokyo',  # Location proche
        'hours': '19:00-20:30',  # Info supplémentaire
        'fee': 'Free'  # Info supplémentaire
    }
]

festivals_events = [
    {
        'name': 'Summer Festival',
        'start_date': '2025/08/01',
        'end_date': '2025/08/05',
        'location': 'Shibuya-ku'
    },
    {
        'name': 'Summer Festival Tokyo',  # Doublon intra-scraper
        'start_date': '2025/08/01',
        'end_date': '2025/08/05',
        'location': 'Shibuya-ku',
        'hours': '10:00-18:00'
    }
]

print("=" * 80)
print("TEST D'INTEGRATION : DEDUPLICATION D'EVENEMENTS")
print("=" * 80)

# Créer DB en mémoire
db = EventDatabase(':memory:')

# 1. Insérer hanabi (priorité 1)
print("\n1. Insertion hanabi (priorité 1)")
print("-" * 80)
saved = db.insert_events(hanabi_events, 'hanabi')
print(f"Résultat : {saved} événements sauvegardés")
total = db.count_events()
print(f"Total DB : {total} événements")

# 2. Insérer festivals (priorité 2) - devrait détecter doublon intra
print("\n2. Insertion festivals (priorité 2)")
print("-" * 80)
saved = db.insert_events(festivals_events, 'festivals')
print(f"Résultat : {saved} événements sauvegardés")
total = db.count_events()
print(f"Total DB : {total} événements")

# 3. Insérer tokyo_cheapo (priorité 5) - devrait enrichir hanabi existant
print("\n3. Insertion tokyo_cheapo (priorité 5)")
print("-" * 80)
saved = db.insert_events(tokyo_cheapo_events, 'tokyo_cheapo')
print(f"Résultat : {saved} événements sauvegardés")
total = db.count_events()
print(f"Total DB : {total} événements")

# 4. Vérifier l'enrichissement
print("\n4. Vérification de l'enrichissement")
print("-" * 80)
events = db.get_events(event_type='hanabi')
if events:
    event = events[0]
    print(f"Nom : {event['name']}")
    print(f"Hours : {event.get('hours', 'N/A')}")
    print(f"Fee : {event.get('fee', 'N/A')}")

    if event.get('hours') and event.get('fee'):
        print("\n[OK] SUCCES : L'evenement hanabi a ete enrichi avec hours et fee de tokyo_cheapo!")
    else:
        print("\n[FAIL] ECHEC : L'enrichissement n'a pas fonctionne")

# 5. Statistiques finales
print("\n5. Statistiques finales")
print("-" * 80)
stats = db.get_events()
for event in stats:
    print(f"- {event['event_type']:15s} | {event['name'][:50]}")

print("\n" + "=" * 80)
print("[OK] TEST D'INTEGRATION TERMINE")
print("=" * 80)
