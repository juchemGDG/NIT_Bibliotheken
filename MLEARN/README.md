# NIT Bibliothek: MLEARN

## Beschreibung
Die Bibliothek `nitbw_mlearn.py` bietet ML-Algorithmen fuer MicroPython: kNN,
logistische Regression, Decision Tree, Random Forest und ein flaches neuronales
Netz. Dazu kommen Hilfsfunktionen fuer Train/Test-Split, Accuracy,
Konfusionsmatrix und Modell-Persistenz. Die Bibliothek ist sensorunabhaengig
und arbeitet mit Feature-Listen von beliebigen Sensoren (z.B. TCS3200 oder AS7262).

Das Zusatzmodul `nitbw_datensammler.py` ermoeglicht interaktives Datensammeln
per Tastendruck direkt auf dem ESP32.

## Features

Algorithmen:
- kNN-Klassifikation mit Min/Max-Skalierung
- Logistische Regression mit Gradient-Descent (binaer)
- Decision-Tree auf Basis des Gini-Index (Multi-Class)
- Random Forest mit bis zu 7 Baeumen und Bootstrap-Sampling
- Flaches neuronales Netz (1 Hidden Layer, ReLU + Softmax, Backpropagation)

Bewertung und Daten:
- CSV-Import fuer Trainingsdaten (`load_csv`)
- Direkte Dateneingabe (`add_sample`)
- Datensatz-Ueberblick (`daten_info`)
- Train/Test-Split mit Zufallsmischung
- Accuracy-Berechnung
- Konfusionsmatrix mit Textausgabe

Didaktische Erklaerungsfunktionen:
- `erklaere_knn` -- zeigt die k Nachbarn mit Abstand und Abstimmung
- `erklaere_tree` -- zeigt den Entscheidungspfad Schritt fuer Schritt
- `feature_wichtigkeit` -- welche Features werden wie oft als Split genutzt?
- `vergleiche` -- trainiert und vergleicht alle Modelle auf einen Blick

Persistenz:
- Modell speichern als JSON (`save_model`)
- Modell laden (`load_model`) -- Typ wird automatisch erkannt

Interaktives Datensammeln (nitbw_datensammler.py):
- Tastendruck-gesteuertes Messen
- Automatische CSV-Erstellung mit Header
- Arbeitet mit beliebigen Sensoren

## Hardware
- ESP32 mit MicroPython
- Alternativ andere MicroPython-Boards mit ausreichend RAM
- Speicherbedarf haengt von CSV-Groesse und Modellkomplexitaet ab

Unterstuetzte Sensoren (fuer Farberkennung):
- TCS3200/TCS230 (4 Kanaele: R, G, B, Klar) -- Bibliothek in `TCS3200/`
- AS7262 (6 Kanaele: Violett bis Rot) -- Bibliothek in `AS7262/`
- Jeder andere Sensor, der eine Liste von Zahlenwerten liefert

Hinweise:
- CSV-Dateien muessen lokal auf dem Board liegen.
- Alle Features muessen numerisch sein.
- Erste CSV-Zeile wird als Header behandelt.
- Fuer das neuronale Netz: kleine Lernrate (0.001-0.01) waehlen.

## Anschluss
Kein direkter Hardwareanschluss fuer MLEARN noetig. Datenquelle ist das
Dateisystem des Boards. Fuer den Datensammler wird ein Taster benoetigt:

```text
Taster           ESP32
Ein Seite  ----> GPIO 12
Andere     ----> GND
```

Der Pin wird intern mit Pullup konfiguriert.

## Installation
- Datei `nitbw_mlearn.py` auf den ESP32 kopieren.
- Optional: `nitbw_datensammler.py` fuer interaktives Datensammeln.
- Sensor-Bibliothek (`nitbw_tcs3200.py` oder `nitbw_as7262.py`) separat kopieren.

```python
from nitbw_mlearn import MLearn
from nitbw_datensammler import DatenSammler  # optional
```

## Schnellstart
```python
from nitbw_mlearn import MLearn

model = MLearn(k=3)
model.load_csv('farben.csv', separator=',', target=6)

# kNN trainieren und vorhersagen
model.train_knn()
pred = model.predict_knn([52, 70, 151, 214, 210, 140])
print(pred)
```

## API-Referenz

### Konstruktor: `MLearn(k=3, lr=0.1, epochs=200)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `k` | `int` | `3` | Anzahl Nachbarn fuer kNN |
| `lr` | `float` | `0.1` | Lernrate fuer logReg und Netz |
| `epochs` | `int` | `200` | Trainingsdurchlaeufe fuer logReg und Netz |

