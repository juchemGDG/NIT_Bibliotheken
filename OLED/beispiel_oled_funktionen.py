"""
Beispiel fuer NIT Bibliothek: OLED
Zeigt: Uebersicht ueber zentrale OLED-Funktionen
Hardware: 128x64 OLED (SSD1306 oder SH1106) per I2C
"""

from oled import OLED
import time
import random


# --- Initialisierung ---
oled = OLED(scl=22, sda=21, chip='ssd1306')


# --- Hauptprogramm ---
# ================================================================
# 1) Textausgabe: Systemschrift (serif) und Sans-Schrift
# ================================================================
oled.clear()
oled.print("1) Textausgabe", 0, 0)             # Systemschrift 8x8
oled.print("Sans-Font", 0, 12, font='sans')    # Sans-Font 5x7
oled.print("SansX2", 0, 24, font='sans', scale=2)  # Sans doppelt
oled.print("Position x=60", 60, 50)            # Verschoben
oled.show()
time.sleep(3)


# ================================================================
# 2) Umlaute und Sonderzeichen (nur Sans-Font)
# ================================================================
oled.clear()
oled.print("2) Umlaute+Sonder", 0, 0)
oled.print("äöü ÄÖÜ ß", 0, 12, font='sans')
oled.print("Größe Übung Öl", 0, 22, font='sans')
oled.print("20.5°C  3.50€", 0, 32, font='sans')
oled.print("(nur mit font='sans')", 0, 50, font='sans')
oled.show()
time.sleep(3)


# ================================================================
# 3) Linien: hline, vline, line
# ================================================================
oled.clear()
oled.print("3) Linien", 0, 0)
oled.hline(0, 12, 128)                         # Horizontale Linie
oled.vline(64, 14, 50)                         # Vertikale Linie
oled.line(0, 14, 127, 63)                      # Diagonale
oled.line(127, 14, 0, 63)                      # Kreuz-Diagonale
oled.show()
time.sleep(3)


# ================================================================
# 4) Rechtecke: draw_rect, fill_rect
# ================================================================
oled.clear()
oled.print("4) Rechtecke", 0, 0)
oled.draw_rect(5, 14, 40, 25)                  # Umriss
oled.fill_rect(55, 14, 40, 25)                 # Gefüllt
oled.draw_rect(105, 14, 20, 25)                # Klein
oled.fill_rect(10, 45, 108, 15)                # Breiter Balken
oled.show()
time.sleep(3)


# ================================================================
# 5) Kreise: draw_circle, fill_circle
# ================================================================
oled.clear()
oled.print("5) Kreise", 0, 0)
oled.draw_circle(30, 38, 20)                   # Umriss
oled.fill_circle(90, 38, 20)                   # Gefüllt
oled.draw_circle(60, 38, 10)                   # Klein
oled.show()
time.sleep(3)


# ================================================================
# 6) Pixel und Muster
# ================================================================
oled.clear()
oled.print("6) Pixel", 0, 0)

# Schachbrettmuster zeichnen
for x in range(0, 128, 4):
    for y in range(14, 64, 4):
        oled.pixel(x, y)

oled.show()
time.sleep(3)


# ================================================================
# 7) Display löschen (clear)
# ================================================================
oled.clear()
oled.print("7) clear()", 0, 0)
oled.print("Gleich wird", 0, 14, font='sans')
oled.print("alles geloescht...", 0, 24, font='sans')
oled.show()
time.sleep(2)

oled.clear()  # Löscht das gesamte Display
time.sleep(1)

oled.print("...und neu!", 0, 28, font='sans')
oled.show()
time.sleep(2)


# ================================================================
# 8) Invertierte Farben
# ================================================================
oled.clear()
oled.print("8) Invertiert", 0, 0)

# Weißer Hintergrund mit schwarzem Text
oled.fill_rect(0, 14, 128, 20)                 # Weiße Fläche
oled.print("Invertiert", 5, 18, color=0)       # Schwarzer Text
oled.print("Normal", 5, 40)                    # Normaler Text
oled.show()
time.sleep(3)


# ================================================================
# 9) map()-Funktion demonstrieren
# ================================================================
oled.clear()
oled.print("9) map()", 0, 0)

