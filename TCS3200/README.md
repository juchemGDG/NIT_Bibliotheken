# NIT Bibliothek: TCS3200

## Beschreibung

Diese Bibliothek steuert den Farbsensor TCS3200 beziehungsweise TCS230 direkt
ueber GPIO-Pins am ESP32 an. Der Sensor liefert keine analogen Spannungen,
sondern ein Rechtecksignal, dessen Frequenz von der gemessenen Farbintensitaet
abhaengt.

Die Implementierung kommt ohne fremde Bibliotheken aus und misst die
Signalperioden direkt mit MicroPython-Mitteln. Neben Rohfrequenzen bietet die
Bibliothek RGB-Umrechnung, Kalibrierung, Helligkeitsmessung und einfache
Farberkennung fuer den Unterricht.

## Features

- Direkte Ansteuerung des TCS3200/TCS230 ohne externe Abhaengigkeiten
- Messung von Periodendauer in Mikrosekunden fuer didaktische Experimente
- Messung von Ausgangsfrequenzen in Hertz fuer alle Filterkanaele
- Umschalten der Farbfilter rot, gruen, blau und klar
- Umschalten der Frequenzskalierung auf 0 %, 2 %, 20 % oder 100 %
- Rohwertmessung fuer alle Kanaele mit einer einzigen Methode
- RGB-Ausgabe als 8-Bit-Werte (0 bis 255)
- Hex-Farbausgabe im Format #RRGGBB

Kalibrierung und Auswertung:

- Weisskalibrierung und Schwarzkalibrierung fuer reproduzierbare Messungen
- Helligkeitsmessung ueber den klaren Kanal
- Dominante-Farbe-Erkennung fuer Rot, Gruen und Blau
- Boolesche Abfrage ueber `ist_farbe(...)` fuer einfache Steuerlogik

## Hardware

### Unterstuetzte Sensoren

| Sensor | Bemerkung |
|---|---|
| TCS3200 | Weit verbreitetes Modul mit 4 weissen LEDs |
| TCS230 | Elektrisch sehr aehnlich, gleiche Ansteuerung |

### Pins des Sensors

| Pin | Funktion |
|---|---|
| `VCC` | Versorgung, meist 3.3 V bis 5 V (modulabhaengig) |
| `GND` | Masse |
| `OUT` | Frequenzausgang zum ESP32 |
| `S2`, `S3` | Auswahl des Farbfilters |
| `S0`, `S1` | Auswahl der Frequenzskalierung |
| `OE` | Output Enable, aktiv LOW, optional |

### Filtertabelle

| S2 | S3 | Aktiver Filter |
|---|---|---|
| 0 | 0 | Rot |
| 0 | 1 | Blau |
| 1 | 0 | Klar (ohne Filter) |
| 1 | 1 | Gruen |

### Frequenzskalierung

| S0 | S1 | Skalierung |
|---|---|---|
| 0 | 0 | Aus (0 %) |
| 0 | 1 | 2 % |
| 1 | 0 | 20 % |
| 1 | 1 | 100 % |

Hinweis: Fuer MicroPython-Messungen ist 2 % meist am stabilsten. 20 % ist oft
ebenfalls nutzbar. 100 % kann fuer einfache Polling-Messungen zu schnell sein.

## Anschluss

```text
TCS3200             ESP32
VCC        -------> 3.3V
GND        -------> GND
OUT        -------> GPIO 27
S2         -------> GPIO 14
S3         -------> GPIO 12
S0         -------> GPIO 26   (optional, fuer Skalierung)
S1         -------> GPIO 25   (optional, fuer Skalierung)
OE         -------> GPIO 33   (optional, aktiv LOW)
```

Hinweise:

- Viele TCS3200-Module haben integrierte LEDs. Diese verbessern die Messung bei
  kurzen Abstaenden deutlich.
- Ein Abstand von ca. 1 bis 3 cm zur Farbkarte liefert meist stabilere Werte als
  groesserer Abstand.
- Wenn S0 und S1 nicht angeschlossen werden, muss die Frequenzskalierung am
  Modul fest verdrahtet sein.

## Installation

Datei `nitbw_tcs3200.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

Anschliessend kann die Bibliothek importiert werden:

```python
from nitbw_tcs3200 import TCS3200
```

## Schnellstart

```python
from nitbw_tcs3200 import TCS3200
import time

sensor = TCS3200(out=27, s2=14, s3=12, s0=26, s1=25)
sensor.set_frequenzskalierung(2)

while True:
    farbe = sensor.dominante_farbe(messungen=8)
    rohwerte = sensor.messen_rohwerte(messungen=8)
    print(farbe, rohwerte)
    time.sleep(0.5)
