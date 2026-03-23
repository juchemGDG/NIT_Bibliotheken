# NIT Bibliothek: DS18B20 (OneWire Temperatursensor)

## Beschreibung

Diese Bibliothek ermoeglicht die Temperaturmessung mit dem DS18B20
OneWire Temperatorsensor am ESP32. Der Sensor misst Temperaturen
im Bereich von -55 °C bis +125 °C mit programmierbarer Aufloesung
(9 bis 12 Bit). Die Bibliothek unterstuetzt Einzelsensoren ebenso
wie mehrere Sensoren am selben OneWire Bus, inklusive ROM-Suche,
Alarm-Schwellwerte und CRC8-Integritaetspruefung.

## Features

**Temperaturmessung:**

- Bereich: -55 °C bis +125 °C
- Aufloesung: 9, 10, 11 oder 12 Bit programmierbar (0.5 °C bis 0.0625 °C)
- Genauigkeit: ±0.5 °C im Bereich -10 °C bis +85 °C
- Messdauer: 94 ms (9 Bit) bis 750 ms (12 Bit)

**OneWire Bus:**

- Single-Wire Kommunikation mit Pull-up Widerstand (4.7 kOhm)
- ROM-Suche zur automatischen Erkennung aller angeschlossenen Sensoren
- Mehrere Sensoren am selben Pin ohne Adressierungskonflikte
- CRC8-Pruefung fuer Datensicherheit (Manchester-kodiert)

**Sensor-Konfiguration:**

- **ROM-Befehle**: SKIP ROM (einzelner Sensor) oder MATCH ROM (Multiple)
- **Aufloesung einstellen**: 9, 10, 11 oder 12 Bit
- **Alarm-Schwellwerte**: TH (Alarm High) und TL (Alarm Low) setzen
- **Parasitaere Stromversorgung**: Unterstuetzt (ohne externe Stromversorgung)

**Fehlerbehandlung:**

- CRC8-Ueberpruefung gegen Uebertragungsfehler
- Timeout-Behandlung bei Sensorstoerung
- Automatische Erkennung bei Sensor-Abzug

## Hardware

### DS18B20 Varianten

| Variante | Form | Bemerkung |
|----------|------|-----------|
| DS18B20 | DIP-8 | Standard, guentig, hoechste Kompatibilitaet |
| DS18B20Z | SMD | Surface-mounted Variante |
| DS18B20U | Ultra-kompakt | Micro-Bauform |
| DS18S20 | DIP-8 | Aelteres Modell (nur 9 Bit fix) |

### Pinbelegung (DIP-8)

```
       ___
     /   \
    | 1 8 |  1: GND (schwarz)
    | 2 7 |  2: DQ (gelb/orange) <- OneWire
    | 3 6 |  3: GND (schwarz)
    | 4 5 |  4: GND (schwarz)
      | |     5: GND (schwarz)
    |_______|  6: (nicht belegt)
               7: (nicht belegt)
               8: VDD (rot, +5V oder +3.3V)
               
Vereinfacht: GND zu GND, DQ zu Pin 4, VDD zu +3.3V
```

### Anschlussbeispiele

**Einzeln (Normal-Betrieb, mit externer Stromversorgung):**

```
ESP32 Pin 4 (GPIO4) --- [4.7 kOhm] --- +3.3V (Pull-up)
                    |
                DS18B20 DQ
                    |
ESP32 GND --------- DS18B20 GND
ESP32 +3.3V ------ DS18B20 VDD (optional fuer Parasit-Modus)
```

**Mehrere Sensoren (am selben Bus, Parallel):**

```
ESP32 Pin 4 ----+--- [4.7 kOhm] --- +3.3V
                |
              DS1 DQ
              DS2 DQ
              DS3 DQ
                |
ESP32 GND -----+-- DS1 GND, DS2 GND, DS3 GND
```

### Tipp: Parasitaere Stromversorgung

Der DS18B20 kann Strom aus der Data Line beziehen. Dazu:
- VDD mit GND verbinden (keine externe Stromversorgung noetig)
- Pull-up Widerstand sollte staerker sein (2.2 kOhm statt 4.7 kOhm)
- Leicht zuverlaessiger wenn externe Stromversorgung vorhanden

## Installation

### 1. Datei kopieren

Kopiere `nitbw_ds18b20.py` in Dein MicroPython-Projekt:

```bash
# Auf dem ESP32
cp nitbw_ds18b20.py /sd/lib/
```

### 2. Import

```python
from nitbw_ds18b20 import DS18B20
from machine import Pin
```

## Schnellstart

