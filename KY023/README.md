# NIT Bibliothek: KY023 (Joystick-Modul)

## Beschreibung

Diese Bibliothek ermoeglicht die Auswertung des KY-023 Joystick-Moduls
am ESP32 mit MicroPython. Das Modul liefert zwei analoge Achsen (VRX/VRY)
und einen digitalen Taster (SW). Die Bibliothek bietet Rohwerte,
normierte Werte, Richtungsdetektion (8-Wege), Winkel/Betrag und eine
Kalibrierung der Mittelstellung fuer reproduzierbare Ergebnisse.

## Features

- Auslesen von VRX und VRY ueber ADC
- Auslesen von SW (Taster), aktiv-low oder aktiv-high
- Normierung auf Bereich -1.0 bis +1.0
- Kalibrierung der Mittelstellung mit Mittelwert ueber mehrere Samples
- Einstellbare Totzone (deadzone) gegen Zittern um die Mittelstellung
- 8-Wege-Richtungslogik: MITTE, OBEN, UNTEN, LINKS, RECHTS und Diagonalen
- Betrag der Auslenkung (0.0 bis 1.0)
- Winkelberechnung in Grad (0 bis 360)
- Einfache Statusdaten als Dictionary fuer Debug-Ausgaben
- Optionales Invertieren von X- und Y-Achse

## Hardware

### KY-023 Modul

Typische Pins am Modul:

- `VRX`: Analoge X-Achse
- `VRY`: Analoge Y-Achse
- `SW`: Taster-Ausgang
- `+`: Versorgung (3.3V)
- `GND`: Masse

Hinweise:

- Betrieb am ESP32 mit 3.3V
- Fuer VRX/VRY ADC-faehige Pins verwenden
- Typische ADC-Pins am ESP32: 32, 33, 34, 35, 36, 39
- SW wird typischerweise mit Pull-up gelesen (gedrueckt = Low)

## Anschluss

Beispielverkabelung fuer ESP32:

- KY023 `+` -> ESP32 `3V3`
- KY023 `GND` -> ESP32 `GND`
- KY023 `VRX` -> ESP32 `GPIO34` (ADC)
- KY023 `VRY` -> ESP32 `GPIO35` (ADC)
- KY023 `SW` -> ESP32 `GPIO32` (Digital IN)

## Installation

1. Datei `nitbw_ky023.py` in das Projekt auf den ESP32 kopieren.
2. Im Skript importieren:

```python
from nitbw_ky023 import KY023
```

## Schnellstart

```python
from nitbw_ky023 import KY023
import time

joystick = KY023(vrx_pin=34, vry_pin=35, sw_pin=32)
joystick.kalibrieren_mitte(samples=100)

while True:
    d = joystick.daten()
    print(
        "x={:+.2f} y={:+.2f} richtung={} taster={}".format(
            d["x"], d["y"], d["richtung"], d["sw"]
        )
    )
    time.sleep(0.2)
```

## API-Referenz

### Konstruktor

```python
KY023(
    vrx_pin,
    vry_pin,
    sw_pin,
    adc_bits=12,
    deadzone=0.12,
    invert_x=False,
    invert_y=False,
    button_active_low=True,
)
```

| Parameter | Typ | Beschreibung |
|---|---|---|
| `vrx_pin` | int | ADC-Pin fuer X-Achse |
| `vry_pin` | int | ADC-Pin fuer Y-Achse |
| `sw_pin` | int | Digital-Pin fuer Taster |
| `adc_bits` | int | ADC-Aufloesung (9-12) |
| `deadzone` | float | Totzone 0.0 bis 1.0 |
| `invert_x` | bool | X-Achse invertieren |
| `invert_y` | bool | Y-Achse invertieren |
| `button_active_low` | bool | True bei Pull-up/gegen GND |

### Methodenuebersicht

- `lesen_roh()` -> Rohdaten `x_raw`, `y_raw`, `sw`
- `lesen_normiert()` -> normierte Daten `x`, `y`, plus Rohdaten und `sw`
- `kalibrieren_mitte(samples=100)` -> kalibriert `center_x` und `center_y`
- `set_deadzone(deadzone)` -> setzt neue Totzone
- `gedrueckt()` -> True wenn Taster gedrueckt
- `betrag()` -> Auslenkung 0.0 bis 1.0
- `winkel_grad()` -> Winkel 0 bis 360 Grad
- `richtung()` -> 8-Wege-Richtung oder `MITTE`
- `daten()` -> kompaktes Status-Dictionary

## Beispiele

Dateien im Ordner `KY023`:

- `beispiel_ky023.py`: Grundmessung mit Rohdaten + normierten Werten
- `beispiel_ky023_richtung.py`: Richtungsdetektion und Taster-Ereignisse
- `beispiel_ky023_kalibrierung.py`: Kalibrierung, Totzone, Winkel/Betrag

Spezielle Snippets:

```python
# Nur Taster pruefen
from nitbw_ky023 import KY023
import time

j = KY023(34, 35, 32)
while True:
    if j.gedrueckt():
        print("Taste gedrueckt")
    time.sleep(0.05)
```

```python
# Richtung statt Rohwerte
from nitbw_ky023 import KY023
import time

j = KY023(34, 35, 32, deadzone=0.2)
j.kalibrieren_mitte()
while True:
    print(j.richtung())
    time.sleep(0.1)
```

```python
# Invertierte Y-Achse
from nitbw_ky023 import KY023

j = KY023(34, 35, 32, invert_y=True)
print(j.lesen_normiert())
```

## Lizenz

MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
