"""
Testskript fuer NIT Bibliothek: MLEARN
Zeigt: Kompletter ML-Test mit 12 Legostein-Farben
       Phase 1: Daten sammeln
       Phase 2: Daten laden und Ueberblick
       Phase 3: Alle Algorithmen trainieren und bewerten
       Phase 4: Didaktische Erklaerungen
       Phase 5: Modell speichern und laden
       Phase 6: Live-Erkennung
Hardware: ESP32 + AS7262 + Taster an GPIO 12 (Pull-Up, andere Seite an GND)

Benoetigte Dateien in /lib:
    - nitbw_as7262.py
    - nitbw_mlearn.py
    - nitbw_datensammler.py
"""

print("Starte Testskript...")

from nitbw_as7262 import AS7262
print("  AS7262 importiert")
from nitbw_mlearn import MLearn
print("  MLearn importiert")
from nitbw_datensammler import DatenSammler
print("  DatenSammler importiert")
from machine import I2C, Pin
import time
print("  Alle Imports abgeschlossen")


# =============================================================
# KONFIGURATION – hier anpassen!
# =============================================================

TASTER_PIN = 12
CSV_DATEI = 'farben_lego.csv'
MODELL_DATEI = 'lego_modell.json'
MESSUNGEN_PRO_LABEL = 20

# --- Anzahl der Farben (Labels) ---
# Aendere ANZAHL_LABELS und passe die Liste darunter an.
# Es werden nur die ersten ANZAHL_LABELS Eintraege verwendet.
ANZAHL_LABELS = 12

# --- Legostein-Farben ---
# Trage hier mindestens ANZAHL_LABELS Farben ein.
ALLE_LABELS = {
    1:  "Weiss",
    2:  "Gelb",
    3:  "dunkelGelb",
    4:  "Orange",
    5:  "Rot",
    6:  "Braun",
    7:  "Gruen",
    8:  "hellGruen",
    9:  "hellblau",
    10: "Blau",
    11: "Lila",
    12: "Schwarz",
}

# Nur die gewaehlte Anzahl verwenden
LABELS = {k: v for k, v in ALLE_LABELS.items() if k <= ANZAHL_LABELS}

LABEL_NAMEN = {float(k): v for k, v in LABELS.items()}
KANAL_NAMEN = ['violett', 'blau', 'gruen', 'gelb', 'orange', 'rot']
SPALTENNAMEN = KANAL_NAMEN + ['label']


# =============================================================
# HILFSFUNKTIONEN
# =============================================================

def zeige_menue():
    print()
    print("=" * 50)
    print("  MLEARN-TESTPROGRAMM: {} Legostein-Farben".format(ANZAHL_LABELS))
    print("=" * 50)
    print()
    print("  1 - Phase 1: Daten sammeln")
    print("  2 - Phase 2: Daten laden und Ueberblick")
    print("  3 - Phase 3: Algorithmus trainieren")
    print("  4 - Phase 4: Didaktische Erklaerungen")
    print("  5 - Phase 5: Modell speichern und laden")
    print("  6 - Phase 6: Live-Erkennung")
    print("  0 - Beenden")
    print()


def warte_auf_enter(text="Weiter mit Enter..."):
    try:
        input(text)
    except EOFError:
        time.sleep(1)


# =============================================================
# SENSOR INITIALISIEREN
# =============================================================

print("Sensor wird initialisiert...")
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = AS7262(i2c, led='messen')
print("AS7262 bereit. Temperatur: {} C".format(sensor.temperatur()))


# =============================================================
# PHASE 1: DATEN SAMMELN
# =============================================================

