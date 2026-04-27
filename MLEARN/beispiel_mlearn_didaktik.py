"""
Beispiel fuer NIT Bibliothek: MLEARN2
Zeigt: Didaktische Funktionen -- Daten verstehen, Modelle erklaeren
Hardware: ESP32 mit MicroPython und CSV-Datei im Dateisystem
"""

from nitbw_mlearn import MLearn


# --- Konfiguration ---

CSV_DATEI = 'farben_as7262.csv'
TARGET_SPALTE = 6  # Label in Spalte 6 (letzte bei AS7262)

feature_namen = ['violett', 'blau', 'gruen', 'gelb', 'orange', 'rot']
label_namen = {1.0: "Rot", 2.0: "Gruen", 3.0: "Blau", 4.0: "Gelb", 5.0: "Weiss"}

# --- Daten laden ---
model = MLearn(k=3, lr=0.005, epochs=200)
model.load_csv(CSV_DATEI, separator=',', target=TARGET_SPALTE)


# ============================================================
# 1) DATEN VERSTEHEN: daten_info()
#    Immer als Erstes aufrufen! Zeigt Klassen, Verteilung,
#    Wertebereiche -- so findet man Fehler frueh.
# ============================================================
model.daten_info(feature_namen)


# --- Daten aufteilen ---
train, test = model.split_data(anteil_test=0.2)
model.data = train

# Ein Beispiel-Datenpunkt zum Erklaeren
beispiel = test[0][0] if test else [52, 70, 151, 214, 210, 140]


# ============================================================
# 2) kNN ERKLAEREN: erklaere_knn()
#    Zeigt die k naechsten Nachbarn mit Abstand.
#    So sieht man, WER abgestimmt hat und WARUM.
# ============================================================
model.train_knn()
model.erklaere_knn(beispiel, label_namen)


# ============================================================
# 3) LOGISTISCHE REGRESSION ERKLAEREN: erklaere_logreg()
#    LogReg ist in dieser Bibliothek binaer (0/1).
#    Beispiel: Klasse 1.0 (Rot) gegen alle anderen Klassen.
# ============================================================
logreg_model = MLearn(lr=0.0005, epochs=250)

for features, label in train:
    bin_label = 1.0 if label == 1.0 else 0.0
    logreg_model.add_sample(features, bin_label)

logreg_model.train_logreg()
logreg_model.erklaere_logreg(beispiel, feature_namen)

# Accuracy auf binaer umgelabelten Testdaten
logreg_test = []
for features, label in test:
    bin_label = 1.0 if label == 1.0 else 0.0
    logreg_test.append((features, bin_label))

logreg_acc = logreg_model.accuracy(logreg_test, logreg_model.predict_logreg)
print("LogReg Accuracy (Rot vs Rest): {:.1f}%".format(logreg_acc * 100))
print()


# ============================================================
# 4) BAUM ERKLAEREN: erklaere_tree()
#    Zeigt den Entscheidungspfad Schritt fuer Schritt.
#    Man sieht genau, welche Fragen der Baum stellt.
# ============================================================
model.train_tree(max_depth=3)
model.erklaere_tree(beispiel, feature_namen, label_namen)


# ============================================================
# 5) FEATURE-WICHTIGKEIT: feature_wichtigkeit()
#    Welche Sensorkanaele tragen am meisten zur Erkennung bei?
#    Nicht alle Features sind gleich wichtig!
# ============================================================
model.feature_wichtigkeit(feature_namen)


# ============================================================
# 6) MODELLVERGLEICH: vergleiche()
#    Trainiert alle Modelle und zeigt Accuracy-Ranking.
#    Welches Modell passt am besten zu MEINEN Daten?
# ============================================================
model.vergleiche(test, label_namen)
