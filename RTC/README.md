# NIT Bibliothek: RTC

## Beschreibung

Diese Bibliothek steuert Echtzeituhr-Module (Real Time Clock) am ESP32 ueber
I2C an. Unterstuetzt werden die gaengigen Chips DS1307 und DS3231.

Die Implementierung ist eigenstaendig (ohne externe Abhaengigkeiten) und
stellt eine einheitliche API fuer Zeitabfrage, Formatierung, Stellen und
Zusatzfunktionen wie Temperatur und Alarme bereit.

## Features

- Einfache Initialisierung mit Factory-Funktion `RTC()`
- Unterstuetzung fuer DS1307 und DS3231 Chips
- Automatische Wochentag-Berechnung beim Stellen
- Flexible Formatierung mit `toString()` und frei definierbaren Platzhaltern

Unterstuetzte Funktionsgruppen:

- **Lesen**: `aktuelleDaten`, `stunden`, `minuten`, `sekunden`, `tag`, `monat`, `jahr`, `wochentag`, `wochentagName`, `monatsName`
- **Formatierung**: `toString` mit Platzhaltern (hh, mm, ss, DD, DDD, MM, MMM, YY, YYYY)
- **Stellen**: `set`, `setVonString`, `stellenSeriell`, `stellenInteraktiv`, `pruefeStellPin`
- **Kalender**: `istSchaltjahr`, `tageImMonat`, `zeitTuple`, `unixZeit`
- **Oszillator**: `laueft`, `start`, `stop`
- **DS3231-spezifisch**: `temperatur`, `alarm1`, `alarm2`, `alarmStatus`, `alarmLoeschen`, `squareWave`
- **DS1307-spezifisch**: `schreibeRAM`, `leseRAM`, `squareWave`

## Hardware

### DS3231 (empfohlen)

- Hochpraezise RTC mit temperaturkompensiertem Quarz (TCXO)
- Integrierter Temperatursensor (Aufloesung 0.25 °C)
- Zwei programmierbare Alarme
- Batterie-Backup (CR2032)
- Typische I2C-Adresse: `0x68`

### DS1307

- Standard-RTC mit externem 32.768 kHz Quarz
- 56 Byte batterigestuetztes RAM
- Square-Wave-Ausgang (1 Hz, 4.096 kHz, 8.192 kHz, 32.768 kHz)
- Batterie-Backup (CR2032)
- Typische I2C-Adresse: `0x68`

### Hinweis zur Genauigkeit

Der DS3231 weicht typischerweise nur ca. 2 ppm ab (~1 Minute pro Jahr).
Der DS1307 kann je nach Quarzqualitaet und Temperatur mehrere Minuten pro Monat abweichen.

## Anschluss

```text
RTC-Modul              ESP32
GND  ----------------> GND
VCC  ----------------> 3.3V
SDA  ----------------> GPIO 21
SCL  ----------------> GPIO 22
```

Hinweis: Die meisten RTC-Module haben integrierte Pull-Up-Widerstaende
auf SDA und SCL. Zusaetzliche Pull-Ups sind in der Regel nicht noetig.

## Installation

Datei `nitbw_rtc.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

Anschliessend kann die Bibliothek direkt mit `from nitbw_rtc import RTC`
importiert werden.

## Schnellstart

```python
from nitbw_rtc import RTC