def phase_1():
    print()
    print("=" * 50)
    print("  PHASE 1: Daten sammeln")
    print("=" * 50)
    print()
    print("So geht's:")
    print("  - Fuer jede der 12 Farben werden {} Messungen gemacht.".format(
        MESSUNGEN_PRO_LABEL))
    print("  - Gesamt: {} Datenpunkte".format(
        MESSUNGEN_PRO_LABEL * len(LABELS)))
    print("  - Halte den Legostein ca. 1-2 cm vor den Sensor.")
    print("  - Druecke den Taster fuer jede Messung.")
    print("  - Drehe/verschiebe den Stein leicht zwischen")
    print("    den Messungen fuer natuerliche Varianz.")
    print()
    print("Deine Farben:")
    for nr, name in sorted(LABELS.items()):
        print("  {:2d} = {}".format(nr, name))
    print()
    print("Die Daten werden in '{}' gespeichert.".format(CSV_DATEI))
    print()

    antwort = input("Datensammlung starten? (j/n): ").strip().lower()
    if antwort != 'j':
        print("Abgebrochen.")
        return

    sammler = DatenSammler(
        taster_pin=TASTER_PIN,
        csv_datei=CSV_DATEI,
        spaltennamen=SPALTENNAMEN,
        separator=','
    )

    sammler.sammle(
        mess_funktion=sensor.messen_roh_liste,
        labels=LABELS,
        messungen_pro_label=MESSUNGEN_PRO_LABEL
    )

    print()
    print("Phase 1 abgeschlossen!")
    print("Datei '{}' mit {} Datenpunkten erstellt.".format(
        CSV_DATEI, len(sammler.get_daten())))


# =============================================================
# PHASE 2: DATEN LADEN UND UEBERBLICK
# =============================================================

train_data = None
test_data = None
model = None


def phase_2():
    global model, train_data, test_data

    print()
    print("=" * 50)
    print("  PHASE 2: Daten laden und Ueberblick")
    print("=" * 50)
    print()
    print("Lade '{}'...".format(CSV_DATEI))

    model = MLearn(k=3, lr=0.005, epochs=200)

    try:
        model.load_csv(CSV_DATEI, separator=',', target=6)
    except Exception as e:
        print("FEHLER beim Laden: {}".format(e))
        print("Hast du Phase 1 schon ausgefuehrt?")
        return

    print()
    print("--- Datensatz-Info ---")
    model.daten_info(feature_namen=KANAL_NAMEN)

    print()
    print("Teile Daten auf: 80% Training / 20% Test...")
    train_data, test_data = model.split_data(anteil_test=0.2)
    model.data = train_data

    print("  Training:  {} Datenpunkte".format(len(train_data)))
    print("  Test:      {} Datenpunkte".format(len(test_data)))
    print()
    print("Phase 2 abgeschlossen!")


# =============================================================
# PHASE 3: ALLE ALGORITHMEN TRAINIEREN UND BEWERTEN
# =============================================================

