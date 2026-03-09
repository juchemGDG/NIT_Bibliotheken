"""
Funktionstest für die LCD-Bibliothek (lcd.py) auf dem ESP32 mit MicroPython.
Für ein 20x4 LCD-Display.

Dieses Programm führt nacheinander viele Funktionen der LCD-Klasse vor.
Nach jedem Abschnitt wird kurz gewartet, damit man das Ergebnis auf dem
Display sehen kann. Am Ende läuft eine Endlosschleife mit einem
simulierten Sensor-Fortschrittsbalken.

Anschlüsse:
LCD (I2C-Adapter)      ESP32
GND  ──────────────>   GND
VCC  ──────────────>   5V (VIN)
SDA  ──────────────>   GPIO 21
SCL  ──────────────>   GPIO 22

Volker Rust
03.2026
"""

from lcd import LCD
import time

# ── LCD initialisieren (20x4, mit Begrüßung) ───────────────────
lcd = LCD(scl=22, sda=21, addr=0x27)


# ================================================================
# 1) Textausgabe: print, print_center, print_right
# ================================================================
lcd.clear()
lcd.print("1) Textausgabe", 0, 0)        # Linksbündig (Standard)
lcd.print_center("- zentriert -", 1)      # Zentriert
lcd.print_right("rechts >", 2)            # Rechtsbündig
lcd.print("Spalte 5", 5, 3)              # Ab Spalte 5
time.sleep(3)


# ================================================================
# 2) Deutsche Umlaute (äöüÄÖÜß) und Herz (♥)
# ================================================================
lcd.clear()
lcd.print("2) Umlaute + ♥", 0, 0)
lcd.print("äöü ÄÖÜ ß", 0, 1)            # Alle 7 Sonderzeichen
lcd.print("Größe Übung Öl", 0, 2)        # Umlaute in Wörtern
lcd.print("Wir ♥ MicroPython!", 0, 3)    # Herz-Zeichen
time.sleep(3)


# ================================================================
# 3) Einzelne Zeile löschen
# ================================================================
lcd.clear()
lcd.print("3) clear_line()", 0, 0)
lcd.print("Diese Zeile bleibt", 0, 1)
lcd.print(">>> wird gelöscht", 0, 2)
lcd.print("Diese Zeile bleibt", 0, 3)
time.sleep(2)

lcd.clear_line(2)                         # Nur Zeile 2 löschen
time.sleep(2)


# ================================================================
# 4) Hintergrundbeleuchtung ein/aus
# ================================================================
lcd.clear()
lcd.print("4) Backlight", 0, 0)
lcd.print("Licht blinkt...", 0, 1)
time.sleep(1)

for i in range(4):
    lcd.backlight(False)
    time.sleep(0.3)
    lcd.backlight(True)
    time.sleep(0.3)

time.sleep(1)


# ================================================================
# 5) Display an/aus (Inhalt bleibt erhalten)
# ================================================================
lcd.clear()
lcd.print("5) Display an/aus", 0, 0)
lcd.print("Text bleibt im RAM", 0, 1)
time.sleep(2)

lcd.display(False)                        # Display aus (Text bleibt)
time.sleep(1)
lcd.display(True)                         # Display wieder an
time.sleep(2)


# ================================================================
# 6) Cursor und Blinken
# ================================================================
lcd.clear()
lcd.print("6) Cursor + Blink", 0, 0)

lcd.print("Unterstrich:", 0, 1)
lcd.cursor(True)                          # Unterstrich-Cursor an
time.sleep(2)
lcd.cursor(False)

lcd.print("Blink-Cursor:", 0, 2)
lcd.blink(True)                           # Blink-Cursor an
time.sleep(2)
lcd.blink(False)

time.sleep(1)


# ================================================================
# 7) Scrollen (Display-Inhalt verschieben)
# ================================================================
lcd.clear()
lcd.print("7) Scroll-Demo", 0, 0)
lcd.print("<-- links  rechts-->", 0, 1)
time.sleep(1)

for i in range(6):                        # 6x nach links
    lcd.scroll_links()
    time.sleep(0.3)

for i in range(12):                       # 12x nach rechts (6 zurück + 6 weiter)
    lcd.scroll_rechts()
    time.sleep(0.3)