rtc = RTC(chip='DS3231', scl=22, sda=21)
print(rtc.toString("DD.MM.YYYY hh:mm:ss"))
```

Hinweis:

- Falls die RTC nicht reagiert, I2C-Adresse pruefen (Standard: `0x68`).
- Fuer DS1307: `RTC(chip='DS1307')` verwenden.
- Die Batterie am Modul sorgt dafuer, dass die Zeit auch ohne Strom erhalten bleibt.

## API-Referenz

### Factory-Funktion

- `RTC(chip='DS3231', i2c=None, addr=0x68, scl=22, sda=21, i2c_id=0)`

Parameterueberblick:

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `chip` | str | `'DS3231'` | Chip-Typ: `'DS1307'` oder `'DS3231'` |
| `i2c` | I2C | `None` | Optionales I2C-Objekt (wird sonst erstellt) |
| `addr` | int | `0x68` | I2C-Adresse des RTC-Moduls |
| `scl` | int | 22 | GPIO-Pin fuer SCL |
| `sda` | int | 21 | GPIO-Pin fuer SDA |
| `i2c_id` | int | 0 | I2C-Bus-ID |

### Gemeinsame Methoden (DS1307 und DS3231)

| Methode | Zweck |
|---|---|
| `aktuelleDaten()` | Alle Datums-/Zeitdaten als dict lesen |
| `stunden()` | Aktuelle Stunde (0-23) |
| `minuten()` | Aktuelle Minute (0-59) |
| `sekunden()` | Aktuelle Sekunde (0-59) |
| `tag()` | Aktueller Tag (1-31) |
| `monat()` | Aktueller Monat (1-12) |
| `jahr()` | Aktuelles Jahr (z.B. 2026) |
| `wochentag()` | Wochentag als Zahl (1=Mo, 7=So) |
| `wochentagName()` | Deutscher Kurzname (Mo-So) |
| `monatsName()` | Deutscher Kurzname (Jan-Dez) |
| `toString(fmt)` | Formatierter Datums-/Zeitstring |
| `set(...)` | RTC auf bestimmte Werte stellen |
| `setVonString(zeitstring)` | RTC aus String stellen (YYYY-MM-DD hh:mm:ss) |
| `stellenSeriell()` | Interaktives Stellen via Seriellen Monitor |
| `stellenInteraktiv(display, ...)` | Stellen mit Display und 3 Tastern |
| `pruefeStellPin(pin_nr, ...)` | Stell-Modus per Pin beim Boot starten |
| `istSchaltjahr(jahr)` | Prueft auf Schaltjahr |
| `tageImMonat(monat, jahr)` | Anzahl Tage im Monat |
| `zeitTuple()` | Zeit als Tuple (kompatibel mit time.localtime) |
| `unixZeit()` | Sekunden seit 2000-01-01 (MicroPython-Epoche) |
| `laueft()` | Prueft ob Oszillator laeuft |
| `start()` | Startet den Oszillator |
| `stop()` | Stoppt den Oszillator |

### DS3231-spezifische Methoden

| Methode | Zweck |
|---|---|
| `temperatur()` | Temperatur in °C (Aufloesung 0.25 °C) |
| `alarm1(stunden, minuten, sekunden, ...)` | Alarm 1 setzen |
| `alarm2(stunden, minuten, ...)` | Alarm 2 setzen (ohne Sekunden) |
| `alarmStatus()` | Tuple (alarm1, alarm2) mit Bool-Werten |
| `alarmLoeschen(alarm_nr)` | Alarm-Flags loeschen |
| `squareWave(frequenz)` | SQW-Pin konfigurieren (1/1024/4096/8192 Hz) |

### DS1307-spezifische Methoden

| Methode | Zweck |
|---|---|
| `schreibeRAM(adresse, daten)` | Bytes in batterigestuetzten RAM schreiben |
| `leseRAM(adresse, laenge)` | Bytes aus RAM lesen (56 Bytes verfuegbar) |
| `squareWave(frequenz)` | SQW-Pin konfigurieren (1/4096/8192/32768 Hz) |

### toString() Platzhalter

| Platzhalter | Beschreibung | Beispiel |
|---|---|---|
| `hh` | Stunde mit fuehrender Null | `09`, `14` |
| `mm` | Minute mit fuehrender Null | `05`, `30` |
| `ss` | Sekunde mit fuehrender Null | `00`, `59` |
| `YYYY` | Jahr vierstellig | `2026` |
| `YY` | Jahr zweistellig | `26` |
| `MM` | Monat mit fuehrender Null | `03`, `12` |
| `MMM` | Deutscher Monatsname | `Mar`, `Dez` |
| `DD` | Tag mit fuehrender Null | `01`, `31` |
| `DDD` | Deutscher Tagesname | `Mo`, `So` |

## Beispiele

- `beispiel_rtc.py`: Einfache Ausgabe von Datum und Uhrzeit im Seriellen Monitor
- `beispiel_rtc_stellen.py`: Uhr ueber die serielle Schnittstelle stellen
- `beispiel_rtc_stellen_mit_tastern.py`: Uhr interaktiv stellen mit 3 Tastern und Display
- `beispiel_rtc_komplett.py`: Alle Funktionen im Ueberblick (Formatierung, Einzelwerte, Temperatur, Alarm)

### Zusatzbeispiele

1. Verschiedene Formatierungen:
```python
from nitbw_rtc import RTC

