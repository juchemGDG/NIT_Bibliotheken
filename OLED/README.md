# NIT Bibliothek: OLED

## Beschreibung
Die Bibliothek `nitbw_oled.py` steuert OLED-Displays mit SSD1306 oder SH1106 ueber I2C an. Neben Textausgabe bietet sie eine umfangreiche Grafik-API mit Linien, Rechtecken, Kreisen und Balkendiagrammen. Alle Zeichenoperationen laufen gepuffert und werden mit `show()` in einem Schritt auf dem Display aktualisiert.

Aktueller Stand: Version 1.5.0

## Features
- Unterstuetzung fuer SSD1306 und SH1106 (128x64 und 128x32)
- Integrierte Treiberlogik ohne externe Zusatzmodule
- Zwei Schriftarten: Systemfont und Sans-Font
- Textausgabe mit Position, Skalierung und Fontwahl
- Pixel-, Linien-, Rechteck- und Kreisfunktionen
- Gefuellte Formen (`fill_rect`, `fill_circle`)
- Hilfsmethoden fuer Datenvisualisierung (`map`, `progress_bar`, `draw_bar`)
- Bitmap-Anzeige (`show_image`) und vereinfachte SVG-Anzeige (`draw_svg`)
- PC-Konverter `svg_zu_bitmap.py` zum Umwandeln von SVG in 1-Bit-Bitmaps
- Optionales Startlogo bei Initialisierung
- Kompakter Buffer-Ansatz fuer flimmerarme Darstellung
- Einfacher Einsatz im Unterricht mit klaren Methoden

## Hardware
- OLED 128x64 oder 128x32 mit SSD1306 oder SH1106 Controller
- I2C-Adresse typischerweise `0x3C` (alternativ oft `0x3D`)
- Versorgung mit 3.3V
- Hinweise:
  - SH1106-Module brauchen `chip='sh1106'`.
  - Standard-Aufloesung ist `width=128, height=64`.
  - Fuer 128x32: `width=128, height=32` setzen.
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
from machine import I2C, Pin
from nitbw_oled import OLED

# I2C initialisieren
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Display initialisieren
oled = OLED(i2c, chip='ssd1306', addr=0x3C)

# Text in den Buffer schreiben
oled.clear()
oled.print('Hallo NIT', 0, 0, font='sans')

# Einmal anzeigen
oled.show()
```

## API-Referenz
Konstruktor: `OLED(i2c, chip='ssd1306', enabled=True, addr=0x3c, logo=True)`
Konstruktor: `OLED(i2c, chip='ssd1306', enabled=True, addr=0x3c, logo=True, width=128, height=64)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `i2c` | `machine.I2C` | - | Initialisierter I2C-Bus |
| `chip` | `str` | `'ssd1306'` | Controller (`ssd1306` oder `sh1106`) |
| `enabled` | `bool` | `True` | Display ein/aus |
| `addr` | `int` | `0x3c` | I2C-Adresse |
| `logo` | `bool` | `True` | Startlogo zeigen |
| `width` | `int` | `128` | Displaybreite in Pixeln |
| `height` | `int` | `64` | Displayhoehe in Pixeln |

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
- `show_image(data, x=0, y=0, width=None, height=None)` – `data` darf Modulname (str), Modul oder bytes sein
- `show_svg(datei, x=0, y=0, scale=1.0, color=1, clear=True)` – SVG-Datei vom ESP32 laden und direkt rendern
- `show_bmp(datei, x=0, y=0, clear=True)` – BMP-Datei vom ESP32 laden (1/24/32-Bit)
- `slideshow(bilder, pause=2.0, loop=False, clear=True, x=0, y=0)`
- `draw_svg(svg, x=0, y=0, scale=1.0, color=1)` – SVG-String direkt zeichnen

## SVG und Bilder anzeigen

Es gibt **mehrere Wege**, Grafiken auf dem OLED darzustellen – vom schnellsten
(Datei direkt vom ESP32 laden) bis zum robustesten (alle SVG-Features via
PC-Konverter):

### Weg 1: Datei direkt vom ESP32 laden (am einfachsten für die Schule)

**SVG-Datei** (nur einfache Formen: Linien/Rechtecke/Kreise/Pfade):
```python
oled.show_svg('icon.svg')   # SVG liegt auf dem Board
oled.show()
```
Unterstuetzt: `line`, `rect`, `circle`, `polyline`, `polygon`, `path` (M/L/H/V/Z).  
**Nicht** unterstuetzt: Ellipsen, Fuellungen, Transformationen, Text.

