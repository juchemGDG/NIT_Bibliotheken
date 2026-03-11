# NIT Bibliothek: COMPASS

## Beschreibung
Die Bibliothek `nitbw_compass.py` bindet GY-261-Kompassmodule unter MicroPython an und berechnet daraus Heading und Himmelsrichtung. Sie unterstuetzt sowohl QMC5883L als auch HMC5883L und ist fuer den Unterricht mit klaren Methoden fuer Kalibrierung und Richtungslogik ausgelegt.

## Features
- Unterstuetzung fuer QMC5883L (`0x0D`) und HMC5883L (`0x1E`)
- Rohdatenzugriff auf X/Y/Z-Magnetfeldachsen
- Feldstaerke in mG (`read_strength`)
- Heading-Berechnung in Grad (`0..360`)
- Richtungsnamen (`N`, `NE`, `E`, ...)
- Einstellbare lokale Deklination
- Automatische Kalibrierung (`auto_calibrate`)
- Manuelle Bias-Kalibrierung (`calibrate_with_bias`)
- Einstellbarer Messbereich (`set_range`)
- Einstellbare Sample-Rate (`set_sample_rate`)
- Einstellbares Oversampling (`set_oversample`)
- Rotationsberechnung zwischen zwei Heading-Werten

## Hardware
- Modul: GY-261 mit QMC5883L oder HMC5883L
- I2C-Adresse:
  - `0x0D` (QMC5883L, haeufig)
  - `0x1E` (HMC5883L)
- Versorgung: 3.3V
- Hinweise:
  - Adresse vorab mit `i2c.scan()` pruefen.
  - Metallteile, Motoren und Magneten beeinflussen die Messung.
  - Nach Umbau oder Ortswechsel neu kalibrieren.

## Anschluss
Beispiel ESP32-Standardpins:

- `VCC -> 3V3`
- `GND -> GND`
- `SCL -> GPIO 22`
- `SDA -> GPIO 21`

## Installation
- Datei `nitbw_compass.py` auf den ESP32 kopieren.
- Import in eigenen Skripten: `from nitbw_compass import Compass`.

## Schnellstart
```python
from machine import I2C, Pin
from nitbw_compass import Compass

# I2C und Kompass initialisieren
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
compass = Compass(i2c, addr=0x0D)

# Deklination fuer den Standort setzen
compass.set_declination(degrees=3, minutes=45)

# Heading und Richtung lesen
print(compass.read_heading())
print(compass.read_heading_direction())
```

## API-Referenz
Konstruktor: `Compass(i2c, addr=ADDRESS, scl=22, sda=21)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `i2c` | `machine.I2C | None` | - | I2C-Objekt oder `None` fuer Auto-Erzeugung |
| `addr` | `int` | `0x0D` | I2C-Adresse des Sensors |
| `scl` | `int` | `22` | SCL-Pin bei `i2c=None` |
| `sda` | `int` | `21` | SDA-Pin bei `i2c=None` |

Wichtige Methoden:
- `read_raw()` -> Rohachsenwerte
- `read_field()` -> kalibrierte Feldwerte (x, y, z)
- `read_strength()` -> Gesamtfeldstaerke
- `read_heading()` -> Winkel in Grad
- `read_heading_direction()` -> Richtungskuerzel
- `set_declination(degrees, minutes=0)`
- `auto_calibrate(samples=100)`
- `calibrate_with_bias(x_bias, y_bias, z_bias=0)`
- `set_range(range_val)`, `set_sample_rate(rate)`, `set_oversample(oversample)`
- `calculate_rotation(start_heading, end_heading)`
- `get_rotation_direction(start_heading, end_heading)`

## Beispiele
Dateien im Ordner:
- `COMPASS/beispiel_compass.py`
- `COMPASS/beispiel_compass_kalibrierung.py`
- `COMPASS/beispiel_compass_rotation.py`

Snippet 1: I2C-Adresse automatisch finden
```python
from machine import I2C, Pin
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
print(i2c.scan())
```

Snippet 2: Kontinuierliche Ausgabe
```python
import time
while True:
    print(compass.read_heading(), compass.read_heading_direction())
    time.sleep(0.5)
```

Snippet 3: Auto-Kalibrierung im Setup
```python
print("Sensor langsam in alle Richtungen drehen...")
compass.auto_calibrate(samples=200)
```

Praktische Hinweise/Fehlersuche:
- Sprunghafte Richtungen: Kalibrierung wiederholen und Stoerquellen entfernen.
- Nur `0x1E` gefunden: `addr=0x1E` setzen.
- Dauerhaft gleiche Werte: Verkabelung und Spannungsversorgung pruefen.
- Heading versetzt: lokale Deklination korrekt setzen.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
