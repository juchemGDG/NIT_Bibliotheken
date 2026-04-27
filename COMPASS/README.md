# NIT Bibliothek: COMPASS

## Beschreibung
Die Bibliothek `nitbw_compass.py` bindet GY-261-Kompassmodule unter MicroPython an und berechnet Heading, Himmelsrichtung und Lagewinkel. Sie unterstuetzt QMC5883L und HMC5883L als Magnetfeldsensoren sowie den ADXL345 Beschleunigungssensor des GY-261 fuer Sensorfusion (neigungskompensiertes Heading). Ausgelegt fuer den Unterricht mit klarer API fuer Kalibrierung, Richtungslogik und Lagedaten.

## Version
`1.1`

## Features

### Magnetfeldsensor (QMC5883L / HMC5883L)
- Unterstuetzung fuer QMC5883L (`0x0D`) und HMC5883L (`0x1E`)
- Rohdatenzugriff auf X/Y/Z-Magnetfeldachsen
- Feldstaerke in mG (`read_strength`)
- Heading-Berechnung in Grad (`0..360`)
- Richtungsnamen 16-teilig (`N`, `NNE`, `NE`, `ENE`, ...)
- Einstellbare lokale Deklination
- Automatische Kalibrierung (`auto_calibrate`)
- Manuelle Bias-Kalibrierung (`calibrate_with_bias`)
- Einstellbarer Messbereich, Sample-Rate und Oversampling
- Rotationsberechnung zwischen zwei Heading-Werten

### Beschleunigungssensor ADXL345 (neu in v1.1)
- Separate Klasse `Accelerometer` fuer den ADXL345
- Rohwerte, Beschleunigung in g und m/s^2
- Pitch (Nickwinkel) und Roll (Rollwinkel) in Grad
- Gesamtneigungswinkel und Lagetext (`waagerecht`, `geneigt`, `hochkant`)
- Automatische Offset-Kalibrierung

### Sensorfusion (neu in v1.1)
- Neigungskompensiertes Heading (`read_heading_tilt_compensated`)
- Korrekte Richtungsangabe auch bei Neigung bis ca. 60 Grad
- Kombinierten Datenabruf aller Sensoren in einem Aufruf (`read_all`)
- Automatischer Fallback auf einfaches Heading wenn ADXL345 fehlt

## Hardware
- Modul: GY-261 mit QMC5883L (oder HMC5883L) und ADXL345
- I2C-Adressen:
  - `0x0D` - QMC5883L (haeufig auf GY-261)
  - `0x1E` - HMC5883L
  - `0x53` - ADXL345 (SDO-Pin LOW, Standard)
  - `0x1D` - ADXL345 (SDO-Pin HIGH, alternativ)
- Versorgung: 3.3 V
- Hinweise:
  - I2C-Adressen vorab mit `i2c.scan()` pruefen.
  - Metallteile, Motoren und Magnete beeinflussen die Messung.
  - Nach Umbau oder Ortswechsel Kalibrierung wiederholen.

## Anschluss
Beispiel ESP32-Standardpins:

| Signal | ESP32   |
|--------|---------|
| VCC    | 3V3     |
| GND    | GND     |
| SCL    | GPIO 22 |
| SDA    | GPIO 21 |

## Installation
- Datei `nitbw_compass.py` auf den ESP32 kopieren.
- Import: `from nitbw_compass import Compass` oder `from nitbw_compass import Compass, Accelerometer`

## Schnellstart

```python
from machine import I2C, Pin
from nitbw_compass import Compass

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# use_accel=True (Standard): ADXL345 wird automatisch gesucht
compass = Compass(i2c, addr=0x0D)

compass.set_declination(degrees=3, minutes=45)

# Einfaches Heading
print(compass.read_heading())
print(compass.read_heading_direction())

# Neigungskompensiertes Heading (Sensorfusion)
print(compass.read_heading_tilt_compensated())
print(compass.read_heading_tilt_compensated_direction())
```

## API-Referenz

### Klasse `Compass`

Konstruktor: `Compass(i2c, addr=0x0D, use_accel=True, accel_addr=None)`

| Parameter    | Typ           | Standard | Beschreibung                                       |
|---|---|---|---|
| `i2c`        | `I2C`         | -        | Initialisiertes I2C-Objekt                         |
| `addr`       | `int`         | `0x0D`   | I2C-Adresse des Magnetfeldsensors                  |
| `use_accel`  | `bool`        | `True`   | ADXL345 automatisch suchen und initialisieren      |
| `accel_addr` | `int / None`  | `None`   | ADXL345-Adresse; `None` = Standard `0x53`          |

**Magnetometer-Methoden:**
- `read_raw()` - Rohachsenwerte (x, y, z)
- `read_field()` - kalibrierte Feldwerte in mG (x, y, z)
- `read_strength()` - Gesamtfeldstaerke in mG
- `read_heading()` - Heading in Grad (0-360)
- `read_heading_direction()` - Himmelsrichtung als Text
- `set_declination(degrees, minutes=0)` - lokale Deklination setzen
- `auto_calibrate(samples=100)` - automatische Kalibrierung (Sensor drehen)
- `calibrate_with_bias(x_bias, y_bias, z_bias=0)` - manuelle Offset-Kalibrierung
- `set_range(range_val)` - Messbereich: `RANGE_2G / 8G / 12G / 30G`
- `set_sample_rate(rate)` - Abtastrate: `RATE_10HZ / 25HZ / 50HZ / 100HZ`
- `set_oversample(oversample)` - Oversampling: `OVERSAMPLE_512 / 256 / 128 / 64`
- `calculate_rotation(start, end)` - Drehwinkel in Grad (-180 bis +180)
- `get_rotation_direction(start, end)` - `"rechts"`, `"links"` oder `"keine Drehung"`