**BMP-Datei** (1-Bit/24-Bit/32-Bit):
```python
oled.show_bmp('foto.bmp')   # BMP liegt auf dem Board
oled.show()
```
Farbbilder werden automatisch in Schwarz/Weiss umgewandelt (Schwellwert 128).  
Fuer PNG/JPG: auf dem PC in BMP umwandeln (z.B. mit GIMP/Paint).

### Weg 2: PC-Konverter (fuer komplexe SVGs mit allen Features)

Wenn die SVG Ellipsen, Fuellungen, Transformationen oder Text enthaelt, nutze
den PC-Konverter `svg_zu_bitmap.py` – er rendert die SVG komplett und erzeugt
eine fertige `.py`-Datei fuer das Board.

Einmalig auf dem PC installieren (kein venv noetig):
```bash
pip3 install --user cairosvg pillow
# macOS zusaetzlich: brew install cairo
```

**Nutzung (4 Wege, am einfachsten per GUI):**

1. **GUI per Doppelklick** (kein Terminal, keine Einstellungen):  
   `svg_zu_bitmap.py` doppelklicken (macOS/Windows) oder in Python-Editor mit
   "Run" starten → Datei-Dialog → SVG auswaehlen → fertig.
2. **Editor / "Run"-Button:** in `svg_zu_bitmap.py` oben `EINSTELLUNGEN`
   anpassen → Datei ausfuehren.
3. **Als Funktion:**
   ```python
   from svg_zu_bitmap import konvertiere
   konvertiere("icon.svg", vorschau=True)
   ```
4. **Kommandozeile:**
   ```bash
   python3 svg_zu_bitmap.py icon.svg -W 128 -H 64
   ```

Das erzeugte `icon_bitmap.py` auf den ESP32 kopieren und anzeigen:
```python
oled.show_image('icon_bitmap')   # WIDTH/HEIGHT werden automatisch gelesen
oled.show()
```

### Weg 3: SVG-String direkt zeichnen (für selbst erstellte einfache Formen)

```python
svg = """<svg width="128" height="64">
  <rect x="10" y="10" width="50" height="30"/>
  <circle cx="80" cy="32" r="20"/>
</svg>"""
oled.draw_svg(svg)
oled.show()
```
Wie bei `show_svg()` nur Linien/Rechtecke/Kreise/Pfade (M/L/H/V/Z).

---

**Zusammenfassung:**
- **Schule/Einstieg:** `show_svg('...')` / `show_bmp('...')` — Dateien aufs Board, fertig.
- **Komplexe SVGs** (Ellipsen, Fuellungen): PC-Konverter (GUI per Doppelklick).
- **Programmierte Formen:** `draw_svg(svg_string)`.

## Beispiele
Dateien im Ordner:
- `OLED/beispiel_oled_schnellstart.py`
- `OLED/beispiel_oled.py`
- `OLED/beispiel_oled_funktionen.py`
- `OLED/beispiel_oled_svg.py`

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
oled = OLED(i2c, chip='sh1106', addr=0x3D)
```

Snippet 4: SSD1306 mit 128x32
```python
oled = OLED(chip='ssd1306', width=128, height=32, logo=False)
oled.clear()
oled.print('128x32 aktiv', 0, 0)
oled.show()
```

Snippet 5: Sans-Font mit Umlauten und Skalierung
```python
oled.clear()
oled.print("Größe Übung Öl", 0, 0, font='sans')
oled.print("Doppelt", 0, 16, font='sans', scale=2)
oled.show()
```

Snippet 6: Kreise und Rechtecke kombinieren
```python
oled.clear()
oled.draw_rect(0, 0, 60, 40)
oled.fill_circle(30, 20, 12)
oled.draw_circle(90, 32, 25)
oled.show()
```

Snippet 7: Balkendiagramm fuer Sensordaten
```python
oled.clear()
oled.print("Sensor", 0, 0)
prozent = 72
oled.progress_bar(10, 20, 108, 12, prozent)
oled.print(f"{prozent}%", 50, 40, font='sans')
oled.show()
```

Snippet 8: Wert abbilden mit map()
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
- Aufloesung falsch: bei 128x32 im Konstruktor `height=32` setzen.
- I2C-Fehler: `addr` mit `i2c.scan()` verifizieren.
- Unscharfe Ausgabe bei Umlaute: Sans-Font via `font='sans'` verwenden.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
