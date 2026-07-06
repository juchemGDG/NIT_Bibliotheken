"""
Beispiel fuer NIT Bibliothek: TOF
Zeigt: Kurzdistanz-Messung mit VL6180X inkl. Zonen-Logik
Hardware: VL6180X am ESP32
"""

from machine import I2C, Pin
from nitbw_tof import TOF
import time


# --- Initialisierung ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# sensor_typ explizit setzen, damit im Unterricht klar ist,
# welcher Sensor verwendet wird.
sensor = TOF(i2c, sensor_typ='vl6180x')
sensor.set_modus(TOF.STANDARD)

# --- Hauptprogramm ---
print("=== VL6180X Kurzdistanz-Beispiel ===")
print("Erkannter Sensor:", sensor.lese_sensor_typ())
print("Messbereich typischerweise bis ca. 200 mm")
print()

while True:
    mm = sensor.messen_mm()

    if mm > 0:
        cm = sensor.messen_cm()
        zone = sensor.zone(nah=50, mittel=120)
        print("Distanz: {:3d} mm | {:4.1f} cm | Zone: {:>6s} | Status: {}".format(
            mm, cm, zone, sensor.status()))
    else:
        print("Keine gueltige Messung (Status: {})".format(sensor.status()))

    time.sleep(0.2)
