# NIT Bibliotheken - OLED Display Treiber

Eine leistungsstarke und benutzerfreundliche MicroPython-Bibliothek zur Ansteuerung von OLED-Displays auf dem **ESP32**. Unterstützt sowohl **SSD1306** als auch **SH1106** Displays mit vollständiger Grafik- und Text-Funktionalität.

## ✨ Features

- **Plug-and-Play Support**: Einfache Initialisierung und Verwendung
- **Dual-Chip Unterstützung**: Kompatibel mit SSD1306 und SH1106 Controllern
- **Umfangreiche Grafik-API**: 
  - Text-Ausgabe (zwei Schriftarten)
  - Linien, Rechtecke, Kreise
  - Pixel-Level Kontrolle
- **Integrierte Bitmap-Schriftart**: Serifenlose 5x7 Schriftart ohne externe Abhängigkeiten
- **Keine externen Abhängigkeiten**: Vollständige Treiber-Implementierung
- **I2C Interface**: Standard I2C Kommunikation mit konfigurierbare Adressen

## 📋 Hardware-Anforderungen

- **Mikrocontroller**: ESP32
- **Display**: OLED Display 128x64 Pixel
  - SSD1306 oder SH1106 Controller
  - I2C Interface
- **Verbindungen**:
  - SCL Pin (Standard: GPIO 22)
  - SDA Pin (Standard: GPIO 21)
  - GND und VCC (3.3V)

## 🚀 Quick Start

### Installation

1. Die Dateien in den OLED-Ordner in Ihr Projekt kopieren
2. Das Modul importieren:

```python
from OLED.oled import OLED

# Display initialisieren (SSD1306)
oled = OLED(scl=22, sda=21, chip='ssd1306')

# Text ausgeben
oled.print("Hello World", 0, 0)

# Display löschen
oled.clear()
```

## 📚 Verwendungsbeispiele

### Beispiel 1: Einfache Text-Ausgabe

```python
from OLED.oled import OLED
import time

# Initialisierung
oled = OLED(scl=22, sda=21, chip='ssd1306')

# Nach dem INIT-Logo (2 Sekunden) startet dieser Code
oled.clear()

# Text mit Systemschriftart
oled.print("NIT Bibliotheken", 0, 0)
oled.print("OLED Display", 0, 10)

time.sleep(2)

# Text mit serifenloser Schriftart
oled.clear()
oled.print("Text in SANS", 0, 0, font='sans')
oled.print("Vergrößert x2", 0, 20, font='sans', scale=2)

time.sleep(2)
```

### Beispiel 2: Geometrische Formen

```python
from OLED.oled import OLED
import time

oled = OLED(scl=22, sda=21, chip='ssd1306')
oled.clear()

# Rechtecke
oled.draw_rect(10, 10, 50, 30)      # Umriss
oled.fill_rect(70, 10, 50, 30)      # Gefüllt

time.sleep(1)
oled.clear()

# Kreise
oled.draw_circle(40, 40, 15)        # Umriss
oled.fill_circle(90, 40, 15)        # Gefüllt

time.sleep(1)
oled.clear()

# Linien
oled.line(0, 0, 127, 63)            # Diagonale
oled.line(127, 0, 0, 63)            # Andere Diagonale

time.sleep(1)
```

### Beispiel 3: Pixelgrafiken

```python
from OLED.oled import OLED
import time

oled = OLED(scl=22, sda=21, chip='ssd1306')
oled.clear()

# Einzelne Pixel setzen
for x in range(0, 128, 2):
    oled.pixel(x, 32, 1)

time.sleep(2)
```

### Beispiel 4: Mehrere Displays (SH1106)

```python
from OLED.oled import OLED

# Display mit SH1106 Controller
oled = OLED(scl=22, sda=21, chip='sh1106', addr=0x3c)

oled.clear()
oled.print("SH1106 Display", 0, 0)
oled.print("Funktioniert!", 0, 10)
```

### Beispiel 5: Display deaktivieren (ohne Hardware)

```python
from OLED.oled import OLED

# Nützlich für Tests ohne Hardware
oled = OLED(enabled=False)

# Alle Befehle werden sicher ignoriert
oled.print("Dies wird nicht angezeigt")
oled.draw_rect(10, 10, 50, 30)
```

## 🔌 PIN-Konfiguration (Beispiel ESP32)

```
ESP32 PIN       Funktion          Standardwert
GPIO 22         I2C SCL           scl=22
GPIO 21         I2C SDA           sda=21
GND             Ground            
3.3V            Power             
```

Sie können die Pins anpassen, wenn Sie andere GPIO-Pins verwenden möchten:

```python
oled = OLED(scl=5, sda=4, chip='ssd1306')  # Alternative Pins
```

## 📖 API Referenz

### Klasse: OLED

#### Initialisierung

```python
OLED(scl=22, sda=21, chip='ssd1306', enabled=True, i2c_id=0, addr=0x3c)
```

**Parameter:**
- `scl` (int): SCL Pin-Nummer (Standard: 22)
- `sda` (int): SDA Pin-Nummer (Standard: 21)
- `chip` (str): Display-Typ - `'ssd1306'` oder `'sh1106'` (Standard: `'ssd1306'`)
- `enabled` (bool): Display aktivieren/deaktivieren (Standard: `True`)
- `i2c_id` (int): I2C Bus ID (Standard: 0)
- `addr` (int): I2C Adresse des Displays (Standard: 0x3c)

