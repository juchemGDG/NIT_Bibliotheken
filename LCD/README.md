# NIT Bibliothek: LCD

## Beschreibung

Diese Bibliothek steuert HD44780-kompatible LCD-Displays am ESP32 ueber einen
PCF8574 I2C-Adapter an. Unterstuetzt werden 16x2 und 20x4 Displays.

Die Implementierung ist eigenstaendig (ohne externe Abhaengigkeiten) und
stellt eine benutzerfreundliche API fuer Textausgabe, Anzeige-Steuerung,
Sonderzeichen und einfache Datenvisualisierung bereit.

## Features

- Einfache Initialisierung und direkte Nutzung mit MicroPython
- Unterstuetzung fuer 16x2 und 20x4 LCD-Module
- Deutsche Umlaute und Sonderzeichen im Text
- Textausgabe linksbuendig, zentriert und rechtsbuendig
- Display-Steuerung fuer Licht, Cursor, Blinken und Scrollen
- Eigene Zeichen (CGRAM) und Balken-/Fortschrittsanzeige
- Hilfsfunktionen zur Werteabbildung (z. B. Sensorwert auf Prozent/Spalten)

Unterstuetzte Funktionsgruppen:

- Text: `print`, `print_center`, `print_right`, `clear_line`
- Anzeige: `backlight`, `display`, `cursor`, `blink`, `scroll_links`, `scroll_rechts`
- Eigene Zeichen: `eigenes_zeichen`, `zeichen_schreiben`
- Visualisierung: `map`, `progress_bar`, `draw_bar`

## Hardware

- ESP32
- HD44780-kompatibles LCD mit I2C-Backpack (PCF8574/PCF8574A)
- Typische I2C-Adresse: `0x27` oder `0x3F`
- Empfohlene Displaygroessen: 16x2 oder 20x4

## Anschluss

```text
LCD (I2C-Adapter)      ESP32
GND  ----------------> GND
VCC  ----------------> 5V (VIN)
SDA  ----------------> GPIO 21
SCL  ----------------> GPIO 22
```

## Installation

