# NIT Bibliothek: BME280

## Beschreibung
Die Bibliothek `nitbw_bme280.py` stellt eine kompakte, aber vollstaendige BME280-Anbindung fuer ESP32 mit MicroPython bereit. Sie liest Temperatur, Luftdruck und Luftfeuchtigkeit aus und bietet zusaetzlich Funktionen fuer Hoehenberechnung und Kalibrierung. Die Implementierung greift direkt auf Sensorregister zu und benoetigt keine Fremdbibliotheken ausser `machine`.

## Features
- Temperaturmessung in Grad Celsius
- Luftdruckmessung in hPa
- Luftfeuchtemessung in Prozent
- Kombinierte Abfrage aller Messwerte in einem Aufruf
- Hoehenberechnung aus Luftdruck
- Kalibrierung ueber bekannte Hoehe (`calibrate_altitude`)
- Setzen eines QNH-Referenzdrucks (`set_sea_level_pressure`)
- Berechnung von Taupunkt und Hitzeindex
- Konfigurierbare Modi: `MODE_SLEEP`, `MODE_FORCED`, `MODE_NORMAL`
- Konfigurierbares Oversampling fuer Temperatur, Druck und Feuchte
- IIR-Filter- und Standby-Konfiguration
- Direkt nutzbar fuer energiesparende Messzyklen

## Hardware
- Sensor: Bosch BME280 (Breakout-Boards mit 3.3V Logik)
- I2C-Adresse: `0x76` (typisch) oder `0x77`
- Versorgung: 3.3V
- Hinweise:
  - Viele Module haben bereits Pull-up-Widerstaende auf SDA/SCL.
  - Manche Boards schalten die Adresse ueber SDO/ADR um.
  - Fuer stabile Hoehenwerte sollte ein plausibler QNH-Wert gesetzt werden.

## Anschluss
Beispiel ESP32-Standardpins:

- `VCC -> 3V3`
- `GND -> GND`
- `SCL -> GPIO 22`
- `SDA -> GPIO 21`

## Installation
- Datei `nitbw_bme280.py` auf den ESP32 kopieren (Root oder `lib/`).
- In Skripten mit `from nitbw_bme280 import BME280` importieren.

## Schnellstart
```python
from machine import I2C, Pin
from nitbw_bme280 import BME280

# I2C und Sensor initialisieren
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = BME280(i2c, addr=0x76)

# Messwerte auslesen
temp, druck, feuchte = sensor.read_all()
print(f"T={temp:.2f} C, p={druck:.2f} hPa, rF={feuchte:.2f}%")
```

## API-Referenz
Konstruktor: `BME280(i2c, addr=0x76)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `i2c` | `machine.I2C` | - | Initialisierter I2C-Bus |
| `addr` | `int` | `0x76` | Sensoradresse (`0x76` oder `0x77`) |

Wichtige Methoden:
- `read_all()` -> `(temperatur, druck, feuchte)`
- `read_temperature()` -> `float`
- `read_pressure()` -> `float`
- `read_humidity()` -> `float`
- `configure(...)` -> setzt Modus/Oversampling/Filter
- `forced_measurement()` -> Einzelmessung im Forced-Mode
- `sleep()` -> Sensor in Sleep-Mode
- `calculate_altitude(pressure=None, sea_level_pressure=None)`
- `set_sea_level_pressure(pressure)`
- `calibrate_altitude(known_altitude)`
- `calculate_dew_point(temperature=None, humidity=None)`
- `calculate_heat_index(temperature=None, humidity=None)`

## Beispiele
Dateien im Ordner:
- `BME280/beispiel_bme280.py`

Snippet 1: Hoehe mit QNH-Wert berechnen
```python
sensor.set_sea_level_pressure(1007.2)
hoehe = sensor.calculate_altitude()
print(f"Hoehe: {hoehe:.1f} m")
```

Snippet 2: Kalibrierung ueber bekannte Hoehe
```python
sensor.calibrate_altitude(312)  # bekannter Standort in m
print(f"Neuer QNH: {sensor.sea_level_pressure:.2f} hPa")
```

Snippet 3: Energiesparende Einzelmessung
```python
sensor.sleep()
temp, druck, feuchte = sensor.forced_measurement()
```

Praktische Hinweise/Fehlersuche:
- Leere I2C-Scans: Verkabelung, Versorgung und Pull-ups pruefen.
- Falsche Werte direkt nach Start: 1-2 Messzyklen verwerfen.
- Hoehenfehler von mehreren zehn Metern: QNH aktualisieren.
- RuntimeError bei Init: Adresse (`0x76`/`0x77`) und Chip-ID pruefen.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
