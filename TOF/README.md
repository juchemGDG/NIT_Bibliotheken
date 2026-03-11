# NIT Bibliothek: TOF (VL53L0X)

## Beschreibung

Diese Bibliothek ermoeglicht die Entfernungsmessung mit dem VL53L0X
Time-of-Flight Lasersensor am ESP32 ueber I2C. Der Sensor misst
Entfernungen per Laser-Lichtlaufzeit mit bis zu 2 Meter Reichweite.
Vier Messmodi erlauben den Kompromiss zwischen Geschwindigkeit, Genauigkeit
und Reichweite, mehrere Sensoren koennen am selben I2C-Bus betrieben werden.

## Features

- Entfernungsmessung in mm und cm (Laser Time-of-Flight)
- Rueckrechnung der Lichtlaufzeit in Nanosekunden (Physik-Bezug)
- Statusabfrage der letzten Messung (Signal, Sigma, Phase)

Vier Messmodi:

- **SCHNELL**: 20 ms, ~60 cm Reichweite, schnelle Hinderniserkennung
- **STANDARD**: 33 ms, ~120 cm Reichweite, allgemeine Messung (Default)
- **GENAU**: 200 ms, ~120 cm Reichweite, hohe Praezision
- **LANGSTRECKE**: 33 ms, ~200 cm Reichweite, maximale Distanz

Filterfunktionen (bekannt aus der Ultraschall-Bibliothek):

- **Mittelwert**: Arithmetisches Mittel aus n Messungen
- **Median**: Robuster gegen Ausreisser
- **Bereich**: Minimum, Maximum und Mittelwert (Streuung sichtbar)

Schwellenwert- und Anwendungslogik:

- **ist_naeher_als(mm)**: Einfache Naeherungserkennung (Bool)
- **zone(nah, mittel)**: Drei-Zonen-Klassifikation (nah / mittel / fern)
- **geschwindigkeit(intervall_ms)**: Annaeherungsgeschwindigkeit in mm/s

Sensor-Konfiguration:

- **set_adresse()**: I2C-Adresse aendern (fuer mehrere Sensoren am Bus)
- **set_timing_budget()**: Timing Budget manuell in µs setzen (Expertenmodus)

## Hardware

### VL53L0X Module

| Modul | Bemerkung |
|---|---|
| GY-VL53L0X (GY-530) | Gaengigstes Breakout, 3.3 V Regler + Levelshifter onboard |
| Adafruit VL53L0X | Hochwertig, Qwiic/STEMMA-kompatibel |
| CJMCU-530 | Guenstige China-Variante |

Alle Module arbeiten mit 3.3 V Logik am ESP32 (I2C-Levelshifter ist auf
den meisten Breakouts bereits integriert).

### Technische Daten

- Messbereich: 30 mm bis ca. 2000 mm (abhaengig vom Modus und Zielobjekt)
- Genauigkeit: ca. ±3 % (typisch, bei gutem Signal)
- Messwinkel: 25° (Sichtfeld, Field of View)
- I2C-Adresse: 0x29 (Standard), aenderbar per Software
- Betriebsspannung: 2.6 V bis 3.5 V (Module meist mit 5 V-Eingang + Regler)

### XSHUT-Pin (fuer Mehrfachsensoren)

Der XSHUT-Pin schaltet den Sensor in den Hardware-Standby:
- **LOW**: Sensor aus (nicht am I2C-Bus)
- **HIGH oder offen**: Sensor aktiv

Dies wird benoetigt, wenn mehrere VL53L0X am selben I2C-Bus betrieben
werden sollen, da alle Sensoren mit derselben Standard-Adresse (0x29) starten.

## Anschluss

### Ein Sensor (Standard)

```text
VL53L0X            ESP32
VIN        -----> 3.3V
SDA        -----> GPIO 21
SCL        -----> GPIO 22
GND        -----> GND
XSHUT      (offen lassen oder an 3.3V)
```

### Zwei Sensoren (mit XSHUT)

```text
VL53L0X #1         ESP32           VL53L0X #2
VIN  ------------> 3.3V  <--------- VIN
SDA  ------------> GPIO 21 <------- SDA     (gleicher Bus!)
SCL  ------------> GPIO 22 <------- SCL     (gleicher Bus!)
GND  ------------> GND   <--------- GND
XSHUT -----------> GPIO 25
                   GPIO 26 <------- XSHUT
```