#### Text & Grafik Methoden

##### `print(string, x=0, y=0, font='serif', scale=1, color=1)`

Gibt Text auf dem Display aus.

**Parameter:**
- `string` (str): Text zum Anzeigen
- `x` (int): X-Position in Pixeln (Standard: 0)
- `y` (int): Y-Position in Pixeln (Standard: 0)
- `font` (str): `'serif'` (8x8 Systemschrift) oder `'sans'` (5x7 Bitmap) (Standard: `'serif'`)
- `scale` (int): Vergrößerungsfaktor für 'sans' Schrift (Standard: 1)
- `color` (int): 1 = An (weiß), 0 = Aus (schwarz) (Standard: 1)

**Beispiel:**
```python
oled.print("Guten Morgen!", 10, 20)
oled.print("GROSS", 0, 40, font='sans', scale=2)
```

##### `pixel(x, y, color=1)`

Setzt einen einzelnen Pixel.

**Parameter:**
- `x` (int): X-Koordinate
- `y` (int): Y-Koordinate
- `color` (int): 1 = An, 0 = Aus (Standard: 1)

##### `draw_rect(x1, y1, b, h, color=1)`

Zeichnet einen leeren Rechteck-Umriss.

**Parameter:**
- `x1` (int): X-Position der oberen linken Ecke
- `y1` (int): Y-Position der oberen linken Ecke
- `b` (int): Breite des Rechtecks
- `h` (int): Höhe des Rechtecks
- `color` (int): 1 = An, 0 = Aus (Standard: 1)

##### `fill_rect(x1, y1, b, h, color=1)`

Zeichnet ein gefülltes Rechteck.

**Parameter:** (gleich wie `draw_rect`)

##### `draw_circle(x, y, r, color=1)`

Zeichnet einen leeren Kreis (Bresenham-Algorithmus).

**Parameter:**
- `x` (int): X-Position des Mittelpunkts
- `y` (int): Y-Position des Mittelpunkts
- `r` (int): Radius des Kreises
- `color` (int): 1 = An, 0 = Aus (Standard: 1)

##### `fill_circle(x, y, r, color=1)`

Zeichnet einen gefüllten Kreis.

**Parameter:** (gleich wie `draw_circle`)

##### `line(x1, y1, x2, y2, color=1)`

Zeichnet eine Linie zwischen zwei Punkten.

**Parameter:**
- `x1` (int): X-Koordinate Startpunkt
- `y1` (int): Y-Koordinate Startpunkt
- `x2` (int): X-Koordinate Endpunkt
- `y2` (int): Y-Koordinate Endpunkt
- `color` (int): 1 = An, 0 = Aus (Standard: 1)

##### `clear()`

Löscht das gesamte Display (schwarzer Bildschirm).

**Beispiel:**
```python
oled.clear()
```

##### `show()`

Aktualisiert das Display manuell (wird normalerweise automatisch aufgerufen).

**Beispiel:**
```python
oled.show()
```

## 🎯 Praktisches Anwendungsbeispiel: Digitale Uhr

```python
from OLED.oled import OLED
import time
from machine import RTC

# Initialisierung
oled = OLED(scl=22, sda=21, chip='ssd1306')

# Beispiel-Zeit einrichten (Stunde, Minute, Sekunde)
rtc = RTC()
rtc.datetime((2025, 3, 8, 0, 14, 30, 0, 0))  # (Jahr, Monat, Tag, Wochentag, Stunde, Minute, Sekunde)

while True:
    oled.clear()
    
    # Aktuelle Zeit lesen
    zeit = rtc.datetime()
    stunden = zeit[4]
    minuten = zeit[5]
    sekunden = zeit[6]
    
    # Zeit formatieren
    zeit_str = f"{stunden:02d}:{minuten:02d}:{sekunden:02d}"
    
    # Anzeigen
    oled.print("Digitale Uhr", 30, 10)
    oled.print(zeit_str, 40, 30, font='sans', scale=3)
    
    time.sleep(1)
```

## 🛠️ Fehlerbehebung

### Problem: Display zeigt nichts an
- **Lösung**: Überprüfen Sie die Verkabelung (SCL/SDA/GND/VCC)
- Überprüfen Sie die I2C Adresse: `i2c.scan()` sollte Ihre Adresse anzeigen
- Probieren Sie die Alternative Adresse `addr=0x3d`

### Problem: Text ist unleserlich
- **Lösung**: Verwenden Sie `font='sans'` für bessere Lesbarkeit auf kleinen Displays
- Verwenden Sie `scale=2` zum Vergrößern

### Problem: SH1106 wird nicht erkannt
- **Lösung**: Verwenden Sie `chip='sh1106'` in der Initialisierung
- Überprüfen Sie die I2C Adresse (oft 0x3c oder 0x3d)

## 📝 Lizenz

MIT License - Siehe LICENSE Datei für Details.

## 👨‍💻 Autor

Stephan Juchem

---

**Viel Spaß mit der OLED-Bibliothek! 🎉**
