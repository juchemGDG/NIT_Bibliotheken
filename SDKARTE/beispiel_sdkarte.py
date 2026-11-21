"""
Beispiel fuer NIT Bibliothek: SDKarte
Zeigt: Karte einhaengen, Datei schreiben, anhaengen, lesen, Dateien auflisten, freien Speicher anzeigen
Hardware: microSD-Kartenmodul (SPI) am ESP32, microSD-Karte FAT32-formatiert (max. 32 GB)
"""

from machine import SPI, Pin
from nitbw_sdkarte import SDKarte


# --- Initialisierung ---
# SPI-Bus: SCK=18, MOSI=23, MISO=19 (D1 R32: D13, D11, D12), CS=5 (D1 R32: D10)
# Die Bibliothek stellt den Takt selbst ein (Start langsam, danach ca. 1,3 MHz).
spi = SPI(2, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
karte = SDKarte(spi, cs=5)   # haengt die Karte unter /sd ein

# --- Hauptprogramm ---
print("=== SD-Karte Grundbeispiel ===")
print("Eingehaengt:", karte.ist_eingehaengt())

# Datei neu schreiben (vorhandener Inhalt wird ersetzt)
karte.schreiben('hallo.txt', 'Hallo SD-Karte!\n')

# Weitere Zeilen anhaengen
karte.zeile_anhaengen('hallo.txt', 'Zweite Zeile')
karte.zeile_anhaengen('hallo.txt', 'Dritte Zeile')

# Ganze Datei als Text lesen
print()
print("Inhalt von", karte.pfad('hallo.txt'))
print(karte.lesen('hallo.txt'))

# Datei zeilenweise lesen (Liste ohne Zeilenumbrueche)
for nummer, zeile in enumerate(karte.zeilen('hallo.txt'), 1):
    print("Zeile {}: {}".format(nummer, zeile))

# Ordner anlegen und darin eine Datei speichern
karte.ordner_anlegen('daten')
karte.zeile_anhaengen('daten/notiz.txt', 'Datei im Unterordner')

# Dateien auflisten
print()
print("Dateien auf der Karte:", karte.dateien())
print("Dateien im Ordner daten:", karte.dateien('daten'))
print("Gibt es hallo.txt?", karte.existiert('hallo.txt'))

# Speicherplatz anzeigen
gesamt, frei = karte.speicher()
print()
print("Speicher: {:.1f} MB gesamt, {:.1f} MB frei".format(gesamt, frei))

# Vor dem Herausziehen der Karte immer aushaengen
karte.aushaengen()
print("Karte ausgehaengt - sie kann jetzt entnommen werden.")
