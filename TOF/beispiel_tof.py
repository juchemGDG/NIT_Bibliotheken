"""
Beispiel fuer NIT Bibliothek: TOF
Zeigt: Grundlegende Entfernungsmessung in mm und cm
Hardware: VL53L0X (GY-530) am ESP32
"""

from machine import I2C, Pin
from nitbw_tof import TOF
import time


# --- Initialisierung ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = TOF(i2c)

# --- Hauptprogramm ---
print("=== VL53L0X Grundbeispiel ===")
print("Messung alle 0.5 Sekunden")
print()

while True:
    mm = sensor.messen_mm()
    cm = sensor.messen_cm()
    laufzeit = sensor.messen_laufzeit()

    if mm > 0:
        print("Entfernung: {:4d} mm  |  {:5.1f} cm  |  Laufzeit: {:d} ns  |  Status: {}".format(
            mm, cm, laufzeit, sensor.status()))
    else:
        print("Kein Objekt erkannt (Status: {})".format(sensor.status()))

    time.sleep(0.5)
