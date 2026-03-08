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