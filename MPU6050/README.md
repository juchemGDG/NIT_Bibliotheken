# NIT Bibliothek: MPU6050

## Beschreibung
Die Bibliothek `nitbw_mpu6050.py` stellt eine vollstaendige MPU6050-Anbindung fuer ESP32 mit MicroPython bereit. Sie liest Beschleunigung (3 Achsen), Winkelgeschwindigkeit (3 Achsen) und Chip-Temperatur aus. Zusaetzlich bietet sie Lagewinkelberechnung (Pitch, Roll), Gyroskop-Kalibrierung und Power-Management. Die Implementierung greift direkt auf Sensorregister zu und benoetigt keine Fremdbibliotheken ausser `machine` und `math`.

## Features
- Beschleunigungsmessung in g und m/s² (3 Achsen)
- Winkelgeschwindigkeit in deg/s (3 Achsen)
- Chip-Temperaturmessung
- Alle Messwerte in einem einzigen I2C-Zugriff (`read_all`)
- Lagewinkelberechnung: Pitch, Roll, Gesamtneigung
- Lagetext: "waagerecht", "leicht geneigt", "stark geneigt", "hochkant"
- Automatische Gyroskop-Kalibrierung (`calibrate_gyro`)
- Manuelles Setzen gespeicherter Kalibrierungsoffsets (`set_gyro_offset`)
- Konfigurierbarer Messbereich: Beschleunigung (±2 / ±4 / ±8 / ±16 g) und Gyroskop (±250 / ±500 / ±1000 / ±2000 deg/s)
- Digitales Tiefpassfilter (DLPF) einstellbar von 5 bis 260 Hz
- Sample-Rate-Divider konfigurierbar
- Sleep-Mode und Wake-Up fuer Energiesparbetrieb
- Chip-Verifikation ueber WHO_AM_I beim Start

## Hardware
- Sensor: InvenSense MPU-6050
- Breakout-Module: GY-521 (weit verbreitet) und kompatible Module
- Versorgung: 3.3V (GY-521 hat integrierten Spannungsregler, auch 5V moeglich)
- Hinweise:
  - GY-521 hat Pull-up-Widerstaende auf SDA/SCL bereits verbaut.
  - AD0-Pin auf GND = Adresse 0x68 (Standard), auf VCC = 0x69 (Alternativadresse).
  - Zwei MPU6050 am selben I2C-Bus moeglich durch Setzen von AD0.

## Anschluss
Beispiel ESP32-Standardpins (GY-521):

- `VCC -> 3V3`
- `GND -> GND`
- `SCL -> GPIO 22`
- `SDA -> GPIO 21`
- `AD0 -> GND` (Adresse 0x68, Standard)

## Installation
- Datei `nitbw_mpu6050.py` auf den ESP32 kopieren (Root oder `lib/`).
- In Skripten mit `from nitbw_mpu6050 import MPU6050` importieren.

## Schnellstart
```python
from machine import I2C, Pin
from nitbw_mpu6050 import MPU6050

# I2C und Sensor initialisieren
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = MPU6050(i2c)

# Alle Messwerte in einem Aufruf
daten = sensor.read_all()
print(f"a=({daten['ax']:.2f},{daten['ay']:.2f},{daten['az']:.2f})g")
print(f"g=({daten['gx']:.1f},{daten['gy']:.1f},{daten['gz']:.1f})deg/s")
print(f"T={daten['temp']:.1f}C")
```

