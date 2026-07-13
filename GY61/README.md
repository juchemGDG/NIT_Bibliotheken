# NIT Bibliothek: GY61

## Beschreibung

Diese Bibliothek bindet den GY-61 mit ADXL335 als analogen 3-Achsen-
Beschleunigungssensor am ESP32 ein. Die drei ADC-Signale werden in
Rohwerte, Spannungen, Beschleunigung in g sowie m/s^2 umgerechnet.
Zusatzfunktionen fuer Neigungswinkel, Ruhelage-Kalibrierung und
Bewegungsdetektion sind direkt enthalten.

## Features

- Einfache Initialisierung mit drei ADC-Pins (XOUT, YOUT, ZOUT)
- Rohwertmessung aller Achsen fuer didaktische ADC-Analyse
- Umrechnung von Rohwerten in Spannung pro Achse
- Beschleunigungsausgabe in g
- Beschleunigungsausgabe in m/s^2
- Berechnung des Beschleunigungsbetrags (Vektorlaenge)
- Neigungsberechnung (Pitch/Roll) in Grad
- Ruhelage-Kalibrierung mit Mittelwertbildung
- Manuelles Setzen von Offset-Werten
- Manuelles Setzen achsweiser Sensitivitaeten
- Einfache Bewegungsdetektion ueber 1g-Abweichung
- Kompakte Gesamtausgabe als Dictionary

## Hardware

### Sensor

- GY-61 Breakout mit ADXL335 (3-Achsen Analog-Beschleunigung)
- Versorgung typischerweise 3.3 V bis 5 V (modulabhaengig)
- Messbereich ADXL335: typischerweise +-3 g

### Anschlussprinzip

Der GY-61 liefert pro Achse ein analoges Spannungssignal:

- `XOUT` -> ADC-Pin am ESP32
- `YOUT` -> ADC-Pin am ESP32
- `ZOUT` -> ADC-Pin am ESP32
- `VCC` -> 3.3V (empfohlen)
- `GND` -> GND

Hinweise:

- Fuer reproduzierbare Messwerte ist eine saubere 3.3V-Versorgung wichtig.
- ADC-Pins 34, 35, 32 (Beispiel) sind reine Eingaenge und gut geeignet.
- ADC2-Pins koennen bei gleichzeitigem WLAN-Betrieb eingeschraenkt sein.

## Anschluss

Beispielverkabelung fuer ESP32:

```text
GY-61 (ADXL335)    ESP32
VCC            ->  3.3V
GND            ->  GND
XOUT           ->  GPIO34 (ADC)
YOUT           ->  GPIO35 (ADC)
ZOUT           ->  GPIO32 (ADC)
```

## Installation

Datei `nitbw_gy61.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

Import:

```python
from nitbw_gy61 import GY61
```

## Schnellstart

```python
from nitbw_gy61 import GY61
import time

sensor = GY61(x_pin=34, y_pin=35, z_pin=32)

while True:
    ax, ay, az = sensor.lesen_g()
    print("X={:+.2f}g  Y={:+.2f}g  Z={:+.2f}g".format(ax, ay, az))
    time.sleep(0.5)
```

## API-Referenz

### Konstruktor

```python
GY61(x_pin, y_pin, z_pin, adc_bits=12, vref=3.3, sensitivitaet_v_g=0.3, attenuation="11db")
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `x_pin` | int | - | GPIO-Pin fuer XOUT (ADC) |
| `y_pin` | int | - | GPIO-Pin fuer YOUT (ADC) |
| `z_pin` | int | - | GPIO-Pin fuer ZOUT (ADC) |
| `adc_bits` | int | 12 | ADC-Aufloesung (9-12) |
| `vref` | float | 3.3 | Referenzspannung in Volt |
| `sensitivitaet_v_g` | float | 0.3 | Startwert Empfindlichkeit in V/g |
| `attenuation` | str | "11db" | ADC-Daempfung: "0db", "2.5db", "6db", "11db" |

### Methodenuebersicht

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `lesen_roh()` | tuple | Rohwerte `(x_raw, y_raw, z_raw)` |
| `lesen_spannung()` | tuple | Spannungen `(vx, vy, vz)` in Volt |
| `lesen_g()` | tuple | Beschleunigung `(ax, ay, az)` in g |
| `lesen_ms2()` | tuple | Beschleunigung `(ax, ay, az)` in m/s^2 |
| `betrag_g()` | float | Betrag des Beschleunigungsvektors in g |
| `neigung_grad()` | tuple | `(pitch, roll)` in Grad |
| `ist_bewegt(schwelle_g=0.15)` | bool | Bewegungserkennung ueber 1g-Abweichung |
| `set_offsets(offset_x, offset_y, offset_z)` | - | Setzt Offsets in Volt |
| `set_sensitivitaet(sens_x, sens_y, sens_z)` | - | Setzt Sensitivitaet je Achse in V/g |
| `kalibrieren_ruhelage(samples=200, erwartung_g=(0,0,1))` | tuple | Offset-Kalibrierung in definierter Ruhelage |
| `daten()` | dict | Kompakte Gesamtausgabe aller Kernwerte |

## Beispiele

- `beispiel_gy61.py`: Grundmessung mit g, m/s^2 und Neigungswinkeln
- `beispiel_gy61_kalibrierung.py`: Ruhelage kalibrieren und Offsets setzen
- `beispiel_gy61_bewegung.py`: Bewegungsdetektion ueber Betragsschwelle

1. Neigungsausgabe fuer Robotik oder Balancing:
```python
from nitbw_gy61 import GY61

sensor = GY61(34, 35, 32)
pitch, roll = sensor.neigung_grad()
print("Pitch={:+.1f} deg, Roll={:+.1f} deg".format(pitch, roll))
```

2. Eigene Sensitivitaet und Offsets setzen:
```python
from nitbw_gy61 import GY61

sensor = GY61(34, 35, 32)
sensor.set_sensitivitaet(0.300, 0.302, 0.298)
sensor.set_offsets(1.645, 1.652, 1.640)
print(sensor.lesen_g())
```

3. Komplette Datenausgabe als Dictionary:
```python
from nitbw_gy61 import GY61

sensor = GY61(34, 35, 32)
werte = sensor.daten()
print(werte["x_raw"], werte["vx"], werte["ax"], werte["pitch"])
```

### Fehlersuche und Hinweise

- **Achsenwerte driften stark**: Sensorversorgung stabilisieren (3.3V), Kabel kurz halten.
- **Ruhewerte nicht bei ca. X=0, Y=0, Z=1 g**: `kalibrieren_ruhelage()` ausfuehren.
- **Sehr verrauschte Daten**: Mittelwertbildung im Anwendercode nutzen (z. B. 10 Samples).
- **Unplausible Spannungen**: ADC-Daempfung pruefen (`attenuation="11db"` ist meist robust).
- **WLAN aktiv und ADC-Werte fehlen**: Andere ADC-Pins pruefen (ADC1 bevorzugen).

## Lizenz

MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
