"""
Beispiel fuer NIT Bibliothek: GY61
Zeigt: Grundmessung in g, m/s^2 und Neigungswinkeln
Hardware: GY-61 (ADXL335) am ESP32 mit 3 ADC-Pins
"""

from nitbw_gy61 import GY61
import time


# --- Initialisierung ---
# XOUT -> GPIO34, YOUT -> GPIO35, ZOUT -> GPIO32
sensor = GY61(x_pin=34, y_pin=35, z_pin=32)

# --- Hauptprogramm ---
print("=== GY61 Grundbeispiel ===")
print("Messung alle 0.5 Sekunden")
print()

while True:
    ax, ay, az = sensor.lesen_g()
    mx, my, mz = sensor.lesen_ms2()
    pitch, roll = sensor.neigung_grad()

    print("a[g]   X:{:+.2f}  Y:{:+.2f}  Z:{:+.2f}".format(ax, ay, az))
    print("a[m/s^2] X:{:+.2f}  Y:{:+.2f}  Z:{:+.2f}".format(mx, my, mz))
    print("Neigung  Pitch:{:+.1f} deg  Roll:{:+.1f} deg".format(pitch, roll))
    print("Betrag: {:.2f} g".format(sensor.betrag_g()))
    print("-" * 56)

    time.sleep(0.5)