### Daten

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `load_csv(filename, separator, target)` | - | CSV-Datei laden |
| `add_sample(features, label)` | - | Einzelnen Datenpunkt hinzufuegen |
| `clear_data()` | - | Alle Daten loeschen |
| `daten_info(feature_namen)` | - | Datensatz-Ueberblick anzeigen |
| `split_data(anteil_test, seed)` | (train, test) | Daten aufteilen |

### Algorithmen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `train_knn()` / `predict_knn(features)` | float | k-Naechste-Nachbarn |
| `train_logreg()` / `predict_logreg(features)` | int | Logistische Regression (0/1) |
| `predict_logreg_proba(features)` | float | Wahrscheinlichkeit fuer Klasse 1 |
| `train_tree(max_depth)` / `predict_tree(features)` | float | Decision Tree |
| `train_forest(n_trees, max_depth)` / `predict_forest(features)` | float | Random Forest (1-7 Baeume) |
| `train_netz(hidden, epochs, lr)` / `predict_netz(features)` | float | Neuronales Netz |
| `predict_netz_wahrscheinlichkeiten(features)` | dict | Wahrscheinlichkeiten pro Klasse |

### Bewertung

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `accuracy(test_data, predict_fn)` | float | Genauigkeit 0.0-1.0 |
| `konfusionsmatrix(test_data, predict_fn)` | dict | Matrix + Textausgabe |
| `vergleiche(test_data, label_namen)` | dict | Alle Modelle trainieren und vergleichen |

### Didaktik (Erklaerungsfunktionen)

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `daten_info(feature_namen)` | - | Datensatz-Ueberblick: Klassen, Wertebereiche |
| `erklaere_knn(features, label_namen)` | float | kNN-Entscheidung nachvollziehen |
| `erklaere_logreg(features, feature_namen)` | int | LogReg-Beitraege und Wahrscheinlichkeit anzeigen |
| `erklaere_tree(features, feature_namen, label_namen)` | float | Entscheidungspfad im Baum anzeigen |
| `feature_wichtigkeit(feature_namen, tree)` | dict | Splits pro Feature zaehlen |
| `vergleiche(test_data, label_namen)` | dict | Alle Modelle vergleichen |

### Persistenz

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `save_model(filename, model_type)` | - | Modell als JSON speichern |
| `load_model(filename)` | str | Modell laden, gibt Typ zurueck |

### Hilfsmethoden

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `scale_features(features)` | list | Min-Max-Skalierung (nach train_knn) |
| `euclidean_distance(p1, p2)` | float | Euklidischer Abstand |
| `gini(labels)` | float | Gini-Index einer Labelgruppe |
| `print_tree(node_index, depth)` | - | Baumstruktur anzeigen |

### Datensammler: `DatenSammler(taster_pin, csv_datei, spaltennamen, separator)`

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `sammle(mess_funktion, labels, messungen_pro_label)` | - | Interaktiv Daten sammeln |
| `sammle_einzeln(mess_funktion, label)` | list | Einzelne Messung durchfuehren |
| `get_daten()` | list | Gesammelte Daten abrufen |

## Beispiele

### Beispieldateien

Dateien im Ordner:
- `beispiel_mlearn.py` -- Grundbeispiel: Alle Algorithmen mit CSV-Daten
- `beispiel_mlearn_didaktik.py` -- Didaktische Funktionen: Daten verstehen, Modelle erklaeren
- `beispiel_mlearn_phase1_as7262.py` -- Daten sammeln mit AS7262
- `beispiel_mlearn_phase1_tcs3200.py` -- Daten sammeln mit TCS3200
- `beispiel_mlearn_phase2_training.py` -- Training und Vergleich aller Modelle
- `beispiel_mlearn_phase3_erkennung.py` -- Live-Erkennung mit gespeichertem Modell
- `beispiel_mlearn_komplett.py` -- Kompletter Workflow in einem Programm
- `test_mlearn_lego.py` -- **Kompletter ML-Workflow mit AS7262**: Daten sammeln (Phase 1),
  Laden und Ueberblick (Phase 2), Training und Bewertung (Phase 3), didaktische
  Erklaerungen (Phase 4), Speichern und Laden (Phase 5), Live-Erkennung (Phase 6).
  Standard: 12 verschiedene Legostein-Farben (konfigurierbar).

### Testdatensaetze und vorgefertigte Modelle

Fuer schnelle Tests ohne zusätzliche Datensammlung:

**`farben_lego.csv`**
  - 12 Labels (Legostein-Farben von Weiss bis Dunkelbraun)
  - 20 Messungen pro Label = 240 Datenpunkte gesamt
  - 6 Features vom AS7262-Sensor: violett, blau, gruen, gelb, orange, rot
  - Kann direkt mit `model.load_csv('farben_lego.csv', target=6)` geladen werden
  - Ideal zum Trainieren und Testen aller ML-Algorithmen