```python
from machine import Pin
from nitbw_ds18b20 import DS18B20
import time

# Initialisierung
sensor = DS18B20(Pin(4))

# Einzelne Messung
temperatur = sensor.messen()
print("Temperatur: {:.2f} °C".format(temperatur))

# Mehrere Sensoren
roms = sensor.search_roms()
print("Sensoren gefunden: {}".format(len(roms)))

for rom in roms:
    temp = sensor.read_temperature(rom)
    print("Sensor: {:.2f} °C".format(temp))
```

## API-Referenz

### Konstruktor

```python
sensor = DS18B20(pin)
```

| Parameter | Typ | Beschreibung |
|-----------|-----|-------------|
| `pin` | `int` oder `Pin` | GPIO-Pin fuer OneWire (z.B. 4 oder Pin(4)) |

**Eigenschaft nach Konstruktion:**
- Default-Aufloesung: 12 Bit (hoechste Genauigkeit)
- CRC8-Lookup-Tabelle wird automatisch initialisiert

### Methoden

#### Temperaturmessung

**`messen(rom=None) -> float`**

Fuehrt eine komplette Konvertierung und Messung durch.

- **Parameter:**
  - `rom`: ROM-Adresse (bytes) zum Selektieren. `None` = SKIP ROM (einzelner Sensor)
- **Rueckgabe:** Temperatur in °C als float, oder `None` bei Fehler
- **Besonderheit:** Wartet automatisch auf Konvertierung (bis zu 800 ms)

Beispiel:
```python
temp = sensor.messen()  # Einzelner Sensor
temp = sensor.messen(roms[0])  # Spezifischer Sensor
```

---

**`convert_temperature(rom=None) -> bool`**

Startet bie Temperaturkonvertierung (Messung), asynchron.

- **Parameter:** `rom` (siehe oben)
- **Rueckgabe:** `True` bei Erfolg, `False` bei Fehler
- **Hinweis:** Konvertierung dauert 94 ms (9 Bit) bis 750 ms (12 Bit). Danach `read_temperature()` aufrufen.

Beispiel:
```python
sensor.convert_temperature()
time.sleep(0.8)
temp = sensor.read_temperature()
```

---

**`read_temperature(rom=None) -> float`**

Liest den aktuellen Temperaturwert (nach erfolgter Konvertierung).

- **Parameter:** `rom` (siehe oben)
- **Rueckgabe:** Temperatur in °C oder `None` bei CRC-Fehler
- **Hinweis:** Nutze diese nach `convert_temperature()` wenn Konvertierung unabhaengig laufen soll.

---

#### Sensor-Konfiguration

**`set_resolution(bits) -> None`**

Setzt die interne Aufloesung ohne Flash zu schreiben.

- **Parameter:** `bits` (9, 10, 11 oder 12, default 12)
- **Hinweis:** Aendert nur lokale Einstellung, nicht den Non-Volatile Memory

Beispiel:
```python
sensor.set_resolution(9)  # Schnellere Messung
sensor.set_resolution(12)  # Hoechste Genauigkeit
```

---

**`write_scratchpad(th, tl, resolution=None, rom=None) -> bool`**

Schreibt Alarm-Schwellwerte und Aufloesung in den Sensor.

- **Parameter:**
  - `th`: Alarm High Temperatur (Integer, z.B. 30 fuer 30 °C)
  - `tl`: Alarm Low Temperatur (Integer, z.B. 10 fuer 10 °C)
  - `resolution`: 9, 10, 11 oder 12, oder None (aktuell beibehalten)
  - `rom`: ROM-Adresse (None = SKIP ROM)
- **Rueckgabe:** `True` bei Erfolg
- **Hinweis:** Alarm-Pins loesen bei Verletzung der Schwellwerte aus (nicht in MicroPython auswertbar, aber persistiert im Sensor)

Beispiel:
```python
sensor.write_scratchpad(th=25, tl=10, resolution=12)
```

---

#### ROM-Verwaltung

**`search_roms() -> list`**

Durchsucht den OneWire Bus nach allen angeschlossenen DS18B20 Sensoren.

- **Rueckgabe:** Liste von ROM-Adressen (jeweils `bytes` mit 8 Bytes)
- **Besonderheit:** Speichert Adressen in `self.roms` ab

Beispiel:
```python
roms = sensor.search_roms()
for rom in roms:
    print(sensor.rom_to_string(rom))
```

---

**`get_rom_list() -> list`**

Gibt die zuletzt gefundenen ROM-Adressen zurueck.

Beispiel:
```python
liste = sensor.get_rom_list()
```

---

**`rom_to_string(rom) -> str`**

Konvertiert eine ROM-Adresse zu Hex-String fuer lesbare Ausgabe.

- **Parameter:** `rom` (bytes)
- **Rueckgabe:** Hex-String (z.B. "28FF1A2C6B010416")

