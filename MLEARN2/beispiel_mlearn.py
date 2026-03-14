"""
Beispiel fuer NIT Bibliothek: MLEARN
Zeigt: Verschiedene ML-Algorithmen mit CSV-Daten
Hardware: ESP32 mit MicroPython und CSV-Datei im Dateisystem
"""

from nitbw_mlearn import MLearn


# --- Initialisierung ---

model = MLearn(k=3)

# CSV laden: feature1,feature2,...,label
# Passe den Dateinamen und target an deine Daten an.
model.load_csv('iris.csv', separator=',', target=0)

# --- Hauptprogramm ---

# kNN trainieren und vorhersagen
model.train_knn()
features = [5.1, 3.5, 1.4, 0.2]
prediction = model.predict_knn(features)
print("kNN Vorhersage: {}".format(prediction))

# Decision Tree trainieren
model.train_tree(max_depth=3)
prediction = model.predict_tree(features)
print("Tree Vorhersage: {}".format(prediction))
model.print_tree()

# Random Forest trainieren (5 Baeume)
model.train_forest(n_trees=5, max_depth=3)
prediction = model.predict_forest(features)
print("Forest Vorhersage: {}".format(prediction))

# Neuronales Netz trainieren
model.train_netz(hidden=8, epochs=200, lr=0.01)
prediction = model.predict_netz(features)
print("Netz Vorhersage: {}".format(prediction))
probs = model.predict_netz_wahrscheinlichkeiten(features)
print("Wahrscheinlichkeiten: {}".format(probs))
