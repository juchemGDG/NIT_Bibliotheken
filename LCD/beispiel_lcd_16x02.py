"""
Beispiel fuer NIT Bibliothek: LCD
Zeigt: Grundlegende Textausgabe auf einem 16x2 LCD
Hardware: HD44780 LCD mit PCF8574 I2C-Adapter
"""

from nitbw_lcd import LCD
from machine import I2C, Pin
import time


# --- Initialisierung ---
# Fuer 16x2 muessen Zeilen und Spalten explizit gesetzt werden.
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = LCD(i2c, addr=0x27, zeilen=2, spalten=16)


# --- Hauptprogramm ---
lcd.print("Gruesse vom NIT", 0, 0)

while True:
    lcd.print("Wir ♥ Python! ", 0, 1)
    time.sleep(1)

    lcd.clear_line(1)
    time.sleep(1)
