"""
Beispiel fuer NIT Bibliothek: LCD
Zeigt: Grundlegende Textausgabe auf einem 20x4 LCD
Hardware: HD44780 LCD mit PCF8574 I2C-Adapter
"""

from nitbw_lcd import LCD
from machine import I2C, Pin
import time


# --- Initialisierung ---
# Bei mehreren Displays muessen unterschiedliche I2C-Adressen verwendet werden.
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = LCD(i2c, addr=0x27)

# --- Hauptprogramm ---
lcd.print("NIT Einheiten", 0, 0)
lcd.print("sind voellig", 0, 1)
lcd.print("COOL - wow ein öäü", 2, 2)

while True:
    lcd.print("Wir ♥ Python!", 3, 3)
    time.sleep(1)

    # Einzelne Zeilen lassen sich loeschen, ohne das gesamte Display zu leeren.
    lcd.clear_line(3)
    time.sleep(1)