**Warum XSHUT?** Alle VL53L0X starten mit Adresse 0x29. Ueber XSHUT
werden die Sensoren einzeln eingeschaltet und jedem eine eigene Adresse
zugewiesen. Ohne XSHUT wuerden sich die Sensoren gegenseitig stoeren.

**Ablauf bei zwei Sensoren:**
1. Beide XSHUT auf LOW → beide Sensoren sind aus
2. XSHUT von Sensor 1 auf HIGH → wacht bei 0x29 auf
3. Adresse von Sensor 1 auf z. B. 0x30 aendern
4. XSHUT von Sensor 2 auf HIGH → wacht bei 0x29 auf (kein Konflikt!)
5. Beide Sensoren sind bereit mit verschiedenen Adressen

Empfohlene GPIO-Pins am ESP32: 21 (SDA), 22 (SCL), 25/26/27 (XSHUT).

## Installation

Datei `nitbw_tof.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

Anschliessend kann die Bibliothek importiert werden:

```python
from nitbw_tof import TOF
```

## Schnellstart

```python
from machine import I2C, Pin
from nitbw_tof import TOF
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = TOF(i2c)

while True:
    mm = sensor.messen_mm()
    if mm > 0:
        print("Entfernung: {} mm".format(mm))
    else:
        print("Kein Objekt erkannt")
    time.sleep(0.5)
```

## API-Referenz

### Konstruktor

```python
TOF(i2c, addr=0x29, xshut=None)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `i2c` | I2C | - | I2C-Bus-Objekt (z. B. `I2C(0, scl=Pin(22), sda=Pin(21))`) |
| `addr` | int | 0x29 | I2C-Adresse des Sensors |
| `xshut` | int/None | None | GPIO-Pin fuer XSHUT (optional, fuer Mehrfachsensoren) |

### Methoden

#### Messmodi

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `set_modus(modus)` | - | Messmodus setzen (siehe Modus-Konstanten) |
| `lese_modus()` | str | Aktuellen Modus als String zurueck ('schnell', 'standard', …) |

#### Modus-Konstanten

| Konstante | Timing Budget | Reichweite | Genauigkeit | Einsatz |
|---|---|---|---|---|
| `TOF.SCHNELL` | 20 ms | ~60 cm | ±5 % | Schnelle Hinderniserkennung |
| `TOF.STANDARD` | 33 ms | ~120 cm | ±3 % | Allgemeine Messung (Default) |
| `TOF.GENAU` | 200 ms | ~120 cm | ±1 % | Praezise Abstandsmessung |
| `TOF.LANGSTRECKE` | 33 ms | ~200 cm | ±5 % | Maximale Reichweite |

#### Grundmessungen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `messen_mm()` | int | Entfernung in Millimetern (oder -1 bei Fehler) |
| `messen_cm()` | float | Entfernung in Zentimetern (oder -1 bei Fehler) |
| `messen_laufzeit()` | int | Lichtlaufzeit hin+zurueck in Nanosekunden (oder -1) |
| `status()` | str | Status der letzten Messung als lesbarer Text |

#### Filterfunktionen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `messen_mittelwert(n=5)` | int | Mittelwert aus n Messungen in mm |
| `messen_median(n=5)` | int | Median aus n Messungen in mm |
| `messen_bereich(n=5)` | tuple | (min, max, mittelwert) in mm |

#### Schwellenwertlogik

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `ist_naeher_als(mm)` | bool | True wenn Objekt naeher als Schwellenwert |
| `zone(nah=100, mittel=500)` | str | 'nah', 'mittel', 'fern' oder 'fehler' |
| `geschwindigkeit(intervall_ms=500)` | float | Geschwindigkeit in mm/s |

#### Sensor-Konfiguration

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `set_adresse(neue_adresse)` | - | I2C-Adresse aendern (fluechtig, bis Neustart) |
| `lese_adresse()` | int | Aktuelle I2C-Adresse |
| `set_timing_budget(us)` | - | Timing Budget manuell in µs setzen (Expertenmodus) |
| `lese_timing_budget()` | int | Aktuelles Timing Budget in µs |

## Beispiele

- `beispiel_tof.py`: Grundlegende Entfernungsmessung in mm/cm mit Statusanzeige
- `beispiel_tof_modi.py`: Alle vier Messmodi vergleichen (Streuung, Reichweite)
- `beispiel_tof_mehrere_sensoren.py`: Zwei Sensoren am selben I2C-Bus mit XSHUT

