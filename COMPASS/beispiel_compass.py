"""
Beispiel fuer NIT Bibliothek: COMPASS
Zeigt: Richtungs- und Magnetfeldmessung mit GY-261
Hardware: GY-261 (QMC5883L/HMC5883L) am I2C-Bus
"""

from machine import I2C, Pin
from nitbw_compass import Compass


# --- Initialisierung ---

# I2C initialisieren
# Standard für QMC5883L: SCL=22, SDA=21
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Kompass initialisieren (funktioniert mit QMC5883L auf 0x0D)
compass = Compass(i2c, addr=0x0D)

# Lokale Deklination setzen (z.B. 3° 45' für Mitteleuropa)
compass.set_declination(degrees=3, minutes=45)

# --- Hauptprogramm ---
# Kompassrichtung auslesen
heading = compass.read_heading()
print(f"Kompassrichtung: {heading:.1f}°")

# Himmelsrichtung auslesen
direction = compass.read_heading_direction()
print(f"Richtung: {direction}")

# Magnetfeldstärke auslesen
x, y, z = compass.read_field()
print(f"Magnetfeld: X={x:.2f} mG, Y={y:.2f} mG, Z={z:.2f} mG")

# Gesamtfeldstärke
strength = compass.read_strength()
print(f"Feldstärke: {strength:.2f} mG")
