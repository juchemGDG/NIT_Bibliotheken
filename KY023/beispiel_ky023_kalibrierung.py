"""
Beispiel fuer NIT Bibliothek: KY023
Zeigt: Kalibrierung, Totzone und Winkel/Betrag
Hardware: KY-023 am ESP32 (VRX, VRY, SW)
"""

from nitbw_ky023 import KY023
import time


# --- Initialisierung ---
joystick = KY023(vrx_pin=34, vry_pin=35, sw_pin=32, deadzone=0.10)

# --- Hauptprogramm ---
print("=== KY-023 Kalibrierungsbeispiel ===")
print("1) Joystick loslassen")
print("2) Danach startet automatische Kalibrierung")
print()
time.sleep(2)

cx, cy = joystick.kalibrieren_mitte(samples=150)
print("Kalibrierte Mitte: X={}, Y={}".format(cx, cy))
print("Aktuelle Totzone:", joystick.deadzone)
print("Taste druecken = Totzone umschalten (0.10 <-> 0.20)")
print()

last_button = False

while True:
    d = joystick.daten()
    button = d["sw"]

    if button and not last_button:
        if joystick.deadzone < 0.15:
            joystick.set_deadzone(0.20)
        else:
            joystick.set_deadzone(0.10)
        print("Neue Totzone:", joystick.deadzone)

    print(
        "betrag={:.2f} winkel={:6.1f} grad richtung={:12s} x={:+.2f} y={:+.2f}".format(
            d["betrag"],
            d["winkel"],
            d["richtung"],
            d["x"],
            d["y"],
        )
    )

    last_button = button
    time.sleep(0.2)
