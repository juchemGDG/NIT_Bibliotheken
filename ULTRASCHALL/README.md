# NIT Bibliothek: Ultraschall

## Beschreibung

Diese Bibliothek ermoeglicht die Entfernungsmessung mit dem HC-SR04 Ultraschallsensor
am ESP32. Sie misst Laufzeiten des Ultraschallsignals und rechnet diese in
Entfernungen um. Neben einfachen Einzelmessungen bietet die Bibliothek
Filterfunktionen, Temperaturkompensation, Kalibrierung und Schwellenwertlogik.

## Features

- Entfernungsmessung in cm, mm und Zoll
- Rohe Laufzeitmessung in Mikrosekunden (didaktisch: Physik der Schallausbreitung)
- Temperaturkompensation der Schallgeschwindigkeit (z. B. mit BME280)

Filterfunktionen:

- **Mittelwert**: Arithmetisches Mittel aus n Messungen
- **Median**: Robuster gegen Ausreisser als der Mittelwert
- **Bereich**: Minimum, Maximum und Mittelwert auf einen Blick (Streuung sichtbar)

Schwellenwert- und Anwendungslogik:

- **ist_naeher_als(cm)**: Einfache Naeherungserkennung (Bool)
- **zone(nah, mittel)**: Drei-Zonen-Klassifikation (nah / mittel / fern)
- **geschwindigkeit(intervall_ms)**: Annaeherungsgeschwindigkeit in cm/s
- **ueberwachen(schwelle, callback)**: Dauerhafter Schwellenwert-Monitor mit Callback

Kalibrierung:

- **kalibrieren(bekannte_distanz_cm)**: Offset-Korrektur anhand einer Referenzdistanz

## Hardware

### HC-SR04 Varianten

| Variante | Logikpegel | Bemerkung |
|---|---|---|
| HC-SR04 | 5 V | Spannungsteiler am Echo-Pin noetig |
| HC-SR04P | 3.3 V | Direkt am ESP32 nutzbar |

### Technische Daten

- Messbereich: 2 cm bis 400 cm
- Genauigkeit: ca. 3 mm (laut Datenblatt)
- Messwinkel: ca. 15°
- Betriebsspannung: 5 V (HC-SR04) / 3.3-5 V (HC-SR04P)

## Anschluss

### HC-SR04P (3.3 V, direkt am ESP32)

```text
HC-SR04P           ESP32
VCC        -----> 3.3V
Trig       -----> GPIO 5
Echo       -----> GPIO 18
GND        -----> GND
```

### HC-SR04 (5 V, mit Spannungsteiler)

```text
HC-SR04            ESP32
VCC        -----> 5V
Trig       -----> GPIO 5
Echo ----+
         |
        [1 kOhm]
         |
         +-------> GPIO 18
         |
        [2 kOhm]
         |
        GND -----> GND
```

Alternativ zum Spannungsteiler kann ein **Levelshifter** (Spannungswandler,
z. B. TXS0108E oder BSS138-basiert) verwendet werden. Der Levelshifter wird
zwischen Echo-Pin und ESP32-GPIO geschaltet und wandelt das 5 V-Signal
zuverlaessig auf 3.3 V um.

**Wichtig**: Der HC-SR04 gibt am Echo-Pin 5 V aus. Ohne Spannungsteiler
oder Levelshifter kann der ESP32 beschaedigt werden! Die 3.3 V-Variante
HC-SR04P ist empfehlenswert, da sie direkt angeschlossen werden kann.

Empfohlene GPIO-Pins am ESP32: 5, 16, 17, 18, 19, 23 (frei von Boot-Konflikten).

## Installation

Datei `nitbw_ultraschall.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

Anschliessend kann die Bibliothek importiert werden:

```python
from nitbw_ultraschall import Ultraschall
```

## Schnellstart

```python
from nitbw_ultraschall import Ultraschall
import time

sensor = Ultraschall(trigger=5, echo=18)

while True:
    cm = sensor.messen_cm()
    if cm > 0:
        print("Entfernung: {:.1f} cm".format(cm))
    else:
        print("Kein Echo")
    time.sleep(0.5)
```

## API-Referenz

### Konstruktor

```python
Ultraschall(trigger, echo, temperatur=20.0)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `trigger` | int | - | GPIO-Pin-Nummer fuer den Trigger-Ausgang |
| `echo` | int | - | GPIO-Pin-Nummer fuer den Echo-Eingang |
| `temperatur` | float | 20.0 | Umgebungstemperatur in °C fuer Schallgeschwindigkeit |

### Methoden

#### Grundmessungen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `messen_cm()` | float | Entfernung in Zentimetern (oder -1 bei Fehler) |
| `messen_mm()` | float | Entfernung in Millimetern (oder -1 bei Fehler) |
| `messen_inch()` | float | Entfernung in Zoll (oder -1 bei Fehler) |
| `messen_laufzeit()` | float | Signallaufzeit hin+zurueck in Mikrosekunden (oder -1) |

