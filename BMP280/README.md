# NIT Bibliothek: BMP280

## Beschreibung
Die Bibliothek `nitbw_bmp280.py` stellt eine kompakte, aber vollstaendige BMP280-Anbindung fuer ESP32 mit MicroPython bereit. Sie liest Temperatur und Luftdruck aus und bietet zusaetzlich Funktionen fuer Hoehenberechnung und Kalibrierung. Aufbau und Methodennamen entsprechen der BME280-Bibliothek, sodass Programme mit wenigen Aenderungen zwischen beiden Sensoren wechseln koennen. Die Implementierung greift direkt auf Sensorregister zu und benoetigt keine Fremdbibliotheken ausser `machine`.

## Features
- Temperaturmessung in Grad Celsius
- Luftdruckmessung in hPa
- Kombinierte Abfrage beider Messwerte in einem Aufruf
- Mittelwertbildung ueber mehrere Messungen (`read_averaged`)
- Hoehenberechnung aus Luftdruck
- Kalibrierung ueber bekannte Hoehe (`calibrate_altitude`)
- Setzen eines QNH-Referenzdrucks (`set_sea_level_pressure`)
- Konfigurierbare Modi: `MODE_SLEEP`, `MODE_FORCED`, `MODE_NORMAL`
- Konfigurierbares Oversampling fuer Temperatur und Druck
- IIR-Filter- und Standby-Konfiguration (bis 4 s)
- Automatische Wartezeit passend zum eingestellten Oversampling
- Erkennt versehentlich angeschlossene BME280 und gibt einen Hinweis aus

## Hardware
- Sensor: Bosch BMP280 (Breakout-Boards wie GY-BMP280 mit 3.3V Logik)
- I2C-Adresse: `0x76` (typisch) oder `0x77`
- Chip-ID: `0x58` (Vorserienmuster: `0x56`/`0x57`)
- Versorgung: 3.3V
- Hinweise:
  - Der BMP280 misst **keine** Luftfeuchte. Taupunkt und Hitzeindex gibt es nur beim BME280.
  - BMP280 und BME280 sehen fast gleich aus. Der BME280 hat ein quadratisches, der BMP280 ein laengliches Gehaeuse. Im Zweifel `get_chip_id()` pruefen (`0x58` = BMP280, `0x60` = BME280).
  - Viele Module haben bereits Pull-up-Widerstaende auf SDA/SCL.
  - Manche Boards schalten die Adresse ueber SDO/ADR um.
  - Die Standby-Zeiten `0x06`/`0x07` bedeuten beim BMP280 2000/4000 ms (beim BME280 10/20 ms).

## Anschluss
Beispiel ESP32-Standardpins:

- `VCC -> 3V3`
- `GND -> GND`
- `SCL -> GPIO 22`
- `SDA -> GPIO 21`

## Installation
- Datei `nitbw_bmp280.py` auf den ESP32 kopieren (Root oder `lib/`).
- In Skripten mit `from nitbw_bmp280 import BMP280` importieren.

## Schnellstart
```python
from machine import I2C, Pin
from nitbw_bmp280 import BMP280

# I2C und Sensor initialisieren
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = BMP280(i2c, addr=0x76)

# Messwerte auslesen
temp, druck = sensor.read_all()
print(f"T={temp:.2f} C, p={druck:.2f} hPa")
```

## API-Referenz
Konstruktor: `BMP280(i2c, addr=0x76)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `i2c` | `machine.I2C` | - | Initialisierter I2C-Bus |
| `addr` | `int` | `0x76` | Sensoradresse (`0x76` oder `0x77`) |

Messen:
- `read_all()` -> `(temperatur, druck)`
- `read_temperature()` -> `float` (C)
- `read_pressure()` -> `float` (hPa)
- `read_averaged(n=10, delay_ms=0)` -> `(temperatur, druck)` als Mittelwert
- `read_raw()` -> `(adc_t, adc_p)` Rohwerte
- `read_compensated_data()` -> Alias fuer `read_all()`

Hoehe:
- `calculate_altitude(pressure=None, sea_level_pressure=None)` -> Hoehe in m
- `calculate_sea_level_pressure(altitude, pressure=None)` -> QNH in hPa
- `set_sea_level_pressure(pressure)`
- `calibrate_altitude(known_altitude)`

Konfiguration und Betrieb:
- `configure(mode, osrs_t, osrs_p, filter_coef, standby)` -> setzt Modus/Oversampling/Filter
- `forced_measurement()` -> Einzelmessung im Forced-Mode
- `sleep()` -> Sensor in Sleep-Mode
- `reset()` -> Soft Reset (danach `configure()` aufrufen)
- `get_chip_id()` -> Chip-ID (`0x58`)
- `get_status()` -> `(measuring, im_update)`

Konstanten:

| Gruppe | Werte |
|---|---|
| Modus | `MODE_SLEEP`, `MODE_FORCED`, `MODE_NORMAL` |
| Oversampling | `OVERSAMPLE_SKIP`, `OVERSAMPLE_X1`, `_X2`, `_X4`, `_X8`, `_X16` |
| Filter | `FILTER_OFF`, `FILTER_2`, `FILTER_4`, `FILTER_8`, `FILTER_16` |
| Standby | `STANDBY_0_5`, `_62_5`, `_125`, `_250`, `_500`, `_1000`, `_2000`, `_4000` |

## Beispiele
Dateien im Ordner:
- `BMP280/beispiel_bmp280.py` - Grundbeispiel Temperatur, Druck, Hoehe
- `BMP280/beispiel_bmp280_hoehenmesser.py` - Relativer Hoehenmesser / Stockwerkserkennung

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
temp, druck = sensor.forced_measurement()
```

Snippet 4: Stabile Werte durch Mittelwert
```python
temp, druck = sensor.read_averaged(n=20, delay_ms=10)
print(f"Mittelwert: {druck:.2f} hPa")
```

Snippet 5: Oversampling und Filter konfigurieren
```python
from nitbw_bmp280 import BMP280
sensor.configure(
    mode=BMP280.MODE_NORMAL,
    osrs_t=BMP280.OVERSAMPLE_X2,
    osrs_p=BMP280.OVERSAMPLE_X16,
    filter_coef=BMP280.FILTER_16,
    standby=BMP280.STANDBY_0_5
)
```

Snippet 6: Wechsel vom BME280
```python
# vorher: from nitbw_bme280 import BME280
from nitbw_bmp280 import BMP280
sensor = BMP280(i2c)
temp, druck = sensor.read_all()   # nur 2 Werte statt 3
```

Praktische Hinweise/Fehlersuche:
- Leere I2C-Scans: Verkabelung, Versorgung und Pull-ups pruefen.
- RuntimeError "BME280 erkannt": Es ist ein BME280 angeschlossen, `nitbw_bme280` verwenden.
- RuntimeError bei Init: Adresse (`0x76`/`0x77`) und Chip-ID pruefen.
- Falsche Werte direkt nach Start: 1-2 Messzyklen verwerfen.
- Hoehenfehler von mehreren zehn Metern: QNH aktualisieren.
- Temperatur etwas zu hoch: Eigenerwaermung durch Board/ESP32, Sensor abgesetzt montieren.
- Nach `reset()` misst der Sensor nicht mehr: `configure()` erneut aufrufen.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
