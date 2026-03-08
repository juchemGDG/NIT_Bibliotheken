# OLED Display Treiber

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

## 🚀 Quick Start

### Installation

Die Dateien oled.py muss heruntergeladen und auf dem ESP32 gespeichert werden. 
Das folgende Beipsiel zeigt die Implementierung:

```python
from oled import OLED

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
from oled import OLED
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
from oled import OLED
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

### Beispiel 3: ADC-Sensor-Visualisierung (Scatterplot)

```python
from oled import OLED
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

### Beispiel 4: Audio-Visualizer mit draw_bar()

```python
from oled import OLED
import time

oled = OLED(scl=22, sda=21, chip='ssd1306')
oled.clear()
oled.print("Audio-Viz", 35, 0, font='sans')
time.sleep(1)

# Simulierte Sensordaten
import random

while True:
    oled.clear()
    
    # Simuliert 4 ADC-Eingänge
    values = [random.randint(0, 4095) for _ in range(4)]
    
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

### Initialisierung

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

### Grafik-Methoden

- `print(string, x=0, y=0, font='serif', scale=1, color=1)` - Text ausgeben
- `pixel(x, y, color=1)` - Einzelnen Pixel setzen
- `draw_rect(x1, y1, b, h, color=1)` - Rechteck-Umriss
- `fill_rect(x1, y1, b, h, color=1)` - Gefülltes Rechteck
- `draw_circle(x, y, r, color=1)` - Kreis-Umriss
- `fill_circle(x, y, r, color=1)` - Gefüllter Kreis
- `line(x1, y1, x2, y2, color=1)` - Beliebige Linie
- `hline(x, y, w, color=1)` - Horizontale Linie
- `vline(x, y, h, color=1)` - Vertikale Linie

### Datenvisualisierungs-Methoden

- `map(value, in_min, in_max, out_min, out_max)` - Sensordaten auf Pixel abbilden
- `progress_bar(x, y, width, height, percent, color=1)` - Fortschrittsbalken
- `draw_bar(x, y, width, height, value_percent, color=1)` - Balkendiagramm

### Verwaltungs-Methoden

- `clear()` - Display löschen
- `show()` - Display aktualisieren

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

MIT License - Siehe `../LICENSE` Datei für Details.

---

**Viel Spaß mit dem OLED Display Treiber! 🎉**
