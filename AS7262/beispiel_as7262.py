"""
Beispiel fuer NIT Bibliothek: AS7262
Zeigt: Rohwerte und kalibrierte Werte aller 6 Spektralkanaele auslesen
Hardware: AS7262 am ESP32 ueber I2C
"""

from nitbw_as7262 import AS7262
from machine import I2C, Pin
import time


# --- Initialisierung ---
# I2C initialisieren
# ESP32 Standard: SCL=22, SDA=21
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Sensor initialisieren
sensor = AS7262(i2c, led=True)


# --- Hauptprogramm ---
while True:
    # Rohwerte lesen (Integer, gut fuer ML)
    roh = sensor.messen_roh()
    print("Rohwerte:")
    for kanal, wert in roh.items():
        print("  {:>8s}: {}".format(kanal, wert))

    # Dominanter Kanal
    print("Staerkster Kanal:", sensor.dominanter_kanal())
    print("Temperatur: {} C".format(sensor.temperatur()))
    print("-" * 30)
    time.sleep(1)
