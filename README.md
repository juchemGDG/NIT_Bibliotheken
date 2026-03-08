# NIT Bibliotheken - OLED Display Treiber

Eine leistungsstarke und benutzerfreundliche MicroPython-Bibliothek zur Ansteuerung von OLED-Displays auf dem **ESP32**. Unterstützt sowohl **SSD1306** als auch **SH1106** Displays mit vollständiger Grafik- und Text-Funktionalität.

## ✨ Features

- **Plug-and-Play Support**: Einfache Initialisierung und Verwendung
- **Dual-Chip Unterstützung**: Kompatibel mit SSD1306 und SH1106 Controllern
- **Umfangreiche Grafik-API**: 
  - Text-Ausgabe (zwei Schriftarten)
  - Linien, Rechtecke, Kreise
  - Pixel-Level Kontrolle
- **Datenvisualisierung**:
  - `map()` - Sensordaten auf Pixel abbilden
  - `progress_bar()` - Fortschrittsbalken
  - `draw_bar()` - Einzelne Balken (Audio-Visualizer, Sensoren)
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

##### `hline(x, y, w, color=1)`

Zeichnet eine horizontale Linie.

**Parameter:**
- `x` (int): X-Startposition
- `y` (int): Y-Position (konstant für horizontale Linie)
- `w` (int): Breite/Länge der Linie
- `color` (int): 1 = An, 0 = Aus (Standard: 1)

##### `vline(x, y, h, color=1)`

Zeichnet eine vertikale Linie.

**Parameter:**
- `x` (int): X-Position (konstant für vertikale Linie)
- `y` (int): Y-Startposition
- `h` (int): Höhe/Länge der Linie
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

##### `map(value, in_min, in_max, out_min, out_max)`

Bildet einen Wert aus einem Eingabebereich auf einen Ausgabebereich ab. Perfekt für die Umrechnung von Sensordaten auf Pixel-Koordinaten.

**Parameter:**
- `value` (int/float): Der abzubildende Wert
- `in_min` (int/float): Minimaler Eingabewert
- `in_max` (int/float): Maximaler Eingabewert
- `out_min` (int/float): Minimaler Ausgabewert (z.B. 0)
- `out_max` (int/float): Maximaler Ausgabewert (z.B. 128)

**Rückgabe:** (int) Der abgebildete Wert

**Beispiel:**
```python
# 10-Bit ADC (0-1023) auf Display-Breite (0-128) abbilden
adc_value = 512
pixel_x = oled.map(adc_value, 0, 1023, 0, 128)

# 12-Bit ADC (0-4095) auf Display-Höhe (0-64) abbilden
adc_value = 2048
pixel_y = oled.map(adc_value, 0, 4095, 0, 64)
```

##### `progress_bar(x, y, width, height, percent, color=1)`

Zeichnet einen Fortschrittsbalken mit Rahmenlinie und gefülltem Inneren (für Batteriestand, Download-Progress, etc.).

**Parameter:**
- `x` (int): X-Position der oberen linken Ecke
- `y` (int): Y-Position der oberen linken Ecke
- `width` (int): Breite des Balkens
- `height` (int): Höhe des Balkens
- `percent` (int): Prozentwert (0-100)
- `color` (int): 1 = An, 0 = Aus (Standard: 1)

**Beispiel:**
```python
oled.clear()
oled.print("Battery:", 0, 0)
oled.progress_bar(0, 15, 128, 8, 75)  # 75% Batterie

oled.print("Download:", 0, 30)
oled.progress_bar(0, 40, 128, 10, 45)  # 45% Download
```

##### `draw_bar(x, y, width, height, value_percent, color=1)`

Zeichnet einen einzelnen Balken basierend auf einem Prozentwert. Kann vertikal oder horizontal ausgerichtet sein.

**Parameter:**
- `x` (int): X-Position der oberen linken Ecke
- `y` (int): Y-Position der oberen linken Ecke
- `width` (int): Breite des Balkens
- `height` (int): Höhe des Balkens
- `value_percent` (int): Der Wert als Prozentsatz (0-100)
- `color` (int): 1 = An, 0 = Aus (Standard: 1)

**Beispiel:**
```python
# Audio-Visualizer mit vertikalen Balken
oled.clear()
for i in range(5):
    # Zufällige Werte (0-100%)
    value = (i * 20 + 10)
    oled.draw_bar(i * 25, 10, 20, 50, value)

# Horizontale Balken
oled.clear()
oled.draw_bar(10, 10, 100, 6, 60)   # 60% gefüllt
oled.draw_bar(10, 20, 100, 6, 80)   # 80% gefüllt
oled.draw_bar(10, 30, 100, 6, 40)   # 40% gefüllt
```

