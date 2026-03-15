"""
Beispiel fuer NIT Bibliothek: MLEARN2
Zeigt: Phase 1 - Daten sammeln mit TCS3200 Farbsensor
Hardware: ESP32 + TCS3200 + Taster an GPIO 12
"""

from nitbw_tcs3200 import TCS3200
from nitbw_datensammler import DatenSammler


# --- Sensor initialisieren ---
sensor = TCS3200(out=27, s2=14, s3=12, s0=26, s1=25)
sensor.set_frequenzskalierung(2)  # 2% Skalierung


def messe_tcs3200():
    """Liest R, G, B, Clear als Feature-Liste."""
    r = sensor.frequenz_lesen('rot')
    g = sensor.frequenz_lesen('gruen')
    b = sensor.frequenz_lesen('blau')
    c = sensor.frequenz_lesen('clear')
    return [r, g, b, c]


# --- Datensammler konfigurieren ---
# Der TCS3200 hat 4 Kanaele: Rot, Gruen, Blau, Clear
sammler = DatenSammler(
    taster_pin=12,
    csv_datei='farben_tcs3200.csv',
    spaltennamen=['rot', 'gruen', 'blau', 'clear', 'label'],
    separator=','
)

# --- Labels definieren ---
labels = {
    1: "Rot",
    2: "Gruen",
    3: "Blau",
    4: "Gelb",
    5: "Weiss",
}

# --- Daten sammeln ---
sammler.sammle(
    mess_funktion=messe_tcs3200,
    labels=labels,
    messungen_pro_label=10
)
