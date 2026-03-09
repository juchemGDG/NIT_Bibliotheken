"""
Beispiel fuer NIT Bibliothek: OLED
Zeigt: Grundlegende Text- und Linienausgabe auf OLED
Hardware: 128x64 OLED (SSD1306 oder SH1106) per I2C
"""

from oled import OLED
import time


# --- Initialisierung ---
# Fuer SH1106-Displays: chip='sh1106'.
# Bei anderer I2C-Adresse z. B.: addr=0x3D.
oled = OLED(scl=22, sda=21, chip='ssd1306')


# --- Hauptprogramm ---
# Nach jeder Zeichenoperation muss oled.show() aufgerufen werden.

oled.clear()

# Text mit Sans-Schriftart (unterstuetzt Umlaute und Sonderzeichen)
oled.print("NIT Einheiten", 0, 0, font='sans')
oled.print("sind voellig", 0, 10, font='sans')
oled.print("COOL - wow ein öäü", 0, 20, font='sans')

# Trennlinie
oled.hline(0, 32, 128)

# Text mit der Systemschriftart (8x8) – diese hat KEINE Umlaute
oled.print("Hallo Welt!", 0, 36)

oled.show()

while True:
    oled.print("Wir lieben Python!", 0, 50, font='sans')
    oled.show()
    time.sleep(1)

    # Bereich überschreiben: schwarzes Rechteck + neu zeichnen
    oled.fill_rect(0, 50, 128, 14, 0)
    oled.show()
    time.sleep(1)
