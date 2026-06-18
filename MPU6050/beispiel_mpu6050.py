"""
Beispiel fuer NIT Bibliothek: MPU6050
Zeigt: Grundlegendes Auslesen von Beschleunigung, Winkelgeschwindigkeit und Temperatur
Hardware: MPU6050 (GY-521) am I2C-Bus (Adresse 0x68)
"""

from machine import I2C, Pin
from nitbw_mpu6050 import MPU6050
from time import sleep_ms


# --- Initialisierung ---

# I2C initialisieren
# ESP32 Standard: SCL=22, SDA=21
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Sensor initialisieren
sensor = MPU6050(i2c)

# --- Hauptprogramm ---

# Alle Messwerte in einem Aufruf lesen
daten = sensor.read_all()
print("--- Alle Messwerte ---")
print(f"Beschleunigung: X={daten['ax']:.3f} g, Y={daten['ay']:.3f} g, Z={daten['az']:.3f} g")
print(f"Gyroskop:       X={daten['gx']:.2f} deg/s, Y={daten['gy']:.2f} deg/s, Z={daten['gz']:.2f} deg/s")
print(f"Temperatur:     {daten['temp']:.2f} C")

print()

# Kontinuierliche Messung
print("--- Kontinuierliche Messung (Strg+C zum Beenden) ---")
while True:
    d = sensor.read_all()
    print(
        f"a: ({d['ax']:+.2f}, {d['ay']:+.2f}, {d['az']:+.2f}) g  "
        f"g: ({d['gx']:+6.1f}, {d['gy']:+6.1f}, {d['gz']:+6.1f}) deg/s  "
        f"T: {d['temp']:.1f} C"
    )
    sleep_ms(200)
