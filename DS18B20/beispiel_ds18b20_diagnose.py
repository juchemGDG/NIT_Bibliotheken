"""
Beispiel fuer NIT Bibliothek: DS18B20
Zeigt: Diagnose von OneWire-Presence, ROM-Suche und Scratchpad-CRC
Hardware: DS18B20 am ESP32 ueber OneWire (Pin 4)
"""

from machine import Pin
from nitbw_ds18b20 import DS18B20
import time


# --- Initialisierung ---
sensor = DS18B20(Pin(4))

# --- Hauptprogramm ---
print("=== DS18B20 Diagnose ===")
print("Pruefe Presence-Puls, ROM-Liste und Scratchpad")
print()

if not sensor.sensor_vorhanden():
    print("Kein Presence-Puls erkannt!")
    print("Pruefe:")
    print("  1) Datenleitung auf GPIO4")
    print("  2) Gemeinsame Masse (GND)")
    print("  3) Pull-up Widerstand 4.7 kOhm zwischen DQ und 3.3V")
    raise SystemExit

print("Presence-Puls erkannt.")
roms = sensor.search_roms()
print("Gefundene Sensoren: {}".format(len(roms)))

for i, rom in enumerate(roms):
    print("  Sensor {} ROM: {}".format(i + 1, sensor.rom_to_string(rom)))

if not roms:
    print("Hinweis: Einzelsensor ohne stabile ROM-Suche -> trotzdem SKIP-ROM-Messung testen")
    temp = sensor.messen()
    print("SKIP-ROM-Messung: {}".format(temp))
    raise SystemExit

print()
print("Lese Rohdaten und CRC...")

while True:
    for i, rom in enumerate(roms):
        sensor.convert_temperature(rom)
        time.sleep(0.8)

        data = sensor.read_scratchpad(rom)
        if data is None:
            print("Sensor {}: Scratchpad-Lesen fehlgeschlagen".format(i + 1))
            continue

        crc_ok = sensor._crc8(data[:8]) == data[8]
        temp = sensor.read_temperature(rom)
        print(
            "Sensor {}: CRC={} Scratchpad={} Temp={}".format(
                i + 1,
                "OK" if crc_ok else "FEHLER",
                " ".join("{:02X}".format(b) for b in data),
                "{:.2f} C".format(temp) if temp is not None else "None",
            )
        )

    print()
    time.sleep(1)