## API-Referenz
Konstruktor: `MPU6050(i2c, addr=0x68)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `i2c` | `machine.I2C` | - | Initialisierter I2C-Bus |
| `addr` | `int` | `0x68` | Sensoradresse (`0x68` oder `0x69`) |

Messwerte:
- `read_all()` -> `dict` mit "ax","ay","az","gx","gy","gz","temp"
- `read_accel()` -> `(ax, ay, az)` in g
- `read_accel_ms2()` -> `(ax, ay, az)` in m/s²
- `read_gyro()` -> `(gx, gy, gz)` in deg/s
- `read_temperature()` -> `float` in degC
- `read_accel_raw()` -> `(x, y, z)` ADC-Rohwerte
- `read_gyro_raw()` -> `(x, y, z)` ADC-Rohwerte

Lagewinkel:
- `read_pitch()` -> `float` in Grad
- `read_roll()` -> `float` in Grad
- `read_pitch_roll()` -> `(pitch, roll)` in Grad
- `read_tilt_angle()` -> `float` Gesamtneigung in Grad
- `is_level(threshold=5.0)` -> `bool`
- `read_orientation_text()` -> `str`

Konfiguration:
- `set_accel_range(range_val)` -> ACCEL_RANGE_2G / _4G / _8G / _16G
- `set_gyro_range(range_val)` -> GYRO_RANGE_250 / _500 / _1000 / _2000
- `set_dlpf(dlpf)` -> DLPF_260HZ bis DLPF_5HZ
- `set_sample_rate_divider(divider)` -> 0-255

Kalibrierung:
- `calibrate_gyro(samples=200)` -> automatische Offset-Kalibrierung im Stillstand
- `set_gyro_offset(offset_x, offset_y, offset_z)` -> manuell setzen

Power Management:
- `sleep()` -> Sleep-Mode aktivieren
- `wake()` -> Sensor aufwecken
- `reset()` -> Software-Reset und Neuinitialisierung

Diagnose:
- `get_who_am_i()` -> `int` Chip-ID (erwartet 0x68)
- `is_available()` -> `bool`

## Beispiele
Dateien im Ordner:
- `MPU6050/beispiel_mpu6050.py`
- `MPU6050/beispiel_mpu6050_neigung.py`
- `MPU6050/beispiel_mpu6050_kalibrierung.py`

Snippet 1: Beschleunigung und Gyroskop separat lesen
```python
ax, ay, az = sensor.read_accel()
gx, gy, gz = sensor.read_gyro()
print(f"Beschleunigung Z: {az:.3f} g")
print(f"Drehrate Z:       {gz:.2f} deg/s")
```

Snippet 2: Pitch und Roll bestimmen
```python
pitch, roll = sensor.read_pitch_roll()
print(f"Pitch: {pitch:+.1f} deg  Roll: {roll:+.1f} deg")
```

Snippet 3: Gyroskop kalibrieren und Offsets speichern
```python
sensor.calibrate_gyro(samples=200)
offset_x = sensor.gyro_offset_x
offset_y = sensor.gyro_offset_y
offset_z = sensor.gyro_offset_z
# Naechstes Mal direkt setzen:
# sensor.set_gyro_offset(offset_x, offset_y, offset_z)
```

Snippet 4: Messbereich auf +/-8 g und +/-500 deg/s erweitern
```python
sensor.set_accel_range(MPU6050.ACCEL_RANGE_8G)
sensor.set_gyro_range(MPU6050.GYRO_RANGE_500)
```

Snippet 5: DLPF auf 10 Hz setzen (starke Glaettung)
```python
sensor.set_dlpf(MPU6050.DLPF_10HZ)
```

Snippet 6: Energiesparen mit Sleep / Wake
```python
sensor.sleep()
# ... warten ...
sensor.wake()
daten = sensor.read_all()
```

Snippet 7: Zwei Sensoren am selben I2C-Bus
```python
# Sensor 1: AD0-Pin auf GND -> 0x68
# Sensor 2: AD0-Pin auf VCC -> 0x69
sensor1 = MPU6050(i2c, addr=0x68)
sensor2 = MPU6050(i2c, addr=0x69)
```

Praktische Hinweise / Fehlersuche:
- RuntimeError beim Start: Verkabelung pruefen, AD0-Pin und Adresse (0x68/0x69) kontrollieren.
- Gyroskop zeigt im Stillstand ungleich Null: `calibrate_gyro()` aufrufen.
- Beschleunigung Z zeigt ca. 1.0 g im Stillstand: Korrekt, das ist die Erdschwerebeschleunigung.
- Winkel springen bei Erschuetterungen: Beschleunigungsbasierte Winkel reagieren auf alle Kraefte. Fuer dynamische Anwendungen Gyroskop-Integration oder Komplementaerfilter nutzen.
- Leerer I2C-Scan: Versorgung (3.3V), Verkabelung und Pull-ups pruefen.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