**`lego_modell.json`**
  - Vortrainiertes neuronales Netz (12 Ausgangsneuronen fuer 12 Farben)
  - Erstellt durch Trainieren auf `farben_lego.csv` mit `test_mlearn_lego.py`
  - Kann direkt geladen werden: `model.load_model('lego_modell.json')`
  - Beispiel fuer Modell-Persistenz und Live-Erkennung

### Snippet 1: Decision Tree mit Bewertung
```python
model = MLearn()
model.load_csv('daten.csv', target=6)
train, test = model.split_data(anteil_test=0.2)
model.data = train
model.train_tree(max_depth=4)
print("Accuracy: {:.1f}%".format(model.accuracy(test, model.predict_tree) * 100))
model.konfusionsmatrix(test, model.predict_tree)
model.print_tree()
```

### Snippet 2: Random Forest (7 Baeume)
```python
model = MLearn()
model.load_csv('farben.csv', target=6)
model.train_forest(n_trees=7, max_depth=3)
print(model.predict_forest([52, 70, 151, 214, 210, 140]))
```

### Snippet 3: Datensatz verstehen
```python
model = MLearn()
model.load_csv('farben.csv', target=6)
model.daten_info(['violett', 'blau', 'gruen', 'gelb', 'orange', 'rot'])
```

### Snippet 4: kNN-Entscheidung erklaeren
```python
model.train_knn()
label_namen = {1.0: "Rot", 2.0: "Gruen", 3.0: "Blau"}
model.erklaere_knn([52, 70, 151, 214, 210, 140], label_namen)
```

### Snippet 5: Baum-Entscheidungspfad und Feature-Wichtigkeit
```python
model.train_tree(max_depth=3)
feature_namen = ['violett', 'blau', 'gruen', 'gelb', 'orange', 'rot']
model.erklaere_tree([52, 70, 151, 214, 210, 140], feature_namen, label_namen)
model.feature_wichtigkeit(feature_namen)
```

### Snippet 6: Alle Modelle vergleichen
```python
train, test = model.split_data(anteil_test=0.2)
model.data = train
model.vergleiche(test)
```

### Snippet 7: Neuronales Netz mit Wahrscheinlichkeiten
```python
model = MLearn(lr=0.005, epochs=300)
model.load_csv('farben.csv', target=6)
model.train_netz(hidden=8)
probs = model.predict_netz_wahrscheinlichkeiten([52, 70, 151, 214, 210, 140])
print(probs)  # {1.0: 0.85, 2.0: 0.05, 3.0: 0.10, ...}
```

### Snippet 8: Modell speichern und laden
```python
# Speichern
model.train_forest(n_trees=5, max_depth=3)
model.save_model('mein_modell.json', model_type='forest')

# Laden (z.B. nach Neustart)
model2 = MLearn()
typ = model2.load_model('mein_modell.json')
print(model2.predict_forest([52, 70, 151, 214, 210, 140]))
```

### Snippet 9: Daten direkt vom Sensor uebergeben (ohne CSV)
```python
from machine import I2C, Pin
from nitbw_as7262 import AS7262
from nitbw_mlearn import MLearn

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = AS7262(i2c, led='messen')
model = MLearn()

# 10 Messungen als Label 1 hinzufuegen
for _ in range(10):
    model.add_sample(sensor.messen_roh_liste(), 1.0)
```

### Snippet 10: Workflow mit TCS3200 statt AS7262
```python
from nitbw_tcs3200 import TCS3200
from nitbw_mlearn import MLearn

sensor = TCS3200(out=27, s2=14, s3=12, s0=26, s1=25)
sensor.set_frequenzskalierung(2)
model = MLearn()
model.load_csv('farben_tcs.csv', target=4)  # 4 Features, Label in Spalte 4
model.train_tree(max_depth=3)
```

Praktische Hinweise / Fehlersuche:
- `Keine Trainingsdaten vorhanden.`: CSV-Pfad / Format pruefen.
- LogReg nutzt nur binaere Labels (0/1): fuer Multi-Class z.B. One-vs-Rest bilden.
- Schlechte Accuracy: Mehr Daten sammeln oder max_depth/k anpassen.
- Speicherengpaesse: Datensatz verkleinern, max_depth reduzieren, weniger Forest-Baeume.
- Netz konvergiert nicht: Lernrate senken (z.B. 0.001) oder mehr Epochen.
- `target` falsch: Zaehlung beginnt bei 0, Label in letzter Spalte = Spaltenanzahl-1.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
