"""
NIT Bibliothek: DATENSAMMLER - Interaktives Datensammeln fuer ML
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Volker Rust / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Sammelt Messdaten per Tasterdruck und speichert sie als CSV-Datei.
Gedacht als Baustein fuer den ML-Workflow: Sammeln -> Trainieren -> Erkennen.
"""

from machine import Pin
import time


class DatenSammler:
    """
    Interaktiver Datensammler fuer ML-Projekte.

    Workflow:
    1) Sensor anschliessen und Messfunktion definieren
    2) DatenSammler erstellen mit Taster-Pin und CSV-Dateiname
    3) sammle() aufrufen: Das Programm fragt Label fuer Label ab
       und speichert die Messwerte nach Tasterdruck in eine CSV-Datei.

    Der Taster wird intern mit Pullup konfiguriert (ein Pin an GPIO,
    anderer Pin an GND). Druecken = LOW = Messung wird ausgeloest.
    """

    def __init__(self, taster_pin, csv_datei='daten.csv',
                 spaltennamen=None, separator=','):
        """
        Erstellt einen neuen DatenSammler.

        Args:
            taster_pin:    GPIO-Pin-Nummer des Tasters (z.B. 12)
            csv_datei:     Dateiname fuer die CSV-Ausgabe
            spaltennamen:  Liste der Spaltennamen (z.B. ['v','b','g','ge','o','r','label'])
                           Falls None, wird kein Header geschrieben.
            separator:     Trennzeichen in der CSV (Standard: Komma)
        """
        self.taster = Pin(taster_pin, Pin.IN, Pin.PULL_UP)
        self.csv_datei = csv_datei
        self.spaltennamen = spaltennamen
        self.separator = separator
        self.daten = []

        # CSV-Datei mit Header anlegen (falls Spaltennamen gegeben)
        if spaltennamen:
            with open(csv_datei, 'w') as f:
                f.write(separator.join(spaltennamen) + '\n')

    def _warte_auf_taster(self):
        """Wartet, bis der Taster gedrueckt und wieder losgelassen wird."""
        # Warten bis gedrueckt (LOW)
        while self.taster.value() == 1:
            time.sleep_ms(20)
        # Entprellen
        time.sleep_ms(50)
        # Warten bis losgelassen (HIGH)
        while self.taster.value() == 0:
            time.sleep_ms(20)
        time.sleep_ms(50)

    def sammle(self, mess_funktion, labels, messungen_pro_label=10):
        """
        Sammelt interaktiv Messdaten fuer mehrere Labels.

        Fuer jedes Label wird der Benutzer aufgefordert, den Sensor
        auf die entsprechende Farbe/Klasse zu richten und den Taster
        zu druecken. Nach jeder Messung werden die Werte in die
        CSV-Datei geschrieben.

        Args:
            mess_funktion:       Funktion, die eine Feature-Liste zurueckgibt.
                                 Z.B. sensor.messen_roh_liste fuer AS7262
                                 oder eine eigene Funktion fuer TCS3200.
            labels:              Dict {label_nummer: "Beschreibung"}
                                 z.B. {1: "Rot", 2: "Blau", 3: "Gruen"}
            messungen_pro_label: Anzahl Messungen pro Label (Standard: 10)
        """
        print("=== Datensammlung starten ===")
        print("Messungen pro Label: {}".format(messungen_pro_label))
        print()

        for label_nr, label_name in sorted(labels.items()):
            print("--- Label {}: {} ---".format(label_nr, label_name))
            print("Sensor auf '{}' richten und Taster druecken.".format(label_name))

            for i in range(messungen_pro_label):
                print("  Messung {}/{} - Taster druecken...".format(
                    i + 1, messungen_pro_label), end='')

                self._warte_auf_taster()

                # Messung durchfuehren
                werte = mess_funktion()
                if not isinstance(werte, list):
                    werte = list(werte)

                # Datenpunkt speichern
                datenpunkt = werte + [float(label_nr)]
                self.daten.append(datenpunkt)

                # In CSV schreiben
                zeile = self.separator.join(str(w) for w in datenpunkt)
                with open(self.csv_datei, 'a') as f:
                    f.write(zeile + '\n')

                print(" OK: {}".format(werte))

            print()

        print("=== Fertig! {} Datenpunkte gesammelt ===".format(len(self.daten)))
        print("Gespeichert in: {}".format(self.csv_datei))

    def sammle_einzeln(self, mess_funktion, label):
        """
        Fuehrt eine einzelne Messung durch und gibt die Werte zurueck.

        Nuetzlich, wenn man den Sammelprozess selbst steuern moechte.

        Args:
            mess_funktion: Funktion, die eine Feature-Liste zurueckgibt
            label:         Label-Nummer fuer diesen Datenpunkt

        Returns:
            list: Feature-Werte + Label als letzer Eintrag
        """
        werte = mess_funktion()
        if not isinstance(werte, list):
            werte = list(werte)

        datenpunkt = werte + [float(label)]
        self.daten.append(datenpunkt)

        # In CSV schreiben
        zeile = self.separator.join(str(w) for w in datenpunkt)
        with open(self.csv_datei, 'a') as f:
            f.write(zeile + '\n')

        return datenpunkt

    def get_daten(self):
        """
        Gibt alle bisher gesammelten Datenpunkte zurueck.

        Returns:
            list: Liste von Listen [feature1, feature2, ..., label]
        """
        return self.daten