```

## API-Referenz

### Konstruktor

```python
TCS3200(out, s2, s3, s0=None, s1=None, oe=None, frequenzskalierung=2)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `out` | int | - | GPIO-Pin fuer OUT |
| `s2` | int | - | GPIO-Pin fuer S2 |
| `s3` | int | - | GPIO-Pin fuer S3 |
| `s0` | int | `None` | Optionaler GPIO-Pin fuer S0 |
| `s1` | int | `None` | Optionaler GPIO-Pin fuer S1 |
| `oe` | int | `None` | Optionaler GPIO-Pin fuer OE |
| `frequenzskalierung` | int | `2` | 0, 2, 20 oder 100 Prozent |

### Sensorsteuerung

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `aktivieren()` | - | Aktiviert den Ausgang, wenn OE angeschlossen ist |
| `deaktivieren()` | - | Deaktiviert den Ausgang, wenn OE angeschlossen ist |
| `set_frequenzskalierung(prozent)` | - | Stellt 0, 2, 20 oder 100 Prozent ein |
| `frequenzskalierung()` | int | Gibt die aktuelle Skalierung zurueck |
| `set_filter(farbe)` | - | Waehlt `rot`, `gruen`, `blau` oder `klar` |
| `filter()` | str | Gibt den aktuell aktiven Filter zurueck |

### Messungen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `messen_periode_us(...)` | float | Mittlere Periodendauer in us |
| `messen_frequenz(...)` | float | Ausgangsfrequenz in Hz |
| `messen_rohwerte(...)` | dict | Frequenzen fuer rot, gruen, blau, klar |
| `messen_helligkeit(...)` | float | Klar-Kanal, mit Kalibrierung in Prozent |

### Farbe und Kalibrierung

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `messen_rgb(...)` | tuple | RGB-Werte von 0 bis 255 |
| `messen_hex(...)` | str | Farbe als Hex-String |
| `dominante_farbe(...)` | str | `rot`, `gruen`, `blau` oder `unbekannt` |
| `ist_farbe(...)` | bool | Prueft eine Ziel-Grundfarbe |
| `kalibrieren_weiss(...)` | dict | Speichert aktuelle Weissreferenz |
| `kalibrieren_schwarz(...)` | dict | Speichert aktuelle Schwarzreferenz |
| `reset_kalibrierung()` | - | Loescht beide Referenzen |
| `kalibrierung()` | dict | Gibt gespeicherte Referenzen zurueck |

## Beispiele

- `beispiel_tcs3200.py`: Rohwerte, Frequenz und dominante Farbe ausgeben
- `beispiel_tcs3200_rgb.py`: Kalibrierung, RGB-Werte, Hex-Farbe und Helligkeit
- `beispiel_tcs3200_farberkennung.py`: Einfache Grundfarberkennung mit `ist_farbe()`

### Zusatzbeispiele

1. Nur den roten Kanal in Hertz lesen:
```python
from nitbw_tcs3200 import TCS3200

sensor = TCS3200(out=27, s2=14, s3=12, s0=26, s1=25)
sensor.set_frequenzskalierung(2)
print(sensor.messen_frequenz('rot', messungen=10))
```

2. Aktiven Filter manuell umschalten:
```python
from nitbw_tcs3200 import TCS3200

sensor = TCS3200(out=27, s2=14, s3=12)
sensor.set_filter('blau')
print('Aktiver Filter:', sensor.filter())
```

3. Helligkeit mit Kalibrierung messen:
```python
from nitbw_tcs3200 import TCS3200

sensor = TCS3200(out=27, s2=14, s3=12, s0=26, s1=25)
sensor.kalibrieren_weiss()
sensor.kalibrieren_schwarz()
print(sensor.messen_helligkeit())
```

4. Farbwert als Hex ausgeben:
```python
from nitbw_tcs3200 import TCS3200

sensor = TCS3200(out=27, s2=14, s3=12, s0=26, s1=25)
print(sensor.messen_hex(messungen=12))
```

5. Farblogik fuer Ampelfarben:
```python
from nitbw_tcs3200 import TCS3200

sensor = TCS3200(out=27, s2=14, s3=12, s0=26, s1=25)

if sensor.ist_farbe('rot'):
    print('Stopp')
elif sensor.ist_farbe('gruen'):
    print('Los')
```

### Fehlersuche

- **Nur -1 oder 0 als Messwert**: OUT-Pin pruefen. Manche Module benoetigen eine
  aktivierte LED-Beleuchtung oder einen kleineren Abstand zur Flaeche.
- **Messwerte springen stark**: Frequenzskalierung auf 2 % setzen und mehr
  Einzelmessungen verwenden.
- **Farben werden vertauscht erkannt**: Filtertabelle bzw. Verkabelung von S2 und
  S3 pruefen.
- **RGB-Werte wirken unplausibel**: Erst Weiss und Schwarz kalibrieren, danach neu
  messen.
- **Sensor reagiert nicht**: Modulversorgung pruefen. Manche Boards arbeiten nur
  sauber mit 5 V Versorgung am Sensor, obwohl die Steuersignale 3.3 V sind.

## Lizenz

MIT-Lizenz, siehe zentrale Datei LICENSE im Repository-Root.