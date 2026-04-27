"""
Beispiel fuer NIT Bibliothek: MLEARN2
Zeigt: Phase 1 - Daten sammeln mit AS7262 Spektralsensor
Hardware: ESP32 + AS7262 + Taster an GPIO 12
"""

from nitbw_as7262 import AS7262
from nitbw_datensammler import DatenSammler
from machine import I2C, Pin


# --- Sensor initialisieren ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = AS7262(i2c, led='messen')

# --- Datensammler konfigurieren ---
# Der AS7262 hat 6 Kanaele: Violett, Blau, Gruen, Gelb, Orange, Rot
sammler = DatenSammler(
    taster_pin=12,
    csv_datei='farben_as7262.csv',
    spaltennamen=['violett', 'blau', 'gruen', 'gelb', 'orange', 'rot', 'label'],
    separator=','
)

# --- Labels definieren ---
# Passe die Labels an deine Farben/Objekte an!
labels = {
    1: "Rot",
    2: "Gruen",
    3: "Blau",
    4: "Gelb",
    5: "Weiss",
}

# --- Daten sammeln ---
# Fuer jede Farbe wird der Sensor auf das Objekt gerichtet.
# Nach Tasterdruck wird gemessen und in die CSV geschrieben.
sammler.sammle(
    mess_funktion=sensor.messen_roh_liste,
    labels=labels,
    messungen_pro_label=10
)
