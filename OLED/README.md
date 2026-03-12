# NIT Bibliothek: OLED

## Beschreibung
Die Bibliothek `nitbw_oled.py` steuert OLED-Displays mit SSD1306 oder SH1106 ueber I2C an. Neben Textausgabe bietet sie eine umfangreiche Grafik-API mit Linien, Rechtecken, Kreisen und Balkendiagrammen. Alle Zeichenoperationen laufen gepuffert und werden mit `show()` in einem Schritt auf dem Display aktualisiert.

## Features
- Unterstuetzung fuer SSD1306 und SH1106 (128x64)
- Integrierte Treiberlogik ohne externe Zusatzmodule
- Zwei Schriftarten: Systemfont und Sans-Font
- Textausgabe mit Position, Skalierung und Fontwahl
- Pixel-, Linien-, Rechteck- und Kreisfunktionen
- Gefuellte Formen (`fill_rect`, `fill_circle`)
- Hilfsmethoden fuer Datenvisualisierung (`map`, `progress_bar`, `draw_bar`)
- Optionales Startlogo bei Initialisierung
- Kompakter Buffer-Ansatz fuer flimmerarme Darstellung
- Einfacher Einsatz im Unterricht mit klaren Methoden

## Hardware
- OLED 128x64 mit SSD1306 oder SH1106 Controller
- I2C-Adresse typischerweise `0x3C` (alternativ oft `0x3D`)
- Versorgung mit 3.3V
- Hinweise:
  - SH1106-Module brauchen `chip='sh1106'`.
  - Falsche Adresse ist die haeufigste Fehlerursache.
  - Lange Leitungen koennen zu I2C-Problemen fuehren.

## Anschluss
Beispiel ESP32-Standardpins:

- `VCC -> 3V3`
- `GND -> GND`
- `SCL -> GPIO 22`
- `SDA -> GPIO 21`

## Installation
- Datei `nitbw_oled.py` auf den ESP32 kopieren.
- Import im Projekt: `from nitbw_oled import OLED`.

## Schnellstart
```python
from nitbw_oled import OLED

# Display initialisieren
oled = OLED(scl=22, sda=21, chip='ssd1306', addr=0x3C)

# Text in den Buffer schreiben
oled.clear()
oled.print('Hallo NIT', 0, 0, font='sans')

# Einmal anzeigen
oled.show()
```

## API-Referenz
Konstruktor: `OLED(scl=22, sda=21, chip='ssd1306', enabled=True, i2c_id=0, addr=0x3c, logo=True)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `scl` | `int` | `22` | SCL-Pin |
| `sda` | `int` | `21` | SDA-Pin |
| `chip` | `str` | `'ssd1306'` | Controller (`ssd1306` oder `sh1106`) |
| `enabled` | `bool` | `True` | Display ein/aus |
| `i2c_id` | `int` | `0` | I2C-Busnummer |
| `addr` | `int` | `0x3c` | I2C-Adresse |
| `logo` | `bool` | `True` | Startlogo zeigen |

Wichtige Methoden:
- `print(string, x=0, y=0, font='serif', scale=1, color=1)`
- `clear()` – löscht nur den Puffer, ohne das Display zu aktualisieren
- `show()` – überträgt den Puffer auf das Display
- `pixel(x, y, color=1)`
- `line(x1, y1, x2, y2, color=1)`
- `hline(x, y, w, color=1)` / `vline(x, y, h, color=1)`
- `draw_rect(...)` / `fill_rect(...)`
- `draw_circle(...)` / `fill_circle(...)`
- `map(value, in_min, in_max, out_min, out_max)`
- `progress_bar(...)` / `draw_bar(...)`

## Beispiele
Dateien im Ordner:
- `OLED/beispiel_oled_schnellstart.py`
- `OLED/beispiel_oled.py`
- `OLED/beispiel_oled_funktionen.py`

Snippet 1: Linie und Text kombinieren
```python
oled.clear()
oled.hline(0, 10, 128)
oled.print('Sensor A', 0, 0)
oled.show()
```

Snippet 2: Fortschrittsbalken
```python
wert = 67
oled.clear()
oled.progress_bar(0, 20, 120, 12, wert)
oled.show()
```

Snippet 3: SH1106 mit anderer Adresse
```python
oled = OLED(chip='sh1106', addr=0x3D)
```

Snippet 4: Sans-Font mit Umlauten und Skalierung
```python
oled.clear()
oled.print("Größe Übung Öl", 0, 0, font='sans')
oled.print("Doppelt", 0, 16, font='sans', scale=2)
oled.show()
```

Snippet 5: Kreise und Rechtecke kombinieren
```python
oled.clear()
oled.draw_rect(0, 0, 60, 40)
oled.fill_circle(30, 20, 12)
oled.draw_circle(90, 32, 25)
oled.show()
```

Snippet 6: Balkendiagramm fuer Sensordaten
```python
oled.clear()
oled.print("Sensor", 0, 0)
prozent = 72
oled.progress_bar(10, 20, 108, 12, prozent)
oled.print(f"{prozent}%", 50, 40, font='sans')
oled.show()
```

Snippet 7: Wert abbilden mit map()
```python
adc_wert = 2048
pixel_x = oled.map(adc_wert, 0, 4095, 0, 127)
oled.pixel(pixel_x, 32)
oled.show()
```

Praktische Hinweise/Fehlersuche:
- Display bleibt leer: `show()` nach dem Zeichnen aufrufen.
- Nach `clear()` muss ebenfalls `show()` aufgerufen werden, damit das Display sichtbar geleert wird.
- Falscher Controller: `chip` auf `ssd1306`/`sh1106` pruefen.
- I2C-Fehler: `addr` mit `i2c.scan()` verifizieren.
- Unscharfe Ausgabe bei Umlaute: Sans-Font via `font='sans'` verwenden.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
