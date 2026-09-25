"""
Beispiel fuer NIT Bibliothek: BMP280
Zeigt: Grundlegendes Auslesen von Temperatur und Luftdruck
Hardware: BMP280 am I2C-Bus (Adresse 0x76 oder 0x77)
"""

from machine import I2C, Pin
from nitbw_bmp280 import BMP280


# --- Initialisierung ---

# I2C initialisieren
# ESP32 Standard: SCL=22, SDA=21
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Sensor initialisieren
sensor = BMP280(i2c)

# --- Hauptprogramm ---
# Messwerte lesen
temperatur, druck = sensor.read_all()
print(f"Temperatur: {temperatur:.2f} C")
print(f"Luftdruck: {druck:.2f} hPa")

# Hoehe berechnen
hoehe = sensor.calculate_altitude()
print(f"Hoehe: {hoehe:.2f} m")
