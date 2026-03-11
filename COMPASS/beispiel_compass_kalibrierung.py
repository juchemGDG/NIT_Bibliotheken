"""
Beispiel fuer NIT Bibliothek: COMPASS
Zeigt: Automatische Kalibrierung und kontinuierliche Heading-Ausgabe
Hardware: GY-261 (QMC5883L/HMC5883L) am I2C-Bus
"""

from machine import I2C, Pin
from nitbw_compass import Compass
import time


# --- Initialisierung ---
# I2C initialisieren
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Kompass initialisieren (QMC5883L auf 0x0D)
compass = Compass(i2c, addr=0x0D)

# Kalibrierung durchführen (Sensor während Kalibrierung in alle Richtungen drehen)
print("Kalibrierung wird durchgeführt...")
print("Drehe den Sensor bitte langsam in alle Richtungen!")
compass.auto_calibrate(samples=200)

# Lokale Deklination setzen
compass.set_declination(degrees=3, minutes=45)

# --- Hauptprogramm ---
# Endlosschleife: kontinuierlich Heading anzeigen
print("\n" + "=" * 50)
print("Kompass läuft...")
print("=" * 50 + "\n")

while True:
    heading = compass.read_heading()
    direction = compass.read_heading_direction()
    
    print(f"Heading: {heading:6.1f}°  |  Richtung: {direction}")
    time.sleep(0.5)
