"""
Beispiel fuer NIT Bibliothek: TOENE
Zeigt: Komplettes Lied als Liste (Alle meine Entchen)
Hardware: ESP32, passiver Piezo-Lautsprecher an PWM-Pin
"""

from machine import Pin
from nitbw_toene import TOENE


# --- Initialisierung ---
speaker = TOENE(Pin(15), geschwindigkeit=60)

entchen = [
    ("C4", 1 / 4), ("D4", 1 / 4), ("E4", 1 / 4), ("F4", 1 / 4),
    ("G4", 1 / 2), ("G4", 1 / 2),
    ("A4", 1 / 4), ("A4", 1 / 4), ("A4", 1 / 4), ("A4", 1 / 4),
    ("G4", 1),
    ("A4", 1 / 4), ("A4", 1 / 4), ("A4", 1 / 4), ("A4", 1 / 4),
    ("G4", 1),
    ("F4", 1 / 4), ("F4", 1 / 4), ("F4", 1 / 4), ("F4", 1 / 4),
    ("E4", 1 / 2), ("E4", 1 / 2),
    ("D4", 1 / 4), ("D4", 1 / 4), ("D4", 1 / 4), ("D4", 1 / 4),
    ("C4", 1),
]


# --- Hauptprogramm ---
speaker.spiele_lied(entchen)
speaker.stop()
print("Ende")