# Simuliert ADC-Werte (0-4095) → Pixel-X (0-127) und Prozent (0-100)
for adc_wert in range(0, 4096, 500):
    pixel_x = oled.map(adc_wert, 0, 4095, 0, 127)
    prozent = oled.map(adc_wert, 0, 4095, 0, 100)

    # Nur den Textbereich überschreiben
    oled.fill_rect(0, 12, 128, 20, 0)
    oled.print(f"ADC:{adc_wert:4d}", 0, 14, font='sans')
    oled.print(f"X:{pixel_x:3d} %:{prozent:3d}", 0, 24, font='sans')

    # Visualisierung: Punkt auf einer Linie
    oled.fill_rect(0, 40, 128, 24, 0)
    oled.hline(0, 50, 128)                     # Achse
    oled.fill_circle(pixel_x, 50, 3)           # Positionsmarker
    oled.show()
    time.sleep(0.5)

time.sleep(1)


# ================================================================
# 10) Fortschrittsbalken (progress_bar)
# ================================================================
oled.clear()
oled.print("10) progress_bar", 0, 0)
oled.print("Lade...", 0, 14, font='sans')

for p in range(0, 101, 2):
    # Balkenbereich löschen und neu zeichnen
    oled.fill_rect(10, 30, 110, 14, 0)
    oled.progress_bar(10, 30, 108, 12, p)

    # Prozent-Anzeige aktualisieren
    oled.fill_rect(90, 14, 38, 10, 0)
    oled.print(f"{p:3d}%", 90, 14, font='sans')
    oled.show()
    time.sleep(0.05)

oled.print("Fertig!", 0, 50, font='sans')
oled.show()
time.sleep(2)


# ================================================================
# 11) draw_bar() – Vertikale Balken nebeneinander
# ================================================================
oled.clear()
oled.print("11) draw_bar()", 0, 0)

for i in range(0, 101, 5):
    # Balkenbereich löschen
    oled.fill_rect(0, 12, 128, 52, 0)

    # 4 vertikale Balken mit unterschiedlichen Werten
    oled.draw_bar(10, 14, 12, 46, i)
    oled.draw_bar(35, 14, 12, 46, 100 - i)
    oled.draw_bar(60, 14, 12, 46, (i + 50) % 101)
    oled.draw_bar(85, 14, 12, 46, abs(50 - i) * 2)

    # Labels
    oled.print("A", 14, 0, font='sans')
    oled.print("B", 39, 0, font='sans')
    oled.print("C", 64, 0, font='sans')
    oled.print("D", 89, 0, font='sans')
    oled.show()
    time.sleep(0.1)

time.sleep(2)


# ================================================================
# 12) Formen-Komposition: Gesicht zeichnen
# ================================================================
oled.clear()
oled.print("12) Komposition", 0, 0)

# Gesicht
oled.draw_circle(64, 38, 24)               # Kopf
oled.fill_circle(54, 32, 3)                # Auge links
oled.fill_circle(74, 32, 3)                # Auge rechts
oled.draw_circle(64, 42, 8)                # Mund (Kreis)
oled.fill_rect(56, 34, 16, 8, 0)           # Obere Hälfte Mund löschen = Lächeln
oled.show()
time.sleep(3)


# ================================================================
# 13) Endlosschleife: Simulierter Sensor-Monitor
# ================================================================
zaehler = 0

while True:
    oled.clear()

    # Titel
    oled.print("Sensor-Monitor", 14, 0, font='sans')
    oled.hline(0, 9, 128)

    # Simulierte Sensorwerte
    temperatur = 200 + random.randint(-30, 30)   # 17.0 - 23.0 °C (x10)
    feuchte = random.randint(30, 80)              # 30-80 %

    # Werte formatiert anzeigen (Sans-Font für °-Zeichen)
    oled.print(f"Temp: {temperatur/10:.1f}°C", 0, 14, font='sans')
    oled.print(f"Feuchte: {feuchte}%", 0, 24, font='sans')

    # Fortschrittsbalken für Feuchte
    oled.print("Feuchte:", 0, 40, font='sans')
    oled.progress_bar(0, 50, 100, 10, feuchte)
    oled.print(f"{feuchte}%", 104, 51, font='sans')

    zaehler += 1
    if zaehler % 10 == 0:
        oled.print(f"#{zaehler}", 100, 0, font='sans')

    oled.show()
    time.sleep(1)
