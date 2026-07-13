"""
Beispiel fuer NIT Bibliothek: GY61
Zeigt: Einfache Bewegungsdetektion ueber Beschleunigungsbetrag
Hardware: GY-61 (ADXL335) am ESP32 mit 3 ADC-Pins
"""

from nitbw_gy61 import GY61
import time


# --- Initialisierung ---
sensor = GY61(x_pin=34, y_pin=35, z_pin=32)

# --- Hauptprogramm ---
print("=== GY61 Bewegungsdetektion ===")
print("Ruhe -> 'stabil', Bewegung/Schock -> 'bewegt'")
print()

while True:
    betrag = sensor.betrag_g()
    bewegt = sensor.ist_bewegt(schwelle_g=0.2)

    if bewegt:
        print("BEWEGT  | Betrag: {:.2f} g".format(betrag))
    else:
        print("stabil  | Betrag: {:.2f} g".format(betrag))

    time.sleep(0.2)
