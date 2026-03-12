"""
Beispiel fuer NIT Bibliothek: TCS3200
Zeigt: RGB-Werte, Hex-Farbe und Helligkeit mit Kalibrierung
Hardware: TCS3200 oder TCS230 am ESP32
"""

from nitbw_tcs3200 import TCS3200
import time


# --- Initialisierung ---
sensor = TCS3200(out=27, s2=14, s3=12, s0=26, s1=25)
sensor.set_frequenzskalierung(2)


# --- Hauptprogramm ---
print("Lege jetzt eine weisse Flaeche unter den Sensor.")
time.sleep(3)
weiss = sensor.kalibrieren_weiss(messungen=20)
print("Weiss gespeichert:", weiss)

print("Lege jetzt eine schwarze Flaeche unter den Sensor.")
time.sleep(3)
schwarz = sensor.kalibrieren_schwarz(messungen=20)
print("Schwarz gespeichert:", schwarz)

while True:
    rot, gruen, blau = sensor.messen_rgb(messungen=10)
    print("RGB:", (rot, gruen, blau))
    print("Hex:", sensor.messen_hex(messungen=10))
    print("Helligkeit: {:.1f} %".format(sensor.messen_helligkeit(messungen=10)))
    print("-" * 30)
    time.sleep(1)