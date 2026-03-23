"""
Beispiel fuer NIT Bibliothek: DS18B20
Zeigt: Alarm-Schwellwerte (TH / TL) und Aufloesung aendern
Hardware: DS18B20 am ESP32 ueber OneWire (Pin 4)
"""

from machine import Pin
from nitbw_ds18b20 import DS18B20
import time


# --- Initialisierung ---
sensor = DS18B20(Pin(4))

# --- Hauptprogramm ---
print("=== DS18B20 Alarm und Aufloesung ===")
print()

# Setze Alarm-Schwellwerte: Warnung bei 25°C, Fehler bei 30°C
print("Schreibe Konfiguration...")
print("  Alarm High (TH): 30 °C")
print("  Alarm Low  (TL): 10 °C")
print("  Aufloesung: 12 Bit")
success = sensor.write_scratchpad(th=30, tl=10, resolution=12)
if success:
    print("Konfiguration erfolgreich")
else:
    print("Fehler beim Schreiben der Konfiguration")

print()
print("Starte Messung mit verschiedenen Aufloesungen...")
print()

try:
    for resolution in [9, 10, 11, 12]:
        sensor.set_resolution(resolution)
        print("--- Aufloesung: {} Bit ---".format(resolution))
        
        for messung in range(3):
            temperatur = sensor.messen()
            
            if temperatur is not None:
                print("  {:6.3f} °C".format(temperatur))
            else:
                print("  Fehler beim Auslesen")
            
            time.sleep(0.5)
        
        print()

except KeyboardInterrupt:
    print("\nProgramm beendet")
