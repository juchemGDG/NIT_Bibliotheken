# NIT Bibliothek: ADS1015

## Beschreibung
Die Bibliothek `nitbw_ads1015.py` stellt eine kompakte ADS1015-Anbindung fuer ESP32 mit MicroPython bereit. Sie unterstuetzt Single-Ended- und Differenzialmessungen ueber I2C und liefert die Werte direkt in Volt oder als Rohdaten. Gain, Datenrate und Messmodus koennen fuer unterschiedliche Sensorsignale angepasst werden.

## Features
- Single-Ended-Messung auf A0 bis A3
- Differenzialmessung (A0-A1, A0-A3, A1-A3, A2-A3)
- 12-bit Rohwertausgabe
- Spannungsumrechnung in Volt
- Einstellbarer Gain (PGA)
- Einstellbare Datenrate bis 3300 SPS
- Single-Shot- und Continuous-Mode
- Sammelabfrage aller vier Kanaele mit `read_all()`
- LSB-Berechnung ueber `get_lsb_mv()`
- Direkte Registeransteuerung ohne Fremdbibliotheken

## Hardware
- Sensor: ADS1015 Breakout-Board
- I2C-Adresse: `0x48` bis `0x4B` (Standard: `0x48`)
- Aufloesung: 12 Bit
- Kanaele: 4 analoge Eingaenge
- Hinweise:
  - Eingangsbereich wird ueber den gewaehlten PGA begrenzt.
  - Viele Module besitzen Pull-ups fuer SDA/SCL bereits on-board.

## Anschluss
Beispielverkabelung fuer ESP32:

- `VCC -> 3V3`
- `GND -> GND`
- `SCL -> GPIO 22`
- `SDA -> GPIO 21`
- `A0..A3 -> Analoge Sensorsignale`

## Installation
- Datei `nitbw_ads1015.py` auf den ESP32 kopieren (Root oder `lib/`).
- Import in deinem Programm: `from nitbw_ads1015 import ADS1015`

## Schnellstart
```python
from machine import I2C, Pin
from nitbw_ads1015 import ADS1015

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
adc = ADS1015(i2c, addr=0x48)

spannung = adc.read_voltage(0)
print(f"A0: {spannung:.3f} V")
```

## API-Referenz
Konstruktor: `ADS1015(i2c, addr=0x48, pga=PGA_4_096V, data_rate=DR_1600)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `i2c` | `machine.I2C` | - | Initialisierter I2C-Bus |
| `addr` | `int` | `0x48` | Sensoradresse |
| `pga` | `int` | `PGA_4_096V` | Vollbereich/Verstaerkung |
| `data_rate` | `int` | `DR_1600` | Datenrate |

Wichtige Methoden:
- `set_gain(pga)`
- `set_data_rate(data_rate)`
- `set_mode(mode)`
- `get_lsb_mv()` -> `float`
- `read_raw(channel=0)` -> `int`
- `read_voltage(channel=0)` -> `float`
- `read_diff_raw(mux=MUX_DIFF_0_1)` -> `int`
- `read_diff_voltage(mux=MUX_DIFF_0_1)` -> `float`
- `read_all()` -> `(ch0, ch1, ch2, ch3)` in Volt

## Beispiele
Dateien im Ordner:
- `ADS1015/beispiel_ads1015.py`
- `ADS1015/beispiel_ads1015_differenzial.py`

Snippet 1: Kanal A0 auslesen
```python
v = adc.read_voltage(0)
print(f"A0: {v:.3f} V")
```

Snippet 2: Alle Kanaele lesen
```python
ch0, ch1, ch2, ch3 = adc.read_all()
print(ch0, ch1, ch2, ch3)
```

Snippet 3: Differenzial A0-A1
```python
vd = adc.read_diff_voltage(ADS1015.MUX_DIFF_0_1)
print(f"Diff A0-A1: {vd:.5f} V")
```

Snippet 4: Gain an kleinen Messbereich anpassen
```python
adc.set_gain(ADS1015.PGA_0_512V)
print(adc.read_voltage(0))
```

Praktische Hinweise/Fehlersuche:
- Keine Werte: I2C-Adresse und Verkabelung pruefen.
- Scheinbar abgeschnittene Werte: PGA-Bereich vergroessern.
- Sehr verrauschte Messung: Datenrate reduzieren und Mittelwert bilden.
- Negative Werte bei Single-Ended: Signalreferenz/GND pruefen.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
