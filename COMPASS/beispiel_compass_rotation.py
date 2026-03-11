"""
Beispiel fuer NIT Bibliothek: COMPASS
Zeigt: Drehwinkelberechnung relativ zu einer Startrichtung
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

# Lokale Deklination setzen
compass.set_declination(degrees=3, minutes=45)

# --- Hauptprogramm ---
print("Drehwinkelmessung - Drehe den Sensor!")
print("=" * 50)
print("Die Messung startet in 3 Sekunden...")
time.sleep(3)

# Start-Richtung aufnehmen
start_heading = compass.read_heading()
print(f"\nStart-Richtung: {start_heading:.1f}°")
print("\nJetzt drehe den Sensor...")
print("(Messung alle 0.5 Sekunden)")
print("-" * 50)

while True:
    time.sleep(0.5)
    
    # Aktuelle Richtung auslesen
    current_heading = compass.read_heading()
    
    # Drehwinkel berechnen
    rotation = compass.calculate_rotation(start_heading, current_heading)
    direction = compass.get_rotation_direction(start_heading, current_heading)
    
    # Ausgabe
    print(f"Aktuell: {current_heading:6.1f}°  |  ", end="")
    print(f"Drehung: {rotation:+7.1f}°  |  ", end="")
    print(f"Richtung: {direction}")
    
    # Optional: Mit Taste 'r' neue Startrichtung setzen
    # (funktioniert in REPL mit input(), hier nur zur Demo)
