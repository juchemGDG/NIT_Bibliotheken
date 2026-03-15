"""
Beispiel fuer NIT Bibliothek: MLEARN2
Zeigt: Phase 3 - Live-Erkennung mit gespeichertem Modell
Hardware: ESP32 + AS7262 (oder TCS3200) + gespeichertes Modell
"""

from nitbw_mlearn import MLearn
from nitbw_as7262 import AS7262
import time


# --- Sensor initialisieren ---
sensor = AS7262(sda=21, scl=22, led=True)

# --- Modell laden ---
model = MLearn()
typ = model.load_model('modell.json')
print("Modelltyp: {}".format(typ))

# --- Label-Namen (muessen zu den Trainingsdaten passen) ---
label_namen = {
    1.0: "Rot",
    2.0: "Gruen",
    3.0: "Blau",
    4.0: "Gelb",
    5.0: "Weiss",
}

# --- Vorhersagefunktion je nach Modelltyp waehlen ---
if typ == 'tree':
    predict_fn = model.predict_tree
elif typ == 'forest':
    predict_fn = model.predict_forest
elif typ == 'knn':
    predict_fn = model.predict_knn
elif typ == 'netz':
    predict_fn = model.predict_netz

# --- Endlosschleife: Messen und Erkennen ---
print("\nStarte Live-Erkennung... (Ctrl+C zum Beenden)")

while True:
    werte = sensor.messen_roh_liste()
    label = predict_fn(werte)
    name = label_namen.get(label, "Unbekannt")

    print("Werte: {} -> {} ({})".format(werte, name, label))
    time.sleep(1)
