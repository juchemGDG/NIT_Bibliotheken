from machine import I2C, Pin
from compass import Compass

# I2C initialisieren
# Standard für QMC5883L: SCL=22, SDA=21
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Kompass initialisieren (funktioniert mit QMC5883L auf 0x0D)
compass = Compass(i2c, addr=0x0D)

# Lokale Deklination setzen (z.B. 3° 45' für Mitteleuropa)
compass.set_declination(degrees=3, minutes=45)

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
