"""
Beispiel fuer NIT Bibliothek: HX711AD
Zeigt: Tara-Funktion und stabile Messung mit Median
Hardware: HX711AD mit Waegezelle am ESP32
"""

from nitbw_hx711ad import HX711AD
from time import sleep


# --- Initialisierung ---
waage = HX711AD(dt_pin=19, sck_pin=18)
waage.set_skala(1000.0)


# --- Hauptprogramm ---
print("=== Tara-Beispiel ===")
print("1) Waage leeren und ruhig halten")
print("2) Tara startet in 2 Sekunden")
sleep(2)

offset = waage.tara(n=30, median=True)
print("Offset gesetzt:", offset)
print()

while True:
    gewicht = waage.messen_gewicht(n=7, median=True)
    print("Aktuelles Gewicht: {:7.2f} g".format(gewicht))
    sleep(0.3)
