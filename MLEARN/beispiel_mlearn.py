"""
Beispiel fuer NIT Bibliothek: MLEARN
Zeigt: KNN-Training und Vorhersage mit CSV-Daten
Hardware: ESP32 mit MicroPython und CSV-Datei im Dateisystem
"""

from nitbw_mlearn import MLearn


# --- Initialisierung ---

# Modell mit k=3 Nachbarn initialisieren
model = MLearn(k=3)

# CSV laden: label,feature1,feature2,...
# Passe den Dateinamen an deine Daten an.
model.load_csv('iris.csv', separator=',', target=0)

# kNN trainieren
model.train_knn()

# --- Hauptprogramm ---
# Vorhersage fuer ein Beispiel-Feature-Set
features = [5.1, 3.5, 1.4, 0.2]
prediction = model.predict_knn(features)
print(f"Vorhersage: {prediction}")
