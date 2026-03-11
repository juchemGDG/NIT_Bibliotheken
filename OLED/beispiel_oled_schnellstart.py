"""
Beispiel fuer NIT Bibliothek: OLED
Zeigt: Minimaler Schnellstart mit Textausgabe auf dem OLED
Hardware: OLED 128x64 (SSD1306 oder SH1106) am I2C-Bus
"""

from nitbw_oled import OLED


# --- Initialisierung ---

# Display initialisieren (SSD1306)
oled = OLED(scl=22, sda=21, chip='ssd1306')

# --- Hauptprogramm ---
# Text ausgeben und anzeigen
oled.print('Hello World', 0, 0)
oled.show()

# Display loeschen
oled.clear()
