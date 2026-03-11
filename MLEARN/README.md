# NIT Bibliothek: MLEARN

## Beschreibung
Die Bibliothek `nitbw_mlearn.py` bietet drei klassische Lernverfahren fuer MicroPython: kNN, logistische Regression und Decision Tree. Sie ist bewusst kompakt gehalten und eignet sich fuer Unterricht, Prototyping und kleine Klassifikationsaufgaben auf dem ESP32.

## Features
- CSV-Import fuer Trainingsdaten (`load_csv`)
- kNN-Klassifikation mit Min/Max-Skalierung
- Euklidische Distanzberechnung fuer kNN
- Logistische Regression mit Gradient-Descent
- Sigmoid mit Overflow-Schutz
- Decision-Tree auf Basis des Gini-Index
- Mehrklassenfaehige Baumklassifikation
- Ausgabe der Baumstruktur (`print_tree`)
- Einheitliche API in einer Klasse
- Fuer MicroPython optimierte, kleine Implementierung

## Hardware
- ESP32 mit MicroPython
- Alternativ andere MicroPython-Boards mit ausreichend RAM
- Speicherbedarf haengt von CSV-Groesse und Baumtiefe ab
- Hinweise:
  - CSV-Dateien muessen lokal auf dem Board liegen.
  - Alle Features muessen numerisch sein.
  - Erste CSV-Zeile wird als Header behandelt.

## Anschluss
Kein direkter Hardwareanschluss noetig. Datenquelle ist das Dateisystem des Boards.

## Installation
- Datei `nitbw_mlearn.py` auf den ESP32 kopieren.
- Import im Projekt: `from nitbw_mlearn import MLearn`.

## Schnellstart
```python
from nitbw_mlearn import MLearn

# Modell und Daten
model = MLearn(k=3)
model.load_csv('iris.csv', separator=',', target=0)

# kNN trainieren und vorhersagen
model.train_knn()
pred = model.predict_knn([5.1, 3.5, 1.4, 0.2])
print(pred)
```

## API-Referenz
Konstruktor: `MLearn(k=3, lr=0.1, epochs=200)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `k` | `int` | `3` | Anzahl Nachbarn fuer kNN |
| `lr` | `float` | `0.1` | Lernrate fuer logistische Regression |
| `epochs` | `int` | `200` | Trainingsdurchlaeufe fuer logistische Regression |

Wichtige Methoden:
- `load_csv(filename, separator=',', target=0)`
- `train_knn()` / `predict_knn(features)`
- `train_logreg()` / `predict_logreg(features)`
- `train_tree(max_depth=3)` / `predict_tree(features)`
- `print_tree(node_index=0, depth=0)`

Hilfsmethoden (intern auch direkt nutzbar):
- `scale_features(features)`
- `euclidean_distance(p1, p2)`
- `gini(labels)`

## Beispiele
Dateien im Ordner:
- `MLEARN/beispiel_mlearn.py`

Snippet 1: Logistische Regression
```python
model = MLearn(lr=0.01, epochs=500)
model.load_csv('binary.csv', target=0)
model.train_logreg()
print(model.predict_logreg([2.3, 1.1]))
```

Snippet 2: Decision Tree
```python
model = MLearn()
model.load_csv('data.csv', target=0)
model.train_tree(max_depth=4)
model.print_tree()
```

Snippet 3: CSV mit anderem Separator
```python
model.load_csv('messwerte.csv', separator=';', target=2)
```

Snippet 4: Decision Tree Struktur ausgeben
```python
model = MLearn()
model.load_csv('data.csv', target=0)
model.train_tree(max_depth=3)
model.print_tree()  # Zeigt Entscheidungsregeln im Terminal
pred = model.predict_tree([5.0, 3.0, 1.5, 0.3])
print(f"Baumvorhersage: {pred}")
```

Snippet 5: Feature-Skalierung manuell nutzen
```python
# Nach train_knn() stehen min/max bereit
model.train_knn()
skaliert = model.scale_features([5.1, 3.5, 1.4, 0.2])
print(f"Skalierte Features: {skaliert}")
```

Snippet 6: Euklidische Distanz zwischen zwei Datenpunkten
```python
dist = model.euclidean_distance([1.0, 2.0], [4.0, 6.0])
print(f"Distanz: {dist:.2f}")
```

Praktische Hinweise/Fehlersuche:
- `Keine Trainingsdaten vorhanden.`: CSV-Pfad/Format pruefen.
- Schlechte Ergebnisse: Features vorab skalieren bzw. Datenqualitaet pruefen.
- Speicherengpaesse: Datensatz verkleinern oder `max_depth` reduzieren.
- Falsche Labelspalte: `target` korrekt setzen.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
