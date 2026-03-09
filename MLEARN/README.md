# MLearn - MicroPython Machine Learning Bibliothek

Eine leichtgewichtige Machine-Learning-Bibliothek für MicroPython mit Implementierungen für k-Nearest Neighbors, Logistische Regression und Decision Trees.

## 🎯 Features

- **k-Nearest Neighbors (kNN)**: Klassifikation basierend auf den k nächsten Nachbarn
- **Logistische Regression**: Binäre Klassifikation mit Gradient Descent
- **Decision Tree**: Multi-Class Klassifikation mit Gini-Index
- **CSV-Datenimport**: Einfaches Laden von Trainingsdaten
- **Speichereffizient**: Optimiert für MicroPython auf Mikrocontrollern

## 📦 Installation

Kopieren Sie die Datei `mlearn.py` auf Ihren MicroPython-Mikrocontroller (z.B. ESP32, Raspberry Pi Pico).

```python
from mlearn import MLearn
```

## 🚀 Verwendungsbeispiele

### 1. k-Nearest Neighbors (kNN)

```python
from mlearn import MLearn

# Modell initialisieren (k=3 Nachbarn)
model = MLearn(k=3)

# Trainingsdaten aus CSV laden
# Format: label,feature1,feature2,...
model.load_csv('iris.csv', separator=',', target=0)

# kNN trainieren (normalisiert die Daten)
model.train_knn()

# Vorhersage
features = [5.1, 3.5, 1.4, 0.2]
prediction = model.predict_knn(features)
print(f"Vorhersage: {prediction}")
```

### 2. Logistische Regression

```python
from mlearn import MLearn

# Modell initialisieren
# lr: Lernrate (default: 0.1)
# epochs: Anzahl Trainingsdurchläufe (default: 200)
model = MLearn(lr=0.01, epochs=1000)

# Daten laden (binäre Klassifikation: 0 oder 1)
model.load_csv('binary_data.csv', separator=',', target=0)

# Logistische Regression trainieren
model.train_logreg()

# Vorhersage (gibt 0 oder 1 zurück)
features = [2.5, 1.8]
prediction = model.predict_logreg(features)
print(f"Klasse: {prediction}")
```

### 3. Decision Tree

```python
from mlearn import MLearn

# Modell initialisieren
model = MLearn()

# Daten laden (unterstützt Multi-Class)
model.load_csv('multiclass_data.csv', separator=',', target=0)

# Decision Tree trainieren
# max_depth: Maximale Baumtiefe (default: 3)
model.train_tree(max_depth=5)

# Baumstruktur ausgeben
print("Baumstruktur:")
model.print_tree()

# Vorhersage
features = [6.5, 3.0, 5.2, 2.0]
prediction = model.predict_tree(features)
print(f"Vorhersage: {prediction}")
```

## 📊 CSV-Datenformat

Die CSV-Datei sollte folgendes Format haben:

```csv
label,feature1,feature2,feature3
0,5.1,3.5,1.4
1,6.2,2.9,4.3
0,4.9,3.0,1.4
```

**Hinweise:**
- Erste Zeile wird als Header übersprungen
- `target`-Parameter gibt die Spalte des Labels an (default: 0)
- Alle Werte müssen numerisch sein

## 🔧 API-Referenz

### Konstruktor

```python
MLearn(k=3, lr=0.1, epochs=200)
```

**Parameter:**
- `k` (int): Anzahl der Nachbarn für kNN (default: 3)
- `lr` (float): Lernrate für logistische Regression (default: 0.1)
- `epochs` (int): Anzahl Trainingsdurchläufe für logistische Regression (default: 200)

### Methoden

#### Daten laden

```python
load_csv(filename, separator=',', target=0)
```
Lädt Trainingsdaten aus einer CSV-Datei.

---

#### k-Nearest Neighbors

```python
train_knn()
```
Trainiert das kNN-Modell (berechnet Min/Max-Werte für Normalisierung).

```python
predict_knn(features)
```
Gibt die vorhergesagte Klasse basierend auf den k nächsten Nachbarn zurück.

---

#### Logistische Regression

```python
train_logreg()
```
Trainiert die logistische Regression mit Gradient Descent.

```python
predict_logreg(features)
```
Gibt 0 oder 1 zurück (binäre Klassifikation).

---

#### Decision Tree

```python
train_tree(max_depth=3)
```
Trainiert einen Decision Tree mit Gini-Index.

```python
predict_tree(features)
```
Gibt die vorhergesagte Klasse zurück (Multi-Class möglich).

```python
print_tree(node_index=0, depth=0)
```
Gibt die Baumstruktur in der Konsole aus.

## 📝 Vollständiges Beispiel

```python
from mlearn import MLearn

# Beispieldaten als CSV speichern
csv_content = """label,sepal_length,sepal_width,petal_length
0,5.1,3.5,1.4
0,4.9,3.0,1.4
1,7.0,3.2,4.7
1,6.4,3.2,4.5
2,6.3,3.3,6.0
2,5.8,2.7,5.1
"""

with open('example.csv', 'w') as f:
    f.write(csv_content)

# 1. kNN Klassifikation
print("=" * 40)
print("k-Nearest Neighbors")
print("=" * 40)
model_knn = MLearn(k=3)
model_knn.load_csv('example.csv', target=0)
model_knn.train_knn()
print(f"Vorhersage: {model_knn.predict_knn([5.0, 3.4, 1.5])}")

# 2. Decision Tree
print("\n" + "=" * 40)
print("Decision Tree")
print("=" * 40)
model_tree = MLearn()
model_tree.load_csv('example.csv', target=0)
model_tree.train_tree(max_depth=3)
model_tree.print_tree()
print(f"Vorhersage: {model_tree.predict_tree([6.5, 3.0, 5.0])}")
```

## ⚙️ Systemanforderungen

- MicroPython 1.19 oder höher
- Mindestens 32 KB RAM verfügbar (abhängig von Datengröße)

## 📚 Anwendungsfälle

- **Sensordaten-Klassifikation**: Klassifizierung von Sensor-Messwerten
- **Pattern Recognition**: Erkennung von Mustern in IoT-Daten
- **Anomalie-Erkennung**: Erkennung ungewöhnlicher Zustände
- **Einfache Vorhersagen**: Temperatur, Luftfeuchtigkeit, etc.

## ⚠️ Einschränkungen

- Keine Feature-Normalisierung bei logistischer Regression (manuell durchführen falls nötig)
- Decision Trees können bei sehr tiefen Bäumen viel Speicher benötigen
- Keine Unterstützung für fehlende Werte (NaN)
- Alle Features müssen numerisch sein

## 📄 Lizenz

Siehe [LICENSE](../LICENSE) Datei im Repository.

## 🤝 Beiträge

Beiträge sind willkommen! Erstellen Sie einen Pull-Request oder öffnen Sie ein Issue.

---

**Hinweis**: Diese Bibliothek ist für Bildungszwecke und einfache IoT-Anwendungen konzipiert. Für komplexe ML-Aufgaben verwenden Sie bitte vollwertige Frameworks wie scikit-learn oder TensorFlow.
