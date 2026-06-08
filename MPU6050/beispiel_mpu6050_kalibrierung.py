"""
Beispiel fuer NIT Bibliothek: MPU6050
Zeigt: Gyroskop-Kalibrierung und Drehgeschwindigkeitsmessung
Hardware: MPU6050 (GY-521) am I2C-Bus (Adresse 0x68)

Das Gyroskop hat einen Null-Offset: Im Stillstand gibt es einen kleinen
Wert ungleich Null aus. Die Kalibrierung bestimmt diesen Offset und
zieht ihn bei allen folgenden Messungen automatisch ab.
"""

from machine import I2C, Pin
from nitbw_mpu6050 import MPU6050
from time import sleep_ms


# --- Initialisierung ---

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = MPU6050(i2c)

# --- Gyroskop ohne Kalibrierung ---

print("=== Gyroskop OHNE Kalibrierung ===")
print("Sensor liegt ruhig - Gyroskop sollte idealer Weise 0 deg/s messen:")
for _ in range(5):
    gx, gy, gz = sensor.read_gyro()
    print(f"  GX={gx:+.2f}  GY={gy:+.2f}  GZ={gz:+.2f} deg/s")
    sleep_ms(100)

print()

# --- Kalibrierung durchfuehren ---
# Sensor waehrend der Kalibrierung absolut ruhig halten!
sensor.calibrate_gyro(samples=200)

print()
print("  Gespeicherte Offsets:")
print(f"  X={sensor.gyro_offset_x:.3f}, Y={sensor.gyro_offset_y:.3f}, Z={sensor.gyro_offset_z:.3f} deg/s")

print()

# --- Gyroskop nach Kalibrierung ---

print("=== Gyroskop NACH Kalibrierung ===")
print("Sensor liegt ruhig - Gyroskop sollte jetzt ca. 0 deg/s zeigen:")
for _ in range(5):
    gx, gy, gz = sensor.read_gyro()
    print(f"  GX={gx:+.2f}  GY={gy:+.2f}  GZ={gz:+.2f} deg/s")
    sleep_ms(100)

print()

# --- Gespeicherte Offsets wiederverwenden ---
# Nach einem Neustart koennen die ermittelten Offsets direkt gesetzt werden,
# statt jedes Mal neu zu kalibrieren.
#
# offset_x = sensor.gyro_offset_x
# offset_y = sensor.gyro_offset_y
# offset_z = sensor.gyro_offset_z
# ...
# sensor.set_gyro_offset(offset_x, offset_y, offset_z)

# --- Messung der Drehgeschwindigkeit ---

print("=== Kontinuierliche Messung nach Kalibrierung (Strg+C zum Beenden) ===")
print("Sensor drehen und Werte beobachten:")
while True:
    gx, gy, gz = sensor.read_gyro()
    betrag = (gx**2 + gy**2 + gz**2) ** 0.5
    print(f"GX={gx:+7.2f}  GY={gy:+7.2f}  GZ={gz:+7.2f} deg/s  |Betrag|={betrag:.2f}")
    sleep_ms(100)