Datei `nitbw_lcd.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

Anschliessend kann die Bibliothek direkt mit `from nitbw_lcd import LCD`
importiert werden.

## Schnellstart

```python
from machine import I2C, Pin
from nitbw_lcd import LCD

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = LCD(i2c, addr=0x27)
lcd.print("Temperatur: 23.5 C", 0, 0)
lcd.print("Gruesse aus Tuebingen", 0, 1)
lcd.print("Wir ♥ Python!", 0, 2)
```

Hinweis:

- Falls das Display nicht reagiert, zuerst die I2C-Adresse pruefen (`0x27`/`0x3F`).
- Bei 16x2-Displays `zeilen=2, spalten=16` setzen.

## API-Referenz

Konstruktor:

- `LCD(i2c, addr=0x27, zeilen=4, spalten=20, enabled=True, begruessung=True)`

Parameterueberblick:

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `i2c` | I2C | - | Initialisiertes I2C-Bus-Objekt |
| `addr` | int | `0x27` | I2C-Adresse des Adapters |
| `zeilen` | int | 4 | Displayzeilen (2 oder 4) |
| `spalten` | int | 20 | Displayspalten (16 oder 20) |
| `enabled` | bool | `True` | Ausgabe aktivieren/deaktivieren |
| `begruessung` | bool | `True` | Startbegruessung anzeigen |

Wichtige Methoden:

- `print(text, spalte=0, zeile=0)`
- `print_center(text, zeile=0)`
- `print_right(text, zeile=0)`
- `clear()`
- `clear_line(zeile)`
- `backlight(an=True)`
- `cursor(an=True)`
- `blink(an=True)`
- `scroll_links()` / `scroll_rechts()`
- `eigenes_zeichen(position, bitmap)`
- `progress_bar(zeile, prozent)`
- `draw_bar(zeile, spalte_start, breite, prozent)`

Kurzbeschreibung der Methoden:

| Methode | Zweck |
|---|---|
| `print(text, spalte=0, zeile=0)` | Text an Position ausgeben |
| `print_center(text, zeile=0)` | Text zentriert ausgeben |
| `print_right(text, zeile=0)` | Text rechtsbuendig ausgeben |
| `clear()` | Gesamtes Display loeschen |
| `clear_line(zeile)` | Einzelne Zeile loeschen |
| `home()` | Cursor auf Startposition setzen |
| `backlight(an=True)` | Hintergrundbeleuchtung schalten |
| `display(an=True)` | Anzeige an/aus (Inhalt bleibt) |
| `cursor(an=True)` | Unterstrich-Cursor schalten |
| `blink(an=True)` | Blink-Cursor schalten |
| `scroll_links()` | Inhalt nach links verschieben |
| `scroll_rechts()` | Inhalt nach rechts verschieben |
| `eigenes_zeichen(position, bitmap)` | Zeichen in CGRAM speichern |
| `zeichen_schreiben(position, spalte, zeile)` | Eigenes Zeichen anzeigen |
| `map(wert, ein_min, ein_max, aus_min, aus_max)` | Wertebereich umrechnen |
| `progress_bar(zeile, prozent)` | Zeilenbreiten-Fortschrittsbalken |
| `draw_bar(zeile, spalte_start, breite, prozent)` | Teilbalken zeichnen |

## Beispiele

- `beispiel_lcd.py`: Grundlegende Ausgabe auf 20x4
- `beispiel_lcd_16x02.py`: Grundlegende Ausgabe auf 16x2
- `beispiel_lcd_funktionen.py`: Umfangreicher Funktionsueberblick

Zusatzbeispiele fuer typische Einsaetze:

1. Anzeige mit Umlauten und Sonderzeichen:
```python
from machine import I2C, Pin
from nitbw_lcd import LCD

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = LCD(i2c, addr=0x27)
lcd.print("23.5 C  Groesse", 0, 0)
lcd.print("Wir ♥ MicroPython", 0, 1)
```

2. Display-Steuerung (Cursor/Blinken/Licht):
```python
from nitbw_lcd import LCD
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = LCD(i2c, addr=0x27)
lcd.cursor(True)
time.sleep(1)
lcd.cursor(False)
lcd.blink(True)
time.sleep(1)
lcd.blink(False)
lcd.backlight(False)
time.sleep(0.5)
lcd.backlight(True)
```

3. Fortschrittsanzeige:
```python
from nitbw_lcd import LCD
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = LCD(i2c, addr=0x27)
for p in range(0, 101, 5):
    lcd.progress_bar(3, p)
    lcd.print(f"{p:3d}%", 16, 1)
    time.sleep(0.1)
```

4. Eigenes Zeichen definieren und anzeigen:
```python
from nitbw_lcd import LCD

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = LCD(i2c, addr=0x27)
# Thermometer-Symbol auf CGRAM-Platz 7 laden
thermo = [0b00100, 0b01010, 0b01010, 0b01010,
          0b01010, 0b11111, 0b11111, 0b01110]
lcd.eigenes_zeichen(7, thermo)
lcd.zeichen_schreiben(7, 0, 0)  # Zeichen an Position (0,0) ausgeben
```

5. Wertebereich umrechnen mit map():
```python
from nitbw_lcd import LCD

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = LCD(i2c, addr=0x27)
adc_wert = 2048
spalte = lcd.map(adc_wert, 0, 4095, 0, 19)
prozent = lcd.map(adc_wert, 0, 4095, 0, 100)
lcd.print(f"Spalte:{spalte} %:{prozent}", 0, 0)
```

6. Mehrere Balken mit draw_bar():
```python
from nitbw_lcd import LCD

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = LCD(i2c, addr=0x27)
lcd.print("T", 0, 2)
lcd.draw_bar(2, 0, 9, 65)   # Temperatur-Balken
lcd.print("F", 10, 2)
lcd.draw_bar(2, 10, 9, 80)  # Feuchte-Balken
```

## Lizenz

MIT Lizenz. Der Modul-Header enthaelt nur die Kurzangabe:
`Lizenz: MIT (siehe LICENSE)`.
Der vollstaendige Lizenztext bleibt zentral in der Datei `LICENSE` im Projektstamm.
