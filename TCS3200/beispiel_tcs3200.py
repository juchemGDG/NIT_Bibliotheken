"""
Beispiel fuer NIT Bibliothek: TCS3200
Zeigt: Rohwerte, Frequenz und dominante Farbe messen
Hardware: TCS3200 oder TCS230 am ESP32
"""

from nitbw_tcs3200 import TCS3200
import time


# --- Initialisierung ---
# OUT=27, S2=14, S3=12, S0=26, S1=25
sensor = TCS3200(out=27, s2=14, s3=12, s0=26, s1=25)

# Fuer stabile Messungen im Unterricht: 2 % Ausgangsfrequenz
sensor.set_frequenzskalierung(2)


# --- Hauptprogramm ---
while True:
    rohwerte = sensor.messen_rohwerte(messungen=8)
    print("Rot:   {:.1f} Hz".format(rohwerte['rot']))
    print("Gruen: {:.1f} Hz".format(rohwerte['gruen']))
    print("Blau:  {:.1f} Hz".format(rohwerte['blau']))
    print("Klar:  {:.1f} Hz".format(rohwerte['klar']))
    print("Periode klar: {:.1f} us".format(
        sensor.messen_periode_us(farbe='klar', messungen=8)))
    print("Dominante Farbe:", sensor.dominante_farbe(messungen=8))
    print("-" * 30)
    time.sleep(1)