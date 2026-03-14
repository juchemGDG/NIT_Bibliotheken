"""
Beispiel fuer NIT Bibliothek: AS7262
Zeigt: Rohwerte und kalibrierte Werte aller 6 Spektralkanaele auslesen
Hardware: AS7262 am ESP32 ueber I2C
"""

from nitbw_as7262 import AS7262
import time


# --- Initialisierung ---
# Sensor auf Standard-Pins (SDA=21, SCL=22), LED eingeschaltet
sensor = AS7262(sda=21, scl=22, led=True)


# --- Hauptprogramm ---
while True:
    # Rohwerte lesen (Integer, gut fuer ML)
    roh = sensor.messen_roh()
    print("Rohwerte:")
    for kanal, wert in roh.items():
        print("  {:>8s}: {}".format(kanal, wert))

    # Dominanter Kanal
    print("Staerkster Kanal:", sensor.dominanter_kanal())
    print("Temperatur: {} C".format(sensor.temperatur()))
    print("-" * 30)
    time.sleep(1)
