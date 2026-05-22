"""
Beispiel fuer NIT Bibliothek: Puls
Zeigt: Ausgabe von ADC-Rohwerten und gemittelten Werten
Hardware: Funduino Pulssensor am ESP32 (Signal -> ADC-Pin)
"""

from nitbw_puls import Pulssensor
import time


# --- Initialisierung ---
sensor = Pulssensor(adc_pin=34)

# --- Hauptprogramm ---
print("=== Pulssensor Rohdaten ===")
print("Sensor ruhig auf Fingerkuppe platzieren.")
print()

while True:
    roh = sensor.lesen_roh()
    mittel = sensor.lesen_roh_mittelwert(samples=8, pause_ms=2)

    print("Rohwert: {:4d}   Mittelwert: {:4d}".format(roh, mittel))
    time.sleep(0.1)
