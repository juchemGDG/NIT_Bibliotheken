"""
NIT Bibliothek: MLEARN - Einfache ML-Algorithmen fuer MicroPython
Fuer ESP32 mit MicroPython

Version:    1.1.0
Autor:      Stephan Juchem
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Enthaelt kNN, logistische Regression und Decision Tree fuer Lern- und Demozwecke.
Die Implementierung ist kompakt gehalten und fuer Mikrocontroller optimiert.
"""

import math

class MLearn:
    """
    Bietet grundlegende ML-Verfahren fuer kleine Datensaetze auf dem ESP32.

    Unterstuetzte Hardware:
    - ESP32 mit MicroPython
    - Andere MicroPython-faehige Boards mit ausreichendem RAM

    Schnittstelle: Dateisystem (CSV)
    """

    def __init__(self, k=3, lr=0.1, epochs=200):
        self.k = k
        self.lr = lr
        self.epochs = epochs
        
        # Rohdaten
        self.data = []  # (features, label)

        # Für kNN-Skalierung
        self.min_values = None
        self.max_values = None

        # Für logistische Regression
        self.weights = None

        # Für Decision Tree
        self.tree = []

    # ---------------------------------------------------------
    # DATEN LADEN
    # ---------------------------------------------------------

    def load_csv(self, filename, separator=',', target=0):
        """
        Lädt Trainingsdaten aus einer CSV-Datei.
        Format: label;f1;f2;...
        target: Index der Zielspalte (Standard: 0)
        """
        try:
            with open(filename, 'r') as f:
                first = True
                for line in f:
                    if first:
                        first = False
                        continue  # Header überspringen
                    values = line.strip().split(separator)
                    if not values or len(values) <= target:
                        continue
                    label = float(values[target])
                    # Alle Werte außer dem Label als Features
                    features = [float(values[i]) for i in range(len(values)) if i != target]
                    self.data.append((features, label))
        except Exception as e:
            print("Fehler beim Laden der CSV-Datei:", e)

    # ---------------------------------------------------------
    # KNN TRAINING
    # ---------------------------------------------------------

    def train_knn(self):
        if not self.data:
            raise ValueError("Keine Trainingsdaten vorhanden.")

        first_features = self.data[0][0]
        self.min_values = first_features[:]
        self.max_values = first_features[:]

        for features, _ in self.data:
            self.min_values = [min(a, b) for a, b in zip(self.min_values, features)]
            self.max_values = [max(a, b) for a, b in zip(self.max_values, features)]

    def scale_features(self, features):
        return [
            (f - mn) / (mx - mn) if mx != mn else 0
            for f, mn, mx in zip(features, self.min_values, self.max_values)
        ]

    def euclidean_distance(self, p1, p2):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

    def predict_knn(self, features):
        if self.min_values is None:
            raise ValueError("Bitte zuerst train_knn() ausführen.")

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

    # ---------------------------------------------------------
    # LOGISTISCHE REGRESSION
    # ---------------------------------------------------------

    def sigmoid(self, z):
        # Schutz gegen Overflow
        if z < -500:
            return 0.0
        elif z > 500:
            return 1.0
        return 1 / (1 + math.exp(-z))

    def train_logreg(self):
        if not self.data:
            raise ValueError("Keine Trainingsdaten vorhanden.")

        n_features = len(self.data[0][0])
        self.weights = [0.0] * (n_features + 1)

        for _ in range(self.epochs):
            for features, label in self.data:
                z = self.weights[0]
                for i in range(n_features):
                    z += self.weights[i+1] * features[i]

                y_hat = self.sigmoid(z)
                error = label - y_hat

                self.weights[0] += self.lr * error
                for i in range(n_features):
                    self.weights[i+1] += self.lr * error * features[i]

    def predict_logreg(self, features):
        if self.weights is None:
            raise ValueError("Bitte zuerst train_logreg() ausführen.")

        z = self.weights[0]
        for i in range(len(features)):
            z += self.weights[i+1] * features[i]

        y_hat = self.sigmoid(z)
        return 1 if y_hat >= 0.5 else 0

    # ---------------------------------------------------------
    # DECISION TREE (Multi-Class)
    # ---------------------------------------------------------

    def gini(self, labels):
        """
        Multi-Class Gini-Index.
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
        counts = {}
        for l in labels:
            counts[l] = counts.get(l, 0) + 1
        return max(counts, key=counts.get)

    def best_split(self, data):
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

    def train_tree(self, max_depth=3):
        if not self.data:
            raise ValueError("Keine Trainingsdaten vorhanden.")

        self.tree = []
        self._build_tree(self.data, depth=0, max_depth=max_depth)

    def _build_tree(self, data, depth, max_depth):
        labels = [l for _, l in data]

        # 1) Alle Labels gleich
        if all(l == labels[0] for l in labels):
            node = {"feature": None, "threshold": None,
                    "left": None, "right": None,
                    "label": labels[0]}
            self.tree.append(node)
            return len(self.tree)-1

        # 2) Maximale Tiefe erreicht
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

    def predict_tree(self, features):
        if not self.tree:
            raise ValueError("Bitte zuerst train_tree() ausführen.")
        
        idx = 0
        max_iterations = len(self.tree) * 2  # Sicherheitsgrenze
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            node = self.tree[idx]

            if node["label"] is not None:
                return node["label"]

            if features[node["feature"]] <= node["threshold"]:
                idx = node["left"]
            else:
                idx = node["right"]
        
        raise RuntimeError("Maximale Iterationen im Decision Tree überschritten.")

    # ---------------------------------------------------------
    # BAUM AUSGEBEN
    # ---------------------------------------------------------

    def print_tree(self, node_index=0, depth=0):
        node = self.tree[node_index]
        indent = "  " * depth

        if node["label"] is not None:
            print(f"{indent}→ Label: {node['label']}")
            return

        f = node["feature"]
        t = node["threshold"]

        print(f"{indent}if feature[{f}] <= {t}:")
        self.print_tree(node["left"], depth + 1)

        print(f"{indent}else:  # feature[{f}] > {t}")
        self.print_tree(node["right"], depth + 1)
