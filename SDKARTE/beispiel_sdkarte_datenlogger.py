"""
Beispiel fuer NIT Bibliothek: SDKarte (Datenlogger)
Zeigt: Alle 2 Sekunden Zeit und Messwert als CSV-Zeile auf die SD-Karte schreiben
Hardware: microSD-Kartenmodul (SPI) am ESP32, Analogsignal (z. B. Potentiometer, LDR) an GPIO 34
"""

from machine import SPI, Pin, ADC
from nitbw_sdkarte import SDKarte
import time


# --- Initialisierung ---
# SPI-Bus: SCK=18, MOSI=23, MISO=19, CS=5
spi = SPI(2, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
karte = SDKarte(spi, cs=5)

# Analogeingang GPIO 34 (nur Eingang), Messbereich bis ca. 3.3 V
adc = ADC(Pin(34))
adc.atten(ADC.ATTN_11DB)

DATEI = 'messung.csv'
KOPF = ['Zeit_s', 'Rohwert', 'Spannung_V']
INTERVALL_MS = 2000

# --- Hauptprogramm ---
print("=== SD-Karte Datenlogger ===")
print("Schreibe alle {} s in {}".format(INTERVALL_MS // 1000, karte.pfad(DATEI)))
print("Beenden mit Ctrl+C")

start = time.ticks_ms()
try:
    while True:
        # Zeit seit Programmstart in Sekunden
        zeit_s = time.ticks_diff(time.ticks_ms(), start) / 1000

        # Messwert lesen: Rohwert (0-65535) und Spannung in Volt
        rohwert = adc.read_u16()
        spannung = adc.read_uv() / 1000000

        # Eine CSV-Zeile anhaengen. Die Kopfzeile wird nur geschrieben,
        # wenn die Datei neu ist. Kommazahlen bekommen ein Dezimalkomma,
        # damit Excel/LibreOffice sie direkt als Zahlen erkennt.
        karte.csv_anhaengen(DATEI, [round(zeit_s, 1), rohwert, round(spannung, 3)],
                            kopf=KOPF)

        print("{:7.1f} s   Rohwert {:5d}   {:.3f} V".format(zeit_s, rohwert, spannung))
        time.sleep_ms(INTERVALL_MS)

except KeyboardInterrupt:
    print("Messung beendet.")

finally:
    # Jede Zeile ist sofort gespeichert; zum Schluss sauber aushaengen
    if karte.existiert(DATEI):
        print("Zeilen in der Datei (inkl. Kopf):", len(karte.zeilen(DATEI)))
    karte.aushaengen()
    print("Karte ausgehaengt.")
