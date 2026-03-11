"""
Beispiel fuer NIT Bibliothek: BME280
Zeigt: Grundlegendes Auslesen von Temperatur, Luftdruck und Feuchte
Hardware: BME280 am I2C-Bus (Adresse 0x76 oder 0x77)
"""

from machine import I2C, Pin
from nitbw_bme280 import BME280


# --- Initialisierung ---

# I2C initialisieren
# ESP32 Standard: SCL=22, SDA=21
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Sensor initialisieren
sensor = BME280(i2c)

# --- Hauptprogramm ---
# Messwerte lesen
temperatur, druck, feuchtigkeit = sensor.read_all()
print(f"Temperatur: {temperatur:.2f} C")
print(f"Luftdruck: {druck:.2f} hPa")
print(f"Feuchtigkeit: {feuchtigkeit:.2f}%")

# Hoehe berechnen
hoehe = sensor.calculate_altitude()
print(f"Hoehe: {hoehe:.2f} m")