### Zusatzbeispiele

1. Modus wechseln – Genau vs. Schnell:
```python
from machine import I2C, Pin
from nitbw_tof import TOF
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = TOF(i2c)

# Genauer Modus fuer praezise Messung
sensor.set_modus(TOF.GENAU)
print("Modus:", sensor.lese_modus())
print("Genau:  {} mm".format(sensor.messen_mm()))

# Schneller Modus fuer Echtzeit-Erkennung
sensor.set_modus(TOF.SCHNELL)
print("Modus:", sensor.lese_modus())
print("Schnell: {} mm".format(sensor.messen_mm()))
```

2. Zwei Sensoren mit XSHUT-Pins einrichten:
```python
from machine import I2C, Pin
from nitbw_tof import TOF
import time

# Beide Sensoren ausschalten
Pin(25, Pin.OUT, value=0)
Pin(26, Pin.OUT, value=0)
time.sleep_ms(50)

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Sensor 1: aufwecken, Adresse aendern auf 0x30
sensor_l = TOF(i2c, addr=0x30, xshut=25)

# Sensor 2: aufwecken, bleibt bei 0x29
sensor_r = TOF(i2c, addr=0x29, xshut=26)

while True:
    print("L: {} mm  R: {} mm".format(
        sensor_l.messen_mm(), sensor_r.messen_mm()))
    time.sleep(0.3)
```

3. Naeherungserkennung mit dem schnellen Modus:
```python
from machine import I2C, Pin
from nitbw_tof import TOF
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = TOF(i2c)
sensor.set_modus(TOF.SCHNELL)

while True:
    if sensor.ist_naeher_als(200):
        print("Objekt naeher als 200 mm!")
    time.sleep(0.1)
```

4. Langstrecke – maximale Reichweite ausloten:
```python
from machine import I2C, Pin
from nitbw_tof import TOF
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = TOF(i2c)
sensor.set_modus(TOF.LANGSTRECKE)

while True:
    mm = sensor.messen_median(n=5)
    if mm > 0:
        print("Langstrecke: {:4d} mm  ({:.1f} cm)".format(mm, mm / 10))
    else:
        print("Kein Echo (Status: {})".format(sensor.status()))
    time.sleep(1)
```

5. Streuungsanalyse (Messqualitaet bewerten):
```python
from machine import I2C, Pin
from nitbw_tof import TOF
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = TOF(i2c)

for name, modus in [("Standard", TOF.STANDARD), ("Genau", TOF.GENAU)]:
    sensor.set_modus(modus)
    minimum, maximum, mittel = sensor.messen_bereich(n=10)
    if minimum > 0:
        print("{}: Mittel {} mm, Streuung {} mm".format(
            name, mittel, maximum - minimum))
```

6. Timing Budget manuell setzen (Expertenmodus):
```python
from machine import I2C, Pin
from nitbw_tof import TOF
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = TOF(i2c)

# Eigener Wert: 66 ms (zwischen Standard und Genau)
sensor.set_timing_budget(66000)
print("Budget: {} us".format(sensor.lese_timing_budget()))
print("Messung: {} mm".format(sensor.messen_mm()))
```

### Fehlersuche

- **Sensor nicht gefunden (OSError)**: I2C-Verkabelung pruefen (SDA/SCL nicht
  vertauscht?). `i2c.scan()` ausfuehren – der Sensor sollte bei 0x29 erscheinen.
- **immer -1 (keine Messung)**: Objekt zu nah (< 30 mm) oder zu weit entfernt.
  `sensor.status()` liefert den Grund (z. B. 'Signal zu schwach').
- **Schwankende Werte**: `messen_median()` verwenden. Alternativ `set_modus(TOF.GENAU)`
  fuer stabilere Messwerte (dauert aber 200 ms pro Messung).
- **Zwei Sensoren, einer antwortet nicht**: XSHUT-Reihenfolge pruefen. Zuerst
  den Sensor mit geaenderter Adresse hochfahren, dann den mit Standard-Adresse.
- **Adresse nach Neustart verloren**: Normal! Die Adressaenderung ist fluechtig.
  Der Code muss bei jedem Boot die Sensoren neu konfigurieren.
- **Messung dauert sehr lange**: Im Modus `GENAU` dauert eine Messung 200 ms.
  Fuer schnellere Reaktion `TOF.SCHNELL` oder `TOF.STANDARD` verwenden.

## Lizenz

MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
