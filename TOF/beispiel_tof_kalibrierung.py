"""
Beispiel fuer NIT Bibliothek: TOF
Zeigt: Offset-Kalibrierung mit Referenzstrecke und korrigierte Messwerte
Hardware: VL53L0X oder VL6180X am ESP32
"""

from machine import I2C, Pin
from nitbw_tof import TOF
import time


# --- Initialisierung ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = TOF(i2c)
sensor.set_modus(TOF.GENAU)

# Bekannte Referenzstrecke in mm (von Sensorfront bis Ziel messen)
referenz_mm = 200

# --- Hauptprogramm ---
print("=== TOF Offset-Kalibrierung ===")
print("Referenzstrecke: {} mm".format(referenz_mm))
print("Kalibrierung laeuft...")

offset_mm, basis_mm = sensor.kalibriere_offset(referenz_mm, n=15, methode='median')
print("Basiswert ohne Offset: {} mm".format(basis_mm))
print("Gesetzter Offset:      {} mm".format(offset_mm))
print()
print("Hinweis: Offset bei Neustart erneut setzen (z. B. aus Konstante).")
print()

while True:
    korrigiert = sensor.messen_mm()
    roh = korrigiert - sensor.lese_offset_mm() if korrigiert > 0 else -1

    if korrigiert > 0 and roh > 0:
        print("Roh: {:4d} mm | Korrigiert: {:4d} mm | Offset: {:+d} mm".format(
            roh, korrigiert, sensor.lese_offset_mm()))
    else:
        print("Keine gueltige Messung (Status: {})".format(sensor.status()))

    time.sleep(0.5)
