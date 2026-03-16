"""
Beispiel fuer NIT Bibliothek: TOENE
Zeigt: Einzelne Noten und kurze Melodie mit Notennamen
Hardware: ESP32, passiver Piezo-Lautsprecher an PWM-Pin
"""

from machine import Pin
from nitbw_toene import TOENE


# --- Initialisierung ---
speaker = TOENE(Pin(15), geschwindigkeit=60)


# --- Hauptprogramm ---
speaker.ton(("A4", 1 / 4))
speaker.ton(("B4", 1 / 2))
speaker.ton(("C5", 1 / 8))

kurzes_lied = [
    ("C4", 1 / 4), ("D4", 1 / 4), ("E4", 1 / 4),
    ("P", 1 / 2),
    ("F4", 1 / 4), ("G4", 1 / 4),
]

speaker.spiele_lied(kurzes_lied)
speaker.stop()
print("Ende")
