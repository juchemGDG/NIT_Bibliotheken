"""
Beispiel fuer NIT Bibliothek: OLED
Zeigt: Minimaler Schnellstart mit Textausgabe auf dem OLED
Hardware: OLED 128x64 (SSD1306 oder SH1106) am I2C-Bus
"""

from nitbw_oled import OLED
from machine import I2C, Pin


# --- Initialisierung ---

# I2C initialisieren
# ESP32 Standard: SCL=22, SDA=21
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Display initialisieren (SSD1306)
oled = OLED(i2c, chip='ssd1306')

# --- Hauptprogramm ---
# Text ausgeben und anzeigen
oled.print('Hello World', 0, 0)
oled.show()

# Display loeschen
oled.clear()
oled.show()
