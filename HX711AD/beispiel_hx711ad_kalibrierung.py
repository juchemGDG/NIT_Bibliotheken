"""
Beispiel fuer NIT Bibliothek: HX711AD
Zeigt: Kalibrierung mit bekanntem Referenzgewicht
Hardware: HX711AD mit Waegezelle am ESP32
"""

from nitbw_hx711ad import HX711AD
from time import sleep


# --- Initialisierung ---
waage = HX711AD(dt_pin=19, sck_pin=18)


# --- Hauptprogramm ---
print("=== HX711AD Kalibrierung ===")
print("Schritt 1: Waage leeren (keine Last)")
sleep(2)

waage.tara(n=30, median=True)
print("Tara abgeschlossen")
print()

print("Schritt 2: Lege jetzt ein bekanntes Gewicht auf")
print("Beispiel: 1000 g")
sleep(5)

referenz_gewicht = 1000.0
skala = waage.kalibrieren(referenz_gewicht=referenz_gewicht, n=30, median=True)
print("Neuer Kalibrierfaktor:", skala)
print()

print("Schritt 3: Laufende Messung mit neuer Kalibrierung")
while True:
    gewicht = waage.messen_gewicht(n=7, median=True)
    print("Gewicht: {:8.2f} g".format(gewicht))
    sleep(0.5)