def phase_3():
    global model, train_data, test_data

    if model is None or test_data is None:
        print("Bitte zuerst Phase 2 ausfuehren!")
        return

    print()
    print("=" * 50)
    print("  PHASE 3: Algorithmus trainieren")
    print("=" * 50)
    print()
    print("  a - kNN (k=3)")
    print("  b - Decision Tree (max_depth=4)")
    print("  c - Random Forest (5 Baeume, max_depth=4)")
    print("  d - Neuronales Netz (12 Neuronen, 200 Epochen)")
    print("  e - Alle nacheinander")
    print()

    try:
        wahl = input("Welchen Algorithmus? (a-e): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("Abgebrochen.")
        return

    if wahl not in ('a', 'b', 'c', 'd', 'e'):
        print("Ungueltige Eingabe.")
        return

    alle = wahl == 'e'

    # --- kNN ---
    if wahl == 'a' or alle:
        print()
        print("-" * 40)
        print("  kNN (k=3)")
        print("-" * 40)
        print("Trainiere kNN...")
        t0 = time.ticks_ms()
        model.train_knn()
        zeit = time.ticks_diff(time.ticks_ms(), t0)
        acc = model.accuracy(test_data, model.predict_knn)
        print("Accuracy: {:.1f}%  (Training: {} ms)".format(acc * 100, zeit))
        print()
        print("Konfusionsmatrix:")
        model.konfusionsmatrix(test_data, model.predict_knn)

    # --- Decision Tree ---
    if wahl == 'b' or alle:
        print()
        print("-" * 40)
        print("  Decision Tree (max_depth=4)")
        print("-" * 40)
        print("Trainiere Decision Tree...")
        t0 = time.ticks_ms()
        model.train_tree(max_depth=4)
        zeit = time.ticks_diff(time.ticks_ms(), t0)
        acc = model.accuracy(test_data, model.predict_tree)
        print("Accuracy: {:.1f}%  (Training: {} ms)".format(acc * 100, zeit))
        print()
        print("Konfusionsmatrix:")
        model.konfusionsmatrix(test_data, model.predict_tree)
        print()
        print("Baumstruktur:")
        model.print_tree()
        print()
        print("Feature-Wichtigkeit:")
        model.feature_wichtigkeit(feature_namen=KANAL_NAMEN)

    # --- Random Forest ---
    if wahl == 'c' or alle:
        print()
        print("-" * 40)
        print("  Random Forest (5 Baeume, max_depth=4)")
        print("-" * 40)
        print("Trainiere Random Forest...")
        t0 = time.ticks_ms()
        model.train_forest(n_trees=5, max_depth=4)
        zeit = time.ticks_diff(time.ticks_ms(), t0)
        acc = model.accuracy(test_data, model.predict_forest)
        print("Accuracy: {:.1f}%  (Training: {} ms)".format(acc * 100, zeit))
        print()
        print("Konfusionsmatrix:")
        model.konfusionsmatrix(test_data, model.predict_forest)

    # --- Neuronales Netz ---
    if wahl == 'd' or alle:
        print()
        print("-" * 40)
        print("  Neuronales Netz (12 Neuronen, 200 Epochen)")
        print("-" * 40)
        print("Trainiere Neuronales Netz (das dauert etwas)...")
        t0 = time.ticks_ms()
        model.train_netz(hidden=12, epochs=200, lr=0.005)
        zeit = time.ticks_diff(time.ticks_ms(), t0)
        acc = model.accuracy(test_data, model.predict_netz)
        print("Accuracy: {:.1f}%  (Training: {} ms)".format(acc * 100, zeit))
        print()
        print("Konfusionsmatrix:")
        model.konfusionsmatrix(test_data, model.predict_netz)

    # --- Vergleich bei "alle" ---
    if alle:
        print()
        print("-" * 40)
        print("  Automatischer Vergleich")
        print("-" * 40)
        model.vergleiche(test_data, label_namen=LABEL_NAMEN)

    print()
    print("Phase 3 abgeschlossen!")


# =============================================================
# PHASE 4: DIDAKTISCHE FUNKTIONEN TESTEN
# =============================================================

def phase_4():
    if model is None:
        print("Bitte zuerst Phase 2 und 3 ausfuehren!")
        return

    print()
    print("=" * 50)
    print("  PHASE 4: Didaktische Erklaerungen")
    print("=" * 50)
    print()
    print("Halte einen Legostein vor den Sensor.")
    print("Das Programm zeigt, wie jeder Algorithmus")
    print("zu seiner Entscheidung kommt.")
    print()
    warte_auf_enter("Stein bereithalten, dann Enter druecken...")

    print("Messe...")
    werte = sensor.messen_roh_liste()
    print("Messwerte: {}".format(werte))
    print()

    gefunden = False

    # --- kNN erklaeren ---
    if model.min_values is not None:
        gefunden = True
        print("-" * 40)
        print("  kNN-Erklaerung:")
        print("-" * 40)
        model.erklaere_knn(werte, label_namen=LABEL_NAMEN)
        warte_auf_enter()

    # --- Decision Tree erklaeren ---
    if model.tree:
        gefunden = True
        print("-" * 40)
        print("  Decision-Tree-Erklaerung:")
        print("-" * 40)
        model.erklaere_tree(werte, feature_namen=KANAL_NAMEN,
                            label_namen=LABEL_NAMEN)
        warte_auf_enter()

    # --- Neuronales Netz Wahrscheinlichkeiten ---
    if model._nn_w1 is not None:
        gefunden = True
        print("-" * 40)
        print("  Neuronales Netz - Wahrscheinlichkeiten:")
        print("-" * 40)
        probs = model.predict_netz_wahrscheinlichkeiten(werte)
        for label_val, prob in sorted(probs.items(),
                                       key=lambda x: x[1], reverse=True):
            name = LABEL_NAMEN.get(label_val, "?")
            balken = "#" * int(prob * 30)
            print("  {:12s}: {:5.1f}% {}".format(name, prob * 100, balken))

    if not gefunden:
        print("Kein Algorithmus trainiert! Bitte zuerst Phase 3 ausfuehren.")

    print()
    print("Phase 4 abgeschlossen!")


# =============================================================
# PHASE 5: MODELL SPEICHERN UND LADEN
# =============================================================

def phase_5():
    global model

    print()
    print("=" * 50)
    print("  PHASE 5: Modell speichern und laden")
    print("=" * 50)
    print()
    print("  a - Modell speichern")
    print("  b - Modell laden")
    print()

    try:
        wahl_aktion = input("Was moechtest du tun? (a/b): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("Abgebrochen.")
        return

    if wahl_aktion == 'a':
        # --- Speichern ---
        if model is None:
            print("Bitte zuerst Phase 2 und 3 ausfuehren!")
            return

        print()
        print("  a - Decision Tree speichern")
        print("  b - Random Forest speichern")
        print("  c - Neuronales Netz speichern")
        print()

        try:
            wahl = input("Welches Modell speichern? (a-c): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("Abgebrochen.")
            return

        if wahl == 'a':
            model_type = 'tree'
            model_name = 'Decision Tree'
        elif wahl == 'b':
            model_type = 'forest'
            model_name = 'Random Forest'
        elif wahl == 'c':
            model_type = 'netz'
            model_name = 'Neuronales Netz'
        else:
            print("Ungueltige Eingabe.")
            return

        print()
        print("Speichere {}-Modell als '{}'...".format(model_name, MODELL_DATEI))
        model.save_model(MODELL_DATEI, model_type=model_type)
        print("Gespeichert!")

    elif wahl_aktion == 'b':
        # --- Laden ---
        print()
        print("Lade Modell aus '{}'...".format(MODELL_DATEI))
        neues_modell = MLearn()
        try:
            typ = neues_modell.load_model(MODELL_DATEI)
        except Exception as e:
            print("FEHLER beim Laden: {}".format(e))
            print("Existiert die Datei '{}'?".format(MODELL_DATEI))
            return

        model = neues_modell
        print("Modell geladen! Typ: '{}'".format(typ))
        print("Du kannst jetzt Phase 4 oder 6 verwenden.")

    else:
        print("Ungueltige Eingabe.")
        return

    print()
    print("Phase 5 abgeschlossen!")


# =============================================================
# PHASE 6: LIVE-ERKENNUNG
# =============================================================

def phase_6():
    print()
    print("=" * 50)
    print("  PHASE 6: Live-Erkennung")
    print("=" * 50)
    print()

    live_model = MLearn()
    try:
        typ = live_model.load_model(MODELL_DATEI)
        print("Modell '{}' geladen (Typ: {})".format(MODELL_DATEI, typ))
    except Exception as e:
        print("FEHLER beim Laden: {}".format(e))
        print("Bitte zuerst Phase 5 ausfuehren!")
        return

    predict_fns = {
        'forest': live_model.predict_forest,
        'netz':   live_model.predict_netz,
        'tree':   live_model.predict_tree,
        'knn':    live_model.predict_knn,
    }
    predict_fn = predict_fns.get(typ, live_model.predict_forest)

    taster = Pin(TASTER_PIN, Pin.IN, Pin.PULL_UP)

    print()
    print("Halte nacheinander verschiedene Legosteine")
    print("vor den Sensor. Die erkannte Farbe wird angezeigt.")
    print("Beende mit Taster oder Ctrl+C.")
    print()
    print("{:>6s}  {:>12s}  {}".format("Nr.", "Erkannt", "Messwerte"))
    print("-" * 50)

    nr = 0
    try:
        while True:
            if taster.value() == 0:
                time.sleep(0.2)
                break
            werte = sensor.messen_roh_liste()
            label = predict_fn(werte)
            name = LABEL_NAMEN.get(label, "Unbekannt")
            nr += 1
            print("{:>6d}  {:>12s}  {}".format(nr, name, werte))
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print("Live-Erkennung beendet nach {} Messungen.".format(nr))

    print()
    print("Phase 6 abgeschlossen!")


# =============================================================
# HAUPTPROGRAMM
# =============================================================

while True:
    zeige_menue()
    try:
        wahl = input("Deine Wahl (0-6): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nBeendet.")
        break

    if wahl == '1':
        phase_1()
    elif wahl == '2':
        phase_2()
    elif wahl == '3':
        phase_3()
    elif wahl == '4':
        phase_4()
    elif wahl == '5':
        phase_5()
    elif wahl == '6':
        phase_6()
    elif wahl == '0':
        print("Tschuess!")
        break
    else:
        print("Ungueltige Eingabe. Bitte 0-6 waehlen.")