## 🎯 Praktische Anwendungsbeispiele

### Beispiel: Digitale Uhr

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

### Beispiel: ADC-Sensor-Visualisierung (Scatterplot)

Echtzeitdarstellung von ADC-Messwerten als Scatterplot. Der Wert wird alle 0,2 Sekunden gemessen, auf die Display-Höhe gemappt und dargestellt.

```python
from OLED.oled import OLED
from machine import ADC, Pin
import time

# Initialisierung
oled = OLED(scl=22, sda=21, chip='ssd1306')

# ADC auf GPIO 32 definieren (12-Bit: 0-4095)
adc = ADC(Pin(32))

# Puffer für Datenpunkte (128 Pixel breit)
data_points = []
max_points = 128

# Konfiguration
MEASURE_INTERVAL = 0.2  # Messen alle 0,2 Sekunden
ADC_MIN = 0
ADC_MAX = 4095

oled.clear()
oled.print("ADC Sensor", 35, 0, font='sans')

last_measure = time.time()

while True:
    current_time = time.time()
    
    # Neue Messung durchführen
    if current_time - last_measure >= MEASURE_INTERVAL:
        # ADC-Wert auslesen (0-4095)
        adc_value = adc.read()
        
        # ADC-Wert auf Display-Höhe (0-63) abbilden
        # Oben = Maximalwert, Unten = Minimalwert
        pixel_y = oled.map(adc_value, ADC_MIN, ADC_MAX, 63, 0)
        
        # Datenpunkt speichern
        data_points.append(pixel_y)
        
        # Maximal 128 Punkte speichern (Bildbreite)
        if len(data_points) > max_points:
            data_points.pop(0)
        
        # Display aktualisieren
        oled.clear()
        
        # Header-Informationen
        oled.print(f"ADC: {adc_value}", 0, 0, font='sans')
        pixel_x = oled.map(adc_value, ADC_MIN, ADC_MAX, 0, 128)
        oled.print(f"Pos: {pixel_x:3d}", 70, 0, font='sans')
        
        # Referenzlinien zeichnen
        oled.hline(0, 32, 128, 0)  # Mittellinie (Mitte = 2048)
        oled.hline(0, 16, 128, 0)  # Quartil oben
        oled.hline(0, 48, 128, 0)  # Quartil unten
        
        # Scatterplot zeichnen
        for i, y in enumerate(data_points):
            pixel_x = int(i * 128 / max_points)
            oled.pixel(pixel_x, y, 1)
        
        oled.display.show()
        last_measure = current_time
    
    time.sleep(0.01)  # Kleine Pause zur CPU-Entlastung
```

### Beispiel: Audio-Visualizer mit draw_bar()

Mehrere Balken zur Visualisierung von Frequenzbändern oder mehreren Sensoren:

```python
from OLED.oled import OLED
from machine import ADC, Pin
import time
import math

# Initialisierung
oled = OLED(scl=22, sda=21, chip='ssd1306')

# 4 ADC Eingänge für verschiedene Sensoren
adc_sensors = [
    ADC(Pin(32)),  # GPIO 32
    ADC(Pin(33)),  # GPIO 33
    ADC(Pin(34)),  # GPIO 34
    ADC(Pin(35)),  # GPIO 35
]

oled.clear()
oled.print("Audio-Viz", 35, 0, font='sans')
time.sleep(1)

while True:
    oled.clear()
    
    # Lese alle 4 ADC-Werte
    values = [adc.read() for adc in adc_sensors]
    
    # Konvertiere zu Prozentwert (0-4095 -> 0-100%)
    percents = [oled.map(v, 0, 4095, 0, 100) for v in values]
    
    # Zeichne 4 vertikale Balken nebeneinander
    bar_width = 28
    bar_height = 50
    spacing = 2
    
    for i, percent in enumerate(percents):
        x = i * (bar_width + spacing) + 2
        oled.draw_bar(x, 10, bar_width, bar_height, percent)
        
        # Zahlenwert über dem Balken
        oled.print(f"{percent:3d}%", x, 62, font='sans')
    
    time.sleep(0.1)
```

### Beispiel: Fortschrittsbalken-Animation

```python
from OLED.oled import OLED
import time

oled = OLED(scl=22, sda=21, chip='ssd1306')

# Simuliere einen Download (0-100%)
oled.clear()
oled.print("Downloading...", 20, 0, font='sans')

for percent in range(0, 101, 5):
    oled.progress_bar(5, 30, 118, 12, percent)
    
    # Prozenttext
    oled.print(f"{percent:3d}%", 55, 48, font='sans')
    
    time.sleep(0.2)

oled.clear()
oled.print("Done!", 50, 30, font='sans')
```

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
