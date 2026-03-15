"""
Beispiel fuer NIT Bibliothek: MLEARN2
Zeigt: Phase 2 - Training und Vergleich aller ML-Modelle
Hardware: ESP32 mit MicroPython und CSV-Datei im Dateisystem
"""

from nitbw_mlearn import MLearn


# --- Daten laden ---
# Passe Dateiname und target-Spalte an deine CSV an!
# target = Index der Label-Spalte (letzte Spalte bei AS7262: 6, bei TCS3200: 4)
model = MLearn(k=3, lr=0.005, epochs=300)
model.load_csv('farben_as7262.csv', separator=',', target=6)

print("Datenpunkte geladen: {}".format(len(model.data)))

# --- Daten aufteilen (80% Training, 20% Test) ---
train, test = model.split_data(anteil_test=0.2, seed=42)
print("Training: {}, Test: {}".format(len(train), len(test)))

# Trainingsdaten setzen
model.data = train

# ============================================================
# Modell 1: kNN
# ============================================================
print("\n=== kNN (k={}) ===".format(model.k))
model.train_knn()
acc = model.accuracy(test, model.predict_knn)
print("Accuracy: {:.1f}%".format(acc * 100))

# ============================================================
# Modell 2: Decision Tree
# ============================================================
print("\n=== Decision Tree ===")
model.train_tree(max_depth=4)
acc = model.accuracy(test, model.predict_tree)
print("Accuracy: {:.1f}%".format(acc * 100))
model.print_tree()

# ============================================================
# Modell 3: Random Forest (5 Baeume)
# ============================================================
print("\n=== Random Forest (5 Baeume) ===")
model.train_forest(n_trees=5, max_depth=3)
acc = model.accuracy(test, model.predict_forest)
print("Accuracy: {:.1f}%".format(acc * 100))

# ============================================================
# Modell 4: Neuronales Netz
# ============================================================
print("\n=== Neuronales Netz ===")
model.train_netz(hidden=8, epochs=300, lr=0.005)
acc = model.accuracy(test, model.predict_netz)
print("Accuracy: {:.1f}%".format(acc * 100))

# --- Konfusionsmatrix des besten Modells ---
print("\n=== Konfusionsmatrix (Forest) ===")
model.konfusionsmatrix(test, model.predict_forest)

# --- Bestes Modell speichern ---
model.save_model('modell.json', model_type='forest')
print("\nModell gespeichert als 'modell.json'")
