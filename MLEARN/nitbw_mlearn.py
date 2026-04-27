"""
NIT Bibliothek: MLEARN - ML-Algorithmen fuer MicroPython
Fuer ESP32 mit MicroPython

Version:    2.2.1
Autor:      Stephan Juchem, Volker Rust / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Enthaelt kNN, logistische Regression, Decision Tree, Random Forest
und ein flaches neuronales Netz fuer Lern- und Demozwecke.
Dazu: Train/Test-Split, Accuracy, Konfusionsmatrix, Modell-Speicherung
und didaktische Erklaerungsfunktionen.

Die Bibliothek ist sensorunabhaengig. Man uebergibt Feature-Listen,
die z.B. vom TCS3200 (3-4 Kanaele) oder AS7262 (6 Kanaele) stammen.
"""

import math
import json

# =====================================================================
# Zufallszahlen (einfacher Linearer Kongruenzgenerator)
# MicroPython hat kein random-Modul auf allen Boards. Deshalb
# bauen wir uns hier einen eigenen, minimalen Zufallsgenerator.
# =====================================================================

_seed = 42

def _set_seed(s):
    """Setzt den Startwert fuer den Zufallsgenerator (Reproduzierbarkeit)."""
    global _seed
    _seed = s

def _rand_int(n):
    """Gibt eine Zufallszahl zwischen 0 und n-1 zurueck."""
    global _seed
    _seed = (_seed * 1103515245 + 12345) & 0x7FFFFFFF
    return _seed % n


