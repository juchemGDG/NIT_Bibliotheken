# NIT Bibliothek: Puls

## Beschreibung
Die Bibliothek `nitbw_puls.py` liest einen analogen Funduino-Pulssensor am ESP32 ueber ADC aus. Sie stellt direkte Rohwerte fuer Visualisierung und Diagnose bereit. Zusaetzlich enthaelt sie eine Funktion zur Bestimmung der Herzfrequenz in BPM auf Basis einer dynamischen Schwellwerterkennung. Die Implementierung ist fuer Unterricht und schnelle Experimente mit MicroPython ausgelegt.

## Features
- Direkte ADC-Rohwertausgabe mit `lesen_roh()`
- Glaettung ueber Mittelwertbildung mit `lesen_roh_mittelwert()`
- BPM-Messung ueber Zeitfenster mit `messen_puls()`
- Dynamische Schwellwertlogik fuer robustere Schlagerkennung
- DC-Anteil-Entfernung im Signal (einfaches High-Pass-Verhalten)
- Plausibilitaetspruefung der Schlagintervalle
- Konfigurierbare Messparameter: Dauer, Sampling, Sperrzeit, Mindestschwelle
- ADC-Konfiguration mit Aufloesung (9-12 Bit)
- Kompatibel mit analogen Pulssensor-Modulen am ESP32
- Didaktisch gut nutzbar fuer Signalverarbeitung im Unterricht

## Hardware
- Sensor: Funduino Pulssensor (analog, 3.3V-kompatibel)
- MCU: ESP32 mit MicroPython
- Signalpin: an einen ADC-faehigen GPIO (z. B. 32, 33, 34, 35)
- Versorgung: 3.3V und GND
- Hinweis:
  - Viele ESP32-Boards haben ADC-Rauschen; stabile Versorgung verbessert das Signal.
  - Bei Bewegung des Fingers schwanken Rohwerte stark.
  - Fuer reproduzierbare Messung Finger ruhig und gleichmaessig auflegen.

## Anschluss
Verkabelungsbeispiel fuer ESP32:

```text
Funduino Pulssensor    ESP32
VCC               ->   3V3
GND               ->   GND
SIG               ->   GPIO34 (ADC)
```

## Installation
- Datei `nitbw_puls.py` auf den ESP32 kopieren (Root oder `lib/`).
- Import im Skript:

```python
from nitbw_puls import Pulssensor
```

## Schnellstart
```python
from nitbw_puls import Pulssensor
import time

sensor = Pulssensor(adc_pin=34)

while True:
    bpm = sensor.messen_puls(dauer_s=10)
    if bpm > 0:
        print("Puls: {:.1f} BPM".format(bpm))
    else:
        print("Kein stabiler Puls erkannt")
    time.sleep(1)
```

## API-Referenz
Konstruktor: `Pulssensor(adc_pin, adc_bits=12, attenuation=None)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `adc_pin` | `int` | - | ADC-GPIO des Sensorsignals |
| `adc_bits` | `int` | `12` | ADC-Aufloesung (9 bis 12 Bit) |
| `attenuation` | `ADC.ATTN_*` | `None` | ADC-Abschwaechung, `None` nutzt wenn moeglich 11 dB |

Methodenuebersicht:
- `lesen_roh()` -> `int`
- `lesen_roh_mittelwert(samples=8, pause_ms=2)` -> `int`
- `messen_puls(dauer_s=10, sample_ms=10, sperrzeit_ms=300, mindest_schwelle=18)` -> `float` (BPM oder `-1`)

## Beispiele
Dateien im Ordner:
- `PULS/beispiel_puls.py`
- `PULS/beispiel_puls_bpm.py`

Snippet 1: Einzelnen Rohwert lesen
```python
from nitbw_puls import Pulssensor
sensor = Pulssensor(adc_pin=34)
print(sensor.lesen_roh())
```

Snippet 2: Glaettung ueber Mittelwert
```python
from nitbw_puls import Pulssensor
sensor = Pulssensor(adc_pin=34)
wert = sensor.lesen_roh_mittelwert(samples=16, pause_ms=2)
print("Glaettung:", wert)
```

Snippet 3: Schnelle BPM-Messung (6 Sekunden)
```python
from nitbw_puls import Pulssensor
sensor = Pulssensor(adc_pin=34)
bpm = sensor.messen_puls(dauer_s=6)
print("BPM:", bpm)
```

Snippet 4: Robustere BPM-Messung (15 Sekunden)
```python
from nitbw_puls import Pulssensor
sensor = Pulssensor(adc_pin=34)
bpm = sensor.messen_puls(dauer_s=15, sample_ms=8, sperrzeit_ms=280)
print("BPM:", bpm)
```

Praktische Hinweise/Fehlersuche:
- `-1` als BPM: Fingerkontakt verbessern, Messdauer vergroessern, Bewegung reduzieren.
- Sehr springende Rohwerte: Versorgung und Masseverbindung pruefen.
- Unplausibel hohe BPM: `sperrzeit_ms` erhoehen (z. B. 320-360).
- Keine Aenderung im Rohsignal: Richtigen ADC-Pin und Verkabelung kontrollieren.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
