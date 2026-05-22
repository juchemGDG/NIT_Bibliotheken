"""
Beispiel fuer NIT Bibliothek: Puls
Zeigt: Herzfrequenzmessung in BPM ueber Zeitfenster
Hardware: Funduino Pulssensor am ESP32 (Signal -> ADC-Pin)
"""

from nitbw_puls import Pulssensor
import time


# --- Initialisierung ---
sensor = Pulssensor(adc_pin=34)

# --- Hauptprogramm ---
print("=== Pulssensor BPM-Messung ===")
print("Finger ruhig auf den Sensor legen.")
print("Messfenster: 10 Sekunden")
print()

while True:
    bpm = sensor.messen_puls(dauer_s=10)

    if bpm > 0:
        print("Herzfrequenz: {:.1f} BPM".format(bpm))
    else:
        print("Kein stabiler Puls erkannt. Fingerposition pruefen.")

    time.sleep(1)
