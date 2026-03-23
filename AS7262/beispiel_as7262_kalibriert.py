"""
Beispiel fuer NIT Bibliothek: AS7262
Zeigt: Kalibrierte Float-Werte als Liste ausgeben
Hardware: AS7262 am ESP32 ueber I2C
"""

from nitbw_as7262 import AS7262
from machine import I2C, Pin
import time


# --- Initialisierung ---
# I2C initialisieren
# ESP32 Standard: SCL=22, SDA=21
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

sensor = AS7262(i2c, led=True, integrationszeit=100, gain=2)


# --- Hauptprogramm ---
print("Kanalnamen:", sensor.KANALNAMEN)

while True:
    # Kalibrierte Werte (Float, Einheit: uW/cm2)
    werte = sensor.messen_kalibriert()
    print("Kalibriert:")
    for kanal, wert in werte.items():
        print("  {:>8s}: {:.2f} uW/cm2".format(kanal, wert))

    # Alternativ als Liste (praktisch fuer ML)
    liste = sensor.messen_kalibriert_liste()
    print("Als Liste:", liste)
    print("-" * 30)
    time.sleep(1)
