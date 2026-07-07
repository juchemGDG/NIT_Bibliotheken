"""
NIT Bibliothek: OLED - Beispiel SVG / Bilder anzeigen

Zeigt die drei Wege, Grafiken auf dem OLED darzustellen:

  Weg 1 (am einfachsten fuer die Schule):
      SVG/BMP-Datei direkt vom ESP32 laden und anzeigen.
      SVG: nur einfache Formen (line/rect/circle/path), keine Ellipsen/Fuellungen.
      BMP: 1-Bit/24-Bit/32-Bit, Farbe -> Schwarz/Weiss.

  Weg 2 (fuer komplexe SVGs mit allen Features):
      SVG vorab auf dem PC mit 'svg_zu_bitmap.py' (GUI per Doppelklick) in
      ein MONO_VLSB-Bitmap wandeln und mit oled.show_image() anzeigen.

  Weg 3 (fuer selbst programmierte Formen):
      SVG-String mit oled.draw_svg() direkt zeichnen.
"""

from machine import I2C, Pin
from nitbw_oled import OLED

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
oled = OLED(i2c, chip='ssd1306', enabled=True)


# ---------------------------------------------------------------
# Weg 1a: SVG-Datei direkt vom ESP32 laden (einfache Formen)
# ---------------------------------------------------------------
# SVG-Datei 'icon.svg' aufs Board kopieren, dann:
# oled.show_svg('icon.svg')
# oled.show()


# ---------------------------------------------------------------
# Weg 1b: BMP-Datei direkt vom ESP32 laden
# ---------------------------------------------------------------
# BMP-Datei 'foto.bmp' aufs Board kopieren, dann:
# oled.show_bmp('foto.bmp')
# oled.show()


# ---------------------------------------------------------------
# Weg 2: PC-Konverter fuer komplexe SVGs (alle Features)
# ---------------------------------------------------------------
# Zuerst auf dem PC erzeugen (GUI per Doppelklick):
#   svg_zu_bitmap.py doppelklicken -> SVG auswaehlen -> fertig
# erzeugt z.B. 'icon_bitmap.py' -> auf den ESP32 kopieren, dann:
#
# Einzelbild (Modulname genuegt, kein 'from ... import' noetig):
# oled.show_image('icon_bitmap')
# oled.show()


# ---------------------------------------------------------------
# Mehrere Bilder als Diashow (kein Import/show pro Bild noetig)
# ---------------------------------------------------------------
# oled.slideshow(['bild1_bitmap', 'bild2_bitmap', 'bild3_bitmap'],
#                pause=1.5, loop=True)


# ---------------------------------------------------------------
# Weg 3: SVG-String direkt zeichnen (selbst programmierte Formen)
# ---------------------------------------------------------------
svg = """
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="64">
  <rect x="2" y="2" width="124" height="60"/>
  <line x1="2" y1="2" x2="126" y2="62"/>
  <circle cx="32" cy="32" r="14"/>
  <polyline points="70,50 80,20 90,45 100,15 110,40"/>
  <path d="M70 10 L120 10 L120 30 Z"/>
</svg>
"""

oled.clear()
oled.draw_svg(svg, x=0, y=0, scale=1.0)
oled.show()


# ---------------------------------------------------------------
# Ansatz A: vorab konvertiertes Bitmap anzeigen
# ---------------------------------------------------------------
# Zuerst auf dem PC erzeugen:
#   python svg_zu_bitmap.py icon.svg -W 128 -H 64
# erzeugt 'icon_bitmap.py' -> auf den ESP32 kopieren, dann:
#
# Einzelbild (Modulname genuegt, kein 'from ... import' noetig):
# oled.clear()
# oled.show_image('icon_bitmap')
# oled.show()


# ---------------------------------------------------------------
# Mehrere Bilder als Diashow (kein Import/show pro Bild noetig)
# ---------------------------------------------------------------
# oled.slideshow(['bild1_bitmap', 'bild2_bitmap', 'bild3_bitmap'],
#                pause=1.5, loop=True)
