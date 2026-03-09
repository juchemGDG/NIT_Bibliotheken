# LCD Display Treiber

Eine benutzerfreundliche MicroPython-Bibliothek zur Ansteuerung von HD44780-kompatiblen LCD-Displays auf dem **ESP32**. Unterstützt **16x2** und **20x4** Displays über **PCF8574 I2C-Adapter** ohne externe Abhängigkeiten.

## ✨ Features

- **Plug-and-Play Support**: Einfache Initialisierung und Verwendung
- **Mehrere Display-Größen**: 16x2 und 20x4 Displays unterstützt
- **Deutsche Umlaute**: äöüÄÖÜß direkt im Text verwendbar
- **Sonderzeichen**: °C, ♥ (Herz) und alle HD44780-ROM-Zeichen nutzbar
- **Umfangreiche Text-API**:
  - `print()` – Text an beliebiger Position ausgeben
  - `print_center()` – Text zentriert ausgeben
  - `print_right()` – Text rechtsbündig ausgeben
  - `clear_line()` – Einzelne Zeile löschen
- **Display-Steuerung**:
  - `backlight()` – Hintergrundbeleuchtung ein/aus
  - `cursor()` – Unterstrich-Cursor ein/aus
  - `blink()` – Blinkender Block-Cursor ein/aus
  - `scroll_links()` / `scroll_rechts()` – Inhalt verschieben
- **Datenvisualisierung**:
  - `map()` – Sensordaten auf Spalten abbilden
  - `progress_bar()` – Fortschrittsbalken mit feiner Auflösung
  - `draw_bar()` – Einzelne Balken (z.B. für Sensorvergleiche)
- **Eigene Zeichen**: Bis zu 8 benutzerdefinierte 5x8-Zeichen (7 für Umlaute, 1 frei)
- **Keine externen Abhängigkeiten**: Vollständige Treiber-Implementierung
- **I2C Interface**: Standard I2C über PCF8574 Portexpander

## 🚀 Quick Start

### Installation

Laden Sie die Datei `lcd.py` auf den ESP32 (z.B. nach `/`). Danach können Sie sie direkt importieren:

```python
from lcd import LCD

# Display initialisieren (20x4 an Adresse 0x27)
lcd = LCD(scl=22, sda=21, addr=0x27)

# Text ausgeben – Umlaute und °C funktionieren direkt!
lcd.print("Temperatur: 23.5°C", 0, 0)
lcd.print("Grüße aus Tübingen", 0, 1)
lcd.print("Wir ♥ Python!", 0, 2)
```

## 📚 Verwendungsbeispiele

### Beispiel 1: Einfache Text-Ausgabe mit Umlauten

```python
from lcd import LCD
import time

# Initialisierung (20x4 Display)
lcd = LCD(scl=22, sda=21, addr=0x27)

lcd.clear()

# Deutsche Umlaute und Sonderzeichen direkt im Text
lcd.print("NIT Bibliotheken", 0, 0)
lcd.print("Ärger mit Öl?", 0, 1)
lcd.print("23.5°C Größe üben", 0, 2)
lcd.print("Wir ♥ MicroPython!", 0, 3)

time.sleep(3)

# Zentrierter Text
lcd.clear()
lcd.print_center("Willkommen!", 0)
lcd.print_center("ESP32 + LCD", 2)

time.sleep(2)
```

### Beispiel 2: Display-Steuerung

```python
from lcd import LCD
import time

lcd = LCD(scl=22, sda=21, addr=0x27)
lcd.clear()

lcd.print("Cursor-Demo:", 0, 0)

# Unterstrich-Cursor anzeigen
lcd.cursor(True)
lcd.print("_", 0, 1)
time.sleep(2)

# Blinkender Cursor
lcd.cursor(False)
lcd.blink(True)
time.sleep(2)
lcd.blink(False)

# Hintergrundbeleuchtung blinken lassen
for i in range(4):
    lcd.backlight(False)
    time.sleep(0.3)
    lcd.backlight(True)
    time.sleep(0.3)
```

### Beispiel 3: Eigene Zeichen (Platz 7 ist frei)

```python
from lcd import LCD
import time

lcd = LCD(scl=22, sda=21, addr=0x27)
lcd.clear()

# CGRAM-Plätze 0-6 sind für Umlaute belegt, Platz 7 für ♥
# Man kann Platz 7 überschreiben, z.B. mit einem Thermometer:
thermometer = [0b00100,
               0b01010,
               0b01010,
               0b01010,
               0b01010,
               0b11111,
               0b11111,
               0b01110]

lcd.eigenes_zeichen(7, thermometer)

lcd.zeichen_schreiben(7, 0, 0)    # Thermometer an Spalte 0, Zeile 0
lcd.print(" 23.5°C", 1, 0)

# Wer MEHR eigene Zeichen braucht, kann dafür Umlaute entfernen.
# Siehe zeichen.txt für Details.
```

