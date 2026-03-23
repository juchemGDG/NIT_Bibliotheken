"""
Beispiel fuer NIT Bibliothek: DS18B20
Zeigt: Grundlegende Temperaturmessung mit einem Sensor
Hardware: DS18B20 am ESP32 ueber OneWire (Pin 4)
"""

from machine import Pin
from nitbw_ds18b20 import DS18B20
import time


# --- Initialisierung ---
sensor = DS18B20(Pin(4))

# Setze Aufloesung auf 12 Bit (optional)
sensor.set_resolution(12)

# --- Hauptprogramm ---
print("=== DS18B20 Grundbeispiel ===")
print("Messung alle 1 Sekunde")
print()

try:
    while True:
        temperatur = sensor.messen()
        
        if temperatur is not None:
            print("Temperatur: {:6.2f} °C".format(temperatur))
        else:
            print("Fehler beim Auslesen")
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\nProgramm beendet")
