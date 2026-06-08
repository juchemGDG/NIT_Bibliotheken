"""
Beispiel fuer NIT Bibliothek: MPU6050
Zeigt: Lagewinkelberechnung - Pitch, Roll und Gesamtneigung aus dem Beschleunigungssensor
Hardware: MPU6050 (GY-521) am I2C-Bus (Adresse 0x68)

Hinweis: Die Winkelberechnung aus dem Beschleunigungssensor ist nur im Stillstand
exakt. Bei Bewegung oder Erschuetterungen treten kurzzeitige Verzerrungen auf.
Fuer eine staendig genaue Winkelmessung bei Bewegung ist ein Komplementaerfilter
(Kombination aus Gyroskop und Beschleunigungssensor) notwendig.
"""

from machine import I2C, Pin
from nitbw_mpu6050 import MPU6050
from time import sleep_ms


# --- Initialisierung ---

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = MPU6050(i2c)

# --- Einzel-Messung ---

pitch, roll = sensor.read_pitch_roll()
neigung = sensor.read_tilt_angle()
lage = sensor.read_orientation_text()

print(f"Pitch:          {pitch:+.1f} deg  (Neigung vorne/hinten)")
print(f"Roll:           {roll:+.1f} deg  (Neigung links/rechts)")
print(f"Gesamtneigung:  {neigung:.1f} deg")
print(f"Lage:           {lage}")
print(f"Waagerecht:     {sensor.is_level()}")

print()

# --- Kontinuierliche Lageausgabe ---

print("--- Kontinuierliche Lageausgabe (Strg+C zum Beenden) ---")
while True:
    pitch, roll = sensor.read_pitch_roll()
    neigung = sensor.read_tilt_angle()
    lage = sensor.read_orientation_text()

    # Einfache Winkelbalken als visuelle Rueckmeldung
    p_balken = int((pitch + 90) / 180 * 20)
    r_balken = int((roll  + 90) / 180 * 20)

    print(
        f"Pitch: {pitch:+6.1f}deg  Roll: {roll:+6.1f}deg  "
        f"Neigung: {neigung:5.1f}deg  [{lage}]"
    )
    sleep_ms(100)