Beispiel:
```python
print(sensor.rom_to_string(roms[0]))  # Ausgabe: 28FF1A2C6B010416
```

---

## Beispiele

Zum Starten eines Beispiels:
```python
import beispiel_ds18b20
# oder
import beispiel_ds18b20_mehrere
# oder
import beispiel_ds18b20_aufloesung
# oder
import beispiel_ds18b20_diagnose
```

### Beispiel 1: Grundmessung (beispiel_ds18b20.py)

Einfache Temperaturabfrage alle 1 Sekunde:

```python
from machine import Pin
from nitbw_ds18b20 import DS18B20
import time

sensor = DS18B20(Pin(4))
sensor.set_resolution(12)  # 12-Bit Aufloesung

while True:
    temperatur = sensor.messen()
    if temperatur is not None:
        print("Temperatur: {:.2f} °C".format(temperatur))
    else:
        print("Messfehler")
    time.sleep(1)
```

### Beispiel 2: Mehrere Sensoren (beispiel_ds18b20_mehrere.py)

Automatische Sensorerkennung und parallele Messung:

```python
from machine import Pin
from nitbw_ds18b20 import DS18B20
import time

sensor = DS18B20(Pin(4))

# Suche alle Sensoren
roms = sensor.search_roms()
print("Sensoren gefunden: {}".format(len(roms)))

while True:
    # Starte Konvertierung bei allen gleichzeitig
    sensor.convert_temperature()
    time.sleep(1)
    
    # Lese einzeln aus
    for i, rom in enumerate(roms):
        temp = sensor.read_temperature(rom)
        rom_str = sensor.rom_to_string(rom)
        if temp is not None:
            print("Sensor {}: {:.2f} °C ({})".format(i+1, temp, rom_str[:8]))
    
    time.sleep(1)
```

### Beispiel 3: Aufloesung und Alarm (beispiel_ds18b20_aufloesung.py)

Konfiguriere Aufloesung und Alarm-Schwellwerte:

```python
from machine import Pin
from nitbw_ds18b20 import DS18B20

sensor = DS18B20(Pin(4))

# Schreibe Alarm-Grenzen
sensor.write_scratchpad(th=30, tl=10, resolution=12)
print("Alarm-Grenzen gesetzt: 30 °C (High), 10 °C (Low)")

# Teste verschiedene Aufloesungen
for resolution in [9, 10, 11, 12]:
    sensor.set_resolution(resolution)
    print("Aufloesung: {} Bit".format(resolution))
    
    for _ in range(3):
        temp = sensor.messen()
        if temp is not None:
            print("  {:.4f} °C".format(temp))
```

### Beispiel 4: Dauermessung mit Fehlerbehandlung

```python
from machine import Pin
from nitbw_ds18b20 import DS18B20
import time

sensor = DS18B20(Pin(4))
fehlercount = 0

try:
    while True:
        temp = sensor.messen()
        
        if temp is not None:
            print("Temp: {:.2f} °C  Fehler: {}".format(temp, fehlercount))
            fehlercount = 0  # Zuruecksetzen
        else:
            fehlercount += 1
            print("Fehler #{} (CRC-Mismatch?)".format(fehlercount))
            if fehlercount > 3:
                print("Zu viele Fehler - Sensor-Fehler vermutet")
        
        time.sleep(1)
        
except KeyboardInterrupt:
    print("Beendet")
```

### Beispiel 5: ROM-Liste speichern und laden

```python
from machine import Pin
from nitbw_ds18b20 import DS18B20
import json

sensor = DS18B20(Pin(4))

# Suche Sensoren und speichere ROM-Adressen
roms = sensor.search_roms()
rom_strs = [sensor.rom_to_string(rom) for rom in roms]

# Speichere als JSON
with open("roms.json", "w") as f:
    json.dump(rom_strs, f)

# Spater: Lade und konvertiere zurueck
with open("roms.json", "r") as f:
    rom_strs = json.load(f)
    roms = [bytes.fromhex(s) for s in rom_strs]

# Nutze ROM-Adressen
for rom in roms:
    temp = sensor.read_temperature(rom)
    print("Temp: {:.2f} °C".format(temp))
```

### Beispiel 6: Diagnose bei Lesefehlern

Prueft Presence-Puls, ROM-Suche und Scratchpad-CRC:

```python
from machine import Pin
from nitbw_ds18b20 import DS18B20

sensor = DS18B20(Pin(4))

print("Presence:", sensor.sensor_vorhanden())
roms = sensor.search_roms()
print("ROMs:", len(roms))

if roms:
    data = sensor.read_scratchpad(roms[0])
    print("Scratchpad:", data)
    print("Temp:", sensor.read_temperature(roms[0]))
```

## Lizenz

MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
