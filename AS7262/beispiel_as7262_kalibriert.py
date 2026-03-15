"""
Beispiel fuer NIT Bibliothek: AS7262
Zeigt: Kalibrierte Float-Werte als Liste ausgeben
Hardware: AS7262 am ESP32 ueber I2C
"""

from nitbw_as7262 import AS7262
import time


# --- Initialisierung ---
sensor = AS7262(sda=21, scl=22, led=True, integrationszeit=100, gain=2)


# --- Hauptprogramm ---
print("Kanalnamen:", sensor.KANALNAMEN)

while True:
    # Kalibrierte Werte (Float, Einheit: uW/cm2)
    werte = sensor.messen_kalibriert()
    print("Kalibriert:")
    for kanal, wert in werte.items():
        print("  {:>8s}: {:.2f} uW/cm2".format(kanal, wert))

    # Alternativ als Liste (praktisch fuer ML)
    liste = sensor.messen_kalibriert_liste()
    print("Als Liste:", liste)
    print("-" * 30)
    time.sleep(1)
