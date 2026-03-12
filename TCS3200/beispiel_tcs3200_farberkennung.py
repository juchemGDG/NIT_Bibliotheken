"""
Beispiel fuer NIT Bibliothek: TCS3200
Zeigt: Einfache Farberkennung fuer Rot, Gruen und Blau
Hardware: TCS3200 oder TCS230 am ESP32
"""

from nitbw_tcs3200 import TCS3200
import time


# --- Initialisierung ---
sensor = TCS3200(out=27, s2=14, s3=12, s0=26, s1=25)
sensor.set_frequenzskalierung(2)


# --- Hauptprogramm ---
while True:
    if sensor.ist_farbe('rot', messungen=10):
        print("Rot erkannt")
    elif sensor.ist_farbe('gruen', messungen=10):
        print("Gruen erkannt")
    elif sensor.ist_farbe('blau', messungen=10):
        print("Blau erkannt")
    else:
        print("Keine eindeutige Grundfarbe erkannt")

    print("Dominante Farbe:", sensor.dominante_farbe(messungen=10))
    time.sleep(0.5)