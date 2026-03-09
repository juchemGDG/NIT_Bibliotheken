from mlearn import MLearn

# Modell mit k=3 Nachbarn initialisieren
model = MLearn(k=3)

# CSV laden: label,feature1,feature2,...
# Passe den Dateinamen an deine Daten an.
model.load_csv('iris.csv', separator=',', target=0)

# kNN trainieren
model.train_knn()

# Vorhersage fuer ein Beispiel-Feature-Set
features = [5.1, 3.5, 1.4, 0.2]
prediction = model.predict_knn(features)
print(f"Vorhersage: {prediction}")
