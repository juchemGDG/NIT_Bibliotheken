"""
Beispiel fuer NIT Bibliothek: TOF
Zeigt: Vergleich der vier Messmodi (Schnell, Standard, Genau, Langstrecke)
Hardware: VL53L0X (GY-530) am ESP32
"""

from machine import I2C, Pin
from nitbw_tof import TOF
import time


# --- Initialisierung ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = TOF(i2c)

# --- Hauptprogramm ---
print("=== Vergleich der Messmodi ===")
print("Jeder Modus wird 5x gemessen, Streuung wird angezeigt.")
print()

modi = [
    (TOF.SCHNELL,      "SCHNELL      (20 ms)"),
    (TOF.STANDARD,     "STANDARD     (33 ms)"),
    (TOF.GENAU,        "GENAU       (200 ms)"),
    (TOF.LANGSTRECKE,  "LANGSTRECKE  (33 ms)"),
]

while True:
    for modus, name in modi:
        sensor.set_modus(modus)

        # 5 Einzelmessungen fuer Streuungsanalyse
        minimum, maximum, mittel = sensor.messen_bereich(n=5)

        if minimum > 0:
            streuung = maximum - minimum
            print("{}: Mittel {:4d} mm  |  Streuung {:3d} mm  ({} - {})".format(
                name, mittel, streuung, minimum, maximum))
        else:
            print("{}: Kein Objekt erkannt".format(name))

    print("-" * 65)
    time.sleep(2)
