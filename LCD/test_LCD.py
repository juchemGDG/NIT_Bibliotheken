"""
Testprogramm für die LCD-Bibliothek (lcd.py) auf dem ESP32 mit MicroPython.
Für ein 20x4 LCD-Display.

Diese Datei entspricht funktional dem Arduino-Beispiel LCD_ZSL_V7.ino
und demonstriert die grundlegende Verwendung der LCD-Klasse.

Anschlüsse:
LCD (I2C-Adapter)      ESP32
GND  ──────────────>   GND
VCC  ──────────────>   5V (VIN)
SDA  ──────────────>   GPIO 21
SCL  ──────────────>   GPIO 22

Achtung Adresse: 0x27 evtl. für andere Displays anpassen. Oft z.B. 0x3F.

Viel Spaß
Volker Rust
03.2026 / v1
"""

from lcd import LCD     # *****  LCD-Bibliothek importieren
import time

# Hier wird das Objekt lcd erstellt (20x4 Display).              # *****
# Bei unterschiedlichen Adressen kann man 2 oder mehr Displays gleichzeitig nutzen.
# Diese benötigen dann einen anderen Objektnamen.
# Tipp: Lötpunkte auf der Rückseite des Displays (A0/A1/A2) ändern die I2C-Adresse.
lcd = LCD(scl=22, sda=21, addr=0x27)                              # *****

# ── Setup-Teil ──────────────────────────────────────────────────
# Der folgende Text wird NUR einmal geschrieben (wie setup() in Arduino)!

# Der Text beginnt bei Spalte 0 in Zeile 0.
lcd.print("NIT Einheiten", 0, 0)                                  # *****

# Umlaute funktionieren direkt – dank eigener Zeichen im CGRAM:
lcd.print("sind völlig", 0, 1)                            # *****

# Text weiter rechts durch Spaltenverschiebung:
lcd.print("COOL - wow ein öäü", 2, 2)

# ── Loop-Teil ───────────────────────────────────────────────────
# Endlosschleife (wie loop() in Arduino)
while True:
    lcd.print("Wir ♥ Python!", 3, 3)
    time.sleep(1)

    # Bestimmte Stellen lassen sich löschen, indem man sie mit
    # Leerzeichen überschreibt. Löschen des ganzen Displays mit:
    # lcd.clear()
    lcd.clear_line(3)
    time.sleep(1)
