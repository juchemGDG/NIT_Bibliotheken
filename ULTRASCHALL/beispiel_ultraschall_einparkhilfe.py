"""
Beispiel fuer NIT Bibliothek: Ultraschall
Zeigt: Einparkhilfe mit Zonenerkennung und Geschwindigkeit
Hardware: HC-SR04 / HC-SR04P am ESP32
"""

from nitbw_ultraschall import Ultraschall
import time


# --- Initialisierung ---
sensor = Ultraschall(trigger=5, echo=18)

# --- Hauptprogramm ---
print("=== Einparkhilfe ===")
print("Zonen: nah (<15 cm), mittel (<60 cm), fern (>60 cm)")
print()

while True:
    # Entfernung mit Median fuer stabile Werte
    distanz = sensor.messen_median(n=3)
    aktuelle_zone = sensor.zone(nah=15, mittel=60)
    geschw = sensor.geschwindigkeit(intervall_ms=300)

    if distanz > 0:
        # Warnstufe anzeigen
        if aktuelle_zone == 'nah':
            warnung = "!!! STOPP !!!"
        elif aktuelle_zone == 'mittel':
            warnung = ">> Vorsicht"
        else:
            warnung = "   Frei"

        # Richtung der Bewegung
        if geschw > 2:
            bewegung = "naehert sich ({:.0f} cm/s)".format(geschw)
        elif geschw < -2:
            bewegung = "entfernt sich ({:.0f} cm/s)".format(abs(geschw))
        else:
            bewegung = "steht"

        print("{:12s}  {:5.1f} cm  |  {}".format(warnung, distanz, bewegung))
    else:
        print("Kein Objekt erkannt")

    time.sleep(0.3)
