"""
Beispiel fuer NIT Bibliothek: Ultraschall
Zeigt: Grundlegende Entfernungsmessung in cm, mm und Laufzeit
Hardware: HC-SR04 / HC-SR04P am ESP32
"""

from nitbw_ultraschall import Ultraschall
import time


# --- Initialisierung ---
# Trigger an GPIO 5, Echo an GPIO 18
sensor = Ultraschall(trigger=5, echo=18)

# --- Hauptprogramm ---
print("=== Ultraschall Grundbeispiel ===")
print("Messung alle 0.5 Sekunden")
print()

while True:
    # Entfernung in cm
    cm = sensor.messen_cm()
    # Entfernung in mm
    mm = sensor.messen_mm()
    # Rohe Laufzeit in Mikrosekunden
    laufzeit = sensor.messen_laufzeit()

    if cm > 0:
        print("Entfernung: {:.1f} cm  |  {:.0f} mm  |  Laufzeit: {} us".format(
            cm, mm, laufzeit))
    else:
        print("Kein Echo (Objekt zu nah, zu weit oder nicht erkannt)")

    time.sleep(0.5)
