# NIT Bibliothek: SDKarte

## Beschreibung

Diese Bibliothek bindet eine microSD-Karte ueber SPI am ESP32 ein. Sie enthaelt
einen eigenen Treiber fuer SD-Karten im SPI-Modus, haengt die Karte als
FAT-Dateisystem ein (Standard: `/sd`) und bietet einfache deutsche Dateifunktionen.
Besonders praktisch fuer Messreihen ist `csv_anhaengen()`: Jede Messung landet als
Zeile in einer CSV-Datei, die sich am PC direkt in Excel oder LibreOffice oeffnen laesst.

## Features

Karte:

- Eigener SPI-Treiber nach SD-Spezifikation (SDSC Version 1 und 2, SDHC), keine weitere Datei noetig
- Einhaengen als FAT-Dateisystem: danach funktionieren auch `open()` und `os.listdir()` unter `/sd`
- SPI-Objekt wird ausserhalb erstellt (wie I2C bei den Sensor-Bibliotheken)
- Alternativ ein fertiges Blockgeraet nutzen, z. B. `machine.SDCard`
- Verstaendliche Fehlermeldungen (Karte antwortet nicht, kein FAT32, nicht eingehaengt)
- Erneuter Programmstart ohne Neustart des ESP32 funktioniert (alte Einhaengung wird geloest)

Dateien:

- **schreiben / anhaengen / zeile_anhaengen**: Text speichern
- **lesen / zeilen**: Text als Ganzes oder als Liste von Zeilen lesen
- **csv_anhaengen**: Messwerte als CSV-Zeile, Kopfzeile nur beim ersten Mal,
  Dezimalkomma fuer deutsche Tabellenkalkulation
- **dateien / existiert / loeschen / ordner_anlegen**: Dateien und Ordner verwalten
- **speicher**: Gesamtgroesse und freier Platz in MB
- Kurze Dateinamen: `'messung.csv'` wird automatisch zu `'/sd/messung.csv'`

## Hardware

### microSD-Kartenmodule

| Modultyp | VCC | Hinweis |
|---|---|---|
| Modul mit 3.3-V-Regler und Pegelwandler (haeufigste Bauform, 6 Pins) | 5 V | Der Regler erzeugt 3.3 V fuer die Karte; an 3.3 V oft unzuverlaessig |
| Reiner 3.3-V-Adapter (ohne Regler) | 3.3 V | Nie an 5 V anschliessen |

### Karten

- **Dateisystem**: FAT32 (oder FAT16). exFAT wird nicht unterstuetzt.
- **Groesse**: SDHC-Karten bis 32 GB (empfohlen 4-32 GB). Groessere SDXC-Karten
  sind ab Werk mit exFAT formatiert und funktionieren erst nach einer
  FAT32-Formatierung mit einem Zusatzprogramm.
- Alte SDSC-Karten bis 2 GB werden ebenfalls unterstuetzt.
- Die Karte am PC formatieren: Dateisystem FAT32, Zuordnungseinheit Standard.

### Technik

- SPI-Modus 0, Start mit 100 kHz, danach ca. 1,32 MHz (zuverlaessig auch mit Steckkabeln)
- Die Karte wird in Bloecken zu 512 Byte gelesen und geschrieben
- Die Bibliothek stellt den SPI-Takt selbst ein; die Baudrate beim Erzeugen des
  SPI-Objekts spielt keine Rolle

## Anschluss

| microSD-Modul | ESP32 DevKit | Wemos D1 R32 |
|---|---|---|
| VCC | 5V (VIN) | 5V |
| GND | GND | GND |
| SCK (CLK) | GPIO 18 | D13 (= GPIO 18) |
| MISO (DO) | GPIO 19 | D12 (= GPIO 19) |
| MOSI (DI) | GPIO 23 | D11 (= GPIO 23) |
| CS | GPIO 5 | D10 (= GPIO 5) |