class MLearn:
    """
    Bietet ML-Verfahren fuer kleine Datensaetze auf dem ESP32:
    kNN, logistische Regression, Decision Tree, Random Forest
    und ein flaches neuronales Netz (Perzeptron mit einer Hidden-Layer).

    Unterstuetzte Hardware:
    - ESP32 mit MicroPython
    - Andere MicroPython-faehige Boards mit ausreichendem RAM

    Schnittstelle: Dateisystem (CSV) oder direkte Dateneingabe
    """

    def __init__(self, k=3, lr=0.1, epochs=200):
        """
        Erstellt ein neues MLearn-Objekt.

        Args:
            k:      Anzahl Nachbarn fuer kNN (Standard: 3)
            lr:     Lernrate fuer logistische Regression und Netz (Standard: 0.1)
            epochs: Trainingsdurchlaeufe fuer logReg und Netz (Standard: 200)
        """
        self.k = k
        self.lr = lr
        self.epochs = epochs

        # Rohdaten: Liste von (features, label) Tupeln
        self.data = []

        # Fuer kNN-Skalierung (Min/Max jedes Features)
        self.min_values = None
        self.max_values = None

        # Fuer logistische Regression (Gewichte)
        self.weights = None

        # Fuer Decision Tree (Liste von Knoten-Dicts)
        self.tree = []

        # Fuer Random Forest (Liste von Baeumen)
        self.forest = []

        # Fuer neuronales Netz (Gewichte und Biases)
        self._nn_w1 = None  # Gewichte Input -> Hidden
        self._nn_b1 = None  # Bias Hidden
        self._nn_w2 = None  # Gewichte Hidden -> Output
        self._nn_b2 = None  # Bias Output
        self._nn_labels = None  # Zuordnung Index -> Label
        self._nn_min = None  # Min-Werte fuer Skalierung
        self._nn_max = None  # Max-Werte fuer Skalierung

    # =============================================================
    # DATEN LADEN UND AUFTEILEN
    # =============================================================

    def load_csv(self, filename, separator=',', target=0):
        """
        Laedt Trainingsdaten aus einer CSV-Datei.

        Die erste Zeile wird als Header uebersprungen.
        Die Zielspalte (Label) wird durch 'target' angegeben.
        Alle anderen Spalten sind Features.

        Args:
            filename:  Pfad zur CSV-Datei auf dem ESP32
            separator: Trennzeichen (Standard: Komma)
            target:    Index der Zielspalte (Standard: 0)

        Beispiel-CSV (target=6, also letzte Spalte):
            violett,blau,gruen,gelb,orange,rot,label
            52,70,151,214,210,140,1
        """
        try:
            with open(filename, 'r') as f:
                first = True
                for line in f:
                    if first:
                        first = False
                        continue  # Header ueberspringen
                    values = line.strip().split(separator)
                    if not values or len(values) <= target:
                        continue
                    label = float(values[target])
                    features = [float(values[i]) for i in range(len(values)) if i != target]
                    self.data.append((features, label))
        except Exception as e:
            print("Fehler beim Laden der CSV-Datei:", e)

    def add_sample(self, features, label):
        """
        Fuegt einen einzelnen Datenpunkt zu den Trainingsdaten hinzu.

        Praktisch, wenn man Daten direkt vom Sensor uebergibt,
        statt sie erst in eine CSV-Datei zu schreiben.

        Args:
            features: Liste von Zahlenwerten (z.B. [52, 70, 151, 214, 210, 140])
            label:    Klassennummer (z.B. 1.0 fuer "Rot")
        """
        self.data.append((list(features), float(label)))

    def clear_data(self):
        """Loescht alle geladenen Trainingsdaten."""
        self.data = []

    def daten_info(self, feature_namen=None):
        """
        Gibt einen Ueberblick ueber den geladenen Datensatz.

        Zeigt Anzahl Datenpunkte, Klassen, Samples pro Klasse
        und Wertebereich pro Feature. Sollte immer als Erstes
        aufgerufen werden, um die Daten zu verstehen.

        Args:
            feature_namen: Optionale Liste mit Namen fuer die Features.
                           Z.B. ['violett','blau','gruen','gelb','orange','rot']
                           Falls None, wird 'Feature 0', 'Feature 1', ... verwendet.
        """
        if not self.data:
            print("Keine Daten geladen.")
            return

        n_punkte = len(self.data)
        n_features = len(self.data[0][0])

        # Klassen zaehlen
        klassen = {}
        for _, label in self.data:
            klassen[label] = klassen.get(label, 0) + 1

        print("\n=== Datensatz-Info ===")
        print("Datenpunkte: {}".format(n_punkte))
        print("Features:    {}".format(n_features))
        print("Klassen:     {}".format(len(klassen)))
        print()

        # Samples pro Klasse
        print("Samples pro Klasse:")
        for label in sorted(klassen):
            balken = '#' * min(klassen[label], 30)
            print("  Klasse {:>4.0f}: {:>4d}  {}".format(label, klassen[label], balken))
        print()

        # Wertebereich pro Feature
        print("Wertebereich pro Feature:")
        for f in range(n_features):
            werte = [d[0][f] for d in self.data]
            f_min = min(werte)
            f_max = max(werte)
            f_mean = sum(werte) / len(werte)
            name = feature_namen[f] if feature_namen and f < len(feature_namen) else "Feature {}".format(f)
            print("  {:>12s}: min={:<8.1f} max={:<8.1f} mittel={:.1f}".format(
                name, f_min, f_max, f_mean))
        print()

    def split_data(self, anteil_test=0.2, seed=None):
        """
        Teilt die Daten in Trainings- und Testdaten auf.

        Das ist wichtig, um zu pruefen, ob das Modell auch mit
        NEUEN Daten richtig liegt (nicht nur mit den Trainingsdaten).

        Die Aufteilung ist standardmaessig zufaellig (bei jedem Aufruf
        anders). Mit seed=<Zahl> kann man einen festen Startwert setzen,
        um reproduzierbare Ergebnisse zu erhalten.

        Args:
            anteil_test: Anteil der Testdaten (0.0 bis 1.0, Standard: 20%)
            seed:        Startwert fuer den Zufallsgenerator
                         (None = zufaellig, Zahl = reproduzierbar)

        Returns:
            tuple: (train_data, test_data) -- zwei Listen von (features, label)
        """
        if seed is None:
            import time
            seed = time.ticks_ms()
        _set_seed(seed)

        # Daten mischen (Fisher-Yates-Shuffle)
        shuffled = self.data[:]
        for i in range(len(shuffled) - 1, 0, -1):
            j = _rand_int(i + 1)
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]

        # Aufteilen
        n_test = max(1, int(len(shuffled) * anteil_test))
        test_data = shuffled[:n_test]
        train_data = shuffled[n_test:]

        return train_data, test_data

    # =============================================================
    # BEWERTUNG: ACCURACY UND KONFUSIONSMATRIX
    # =============================================================

    def accuracy(self, test_data, predict_fn):
        """
        Berechnet die Genauigkeit (Accuracy) eines Modells.

        Accuracy = Anzahl richtige Vorhersagen / Gesamtanzahl

        Args:
            test_data:  Liste von (features, label) Tupeln
            predict_fn: Vorhersagefunktion, z.B. self.predict_knn

        Returns:
            float: Genauigkeit von 0.0 bis 1.0 (1.0 = 100% richtig)
        """
        if not test_data:
            return 0.0

        richtig = 0
        for features, label in test_data:
            vorhersage = predict_fn(features)
            if vorhersage == label:
                richtig += 1

        return richtig / len(test_data)

    def konfusionsmatrix(self, test_data, predict_fn):
        """
        Erstellt eine Konfusionsmatrix und gibt sie als Text aus.

        Die Konfusionsmatrix zeigt, welche Klassen verwechselt werden.
        Zeilen = tatsaechliche Klasse, Spalten = vorhergesagte Klasse.
        Auf der Diagonale stehen die richtigen Vorhersagen.

        Args:
            test_data:  Liste von (features, label) Tupeln
            predict_fn: Vorhersagefunktion

        Returns:
            dict: Matrix als verschachteltes Dictionary
                  matrix[echtes_label][vorhergesagtes_label] = Anzahl
        """
        # Alle vorkommenden Labels sammeln
        alle_labels = sorted(set(l for _, l in test_data))

        # Matrix initialisieren (alle Felder auf 0)
        matrix = {}
        for echt in alle_labels:
            matrix[echt] = {}
            for pred in alle_labels:
                matrix[echt][pred] = 0

        # Matrix fuellen
        for features, echt in test_data:
            pred = predict_fn(features)
            if pred in matrix[echt]:
                matrix[echt][pred] += 1

        # Textausgabe
        print("\nKonfusionsmatrix (Zeile=echt, Spalte=vorhergesagt):")
        header = "       " + "".join("{:>6.0f}".format(l) for l in alle_labels)
        print(header)
        for echt in alle_labels:
            zeile = "{:>6.0f} ".format(echt)
            for pred in alle_labels:
                zeile += "{:>6d}".format(matrix[echt][pred])
            print(zeile)
        print()

        return matrix

    # =============================================================
    # kNN (k-Naechste-Nachbarn)
    #
    # Idee: Ein neuer Datenpunkt wird der Klasse zugeordnet,
    # die unter seinen k naechsten Nachbarn am haeufigsten vorkommt.
    # =============================================================

    def train_knn(self):
        """
        Bereitet kNN vor, indem Min/Max-Werte fuer Skalierung berechnet werden.

        Skalierung ist wichtig, damit alle Features gleich stark zaehlen.
        Ohne Skalierung wuerden Features mit grossen Zahlenwerten
        (z.B. 0-10000) die Features mit kleinen Werten (z.B. 0-10) dominieren.
        """
        if not self.data:
            raise ValueError("Keine Trainingsdaten vorhanden.")

        first_features = self.data[0][0]
        self.min_values = first_features[:]
        self.max_values = first_features[:]

        for features, _ in self.data:
            self.min_values = [min(a, b) for a, b in zip(self.min_values, features)]
            self.max_values = [max(a, b) for a, b in zip(self.max_values, features)]

    def scale_features(self, features):
        """
        Skaliert Features auf den Bereich 0 bis 1 (Min-Max-Normalisierung).

        Args:
            features: Liste von Feature-Werten

        Returns:
            list: Skalierte Werte zwischen 0.0 und 1.0
        """
        return [
            (f - mn) / (mx - mn) if mx != mn else 0
            for f, mn, mx in zip(features, self.min_values, self.max_values)
        ]

    def euclidean_distance(self, p1, p2):
        """
        Berechnet den euklidischen Abstand zwischen zwei Punkten.

        Das ist der "normale" Abstand, den man auch mit einem Lineal
        messen wuerde -- nur in beliebig vielen Dimensionen.

        Args:
            p1: Erster Punkt (Liste von Zahlen)
            p2: Zweiter Punkt (Liste von Zahlen)

        Returns:
            float: Abstand
        """
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

    def predict_knn(self, features):
        """
        Sagt die Klasse eines neuen Datenpunkts per kNN vorher.

        Ablauf:
        1) Neuen Punkt und alle Trainingspunkte skalieren
        2) Abstand zu allen Trainingspunkten berechnen
        3) Die k naechsten Nachbarn finden
        4) Mehrheitsentscheidung: Welches Label kommt am haeufigsten vor?

        Args:
            features: Feature-Liste des neuen Datenpunkts

        Returns:
            float: Vorhergesagtes Label
        """
        if self.min_values is None:
            raise ValueError("Bitte zuerst train_knn() ausfuehren.")

        scaled_query = self.scale_features(features)
        distances = []

        for stored_features, label in self.data:
            scaled_stored = self.scale_features(stored_features)
            dist = self.euclidean_distance(scaled_query, scaled_stored)
            distances.append((dist, label))

        distances.sort(key=lambda x: x[0])
        k_nearest = distances[:self.k]

        counts = {}
        for _, label in k_nearest:
            counts[label] = counts.get(label, 0) + 1

        return max(counts, key=counts.get)

    def erklaere_knn(self, features, label_namen=None):
        """
        Erklaert eine kNN-Vorhersage Schritt fuer Schritt.

        Zeigt die k naechsten Nachbarn mit Abstand und Label,
        damit man nachvollziehen kann, warum kNN so entschieden hat.
        Macht kNN transparent statt "magisch".

        Args:
            features:     Feature-Liste des neuen Datenpunkts
            label_namen:  Optionales Dict {label: "Name"}
                          z.B. {1.0: "Rot", 2.0: "Gruen"}
        """
        if self.min_values is None:
            raise ValueError("Bitte zuerst train_knn() ausfuehren.")

        scaled_query = self.scale_features(features)
        distances = []

        for stored_features, label in self.data:
            scaled_stored = self.scale_features(stored_features)
            dist = self.euclidean_distance(scaled_query, scaled_stored)
            distances.append((dist, label, stored_features))

        distances.sort(key=lambda x: x[0])
        k_nearest = distances[:self.k]

        # Abstimmung
        counts = {}
        for _, label, _ in k_nearest:
            counts[label] = counts.get(label, 0) + 1
        vorhersage = max(counts, key=counts.get)

        # Ergebnis anzeigen
        v_name = ""
        if label_namen and vorhersage in label_namen:
            v_name = " ({})".format(label_namen[vorhersage])

        print("\n=== kNN-Erklaerung (k={}) ===".format(self.k))
        print("Eingabe: {}".format(features))
        print("Vorhersage: {}{}".format(vorhersage, v_name))
        print()

        for i, (dist, label, orig) in enumerate(k_nearest):
            l_name = ""
            if label_namen and label in label_namen:
                l_name = " ({})".format(label_namen[label])
            print("  Nachbar {}: Abstand {:.2f}, Label {}{}".format(
                i + 1, dist, label, l_name))
            print("             Werte: {}".format(orig))

        print()
        print("Abstimmung:")
        for label in sorted(counts):
            l_name = ""
            if label_namen and label in label_namen:
                l_name = " ({})".format(label_namen[label])
            print("  Label {}{}: {} Stimme(n)".format(label, l_name, counts[label]))
        print()

        return vorhersage

    # =============================================================
    # LOGISTISCHE REGRESSION
    #
    # Idee: Eine Gerade (oder Hyperebene) trennt zwei Klassen.
    # Die Sigmoid-Funktion macht aus dem Ergebnis eine
    # Wahrscheinlichkeit zwischen 0 und 1.
    # Nur fuer ZWEI Klassen (binaere Klassifikation) geeignet!
    # =============================================================

    def sigmoid(self, z):
        """
        Die Sigmoid-Funktion: verwandelt jede Zahl in einen Wert zwischen 0 und 1.

        Fuer grosse positive z -> nahe 1
        Fuer grosse negative z -> nahe 0
        Fuer z=0 -> genau 0.5
        """
        if z < -500:
            return 0.0
        elif z > 500:
            return 1.0
        return 1 / (1 + math.exp(-z))

    def train_logreg(self):
        """
        Trainiert die logistische Regression mit Gradient Descent.

        In jeder Epoche wird jeder Datenpunkt einmal durchlaufen
        und die Gewichte ein kleines Stueck in die richtige Richtung
        angepasst (gesteuert durch die Lernrate lr).

        Hinweis:
        Logistische Regression in dieser Bibliothek ist binaer,
        die Labels muessen also 0 oder 1 sein.
        """
        if not self.data:
            raise ValueError("Keine Trainingsdaten vorhanden.")

        erlaubte_labels = set([0.0, 1.0])
        labels = set([label for _, label in self.data])
        if not labels.issubset(erlaubte_labels):
            raise ValueError(
                "Logistische Regression braucht binaere Labels (0/1). Gefunden: {}".format(
                    sorted(list(labels))
                )
            )

        n_features = len(self.data[0][0])
        self.weights = [0.0] * (n_features + 1)

        for _ in range(self.epochs):
            for features, label in self.data:
                z = self.weights[0]
                for i in range(n_features):
                    z += self.weights[i + 1] * features[i]

                y_hat = self.sigmoid(z)
                error = label - y_hat

                self.weights[0] += self.lr * error
                for i in range(n_features):
                    self.weights[i + 1] += self.lr * error * features[i]

    def predict_logreg_proba(self, features):
        """
        Gibt die Wahrscheinlichkeit fuer Klasse 1 zurueck.

        Args:
            features: Feature-Liste

        Returns:
            float: Wahrscheinlichkeit fuer Klasse 1 (0.0 bis 1.0)
        """
        if self.weights is None:
            raise ValueError("Bitte zuerst train_logreg() ausfuehren.")

        z = self.weights[0]
        for i in range(len(features)):
            z += self.weights[i + 1] * features[i]

        return self.sigmoid(z)

    def predict_logreg(self, features):
        """
        Sagt die Klasse (0 oder 1) per logistischer Regression vorher.

        Args:
            features: Feature-Liste

        Returns:
            int: 0 oder 1
        """
        y_hat = self.predict_logreg_proba(features)
        return 1 if y_hat >= 0.5 else 0

    def erklaere_logreg(self, features, feature_namen=None):
        """
        Erklaert die Vorhersage der logistischen Regression.

        Zeigt Bias, Feature-Beitraege, Gesamtsumme z,
        Wahrscheinlichkeit fuer Klasse 1 und finale Klasse.

        Args:
            features: Feature-Liste des Datenpunkts
            feature_namen: Optionale Liste mit Feature-Namen

        Returns:
            int: Vorhergesagte Klasse (0 oder 1)
        """
        if self.weights is None:
            raise ValueError("Bitte zuerst train_logreg() ausfuehren.")

        if len(features) + 1 != len(self.weights):
            raise ValueError("Feature-Anzahl passt nicht zum trainierten Modell.")

        print("\n=== LogReg-Erklaerung ===")
        print("Eingabe: {}".format(features))

        z = self.weights[0]
        print("Bias (w0): {:.6f}".format(self.weights[0]))

        for i, x in enumerate(features):
            beitrag = self.weights[i + 1] * x
            z += beitrag
            fname = "feature[{}]".format(i)
            if feature_namen and i < len(feature_namen):
                fname = "{}(feature[{}])".format(feature_namen[i], i)
            print(
                "  {:>18s}: w={:>10.6f}, x={:>10.4f}, w*x={:>11.6f}".format(
                    fname,
                    self.weights[i + 1],
                    x,
                    beitrag,
                )
            )

        p1 = self.sigmoid(z)
        p0 = 1.0 - p1
        klasse = 1 if p1 >= 0.5 else 0

        print("z = {:.6f}".format(z))
        print("P(Klasse 1) = {:.4f}".format(p1))
        print("P(Klasse 0) = {:.4f}".format(p0))
        print("Vorhersage  = {}".format(klasse))
        print()

        return klasse

    # =============================================================
    # DECISION TREE (Entscheidungsbaum, Multi-Class)
    #
    # Idee: Der Baum stellt ja/nein-Fragen zu den Features.
    # "Ist Feature[2] kleiner als 500?" -> links ja, rechts nein.
    # Am Ende jedes Astes steht ein Label (die Vorhersage).
    # =============================================================

    def gini(self, labels):
        """
        Berechnet den Gini-Index fuer eine Liste von Labels.

        Der Gini-Index misst die "Unreinheit" einer Gruppe:
        - 0.0 = alle Labels gleich (perfekt rein)
        - nahe 0.5 = Labels bunt gemischt (sehr unrein)

        Der Baum sucht Splits, die den Gini-Index minimieren.
        """
        n = len(labels)
        if n == 0:
            return 0.0

        counts = {}
        for l in labels:
            counts[l] = counts.get(l, 0) + 1

        g = 1.0
        for c in counts.values():
            p = c / n
            g -= p * p
        return g

    def majority_label(self, labels):
        """Gibt das haeufigste Label zurueck (Mehrheitsentscheidung)."""
        counts = {}
        for l in labels:
            counts[l] = counts.get(l, 0) + 1
        return max(counts, key=counts.get)

    def best_split(self, data):
        """
        Findet den besten Split: Welches Feature bei welchem Schwellenwert
        teilt die Daten am saubersten in zwei Gruppen?

        Probiert jedes Feature und jeden Wert durch und nimmt den
        Split mit dem kleinsten gewichteten Gini-Index.
        """
        best_feature = None
        best_threshold = None
        best_gini = 999
        best_left = None
        best_right = None

        n_features = len(data[0][0])

        for f in range(n_features):
            values = sorted(set(d[0][f] for d in data))

            for t in values:
                left = [d for d in data if d[0][f] <= t]
                right = [d for d in data if d[0][f] > t]

                if len(left) == 0 or len(right) == 0:
                    continue

                g = (len(left)/len(data))*self.gini([l for _,l in left]) + \
                    (len(right)/len(data))*self.gini([l for _,l in right])

                if g < best_gini:
                    best_gini = g
                    best_feature = f
                    best_threshold = t
                    best_left = left
                    best_right = right

        return best_feature, best_threshold, best_left, best_right

    def train_tree(self, max_depth=3, data=None):
        """
        Trainiert einen Decision Tree.

        Args:
            max_depth: Maximale Tiefe des Baums. Flache Baeume (2-4)
                       sind schnell und vermeiden Overfitting.
            data:      Optionale Trainingsdaten (fuer Random Forest intern).
                       Falls None, werden self.data verwendet.
        """
        training_data = data if data is not None else self.data
        if not training_data:
            raise ValueError("Keine Trainingsdaten vorhanden.")

        self.tree = []
        self._build_tree(training_data, depth=0, max_depth=max_depth)

    def _build_tree(self, data, depth, max_depth):
        """Rekursiver Aufbau des Baums."""
        labels = [l for _, l in data]

        # 1) Alle Labels gleich -> Blattknoten
        if all(l == labels[0] for l in labels):
            node = {"feature": None, "threshold": None,
                    "left": None, "right": None,
                    "label": labels[0]}
            self.tree.append(node)
            return len(self.tree)-1

        # 2) Maximale Tiefe erreicht -> Mehrheitsentscheidung
        if depth >= max_depth:
            majority = self.majority_label(labels)
            node = {"feature": None, "threshold": None,
                    "left": None, "right": None,
                    "label": majority}
            self.tree.append(node)
            return len(self.tree)-1

        # 3) Besten Split finden
        f, t, left, right = self.best_split(data)

        if f is None:
            majority = self.majority_label(labels)
            node = {"feature": None, "threshold": None,
                    "left": None, "right": None,
                    "label": majority}
            self.tree.append(node)
            return len(self.tree)-1

        node = {"feature": f, "threshold": t,
                "left": None, "right": None,
                "label": None}
        self.tree.append(node)
        idx = len(self.tree)-1

        left_idx = self._build_tree(left, depth+1, max_depth)
        right_idx = self._build_tree(right, depth+1, max_depth)

        self.tree[idx]["left"] = left_idx
        self.tree[idx]["right"] = right_idx

        return idx

    def _predict_single_tree(self, tree, features):
        """Vorhersage mit einem einzelnen Baum (intern fuer Forest)."""
        idx = 0
        max_iterations = len(tree) * 2
        iterations = 0

        while iterations < max_iterations:
            iterations += 1
            node = tree[idx]

            if node["label"] is not None:
                return node["label"]

            if features[node["feature"]] <= node["threshold"]:
                idx = node["left"]
            else:
                idx = node["right"]

        raise RuntimeError("Maximale Iterationen im Decision Tree ueberschritten.")

    def predict_tree(self, features):
        """
        Sagt die Klasse per Decision Tree vorher.

        Der Datenpunkt wandert von der Wurzel durch den Baum,
        bis er an einem Blattknoten ankommt. Dessen Label
        ist die Vorhersage.

        Args:
            features: Feature-Liste

        Returns:
            float: Vorhergesagtes Label
        """
        if not self.tree:
            raise ValueError("Bitte zuerst train_tree() ausfuehren.")

        return self._predict_single_tree(self.tree, features)

    # ---------------------------------------------------------
    # BAUM AUSGEBEN
    # ---------------------------------------------------------

    def print_tree(self, node_index=0, depth=0):
        """
        Gibt den Decision Tree als lesbaren Text aus.

        Zeigt die Entscheidungsregeln des Baums, z.B.:
          if feature[2] <= 500:
            -> Label: 3.0
          else:
            -> Label: 5.0
        """
        node = self.tree[node_index]
        indent = "  " * depth

        if node["label"] is not None:
            print("{}-> Label: {}".format(indent, node['label']))
            return

        f = node["feature"]
        t = node["threshold"]

        print("{}if feature[{}] <= {}:".format(indent, f, t))
        self.print_tree(node["left"], depth + 1)

        print("{}else:  # feature[{}] > {}".format(indent, f, t))
        self.print_tree(node["right"], depth + 1)

    def erklaere_tree(self, features, feature_namen=None, label_namen=None):
        """
        Zeigt den Entscheidungspfad des Decision Trees Schritt fuer Schritt.

        Man sieht genau, welche Fragen der Baum stellt und wie er
        zur Vorhersage kommt. Das macht den Baum nachvollziehbar.

        Args:
            features:      Feature-Liste des Datenpunkts
            feature_namen: Optionale Liste mit Feature-Namen
            label_namen:   Optionales Dict {label: "Name"}

        Returns:
            float: Vorhergesagtes Label
        """
        if not self.tree:
            raise ValueError("Bitte zuerst train_tree() ausfuehren.")

        print("\n=== Tree-Erklaerung ===")
        print("Eingabe: {}".format(features))
        print()

        idx = 0
        schritt = 1
        max_iterations = len(self.tree) * 2
        iterations = 0

        while iterations < max_iterations:
            iterations += 1
            node = self.tree[idx]

            if node["label"] is not None:
                l_name = ""
                if label_namen and node["label"] in label_namen:
                    l_name = " ({})".format(label_namen[node["label"]])
                print("-> Vorhersage: {}{}".format(node["label"], l_name))
                print()
                return node["label"]

            f = node["feature"]
            t = node["threshold"]
            wert = features[f]

            f_name = "feature[{}]".format(f)
            if feature_namen and f < len(feature_namen):
                f_name = "{}(feature[{}])".format(feature_namen[f], f)

            if wert <= t:
                richtung = "JA -> links"
                idx = node["left"]
            else:
                richtung = "NEIN -> rechts"
                idx = node["right"]

            print("Schritt {}: {} = {:.1f} <= {}?  {}".format(
                schritt, f_name, wert, t, richtung))
            schritt += 1

        raise RuntimeError("Maximale Iterationen im Decision Tree ueberschritten.")

    def feature_wichtigkeit(self, feature_namen=None, tree=None):
        """
        Zeigt, wie oft jedes Feature als Split im Decision Tree verwendet wird.

        Features, die haeufig zum Aufteilen genutzt werden, sind "wichtiger"
        fuer die Unterscheidung der Klassen. Bei Farbsensoren sieht man so,
        welche Kanaele am meisten zur Erkennung beitragen.

        Args:
            feature_namen: Optionale Liste mit Feature-Namen
            tree:          Optionaler Baum (falls None: self.tree)

        Returns:
            dict: {feature_index: anzahl_splits}
        """
        baum = tree if tree is not None else self.tree
        if not baum:
            raise ValueError("Bitte zuerst train_tree() ausfuehren.")

        # Anzahl Features ermitteln
        n_features = 0
        for node in baum:
            if node["feature"] is not None and node["feature"] >= n_features:
                n_features = node["feature"] + 1

        # Splits pro Feature zaehlen
        wichtigkeit = {}
        for f in range(n_features):
            wichtigkeit[f] = 0
        for node in baum:
            if node["feature"] is not None:
                wichtigkeit[node["feature"]] = wichtigkeit.get(node["feature"], 0) + 1

        # Sortiert nach Wichtigkeit ausgeben
        print("\n=== Feature-Wichtigkeit (Anzahl Splits) ===")
        gesamt = sum(wichtigkeit.values())
        for f in sorted(wichtigkeit, key=wichtigkeit.get, reverse=True):
            name = "Feature {}".format(f)
            if feature_namen and f < len(feature_namen):
                name = feature_namen[f]
            anteil = wichtigkeit[f] / gesamt if gesamt > 0 else 0
            balken = '#' * min(int(anteil * 20 + 0.5), 20)
            print("  {:>12s}: {:>2d} Splits  {:>5.1f}%  {}".format(
                name, wichtigkeit[f], anteil * 100, balken))
        print()

        return wichtigkeit

    # =============================================================
    # RANDOM FOREST (Zufallswald)
    #
    # Idee: Statt eines einzelnen Baums trainieren wir MEHRERE
    # Baeume, jeder auf einer leicht anderen Teilmenge der Daten.
    # Die Vorhersage ist eine Mehrheitsentscheidung aller Baeume.
    # Das ist robuster als ein einzelner Baum.
    #
    # Besonders beim AS7262 mit 6 Kanaelen sind die Baeume oft
    # extrem flach (Tiefe 2-3), daher sind bis zu 7 Baeume
    # speichertechnisch kein Problem.
    # =============================================================

    def _bootstrap_sample(self, data, seed_offset=0):
        """
        Erzeugt eine Bootstrap-Stichprobe (Ziehen mit Zuruecklegen).

        Aus n Datenpunkten werden n Stueck ZUFAELLIG gezogen,
        wobei manche doppelt und manche gar nicht vorkommen.
        Das sorgt dafuer, dass jeder Baum etwas andere Daten sieht.
        """
        n = len(data)
        _set_seed(seed_offset)
        sample = []
        for _ in range(n):
            idx = _rand_int(n)
            sample.append(data[idx])
        return sample

    def train_forest(self, n_trees=5, max_depth=3, seed=42):
        """
        Trainiert einen Random Forest mit mehreren Decision Trees.

        Args:
            n_trees:   Anzahl der Baeume (1-7, Standard: 5).
                       Mehr Baeume = stabilere Vorhersage, aber mehr Speicher.
            max_depth: Maximale Tiefe jedes Baums (Standard: 3).
            seed:      Startwert fuer den Zufallsgenerator.
        """
        if not self.data:
            raise ValueError("Keine Trainingsdaten vorhanden.")

        if n_trees < 1 or n_trees > 7:
            raise ValueError("Anzahl Baeume muss zwischen 1 und 7 liegen.")

        self.forest = []

        for i in range(n_trees):
            # Jeder Baum bekommt eine andere Bootstrap-Stichprobe
            sample = self._bootstrap_sample(self.data, seed_offset=seed + i * 7)

            # Temporaer einen Baum trainieren
            old_tree = self.tree
            self.tree = []
            self._build_tree(sample, depth=0, max_depth=max_depth)
            self.forest.append(self.tree)
            self.tree = old_tree

        print("Random Forest trainiert: {} Baeume, max. Tiefe {}".format(
            n_trees, max_depth))

    def predict_forest(self, features):
        """
        Sagt die Klasse per Random Forest vorher (Mehrheitsentscheidung).

        Jeder Baum stimmt ab, das Label mit den meisten Stimmen gewinnt.

        Args:
            features: Feature-Liste

        Returns:
            float: Vorhergesagtes Label
        """
        if not self.forest:
            raise ValueError("Bitte zuerst train_forest() ausfuehren.")

        # Jeden Baum abstimmen lassen
        stimmen = {}
        for tree in self.forest:
            label = self._predict_single_tree(tree, features)
            stimmen[label] = stimmen.get(label, 0) + 1

        # Mehrheitsentscheidung
        return max(stimmen, key=stimmen.get)

    # =============================================================
    # FLACHES NEURONALES NETZ (1 Hidden Layer)
    #
    # Das ist der einfachste Typ eines neuronalen Netzes:
    #
    #   Eingabe (z.B. 6 Sensorwerte)
    #       |
    #   Hidden Layer (z.B. 8 Neuronen)  <-- hier "lernt" das Netz Muster
    #       |
    #   Ausgabe (z.B. 8 Klassen)        <-- Wahrscheinlichkeit pro Klasse
    #
    # Jedes Neuron berechnet:
    #   ausgabe = aktivierung(summe(gewicht * eingabe) + bias)
    #
    # Das Training passt die Gewichte schrittweise an (Backpropagation).
    # =============================================================

    def _nn_relu(self, x):
        """
        ReLU-Aktivierungsfunktion: gibt x zurueck wenn positiv, sonst 0.

        ReLU ist einfach und effizient. Statt einer komplizierten Kurve
        wird einfach alles Negative auf Null gesetzt.
        """
        return x if x > 0 else 0.0

    def _nn_relu_ableitung(self, x):
        """Ableitung von ReLU: 1 wenn x > 0, sonst 0."""
        return 1.0 if x > 0 else 0.0

    def _nn_softmax(self, werte):
        """
        Softmax: Wandelt eine Liste von Zahlen in Wahrscheinlichkeiten um.

        Die Ausgaben summieren sich zu 1.0. Das Neuron mit dem
        hoechsten Wert bekommt die groesste Wahrscheinlichkeit.
        """
        # Stabilisierung: groessten Wert abziehen (verhindert Overflow)
        max_val = max(werte)
        exp_werte = []
        for w in werte:
            diff = w - max_val
            if diff < -500:
                exp_werte.append(0.0)
            else:
                exp_werte.append(math.exp(diff))
        summe = sum(exp_werte)
        if summe == 0:
            return [1.0 / len(werte)] * len(werte)
        return [e / summe for e in exp_werte]

    def _nn_scale(self, features):
        """Skaliert Features auf 0-1 mit den beim Training berechneten Min/Max-Werten."""
        return [
            (f - mn) / (mx - mn) if mx != mn else 0.0
            for f, mn, mx in zip(features, self._nn_min, self._nn_max)
        ]

    def train_netz(self, hidden=8, epochs=None, lr=None):
        """
        Trainiert ein flaches neuronales Netz (1 Hidden Layer).

        Das Netz lernt, Features auf Klassen abzubilden.
        Es kann beliebig viele Klassen unterscheiden.

        Args:
            hidden:  Anzahl Neuronen in der versteckten Schicht.
                     Faustregel: etwa so viele wie Klassen, oder etwas mehr.
            epochs:  Trainingsdurchlaeufe (Standard: self.epochs)
            lr:      Lernrate (Standard: self.lr)
        """
        if not self.data:
            raise ValueError("Keine Trainingsdaten vorhanden.")

        if epochs is None:
            epochs = self.epochs
        if lr is None:
            lr = self.lr

        n_features = len(self.data[0][0])

        # Min/Max-Skalierung berechnen (wie bei kNN)
        first_features = self.data[0][0]
        self._nn_min = first_features[:]
        self._nn_max = first_features[:]
        for features, _ in self.data:
            self._nn_min = [min(a, b) for a, b in zip(self._nn_min, features)]
            self._nn_max = [max(a, b) for a, b in zip(self._nn_max, features)]

        # Welche Labels gibt es? Sortiert, damit Index stabil bleibt.
        self._nn_labels = sorted(set(l for _, l in self.data))
        n_output = len(self._nn_labels)
        # Zuordnung: Label -> Index
        label_to_idx = {l: i for i, l in enumerate(self._nn_labels)}

        # ---- Gewichte zufaellig initialisieren ----
        # Kleine Zufallswerte zwischen -0.5 und +0.5
        _set_seed(42)

        # Gewichte: Input -> Hidden (n_features x hidden)
        self._nn_w1 = []
        for _ in range(n_features):
            zeile = []
            for _ in range(hidden):
                zeile.append((_rand_int(1000) / 1000.0 - 0.5))
            self._nn_w1.append(zeile)

        # Bias Hidden
        self._nn_b1 = [0.0] * hidden

        # Gewichte: Hidden -> Output (hidden x n_output)
        self._nn_w2 = []
        for _ in range(hidden):
            zeile = []
            for _ in range(n_output):
                zeile.append((_rand_int(1000) / 1000.0 - 0.5))
            self._nn_w2.append(zeile)

        # Bias Output
        self._nn_b2 = [0.0] * n_output

        # ---- Training (Backpropagation) ----
        for epoche in range(epochs):
            gesamt_loss = 0.0

            for features, label in self.data:
                idx_label = label_to_idx[label]

                # Features skalieren (0-1)
                features = self._nn_scale(features)

                # === FORWARD PASS ===
                # Schritt 1: Input -> Hidden
                hidden_raw = [0.0] * hidden
                for h in range(hidden):
                    summe = self._nn_b1[h]
                    for f in range(n_features):
                        summe += features[f] * self._nn_w1[f][h]
                    hidden_raw[h] = summe

                # ReLU-Aktivierung
                hidden_out = [self._nn_relu(h) for h in hidden_raw]

                # Schritt 2: Hidden -> Output
                output_raw = [0.0] * n_output
                for o in range(n_output):
                    summe = self._nn_b2[o]
                    for h in range(hidden):
                        summe += hidden_out[h] * self._nn_w2[h][o]
                    output_raw[o] = summe

                # Softmax-Aktivierung (Wahrscheinlichkeiten)
                output_prob = self._nn_softmax(output_raw)

                # === LOSS BERECHNEN ===
                # Cross-Entropy-Loss fuer den richtigen Label-Index
                p = output_prob[idx_label]
                if p > 1e-15:
                    gesamt_loss -= math.log(p)

                # === BACKWARD PASS (Backpropagation) ===
                # Schritt 1: Fehler am Output berechnen
                # Bei Softmax + Cross-Entropy ist der Gradient einfach:
                # delta_output = output_prob - one_hot_target
                d_output = output_prob[:]
                d_output[idx_label] -= 1.0  # one-hot abziehen

                # Schritt 2: Gewichte Hidden->Output anpassen
                for h in range(hidden):
                    for o in range(n_output):
                        self._nn_w2[h][o] -= lr * d_output[o] * hidden_out[h]
                for o in range(n_output):
                    self._nn_b2[o] -= lr * d_output[o]

                # Schritt 3: Fehler an Hidden berechnen
                d_hidden = [0.0] * hidden
                for h in range(hidden):
                    for o in range(n_output):
                        d_hidden[h] += d_output[o] * self._nn_w2[h][o]
                    # ReLU-Ableitung anwenden
                    d_hidden[h] *= self._nn_relu_ableitung(hidden_raw[h])

                # Schritt 4: Gewichte Input->Hidden anpassen
                for f in range(n_features):
                    for h in range(hidden):
                        self._nn_w1[f][h] -= lr * d_hidden[h] * features[f]
                for h in range(hidden):
                    self._nn_b1[h] -= lr * d_hidden[h]

            # Fortschritt alle 10 Epochen anzeigen
            if (epoche + 1) % 10 == 0 or epoche == 0:
                avg_loss = gesamt_loss / len(self.data)
                print("Epoche {:>4d}/{}: Loss = {:.8f}".format(
                    epoche + 1, epochs, avg_loss))

    def predict_netz(self, features):
        """
        Sagt die Klasse per neuronalem Netz vorher.

        Der Datenpunkt wird durch das Netz geschickt (Forward Pass).
        Die Klasse mit der hoechsten Wahrscheinlichkeit wird zurueckgegeben.

        Args:
            features: Feature-Liste

        Returns:
            float: Vorhergesagtes Label
        """
        if self._nn_w1 is None:
            raise ValueError("Bitte zuerst train_netz() ausfuehren.")

        n_features = len(features)
        hidden = len(self._nn_b1)
        n_output = len(self._nn_b2)

        # Features skalieren
        features = self._nn_scale(features)

        # Forward Pass: Input -> Hidden
        hidden_out = []
        for h in range(hidden):
            summe = self._nn_b1[h]
            for f in range(n_features):
                summe += features[f] * self._nn_w1[f][h]
            hidden_out.append(self._nn_relu(summe))

        # Forward Pass: Hidden -> Output
        output_raw = []
        for o in range(n_output):
            summe = self._nn_b2[o]
            for h in range(hidden):
                summe += hidden_out[h] * self._nn_w2[h][o]
            output_raw.append(summe)

        # Softmax und bestes Label
        probs = self._nn_softmax(output_raw)
        best_idx = 0
        best_val = probs[0]
        for i in range(1, len(probs)):
            if probs[i] > best_val:
                best_val = probs[i]
                best_idx = i
        return self._nn_labels[best_idx]

    def predict_netz_wahrscheinlichkeiten(self, features):
        """
        Gibt die Wahrscheinlichkeiten fuer alle Klassen zurueck.

        Nuetzlich, um zu sehen, wie "sicher" das Netz ist.

        Args:
            features: Feature-Liste

        Returns:
            dict: {label: wahrscheinlichkeit} fuer jede Klasse
        """
        if self._nn_w1 is None:
            raise ValueError("Bitte zuerst train_netz() ausfuehren.")

        n_features = len(features)
        hidden = len(self._nn_b1)
        n_output = len(self._nn_b2)

        # Features skalieren
        features = self._nn_scale(features)

        hidden_out = []
        for h in range(hidden):
            summe = self._nn_b1[h]
            for f in range(n_features):
                summe += features[f] * self._nn_w1[f][h]
            hidden_out.append(self._nn_relu(summe))

        output_raw = []
        for o in range(n_output):
            summe = self._nn_b2[o]
            for h in range(hidden):
                summe += hidden_out[h] * self._nn_w2[h][o]
            output_raw.append(summe)

        probs = self._nn_softmax(output_raw)
        return {label: round(p, 4) for label, p in zip(self._nn_labels, probs)}

    # =============================================================
    # MODELLVERGLEICH
    # =============================================================

    def vergleiche(self, test_data, label_namen=None):
        """
        Testet alle bereits trainierten Modelle und zeigt eine Vergleichstabelle.

        So sehen Schueler auf einen Blick, welches Modell am besten
        zu ihren Daten passt. Jedes Modell hat Staerken und Schwaechen.

        Hinweis: Nur Modelle, die vorher trainiert wurden, werden bewertet.
        Nicht trainierte Modelle werden uebersprungen.

        Args:
            test_data:   Liste von (features, label) zum Testen
            label_namen: Optionales Dict {label: "Name"} (fuer Konfusionsmatrix)

        Returns:
            dict: {modellname: accuracy} fuer alle getesteten Modelle
        """
        ergebnisse = {}

        # kNN – pruefe ob Trainingsdaten vorhanden
        if self.data:
            try:
                acc = self.accuracy(test_data, self.predict_knn)
                ergebnisse["kNN (k={})".format(self.k)] = acc
            except Exception:
                pass

        # Logistische Regression – pruefe ob Gewichte vorhanden
        if self.weights is not None:
            try:
                acc = self.accuracy(test_data, self.predict_logreg)
                ergebnisse["Logistische Regression"] = acc
            except Exception:
                pass

        # Decision Tree – pruefe ob Baum trainiert wurde
        if self.tree:
            try:
                acc = self.accuracy(test_data, self.predict_tree)
                ergebnisse["Decision Tree"] = acc
            except Exception:
                pass

        # Random Forest – pruefe ob Wald trainiert wurde
        if self.forest:
            try:
                acc = self.accuracy(test_data, self.predict_forest)
                ergebnisse["Random Forest ({})".format(len(self.forest))] = acc
            except Exception:
                pass

        # Neuronales Netz – pruefe ob Gewichte vorhanden
        if getattr(self, 'w_hidden', None):
            try:
                acc = self.accuracy(test_data, self.predict_netz)
                ergebnisse["Neuronales Netz"] = acc
            except Exception:
                pass

        if not ergebnisse:
            print("Keine trainierten Modelle vorhanden. Bitte zuerst trainieren.")

        # Ergebnisse anzeigen
        print("\n=== Modellvergleich ===")
        bestes_modell = None
        beste_acc = -1

        for name, acc in ergebnisse.items():
            if isinstance(acc, float):
                balken = '#' * int(acc * 20 + 0.5)
                print("  {:>20s}: {:>5.1f}%  {}".format(name, acc * 100, balken))
                if acc > beste_acc:
                    beste_acc = acc
                    bestes_modell = name
            else:
                print("  {:>20s}: {}".format(name, acc))

        if bestes_modell:
            print("\n  Bestes Modell: {} ({:.1f}%)".format(bestes_modell, beste_acc * 100))
        print()

        return ergebnisse

    # =============================================================
    # MODELL SPEICHERN UND LADEN
    #
    # Damit man nach einem Neustart des ESP32 nicht neu trainieren
    # muss, koennen Modelle als JSON-Datei gespeichert werden.
    # =============================================================

    def save_model(self, filename, model_type='tree'):
        """
        Speichert ein trainiertes Modell als JSON-Datei.

        Args:
            filename:   Dateipfad (z.B. 'modell.json')
            model_type: 'tree', 'forest', 'knn', 'logreg' oder 'netz'
        """
        modell = {"type": model_type}

        if model_type == 'tree':
            modell["tree"] = self.tree
        elif model_type == 'forest':
            modell["forest"] = self.forest
        elif model_type == 'knn':
            modell["data"] = self.data
            modell["k"] = self.k
            modell["min_values"] = self.min_values
            modell["max_values"] = self.max_values
        elif model_type == 'logreg':
            modell["weights"] = self.weights
        elif model_type == 'netz':
            modell["w1"] = self._nn_w1
            modell["b1"] = self._nn_b1
            modell["w2"] = self._nn_w2
            modell["b2"] = self._nn_b2
            modell["labels"] = self._nn_labels
            modell["nn_min"] = self._nn_min
            modell["nn_max"] = self._nn_max
        else:
            raise ValueError("model_type muss 'tree', 'forest', 'knn', 'logreg' oder 'netz' sein.")

        with open(filename, 'w') as f:
            json.dump(modell, f)
        print("Modell gespeichert: {}".format(filename))

    def load_model(self, filename):
        """
        Laedt ein gespeichertes Modell aus einer JSON-Datei.

        Der Modelltyp wird automatisch erkannt.

        Args:
            filename: Dateipfad (z.B. 'modell.json')

        Returns:
            str: Typ des geladenen Modells ('tree', 'forest', 'knn', 'logreg', 'netz')
        """
        with open(filename, 'r') as f:
            modell = json.load(f)

        model_type = modell["type"]

        if model_type == 'tree':
            self.tree = modell["tree"]
        elif model_type == 'forest':
            self.forest = modell["forest"]
        elif model_type == 'knn':
            self.data = [(d[0], d[1]) for d in modell["data"]]
            self.k = modell["k"]
            self.min_values = modell["min_values"]
            self.max_values = modell["max_values"]
        elif model_type == 'logreg':
            self.weights = modell["weights"]
        elif model_type == 'netz':
            self._nn_w1 = modell["w1"]
            self._nn_b1 = modell["b1"]
            self._nn_w2 = modell["w2"]
            self._nn_b2 = modell["b2"]
            self._nn_labels = modell["labels"]
            self._nn_min = modell["nn_min"]
            self._nn_max = modell["nn_max"]

        print("Modell geladen: {} ({})".format(filename, model_type))
        return model_type
