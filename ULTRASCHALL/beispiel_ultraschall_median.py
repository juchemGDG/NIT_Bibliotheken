"""
Beispiel fuer NIT Bibliothek: Ultraschall
Zeigt: Vergleich von Mittelwert, Median und Streuung
Hardware: HC-SR04 / HC-SR04P am ESP32
"""

from nitbw_ultraschall import Ultraschall
import time


# --- Initialisierung ---
sensor = Ultraschall(trigger=5, echo=18)

# --- Hauptprogramm ---
print("=== Mittelwert vs. Median ===")
print("Jeweils 7 Messungen pro Durchlauf")
print()

while True:
    mittelwert = sensor.messen_mittelwert(n=7)
    median = sensor.messen_median(n=7)
    minimum, maximum, durchschnitt = sensor.messen_bereich(n=7)

    print("Mittelwert: {:6.1f} cm".format(mittelwert))
    print("Median:     {:6.1f} cm".format(median))
    print("Bereich:    {:6.1f} - {:.1f} cm (Streuung: {:.1f} cm)".format(
        minimum, maximum, maximum - minimum))
    print("-" * 40)

    time.sleep(1)