Beim D1 R32 liegen die Leitungen am Arduino-SPI-Platz D13/D12/D11/D10. Die
GPIO-Nummern sind dieselben wie beim DevKit, der Code bleibt gleich:

```python
from machine import SPI, Pin
spi = SPI(2, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
```

**Hinweise**: Kabel moeglichst kurz halten (unter 20 cm). Bei reinen 3.3-V-Adaptern
VCC an 3.3V anschliessen. MOSI ist am Modul oft mit DI, MISO mit DO beschriftet.

## Installation

Datei `nitbw_sdkarte.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

Anschliessend kann die Bibliothek importiert werden:

```python
from nitbw_sdkarte import SDKarte
```

## Schnellstart

```python
from machine import SPI, Pin
from nitbw_sdkarte import SDKarte

spi = SPI(2, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
karte = SDKarte(spi, cs=5)            # haengt die Karte unter /sd ein

karte.zeile_anhaengen('log.txt', 'Hallo SD-Karte')
print(karte.lesen('log.txt'))
print(karte.dateien())

karte.csv_anhaengen('messung.csv', [1.5, 23.4], kopf=['Zeit_s', 'Temperatur_C'])

karte.aushaengen()                    # vor dem Herausziehen
```

## API-Referenz

### Konstruktor

```python
SDKarte(spi, cs, pfad='/sd', geraet=None, einhaengen=True)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `spi` | machine.SPI | - | Fertiges SPI-Objekt (ausserhalb erstellt) |
| `cs` | int | - | GPIO-Pin-Nummer fuer Chip Select (z. B. 5) |
| `pfad` | str | `'/sd'` | Einhaengepunkt im Dateisystem |
| `geraet` | Blockgeraet/None | None | Fertiges Blockgeraet (z. B. `machine.SDCard`); dann duerfen `spi` und `cs` `None` sein |
| `einhaengen` | bool | True | `True` = sofort einhaengen, `False` = spaeter mit `einhaengen()` |

### Methoden

#### Einhaengen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `einhaengen()` | - | Karte initialisieren und unter `pfad` einhaengen (auch nach Kartenwechsel) |
| `aushaengen()` | - | Karte aushaengen, vor dem Herausziehen aufrufen |
| `ist_eingehaengt()` | bool | True, wenn die Karte eingehaengt ist |
| `pfad(datei)` | str | Vollstaendiger Pfad: `'messung.csv'` -> `'/sd/messung.csv'` |

#### Schreiben

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `schreiben(datei, text)` | - | Datei neu schreiben (vorhandener Inhalt wird ersetzt) |
| `anhaengen(datei, text)` | - | Text unveraendert ans Ende anhaengen |
| `zeile_anhaengen(datei, text)` | - | Text plus Zeilenumbruch anhaengen |
| `csv_anhaengen(datei, werte, kopf=None, trenner=';', dezimalkomma=True)` | - | Werteliste als CSV-Zeile anhaengen; `kopf` nur, wenn die Datei neu ist |

#### Lesen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `lesen(datei)` | str | Ganzen Dateiinhalt lesen |
| `zeilen(datei)` | list | Liste der Zeilen ohne Zeilenumbruch |

#### Dateien, Ordner und Speicher

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `dateien(ordner='')` | list | Alphabetisch sortierte Namen im Ordner (Standard: Hauptverzeichnis) |
| `existiert(datei)` | bool | True, wenn Datei oder Ordner vorhanden ist |
| `loeschen(datei)` | - | Datei oder leeren Ordner loeschen |
| `ordner_anlegen(name)` | - | Ordner anlegen, auch mehrere Ebenen (`'daten/2026'`); vorhanden = kein Fehler |
| `speicher()` | tuple | `(gesamt_mb, frei_mb)` |

### Pfade

Alle Dateifunktionen beziehen sich auf die Karte:

| Angabe | wird zu |
|---|---|
| `'messung.csv'` | `'/sd/messung.csv'` |
| `'daten/messung.csv'` | `'/sd/daten/messung.csv'` |
| `'/daten/messung.csv'` | `'/sd/daten/messung.csv'` |
| `'/sd/messung.csv'` | bleibt `'/sd/messung.csv'` |

### CSV-Format

`csv_anhaengen()` schreibt Kommazahlen mit Dezimalkomma und trennt die Spalten mit
Semikolon. So erkennt eine deutsche Tabellenkalkulation die Werte direkt als Zahlen:

```text
Zeit_s;Rohwert;Spannung_V
0,0;30120;1,512
2,0;30388;1,525
```

Texte, die das Trennzeichen enthalten, werden in Anfuehrungszeichen gesetzt,
`None` ergibt ein leeres Feld. Fuer englische Programme: `trenner=','` und
`dezimalkomma=False`.

### Fehlermeldungen

| Meldung (Anfang) | Ursache |
|---|---|
| `SD-Karte antwortet nicht` | Verkabelung, CS-Pin, Versorgung oder Karte nicht eingesteckt |
| `Kein FAT-Dateisystem` | Karte nicht FAT32-formatiert (z. B. exFAT bei Karten ueber 32 GB) |
| `SD-Karte wird nicht unterstuetzt` | Sehr alte MMC-Karte oder gestoerte Verbindung |
| `SD-Karte ist nicht eingehaengt` | Nach `aushaengen()` oder `einhaengen=False` zuerst `einhaengen()` |
| `Datei nicht gefunden` | Dateiname falsch geschrieben |
| `Ordner nicht gefunden` | Unterordner fehlt, vorher `ordner_anlegen()` |

## Beispiele

- `beispiel_sdkarte.py`: Einhaengen, schreiben, anhaengen, lesen, Dateien auflisten, freien Speicher anzeigen
- `beispiel_sdkarte_datenlogger.py`: Alle 2 Sekunden Zeit und Messwert (ADC an GPIO 34) in `messung.csv`

### Zusatzbeispiele

1. Temperatur, Luftdruck und Feuchte mit BME280 protokollieren:
```python
from machine import I2C, SPI, Pin
from nitbw_bme280 import BME280
from nitbw_sdkarte import SDKarte
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = BME280(i2c)
spi = SPI(2, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
karte = SDKarte(spi, cs=5)

kopf = ['Zeit_s', 'Temperatur_C', 'Druck_hPa', 'Feuchte_Prozent']
start = time.ticks_ms()
for _ in range(60):
    t, p, h = sensor.read_all()
    zeit = time.ticks_diff(time.ticks_ms(), start) / 1000
    karte.csv_anhaengen('wetter.csv', [round(zeit, 1), round(t, 2), round(p, 1), round(h, 1)],
                        kopf=kopf)
    time.sleep(10)
karte.aushaengen()
```

2. CSV-Datei wieder einlesen und auswerten:
```python
from machine import SPI, Pin
from nitbw_sdkarte import SDKarte

spi = SPI(2, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
karte = SDKarte(spi, cs=5)

werte = []
for zeile in karte.zeilen('messung.csv')[1:]:      # Kopfzeile ueberspringen
    spalten = zeile.split(';')
    werte.append(float(spalten[2].replace(',', '.')))
print("Mittelwert: {:.3f} V".format(sum(werte) / len(werte)))
```

3. Fuer jeden Programmstart eine neue Datei (`lauf_001.csv`, `lauf_002.csv`, ...):
```python
from machine import SPI, Pin
from nitbw_sdkarte import SDKarte

spi = SPI(2, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
karte = SDKarte(spi, cs=5)
karte.ordner_anlegen('laeufe')

nummer = 1
while karte.existiert('laeufe/lauf_{:03d}.csv'.format(nummer)):
    nummer += 1
datei = 'laeufe/lauf_{:03d}.csv'.format(nummer)
print("Schreibe in", karte.pfad(datei))
karte.csv_anhaengen(datei, [0, 0.0], kopf=['Nr', 'Wert'])
```

4. Normale Python-Dateifunktionen unter `/sd` nutzen:
```python
from machine import SPI, Pin
from nitbw_sdkarte import SDKarte
import os

spi = SPI(2, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
karte = SDKarte(spi, cs=5)

with open('/sd/notiz.txt', 'w') as f:      # oder open(karte.pfad('notiz.txt'), 'w')
    f.write('Direkt mit open() geschrieben\n')
print(os.listdir('/sd'))
```

5. Fertigen Kartentreiber der Firmware verwenden (`machine.SDCard`):
```python
from machine import SDCard
from nitbw_sdkarte import SDKarte

# slot=2 = SPI-Betrieb mit SCK 18, MISO 19, MOSI 23, CS 5 (dieselben Pins wie oben).
# Boards mit eingebautem SD-Slot (z. B. ESP32-CAM): SDCard(slot=1)
# Nicht gleichzeitig mit SPI(2, ...) auf denselben Pins verwenden.
karte = SDKarte(None, None, geraet=SDCard(slot=2))
print(karte.dateien())
```

6. Karte im laufenden Betrieb wechseln:
```python
from machine import SPI, Pin
from nitbw_sdkarte import SDKarte

spi = SPI(2, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
karte = SDKarte(spi, cs=5)

karte.aushaengen()
input("Karte wechseln und Enter druecken ...")
karte.einhaengen()          # neue Karte wird initialisiert
print(karte.dateien())
```

### Fehlersuche

- **`SD-Karte antwortet nicht`**: Verkabelung pruefen (MOSI = DI, MISO = DO, nicht
  vertauschen), CS-Pin im Code und am Kabel vergleichen. Module mit Spannungsregler
  brauchen VCC = 5 V. Karte ganz einstecken (Klick). Gemeinsames GND.
- **`Kein FAT-Dateisystem`**: Karte am PC mit FAT32 formatieren. Karten ueber 32 GB
  sind meist exFAT und muessen umformatiert werden; einfacher ist eine Karte bis 32 GB.
- **Fehler erst nach einiger Zeit oder bei langen Kabeln**: Kabel kuerzen, stabile
  Versorgung (5 V) verwenden, andere Karte probieren.
- **Weitere SPI-Geraete am selben Bus (Display, RFID)**: Manche microSD-Module geben
  die MISO-Leitung nicht frei und stoeren andere Geraete. Dann einen eigenen SPI-Bus
  verwenden, z. B. `SPI(1, ...)` mit anderen Pins. Ausserdem stellt die Bibliothek
  den gemeinsamen SPI-Takt auf ca. 1,32 MHz.
- **Daten fehlen nach dem Ausschalten**: Die Methoden dieser Bibliothek schliessen
  die Datei nach jedem Aufruf, die Daten sind dann gespeichert. Bei eigenem `open()`
  die Datei mit `with` oder `close()` schliessen. Vor dem Herausziehen
  `aushaengen()` aufrufen.
- **Excel zeigt alle Werte in einer Spalte**: Die Datei ist fuer deutsche
  Einstellungen gedacht (Semikolon, Dezimalkomma). Fuer englische Programme
  `trenner=','` und `dezimalkomma=False` verwenden.
- **`speicher()` dauert beim ersten Aufruf lange**: Bei grossen Karten muss das
  Dateisystem den freien Platz eventuell erst zaehlen. Weitere Aufrufe sind schnell.
- **Sehr schnelle Messreihen**: Jeder Aufruf oeffnet und schliesst die Datei
  (einige 10 ms). Fuer Messungen schneller als ca. 10 pro Sekunde die Werte
  sammeln und seltener schreiben.

## Lizenz

MIT-Lizenz, siehe zentrale Datei LICENSE im Repository-Root.
