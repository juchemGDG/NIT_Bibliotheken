"""
Beispiel fuer NIT Bibliothek: MLEARN2
Zeigt: Kompletter ML-Workflow in einem Programm
       Phase 1: Daten sammeln -> Phase 2: Training -> Phase 3: Erkennung
Hardware: ESP32 + AS7262 + Taster an GPIO 12
"""

from nitbw_as7262 import AS7262
from nitbw_mlearn import MLearn
from nitbw_datensammler import DatenSammler
from machine import I2C, Pin
import time


# === KONFIGURATION ===

TASTER_PIN = 12
CSV_DATEI = 'farben_komplett.csv'
MODELL_DATEI = 'modell_komplett.json'
MESSUNGEN_PRO_LABEL = 10

labels = {
    1: "Rot",
    2: "Gruen",
    3: "Blau",
}


# === PHASE 1: DATEN SAMMELN ===

print("=" * 40)
print("PHASE 1: Daten sammeln")
print("=" * 40)

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = AS7262(i2c, led='messen')

sammler = DatenSammler(
    taster_pin=TASTER_PIN,
    csv_datei=CSV_DATEI,
    spaltennamen=['violett', 'blau', 'gruen', 'gelb', 'orange', 'rot', 'label'],
    separator=','
)

sammler.sammle(
    mess_funktion=sensor.messen_roh_liste,
    labels=labels,
    messungen_pro_label=MESSUNGEN_PRO_LABEL
)


# === PHASE 2: TRAINING ===

print()
print("=" * 40)
print("PHASE 2: Training")
print("=" * 40)

model = MLearn(k=3, lr=0.005, epochs=200)
model.load_csv(CSV_DATEI, separator=',', target=6)

# Daten aufteilen
train, test = model.split_data(anteil_test=0.2)
model.data = train

# Random Forest trainieren
model.train_forest(n_trees=5, max_depth=3)
acc = model.accuracy(test, model.predict_forest)
print("Forest Accuracy: {:.1f}%".format(acc * 100))
model.konfusionsmatrix(test, model.predict_forest)

# Modell speichern
model.save_model(MODELL_DATEI, model_type='forest')


# === PHASE 3: LIVE-ERKENNUNG ===

print()
print("=" * 40)
print("PHASE 3: Live-Erkennung")
print("=" * 40)

# Modell frisch laden (wie nach Neustart)
model2 = MLearn()
model2.load_model(MODELL_DATEI)

label_namen = {float(k): v for k, v in labels.items()}

print("Starte Erkennung... (Ctrl+C zum Beenden)")

while True:
    werte = sensor.messen_roh_liste()
    label = model2.predict_forest(werte)
    name = label_namen.get(label, "?")
    print("{} -> {} ({})".format(werte, name, label))
    time.sleep(1)
