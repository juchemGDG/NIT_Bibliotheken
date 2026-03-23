"""
Beispiel fuer NIT Bibliothek: KY023
Zeigt: Richtungsdetektion (8-Wege) und Taster-Ereignisse
Hardware: KY-023 am ESP32 (VRX, VRY, SW)
"""

from nitbw_ky023 import KY023
import time


# --- Initialisierung ---
joystick = KY023(vrx_pin=34, vry_pin=35, sw_pin=32, deadzone=0.18)
joystick.kalibrieren_mitte(samples=120)

last_direction = None
last_button = False

# --- Hauptprogramm ---
print("=== KY-023 Richtungsbeispiel ===")
print("Bewege den Stick in die Richtungen, Taste zum Test druecken")
print()

while True:
    direction = joystick.richtung()
    button = joystick.gedrueckt()

    if direction != last_direction:
        print("Richtung:", direction)
        last_direction = direction

    if button and not last_button:
        print("Taster: GEDRUECKT")
    elif (not button) and last_button:
        print("Taster: LOSGELASSEN")

    last_button = button
    time.sleep(0.05)
