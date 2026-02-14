"""
Script pour obtenir le mois actuel en français.

Usage: python scripts/get_current_month.py
Output: mars (exemple)
"""

from datetime import datetime

MONTHS_FR = {
    1: "janvier",
    2: "février",
    3: "mars",
    4: "avril",
    5: "mai",
    6: "juin",
    7: "juillet",
    8: "août",
    9: "septembre",
    10: "octobre",
    11: "novembre",
    12: "décembre"
}

if __name__ == "__main__":
    now = datetime.now()
    print(MONTHS_FR[now.month])
