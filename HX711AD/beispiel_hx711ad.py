"""
Beispiel fuer NIT Bibliothek: HX711AD
Zeigt: Grundlegendes Auslesen von Rohwert und Gewicht
Hardware: HX711AD mit Waegezelle am ESP32
"""

from nitbw_hx711ad import HX711AD
from time import sleep


# --- Initialisierung ---
# DT an GPIO 19, SCK an GPIO 18
waage = HX711AD(dt_pin=19, sck_pin=18, kanal="A", gain=128)

# Grober Startwert fuer typische 5-kg-Waegezellen (danach sauber kalibrieren)
waage.set_skala(1000.0)

print("=== HX711AD Grundbeispiel ===")
print("Leere Waage... Tara wird gesetzt")
waage.tara(n=20, median=True)
print("Tara abgeschlossen")
print()


# --- Hauptprogramm ---
while True:
    roh = waage.messen_roh()
    wert = waage.messen_wert(n=5, median=True)
    gewicht_g = waage.messen_gewicht(n=5, median=True)

    print("Roh: {:>9d} | Netto: {:>9d} | Gewicht: {:>8.2f} g".format(
        roh, wert, gewicht_g
    ))
    sleep(0.5)