**Sensorfusion-Methoden (neu v1.1):**
- `has_accelerometer()` - True wenn ADXL345 verfuegbar
- `read_heading_tilt_compensated()` - neigungskompensiertes Heading in Grad
- `read_heading_tilt_compensated_direction()` - kompensierte Himmelsrichtung
- `read_all()` - alle Sensor-Daten als `dict` (Magnetfeld + Beschleunigung)

### Klasse `Accelerometer` (neu v1.1)

Konstruktor: `Accelerometer(i2c, addr=0x53)`

| Parameter | Typ   | Standard | Beschreibung                     |
|---|---|---|---|
| `i2c`     | `I2C` | -        | I2C-Objekt                       |
| `addr`    | `int` | `0x53`   | I2C-Adresse (`0x53` oder `0x1D`) |

**Methoden:**
- `read_raw()` - Roh-ADC-Werte (x, y, z)
- `read_accel()` - Beschleunigung in g (x, y, z)
- `read_accel_ms2()` - Beschleunigung in m/s^2 (x, y, z)
- `read_pitch()` - Nickwinkel in Grad
- `read_roll()` - Rollwinkel in Grad
- `read_pitch_roll()` - Pitch und Roll mit einer Messung
- `read_tilt_angle()` - Gesamtneigung gegenueber Waagerechten in Grad
- `is_level(threshold=5.0)` - True wenn Neigung innerhalb Toleranz
- `read_orientation_text()` - Lagetext: `"waagerecht"`, `"leicht geneigt"`, `"stark geneigt"`, `"hochkant"`
- `calibrate(samples=50)` - automatische Offset-Kalibrierung (Sensor waagerecht halten)
- `set_offset(x, y, z)` - manuelle Offsets setzen
- `get_device_id()` - Chip-ID lesen (ADXL345 = `0xE5`)
- `is_available()` - True wenn Sensor antwortet

## Beispiele
Dateien im Ordner:
- `COMPASS/beispiel_compass.py` - Grundfunktionen: Heading und Richtung
- `COMPASS/beispiel_compass_kalibrierung.py` - Kalibrierung des Magnetometers
- `COMPASS/beispiel_compass_rotation.py` - Drehwinkelmessung
- `COMPASS/beispiel_sensorfusion.py` - Beschleunigungssensor und Sensorfusion (neu v1.1)

Snippet 1: I2C-Adressen pruefen
```python
from machine import I2C, Pin
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
print([hex(a) for a in i2c.scan()])
# Erwartet: [0x0d, 0x53] (QMC5883L + ADXL345)
```

Snippet 2: Neigungskompensiertes Heading
```python
import time
while True:
    h = compass.read_heading_tilt_compensated()
    r = compass.read_heading_tilt_compensated_direction()
    print(f"{h:.1f}Grad -> {r}")
    time.sleep(0.5)
```

Snippet 3: Lagewinkel lesen
```python
if compass.has_accelerometer():
    pitch, roll = compass.accel.read_pitch_roll()
    print(f"Pitch: {pitch:.1f} Grad  Roll: {roll:.1f} Grad")
    print(compass.accel.read_orientation_text())
```

Snippet 4: Alle Daten auf einmal
```python
d = compass.read_all()
print(f"Heading: {d['heading']:.1f}Grad  Kompensiert: {d['heading_tc']:.1f}Grad")
print(f"Neigung: {d['tilt']:.1f}Grad  Pitch: {d['pitch']:.1f}Grad  Roll: {d['roll']:.1f}Grad")
```

Snippet 5: Auto-Kalibrierung Magnetometer
```python
print("Sensor in alle Richtungen drehen...")
compass.auto_calibrate(samples=200)
```

Snippet 6: Drehwinkel berechnen
```python
start = compass.read_heading()
time.sleep(2)
aktuell = compass.read_heading()
rotation = compass.calculate_rotation(start, aktuell)
print(f"Drehung: {rotation:.1f} Grad  Richtung: {compass.get_rotation_direction(start, aktuell)}")
```

## Praktische Hinweise / Fehlersuche
- **Nur `0x1E` gefunden:** `addr=0x1E` im Konstruktor setzen (HMC5883L-Variante).
- **ADXL345 nicht gefunden:** SDO-Pin pruefen; alternativ `accel_addr=0x1D` setzen.
- **Sprunghafte Richtungen:** Kalibrierung wiederholen, Stoerquellen (Motoren, Batterien) entfernen.
- **Heading versetzt:** Lokale Deklination korrekt einstellen (`set_declination`).
- **Sensorfusion liefert keine Verbesserung:** Beschleunigungssensor kalibrieren (`compass.accel.calibrate()`).

## Lizenz
MIT-Lizenz, siehe `LICENSE` im Repository-Root.