rtc = RTC(chip='DS3231', scl=22, sda=21)
print(rtc.toString("DD.MM.YYYY hh:mm:ss"))   # 10.03.2026 14:30:00
print(rtc.toString("DDD, DD. MMM YYYY"))      # Tue, 10. Mar 2026
print(rtc.toString("hh:mm"))                  # 14:30
print(rtc.toString("YYYY-MM-DD"))             # 2026-03-10
```

2. Temperatur mit Uhrzeit (DS3231):
```python
from nitbw_rtc import RTC
import time

rtc = RTC(chip='DS3231', scl=22, sda=21)
while True:
    print("{} - {:.1f} C".format(
        rtc.toString("hh:mm:ss"),
        rtc.temperatur()))
    time.sleep(1)
```

3. Stell-Pin mit LCD:
```python
from nitbw_rtc import RTC
from nitbw_lcd import LCD

rtc = RTC(chip='DS3231', scl=22, sda=21)
lcd = LCD(scl=22, sda=21, addr=0x27)

# GPIO 4 = Stell-Taster, GPIO 12/13/14 = Hoch/Runter/Enter
rtc.pruefeStellPin(pin_nr=4, display=lcd,
                   pin_hoch=12, pin_runter=13, pin_enter=14)
```

4. Schaltjahr und Tage im Monat pruefen:
```python
from nitbw_rtc import RTC

rtc = RTC(chip='DS3231', scl=22, sda=21)
print("Schaltjahr:", rtc.istSchaltjahr())
print("Tage im Feb 2024:", rtc.tageImMonat(2, 2024))
```

5. Unix-Zeit und Zeit-Tuple abfragen:
```python
from nitbw_rtc import RTC

rtc = RTC(chip='DS3231', scl=22, sda=21)
print("Sekunden seit 2000:", rtc.unixZeit())
print("Zeit-Tuple:", rtc.zeitTuple())
```

6. Oszillator pruefen und starten (DS1307):
```python
from nitbw_rtc import RTC

rtc = RTC(chip='DS1307', scl=22, sda=21)
if not rtc.laueft():
    print("Oszillator steht - wird gestartet")
    rtc.start()
```

7. DS3231 Alarme verwenden:
```python
from nitbw_rtc import RTC

rtc = RTC(chip='DS3231', scl=22, sda=21)
rtc.alarm1(stunden=14, minuten=30, sekunden=0)
print("Alarm auf 14:30 gesetzt")
a1, a2 = rtc.alarmStatus()
print("Alarm 1 aktiv:", a1)
rtc.alarmLoeschen()
```

### Fehlersuche

- **RTC nicht gefunden**: I2C-Verkabelung pruefen. SDA und SCL nicht vertauscht?
  I2C-Scan ausfuehren: `from machine import I2C, Pin; print(I2C(0, scl=Pin(22), sda=Pin(21)).scan())`
- **Falsche Uhrzeit nach Stromausfall**: Batterie (CR2032) pruefen oder ersetzen.
- **DS1307 steht still**: `rtc.laueft()` pruefen, ggf. `rtc.start()` aufrufen.
  Das CH-Bit kann bei fabrikneuen Modulen gesetzt sein.
- **DS3231 Temperatur ungenau**: Der Sensor misst die Chip-Temperatur, nicht die
  Umgebungstemperatur. Abweichungen von 1-3 °C sind normal.

## Lizenz

MIT Lizenz. Der Modul-Header enthaelt nur die Kurzangabe:
`Lizenz: MIT (siehe LICENSE)`.
Der vollstaendige Lizenztext bleibt zentral in der Datei `LICENSE` im Projektstamm.
