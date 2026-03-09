# NIT Bibliotheken - ESP32 MicroPython

Sammlung von praktischen und benutzerfreundlichen Bibliotheken für den **NIT Unterricht** am ESP32 mit **MicroPython**.

Diese Sammlung stellt optimierte Treiber und Bibliotheken zur Verfügung, um den Unterricht zu vereinfachen und schnelle Erfolge bei der Arbeit mit dem ESP32 zu erzielen.

## 📦 Verfügbare Bibliotheken

### 🖥️ OLED Display Treiber ([OLED/README.md](OLED/README.md))

Eine leistungsstarke MicroPython-Bibliothek zur Ansteuerung von OLED-Displays auf dem ESP32.

**Unterstützte Hardware:**
- **SSD1306** OLED Display (128x64 Pixel)
- **SH1106** OLED Display (128x64 Pixel)
- I2C Interface

**Features:**
- Einfache Initialisierung: `from oled import OLED`
- Vollständige Grafik-API (Linien, Kreise, Rechtecke, Text)
- Datenvisualisierung (`map()`, `progress_bar()`, `draw_bar()`)
- Zwei integrierte Schriftarten
- Keine externen Abhängigkeiten

**Quick Start:**
```python
from oled import OLED

oled = OLED(scl=22, sda=21, chip='ssd1306')
oled.print("Hello World", 0, 0)
```

Weitere Details und Beispiele finden Sie in der [OLED/README.md](OLED/README.md).

---

### 🌡️ BME280 Sensor Bibliothek ([BME280/README.md](BME280/README.md))

Eine leistungsstarke MicroPython-Bibliothek zur Ansteuerung des BME280 auf dem ESP32.

**Unterstützte Hardware:**
- **BME280** Umweltsensor (Temperatur, Luftdruck, Luftfeuchtigkeit)
- I2C Interface (`0x76` oder `0x77`)

**Features:**
- Einfache Initialisierung: `from bme280 import BME280`
- Temperatur-, Luftdruck- und Feuchtemessung
- Höhenberechnung und Kalibrierung über Luftdruck
- Taupunkt- und Hitzeindexberechnung
- Konfigurierbare Betriebsmodi und Oversampling
- Keine externen Abhängigkeiten (außer `machine`)

**Quick Start:**
```python
from machine import I2C, Pin
from bme280 import BME280

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = BME280(i2c)

temperatur, druck, feuchtigkeit = sensor.read_all()
print(f"Temperatur: {temperatur:.2f}°C")
print(f"Luftdruck: {druck:.2f} hPa")
print(f"Feuchtigkeit: {feuchtigkeit:.2f}%")

hoehe = sensor.calculate_altitude()
print(f"Höhe: {hoehe:.2f} m")
```

Weitere Details und Beispiele finden Sie in der [BME280/README.md](BME280/README.md).

---

### 🤖 MLEARN - Machine Learning ([MLEARN/README.md](MLEARN/README.md))

Eine leichtgewichtige Machine-Learning-Bibliothek für MicroPython mit Implementierungen klassischer ML-Algorithmen.

**Implementierte Algorithmen:**
- **k-Nearest Neighbors (kNN)** - Klassifikation basierend auf nächsten Nachbarn
- **Logistische Regression** - Binäre Klassifikation mit Gradient Descent
- **Decision Tree** - Multi-Class Klassifikation mit Gini-Index

**Features:**
- CSV-Datenimport mit flexiblem Format
- Automatische Feature-Normalisierung (kNN)
- Speicheroptimiert für Mikrocontroller
- Einfache API für alle drei Algorithmen
- Baumstruktur-Visualisierung für Decision Trees

**Quick Start:**
```python
from mlearn import MLearn

# k-Nearest Neighbors
model = MLearn(k=3)
model.load_csv('data.csv', separator=',', target=0)
model.train_knn()
prediction = model.predict_knn([5.1, 3.5, 1.4])

# Decision Tree
model = MLearn()
model.load_csv('data.csv')
model.train_tree(max_depth=5)
prediction = model.predict_tree([6.5, 3.0, 5.2])
```

Weitere Details und Beispiele finden Sie in der [MLEARN/README.md](MLEARN/README.md).

### 📟 LCD Display Treiber ([LCD/README.md](LCD/README.md))

Eine benutzerfreundliche MicroPython-Bibliothek zur Ansteuerung von HD44780-kompatiblen LCD-Displays auf dem ESP32.

**Unterstützte Hardware:**
- **16x2** und **20x4** LCD-Displays
- I2C Interface über **PCF8574** Portexpander

**Features:**
- Einfache Initialisierung: `from lcd import LCD`
- **Deutsche Umlaute** (äöüÄÖÜß) direkt im Text verwendbar
- **Sonderzeichen**: °C, ♥ (Herz) und HD44780-ROM-Zeichen
- Vollständige Text-API (`print`, `print_center`, `print_right`)
- Datenvisualisierung (`map()`, `progress_bar()`, `draw_bar()`)
- Eigene Zeichen (1 freier Platz, 7 für Umlaute belegt)
- Keine externen Abhängigkeiten

**Quick Start:**
```python
from lcd import LCD

lcd = LCD(scl=22, sda=21, addr=0x27)
lcd.print("Temperatur: 23.5°C", 0, 0)
lcd.print("Grüße! ♥", 0, 1)
```

Weitere Details und Beispiele finden Sie in der [LCD/README.md](LCD/README.md).

---

### 🧭 GY-261 Kompass Sensor ([COMPASS/README.md](COMPASS/README.md))

Eine leistungsstarke MicroPython-Bibliothek zur Ansteuerung des GY-261 Kompass-Sensors (HMC5883L) auf dem ESP32.

**Unterstützte Hardware:**
- **GY-261** 3-Achsen Magnetometer (HMC5883L)
- I2C Interface (`0x1E`)

**Features:**
- Einfache Initialisierung: `from compass import Compass`
- 3-Achsen Magnetfeld-Messung (X, Y, Z)
- Kompassrichtung (Heading) in Grad (0°-360°)
- Himmelsrichtungen (N, NE, E, SE, S, SW, W, NW)
- Automatische Offset-Kalibrierung
- Lokale Deklinationswinkel-Verwaltung
- 8 einstellbare Messbereiche (Gains)
- Digitale Filter und Sample Rate Einstellung
- Feldstärke-Berechnung
- Keine externen Abhängigkeiten

**Quick Start:**
```python
from machine import I2C, Pin
from compass import Compass

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
compass = Compass(i2c)

# Kompassrichtung auslesen
heading = compass.read_heading()
print(f"Heading: {heading:.1f}°")

# Himmelsrichtung
direction = compass.read_heading_direction()
print(f"Richtung: {direction}")
```

Weitere Details und Beispiele finden Sie in der [COMPASS/README.md](COMPASS/README.md).

---