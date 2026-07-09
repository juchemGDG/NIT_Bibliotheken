"""
Beispiel fuer NIT Bibliothek: MP3
Zeigt: Wiedergabe aus numerischen Ordnern und Wiederholung
Hardware: ESP32, MP3-TF-16P, Lautsprecher, MicroSD-Karte
"""

from machine import Pin, UART
from time import sleep
from nitbw_mp3 import MP3TF16P


# --- Initialisierung ---

uart = UART(2, baudrate=9600, tx=Pin(17), rx=Pin(16))
player = MP3TF16P(uart)
player.set_source(MP3TF16P.DEVICE_TF)
player.set_volume(18)

# --- Hauptprogramm ---

# Spielt Datei 003 aus Ordner 01 (Dateiname typischerweise 003.mp3)
print("Spiele Ordner 01, Titel 003")
player.play_folder(folder=1, track=3)
sleep(6)

print("Aktiviere Titelwiederholung")
player.repeat_current(True)
sleep(6)

print("Deaktiviere Titelwiederholung und starte Zufallswiedergabe")
player.repeat_current(False)
player.random_all()
sleep(8)

player.stop()
print("Fertig")
