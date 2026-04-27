"""
Beispiel fuer NIT Bibliothek: KY023
Zeigt: Grundlegende Roh- und Normwerte des Joystick-Moduls
Hardware: KY-023 am ESP32 (VRX, VRY, SW)
"""

from nitbw_ky023 import KY023
import time


# --- Initialisierung ---
# Typische ADC-Pins am ESP32: 32, 33, 34, 35, 36, 39
joystick = KY023(vrx_pin=34, vry_pin=35, sw_pin=32)

print("Kalibriere Mittelstellung, bitte Joystick nicht bewegen...")
cx, cy = joystick.kalibrieren_mitte(samples=100)
print("Mitte X={}, Mitte Y={}".format(cx, cy))
print()

# --- Hauptprogramm ---
print("=== KY-023 Grundbeispiel ===")
print("Ausgabe alle 200 ms")
print()

while True:
    d = joystick.daten()
    print(
        "x_raw={:4d} y_raw={:4d} | x={:+.2f} y={:+.2f} | sw={} | richtung={}".format(
            d["x_raw"],
            d["y_raw"],
            d["x"],
            d["y"],
            "GEDRUECKT" if d["sw"] else "offen",
            d["richtung"],
        )
    )
    time.sleep(0.2)
