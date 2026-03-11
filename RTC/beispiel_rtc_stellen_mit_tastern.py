"""
Beispiel fuer NIT Bibliothek: RTC
Zeigt: Uhr interaktiv stellen mit 3 Tastern und einem Display

Hardware:
    - DS3231 oder DS1307 RTC-Modul am ESP32 (I2C)
    - LCD 20x4 Display (I2C) ODER OLED Display (I2C)
    - 3 Taster an GPIO-Pins (mit internem PULL_DOWN)

Verkabelung Taster:
    - Taster "Hoch"   -> GPIO 25
    - Taster "Runter"  -> GPIO 26
    - Taster "Enter"   -> GPIO 27
    Jeder Taster verbindet den GPIO-Pin mit 3.3V wenn gedrueckt.
    Die internen Pull-Down-Widerstaende werden von der Bibliothek aktiviert.

Bedienung:
    1. Das Display zeigt den aktuellen Wert (Tag, Monat, Jahr, ...)
    2. Mit "Hoch" und "Runter" den Wert aendern
    3. Mit "Enter" zum naechsten Wert weiter
    4. Nach der letzten Eingabe (Sekunde) wird die RTC gestellt
"""

from nitbw_rtc import RTC
import time

# Fuer LCD-Display folgende Zeile verwenden:
from nitbw_lcd import LCD
# Fuer OLED-Display stattdessen diese Zeile verwenden:
# from nitbw_oled import OLED


# --- Konfiguration ---
# GPIO-Pins fuer die 3 Taster (an eigene Verkabelung anpassen)
PIN_HOCH   = 25
PIN_RUNTER = 26
PIN_ENTER  = 27


# --- Initialisierung RTC ---
rtc = RTC(chip='DS3231', scl=22, sda=21)

# --- Initialisierung Display ---
# LCD 20x4 (I2C-Adresse wird automatisch erkannt)
display = LCD(cols=20, rows=4, scl=22, sda=21)

# Fuer OLED stattdessen:
# display = OLED(scl=22, sda=21)


# --- Aktuelle Zeit anzeigen ---
print("=== RTC Stellen mit Tastern ===")
print("Aktuelle Zeit:", rtc.toString("DDD DD.MM.YYYY hh:mm:ss"))
print()

# --- Interaktives Stellen starten ---
# Die Methode zeigt auf dem Display nacheinander:
#   Tag -> Monat -> Jahr -> Stunde -> Minute -> Sekunde
# und laesst den Benutzer jeden Wert mit den Tastern einstellen.
#
# HINWEIS: stellenInteraktiv() blockiert das Programm!
# Die Methode laeuft in einer Schleife und wartet auf Tastendruecke.
# Erst wenn alle 6 Werte mit "Enter" bestaetigt wurden,
# wird die RTC gestellt und das Programm laeuft hier weiter.
# Zwischenergebnisse werden auf dem Display angezeigt.
print("Bitte die Uhr mit den Tastern stellen...")
print("  Hoch   (GPIO", PIN_HOCH, "): Wert erhoehen")
print("  Runter (GPIO", PIN_RUNTER, "): Wert verringern")
print("  Enter  (GPIO", PIN_ENTER, "): Naechster Wert / Bestaetigen")
print()

rtc.stellenInteraktiv(display, PIN_HOCH, PIN_RUNTER, PIN_ENTER)

# --- Neue Zeit anzeigen ---
print()
print("RTC wurde gestellt!")
print("Neue Zeit:", rtc.toString("DDD DD.MM.YYYY hh:mm:ss"))
print()

# --- Danach laeuft die Uhr weiter ---
print("Zeit laeuft weiter:")
while True:
    print(rtc.toString("hh:mm:ss"))
    time.sleep(1)
