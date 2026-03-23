# NIT Bibliothek: AS7262

## Beschreibung

Die Bibliothek `nitbw_as7262.py` steuert den AS7262 6-Kanal-Spektralsensor
ueber I2C an. Der Sensor misst Lichtintensitaeten in sechs Wellenlaengen
des sichtbaren Spektrums (Violett bis Rot). Die Kommunikation erfolgt
ueber das virtuelle Registerinterface des AS7262.

## Features

- I2C-Ansteuerung ueber das virtuelle Register-Protokoll des AS7262
- Messung von 6 Spektralkanaelen: Violett (450 nm), Blau (500 nm),
  Gruen (550 nm), Gelb (570 nm), Orange (600 nm), Rot (650 nm)
- Rohwerte als 16-Bit-Ganzzahlen (gut fuer ML-Training)
- Kalibrierte Werte als Float in uW/cm2 (sensorintern korrigiert)
- Ausgabe als Dictionary oder als Liste (direkt fuer ML verwendbar)
- Einstellbare Integrationszeit (1-255, je 2.8 ms)
- Einstellbare Verstaerkung (1x, 3.7x, 16x, 64x)
- Steuerung der eingebauten LED
- Temperaturmessung des Sensors
- Erkennung des dominanten Farbkanals
- Keine externen Abhaengigkeiten ausser `machine` und `struct`

## Hardware

### Unterstuetzter Sensor

| Sensor | Bemerkung |
|---|---|
| AS7262 | 6-Kanal sichtbares Licht, I2C-Adresse 0x49 |

### Wellenlaengen der Kanaele

| Kanal | Wellenlaenge | Name im Code |
|---|---|---|
| V | 450 nm | `violett` |
| B | 500 nm | `blau` |
| G | 550 nm | `gruen` |
| Y | 570 nm | `gelb` |
| O | 600 nm | `orange` |
| R | 650 nm | `rot` |

## Anschluss

```text
AS7262              ESP32
VCC        -------> 3.3V
GND        -------> GND
SDA        -------> GPIO 21
SCL        -------> GPIO 22
```

Hinweise:

- Der AS7262 arbeitet mit 3.3 V. Kein Levelshifter noetig am ESP32.
- 4.7 kOhm Pullup-Widerstaende an SDA und SCL werden empfohlen,
  sind aber auf vielen Breakout-Boards bereits vorhanden.
- Abstand zum Messobjekt: ca. 1-3 cm mit eingebauter LED.

## Installation

Datei `nitbw_as7262.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

```python
from nitbw_as7262 import AS7262
```

## Schnellstart

```python
from machine import I2C, Pin
from nitbw_as7262 import AS7262
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = AS7262(i2c, led=True)

while True:
    roh = sensor.messen_roh()
    for kanal, wert in roh.items():
        print("{}: {}".format(kanal, wert))
    print("---")
    time.sleep(1)
```

## API-Referenz

### Konstruktor

```python
AS7262(i2c, led=False,
       integrationszeit=50, gain=1)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `i2c` | I2C | - | Initialisiertes I2C-Objekt |
| `led` | bool | `False` | True schaltet die LED ein |
| `integrationszeit` | int | `50` | Messzeit in Einheiten von 2.8 ms (1-255) |
| `gain` | int | `1` | 0=1x, 1=3.7x, 2=16x, 3=64x |

### Konfiguration

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `set_integrationszeit(wert)` | - | Integrationszeit 1-255 einstellen |
| `set_gain(gain)` | - | Verstaerkung 0-3 einstellen |
| `set_led(an)` | - | LED ein (True) oder aus (False) |
| `temperatur()` | int | Sensortemperatur in Grad Celsius |

### Messungen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `messen_roh()` | dict | 6 Rohwerte als Dictionary |
| `messen_roh_liste()` | list | 6 Rohwerte als Liste |
| `messen_kalibriert()` | dict | 6 kalibrierte Float-Werte als Dictionary |
| `messen_kalibriert_liste()` | list | 6 kalibrierte Float-Werte als Liste |
| `dominanter_kanal()` | str | Name des staerksten Kanals |

## Beispiele

- `beispiel_as7262.py`: Rohwerte und dominanten Kanal ausgeben
- `beispiel_as7262_kalibriert.py`: Kalibrierte Werte und Listenausgabe

### Zusatzbeispiele

1. Nur Rohwerte als Liste (fuer ML):
```python
from machine import I2C, Pin
from nitbw_as7262 import AS7262

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = AS7262(i2c, led=True)
features = sensor.messen_roh_liste()
print(features)  # [violett, blau, gruen, gelb, orange, rot]
```

2. Integrationszeit und Gain anpassen:
```python
sensor = AS7262(i2c, integrationszeit=100, gain=2)
# Laengere Messung, hoehere Empfindlichkeit
```

3. Bestehendes I2C-Objekt weiterverwenden:
```python
from machine import I2C, Pin
i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)
sensor = AS7262(i2c, led=True)
```

Praktische Hinweise / Fehlersuche:

- `AS7262 nicht gefunden`: Verkabelung pruefen, I2C-Scanner nutzen.
- Messwerte immer Null: LED einschalten oder Gain erhoehen.
- Werte uebersteuert (65535): Gain reduzieren oder Integrationszeit verringern.
- Langsame Messung: Integrationszeit senken (z. B. auf 20).

## Lizenz

MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
