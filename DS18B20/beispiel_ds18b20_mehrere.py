"""
Beispiel fuer NIT Bibliothek: DS18B20
Zeigt: Mehrere Sensoren am selben OneWire Bus
Hardware: Mehrere DS18B20 in Serie am ESP32 ueber OneWire (Pin 4)
"""

from machine import Pin
from nitbw_ds18b20 import DS18B20
import time


# --- Initialisierung ---
sensor = DS18B20(Pin(4))

# Suche alle Sensoren am Bus
print("Suche DS18B20 Sensoren...")
roms = sensor.search_roms()
print("Gefunden: {} Sensor(en)".format(len(roms)))

for i, rom in enumerate(roms):
    rom_str = sensor.rom_to_string(rom)
    print("  Sensor {}: {}".format(i+1, rom_str))

print()

if not roms:
    print("Keine Sensoren gefunden! Pruefe Verkabelung.")
    import sys
    sys.exit(1)

# --- Hauptprogramm ---
print("=== DS18B20 Mehrere Sensoren ===")
print("Messung alle 2 Sekunden")
print()

try:
    while True:
        # Starte Konvertierung an ALLEN Sensoren gleichzeitig
        sensor.convert_temperature()
        
        # Warte auf Konvertierung
        time.sleep(1)
        
        # Lese Temparaturen einzeln aus
        for i, rom in enumerate(roms):
            temperatur = sensor.read_temperature(rom)
            rom_str = sensor.rom_to_string(rom)
            
            if temperatur is not None:
                print("Sensor {}: {:7.2f} °C ({})".format(i+1, temperatur, rom_str[:8]))
            else:
                print("Sensor {}: Fehler".format(i+1))
        
        print()
        time.sleep(1)

except KeyboardInterrupt:
    print("\nProgramm beendet")