### Beispiel 4: ADC-Sensor mit Fortschrittsbalken

```python
from lcd import LCD
from machine import ADC, Pin
import time

lcd = LCD(scl=22, sda=21, addr=0x27)

# ADC auf GPIO 32 definieren (12-Bit: 0-4095)
adc = ADC(Pin(32))

while True:
    # ADC-Wert auslesen
    adc_wert = adc.read()

    # Wert auf Prozent abbilden
    prozent = lcd.map(adc_wert, 0, 4095, 0, 100)

    # Anzeige aktualisieren
    lcd.print("Sensorwert:", 0, 0)
    lcd.print(f"ADC: {adc_wert:4d}", 0, 1)
    lcd.print(f"    {prozent:3d}%", 0, 2)
    lcd.print(f"    ({adc_wert/4095*3.3:.2f}V)", 0, 3)

    # Fortschrittsbalken in Zeile 3
    lcd.progress_bar(3, prozent)

    time.sleep(0.2)
```

### Beispiel 5: Scrollender Text

```python
from lcd import LCD
import time

lcd = LCD(scl=22, sda=21, addr=0x27)
lcd.clear()

lcd.print("<<< Scroll-Demo >>>", 0, 0)
lcd.print("Text bewegt sich!", 0, 1)

# Text 10x nach links scrollen
for i in range(10):
    lcd.scroll_links()
    time.sleep(0.4)

# Und 10x zurück nach rechts
for i in range(10):
    lcd.scroll_rechts()
    time.sleep(0.4)
```

## 🔧 API-Referenz

### Konstruktor

| Parameter     | Typ   | Standard | Beschreibung                           |
|---------------|-------|----------|----------------------------------------|
| `scl`         | int   | 22       | GPIO-Pin für SCL                       |
| `sda`         | int   | 21       | GPIO-Pin für SDA                       |
| `addr`        | int   | 0x27     | I2C-Adresse (oft auch 0x3F)           |
| `zeilen`      | int   | 4        | Anzahl der Zeilen (2 oder 4)          |
| `spalten`     | int   | 20       | Anzahl der Spalten (16 oder 20)       |
| `enabled`     | bool  | True     | Display aktivieren/deaktivieren        |
| `i2c_id`      | int   | 0        | I2C-Bus-ID                             |
| `begruessung` | bool  | True     | Startbegrüßung anzeigen               |

### Textausgabe

| Methode                        | Beschreibung                              |
|--------------------------------|-------------------------------------------|
| `print(text, spalte, zeile)`   | Text an Position ausgeben                 |
| `print_center(text, zeile)`    | Text zentriert ausgeben                   |
| `print_right(text, zeile)`     | Text rechtsbündig ausgeben                |
| `clear()`                      | Gesamtes Display löschen                  |
| `clear_line(zeile)`            | Eine Zeile löschen                        |
| `home()`                       | Cursor auf (0,0) setzen                   |

### Display-Steuerung

| Methode              | Beschreibung                              |
|----------------------|-------------------------------------------|
| `backlight(an)`      | Hintergrundbeleuchtung ein/aus            |
| `display(an)`        | Display ein/aus (Inhalt bleibt erhalten)  |
| `cursor(an)`         | Unterstrich-Cursor ein/aus                |
| `blink(an)`          | Blinkender Block-Cursor ein/aus           |
| `scroll_links()`     | Displayinhalt nach links verschieben      |
| `scroll_rechts()`    | Displayinhalt nach rechts verschieben     |

### Eigene Zeichen

| Methode                                    | Beschreibung                            |
|--------------------------------------------|-----------------------------------------|
| `eigenes_zeichen(position, bitmap)`        | Eigenes Zeichen speichern (0-7)         |
| `zeichen_schreiben(position, spalte, zeile)` | Eigenes Zeichen anzeigen              |

### Hilfsfunktionen

| Methode                                              | Beschreibung                            |
|------------------------------------------------------|-----------------------------------------|
| `map(wert, ein_min, ein_max, aus_min, aus_max)`     | Wert auf anderen Bereich abbilden       |
| `progress_bar(zeile, prozent)`                       | Fortschrittsbalken zeichnen             |
| `draw_bar(zeile, spalte_start, breite, prozent)`    | Einzelnen Balken zeichnen               |

## 🔌 Anschlüsse

```
LCD (I2C-Adapter)      ESP32
─────────────────      ─────
GND  ──────────────>   GND
VCC  ──────────────>   5V (VIN)
SDA  ──────────────>   GPIO 21
SCL  ──────────────>   GPIO 22
```

> **Hinweis:** Die I2C-Adresse ist abhängig vom PCF8574-Chip auf dem Adapter.
> Häufige Adressen: `0x27` (PCF8574) oder `0x3F` (PCF8574A).
> Mit einem I2C-Scanner lässt sich die korrekte Adresse ermitteln.

## 📄 Lizenz

MIT License – siehe Datei-Header in `lcd.py`.
