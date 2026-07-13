"""
Beispiel fuer NIT Bibliothek: GY61
Zeigt: Offset-Kalibrierung in Ruhelage und danach stabile Messung
Hardware: GY-61 (ADXL335) am ESP32 mit 3 ADC-Pins
"""

from nitbw_gy61 import GY61
import time


# --- Initialisierung ---
sensor = GY61(x_pin=34, y_pin=35, z_pin=32)

# --- Hauptprogramm ---
print("=== GY61 Kalibrierung ===")
print("Sensor ruhig mit Z-Achse nach oben auf den Tisch legen...")
time.sleep(2)

offsets = sensor.kalibrieren_ruhelage(samples=300, erwartung_g=(0.0, 0.0, 1.0))
print("Offsets gesetzt (V): X={:.4f}, Y={:.4f}, Z={:.4f}".format(
    offsets[0], offsets[1], offsets[2]))
print()

while True:
    ax, ay, az = sensor.lesen_g()
    print("Kalibriert a[g]: X={:+.3f}, Y={:+.3f}, Z={:+.3f}".format(ax, ay, az))
    time.sleep(0.4)
