"""
Testprogramm für die LCD-Bibliothek (lcd.py) auf dem ESP32 mit MicroPython.
Für ein 16x2 LCD-Display.

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

# Hier wird das Objekt lcd für ein 16x2 Display erstellt.        # *****
# zeilen=2 und spalten=16 müssen angegeben werden!
lcd = LCD(scl=22, sda=21, addr=0x27, zeilen=2, spalten=16)       # *****

# ── Setup-Teil ──────────────────────────────────────────────────
# Der folgende Text wird NUR einmal geschrieben (wie setup() in Arduino)!

# Umlaute funktionieren direkt – dank eigener Zeichen im CGRAM:
lcd.print("Grüße vom NIT", 0, 0)                                  # *****

# ── Loop-Teil ───────────────────────────────────────────────────
# Endlosschleife (wie loop() in Arduino)
while True:
    lcd.print("Wir ♥ Python! ", 0, 1)
    time.sleep(1)

    lcd.clear_line(1)
    time.sleep(1)