for i in range(6):                        # 6x zurück zur Mitte
    lcd.scroll_links()
    time.sleep(0.3)

time.sleep(1)


# ================================================================
# 8) Eigenes Zeichen auf Platz 7 (0-6 = Umlaute)
# ================================================================
lcd.clear()
lcd.print("8) Eigenes Zeichen", 0, 0)

# Thermometer-Symbol auf den freien Platz 7 laden
thermo = [0b00100,
          0b01010,
          0b01010,
          0b01010,
          0b01010,
          0b11111,
          0b11111,
          0b01110]

lcd.eigenes_zeichen(7, thermo)

lcd.print("Thermometer:", 0, 1)
lcd.zeichen_schreiben(7, 13, 1)          # Thermometer anzeigen

lcd.print("Herz ist schon da:", 0, 2)
lcd.print("♥", 19, 2)                    # Herz über Text-Mapping

time.sleep(3)


# ================================================================
# 9) map()-Funktion demonstrieren
# ================================================================
lcd.clear()
lcd.print("9) map()-Funktion", 0, 0)

# Simuliert einen ADC-Wert (0-4095) → Spalte (0-19) und Prozent (0-100)
for adc_wert in range(0, 4096, 500):
    spalte = lcd.map(adc_wert, 0, 4095, 0, 19)
    prozent = lcd.map(adc_wert, 0, 4095, 0, 100)
    lcd.clear_line(1)
    lcd.print(f"ADC: {adc_wert:4d}", 0, 1)
    lcd.clear_line(2)
    lcd.print(f"Spalte:{spalte:2d} %:{prozent:3d}", 0, 2)
    time.sleep(0.5)

time.sleep(1)


# ================================================================
# 10) Fortschrittsbalken (progress_bar)
#     Achtung: Überschreibt CGRAM-Plätze 0-5 (Umlaute)!
#     Nach diesem Test funktionieren Umlaute nicht mehr korrekt.
# ================================================================
lcd.clear()
lcd.print("10) Fortschritt", 0, 0)
lcd.print("Lade...", 0, 1)

# Fortschrittsbalken von 0% bis 100% füllen
for p in range(0, 101, 2):
    lcd.progress_bar(3, p)
    lcd.print(f"{p:3d}%", 16, 1)
    time.sleep(0.05)

lcd.print("Fertig!", 0, 2)
time.sleep(2)


# ================================================================
# 11) draw_bar() – Mehrere Balken nebeneinander
# ================================================================
lcd.clear()
lcd.print("11) draw_bar()", 0, 0)
lcd.print("T", 0, 1)                     # Label Temperatur
lcd.print("F", 10, 1)                    # Label Feuchte

# Simulierte Werte hochzählen
for i in range(0, 101, 5):
    lcd.draw_bar(2, 0, 9, i)             # Balken 1 (Spalte 0-8)
    lcd.draw_bar(2, 10, 9, 100 - i)      # Balken 2 (Spalte 10-18)
    lcd.print(f"{i:3d}%", 0, 3)
    lcd.print(f"{100-i:3d}%", 10, 3)
    time.sleep(0.1)

time.sleep(2)


# ================================================================
# 12) Endlosschleife: Simulierter Sensor-Monitor
# ================================================================
lcd.clear()
lcd.print_center("== Sensor-Monitor ==", 0)

import random
zaehler = 0

while True:
    # Simulierte Sensorwerte
    temperatur = 200 + random.randint(-30, 30)   # 17.0 - 23.0 °C (x10)
    feuchte = random.randint(30, 80)              # 30-80 %

    # Werte formatiert anzeigen
    lcd.print(f"Temp: {temperatur/10:.1f}°C  ", 0, 1)
    lcd.print(f"Feuchte: {feuchte:2d}%  ", 0, 2)

    # Fortschrittsbalken für Feuchte in Zeile 3
    lcd.progress_bar(3, feuchte)

    zaehler += 1

    # Alle 20 Durchläufe kurz den Zähler anzeigen
    if zaehler % 20 == 0:
        lcd.print_right(f"#{zaehler}", 0)

    time.sleep(1)