#### Filterfunktionen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `messen_mittelwert(n=5)` | float | Mittelwert aus n Messungen in cm |
| `messen_median(n=5)` | float | Median aus n Messungen in cm (robust gegen Ausreisser) |
| `messen_bereich(n=5)` | tuple | (min, max, mittelwert) in cm - zeigt Streuung |

#### Schwellenwertlogik

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `ist_naeher_als(cm)` | bool | True wenn Objekt naeher als Schwellenwert |
| `zone(nah=10, mittel=50)` | str | Gibt 'nah', 'mittel', 'fern' oder 'fehler' zurueck |

#### Geschwindigkeit und Ueberwachung

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `geschwindigkeit(intervall_ms=500)` | float | Geschwindigkeit in cm/s (positiv = naehert sich) |
| `ueberwachen(schwelle_cm, callback, intervall_ms=200)` | - | Dauerhafter Monitor (blockiert, Ctrl+C zum Beenden) |

#### Kalibrierung und Temperatur

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `kalibrieren(bekannte_distanz_cm, n=10)` | - | Offset-Korrektur anhand bekannter Referenzdistanz |
| `set_temperatur(grad_c)` | - | Schallgeschwindigkeit an Temperatur anpassen |

## Beispiele

- `beispiel_ultraschall.py`: Grundlegende Entfernungsmessung in cm, mm und Laufzeit
- `beispiel_ultraschall_median.py`: Vergleich von Mittelwert, Median und Streuung
- `beispiel_ultraschall_einparkhilfe.py`: Einparkhilfe mit Zonen und Geschwindigkeit

### Zusatzbeispiele

1. Temperaturkompensation mit BME280:
```python
from nitbw_ultraschall import Ultraschall
from machine import I2C, Pin
from nitbw_bme280 import BME280
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
bme = BME280(i2c)
sensor = Ultraschall(trigger=5, echo=18)

while True:
    temp, _, _ = bme.read_all()
    sensor.set_temperatur(temp)
    cm = sensor.messen_cm()
    print("Temp: {:.1f} C  ->  Entfernung: {:.1f} cm".format(temp, cm))
    time.sleep(1)
```

2. Sensor kalibrieren (Objekt auf 30 cm Abstand stellen):
```python
from nitbw_ultraschall import Ultraschall

sensor = Ultraschall(trigger=5, echo=18)

# Schritt 1: Sensor ausrichten, Objekt auf exakt 30 cm
sensor.kalibrieren(bekannte_distanz_cm=30.0, n=10)

# Schritt 2: Ab jetzt misst der Sensor mit Offset-Korrektur
print("Korrigierte Messung: {:.1f} cm".format(sensor.messen_cm()))
```

3. Naeherungserkennung (einfacher Alarmsensor):
```python
from nitbw_ultraschall import Ultraschall
import time

sensor = Ultraschall(trigger=5, echo=18)

while True:
    if sensor.ist_naeher_als(20):
        print("ALARM: Objekt naeher als 20 cm!")
    time.sleep(0.2)
```

4. Ueberwachung mit Callback-Funktion:
```python
from nitbw_ultraschall import Ultraschall

sensor = Ultraschall(trigger=5, echo=18)

def alarm(distanz):
    print("Objekt erkannt bei {:.1f} cm!".format(distanz))

# Ruft alarm() auf, sobald etwas naeher als 25 cm kommt
sensor.ueberwachen(schwelle_cm=25, callback=alarm, intervall_ms=100)
```

5. Entfernung in Zoll (fuer internationale Projekte):
```python
from nitbw_ultraschall import Ultraschall
import time

sensor = Ultraschall(trigger=5, echo=18)

while True:
    inch = sensor.messen_inch()
    if inch > 0:
        print("Distance: {:.1f} inches".format(inch))
    time.sleep(0.5)
```

6. Streuungsanalyse (zeigt Messqualitaet):
```python
from nitbw_ultraschall import Ultraschall
import time

sensor = Ultraschall(trigger=5, echo=18)

while True:
    minimum, maximum, mittel = sensor.messen_bereich(n=10)
    if minimum > 0:
        streuung = maximum - minimum
        print("Mittel: {:.1f} cm  Streuung: {:.1f} cm  ({:.0f}%)".format(
            mittel, streuung, streuung / mittel * 100))
    time.sleep(2)
```

### Fehlersuche

- **Immer -1 (kein Echo)**: Verkabelung pruefen. Trigger und Echo nicht vertauscht?
  Bei HC-SR04 (5 V): Spannungsteiler am Echo-Pin vorhanden?
- **Schwankende Messwerte**: `messen_median()` statt `messen_cm()` verwenden.
  Weiche Oberflaechen oder schraege Flaechen reflektieren Ultraschall schlecht.
- **Falsche Entfernungen bei Hitze/Kaelte**: `set_temperatur()` nutzen.
  Bei 0 °C ist die Schallgeschwindigkeit ca. 4 % langsamer als bei 20 °C.
- **Messwerte weichen systematisch ab**: `kalibrieren()` ausfuehren.
  Objekt auf bekannten Abstand stellen und Offset automatisch berechnen lassen.
- **Minimaler Abstand**: Objekte unter 2 cm koennen nicht zuverlaessig gemessen werden
  (Sensorlimit).

## Lizenz

MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
