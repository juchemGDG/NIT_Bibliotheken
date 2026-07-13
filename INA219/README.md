# NIT Bibliothek: INA219

## Beschreibung
Die Bibliothek `nitbw_ina219.py` bindet das INA219-Breakout fuer ESP32 mit MicroPython an. Sie erfasst Busspannung, Shunt-Spannung, Strom und Leistung ueber I2C und stellt daraus auch die Lastspannung bereit. Die Implementierung arbeitet direkt auf Registerebene und kommt ohne externe Pakete aus.

## Features
- Messung der Busspannung in Volt
- Messung der Shunt-Spannung in mV und V
- Strommessung in mA und A
- Leistungsmessung in mW und W
- Lastspannung aus Bus + Shunt berechnet
- Kompakte Sammelmessung ueber `read_all()`
- Konfigurierbarer Spannungs- und Gain-Bereich
- Konfigurierbare ADC-Aufloesung und Messmodus
- Frei kalibrierbar ueber Shunt-Widerstand und erwarteten Maximalstrom
- Statusabfrage fuer `conversion_ready()` und `overflow()`

## Hardware
- Sensor: INA219 Breakout-Board
- I2C-Adresse: `0x40` bis `0x4F` (standardmaessig `0x40`)
- Versorgung: 3.3V oder 5V (je nach Breakout, Logikpegel beachten)
- Shunt: Viele Module enthalten `0.1 Ohm`
- Hinweise:
  - I2C-Pull-ups sind oft bereits auf dem Breakout vorhanden.
  - Fuer gute Genauigkeit `shunt_ohms` und `max_expected_current` passend setzen.

## Anschluss
Beispielverkabelung fuer ESP32:

- `VCC -> 3V3`
- `GND -> GND`
- `SCL -> GPIO 22`
- `SDA -> GPIO 21`
- Lastpfad ueber das Modul:
  - Versorgung `+` -> `VIN+`
  - `VIN-` -> Last `+`
  - Last `-` -> Versorgung `-`

## Installation
- Datei `nitbw_ina219.py` auf den ESP32 kopieren (Root oder `lib/`).
- In Skripten importieren mit: `from nitbw_ina219 import INA219`

## Schnellstart
```python
from machine import I2C, Pin
from nitbw_ina219 import INA219

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = INA219(i2c, addr=0x40, shunt_ohms=0.1, max_expected_current=2.0)

bus_v, shunt_mv, current_ma, power_mw, load_v = sensor.read_all()
print(f"Bus: {bus_v:.3f} V")
print(f"Strom: {current_ma:.2f} mA")
print(f"Leistung: {power_mw:.2f} mW")
```

## API-Referenz
Konstruktor: `INA219(i2c, addr=0x40, shunt_ohms=0.1, max_expected_current=2.0)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `i2c` | `machine.I2C` | - | Initialisierter I2C-Bus |
| `addr` | `int` | `0x40` | Sensoradresse |
| `shunt_ohms` | `float` | `0.1` | Shunt-Widerstand in Ohm |
| `max_expected_current` | `float` | `2.0` | Erwarteter Maximalstrom in A |

Oeffentliche Methoden (Auswahl):
- `reset()`
- `configure(bus_range, gain, bus_adc, shunt_adc, mode)`
- `calibrate(shunt_ohms=None, max_expected_current=None)`
- `conversion_ready()` -> `bool`
- `overflow()` -> `bool`
- `read_shunt_voltage_v()` / `read_shunt_voltage_mv()`
- `read_bus_voltage_v()`
- `read_load_voltage_v()`
- `read_current_a()` / `read_current_ma()`
- `read_power_w()` / `read_power_mw()`
- `read_all()` -> `(bus_v, shunt_mv, current_ma, power_mw, load_v)`

## Beispiele
Dateien im Ordner:
- `INA219/beispiel_ina219.py`
- `INA219/beispiel_ina219_lastprofil.py`

Snippet 1: Zyklisches Auslesen
```python
from machine import I2C, Pin
from time import sleep
from nitbw_ina219 import INA219

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = INA219(i2c)

while True:
    bus_v, shunt_mv, current_ma, power_mw, _ = sensor.read_all()
    print(bus_v, shunt_mv, current_ma, power_mw)
    sleep(1)
```

Snippet 2: Eigene Kalibrierung fuer kleinen Strombereich
```python
sensor.calibrate(shunt_ohms=0.1, max_expected_current=0.5)
print(f"Strom: {sensor.read_current_ma():.2f} mA")
```

Snippet 3: Nur Leistung erfassen
```python
leistung_mw = sensor.read_power_mw()
print(f"Leistung: {leistung_mw:.1f} mW")
```

Snippet 4: Auf Ueberlauf pruefen
```python
if sensor.overflow():
    print("Messbereich zu klein, Gain/Kalibrierung pruefen")
```

Praktische Hinweise/Fehlersuche:
- Keine I2C-Antwort: Verkabelung und Adresse mit I2C-Scan pruefen.
- Strom immer 0: Lastpfad (`VIN+`/`VIN-`) und Kalibrierung kontrollieren.
- Unplausible Werte: Shunt-Widerstand auf dem Modul pruefen und richtig setzen.
- Haeufiger Overflow: Gain oder Strombereich anpassen.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
