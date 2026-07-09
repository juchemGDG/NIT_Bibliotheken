"""
Beispiel fuer NIT Bibliothek: MP3
Zeigt: Grundlegende Wiedergabe vom MP3-TF-16P
Hardware: ESP32, MP3-TF-16P, Lautsprecher, MicroSD-Karte
"""

from machine import Pin, UART
from time import sleep
from nitbw_mp3 import MP3TF16P


# --- Initialisierung ---

# UART fuer MP3-Modul (an eigenes Board anpassen)
uart = UART(2, baudrate=9600, tx=Pin(17), rx=Pin(16))

# Player initialisieren
player = MP3TF16P(uart)
player.set_source(MP3TF16P.DEVICE_TF)
player.set_volume(20)

# --- Hauptprogramm ---

print("Starte Titel 0001 im MP3-Ordner...")
player.play_mp3(1)
sleep(5)

print("Pausiere 2 Sekunden...")
player.pause()
sleep(2)

print("Setze Wiedergabe fort...")
player.resume()
sleep(5)

print("Stoppe Wiedergabe")
player.stop()
