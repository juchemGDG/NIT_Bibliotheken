"""
NIT Bibliothek: VIBRATION - Schwingungsmerkmale und Referenzprofile
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Volker Rust / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-10

Berechnet Merkmale aus Beschleunigungsfenstern und vergleicht sie mit einer
gespeicherten gesunden Referenz. Der Sensor wird unabhaengig uebergeben.
"""

import json
import math
import time


FEATURE_NAMES = (
    "x_rms_ac", "x_peak_to_peak", "x_crest_factor", "x_zero_cross_hz",
    "y_rms_ac", "y_peak_to_peak", "y_crest_factor", "y_zero_cross_hz",
    "z_rms_ac", "z_peak_to_peak", "z_crest_factor", "z_zero_cross_hz",
)


def sammle_fenster(sensor, anzahl=128, abtastrate=200):
    """Liest ein zeitgesteuertes Beschleunigungsfenster vom ADXL345."""
    if anzahl < 2:
        raise ValueError("Ein Messfenster braucht mindestens zwei Samples.")
    if abtastrate not in (25, 50, 100, 200, 400):
        raise ValueError("Abtastrate muss 25, 50, 100, 200 oder 400 Hz sein.")

    sensor.set_sample_rate(abtastrate)
    periode_us = 1000000 // abtastrate
    time.sleep_ms(10)
    deadline = time.ticks_us()
    fenster = []

    for index in range(anzahl):
        if index:
            deadline = time.ticks_add(deadline, periode_us)
            wartezeit = time.ticks_diff(deadline, time.ticks_us())
            if wartezeit > 0:
                time.sleep_us(wartezeit)
            verspaetung = time.ticks_diff(time.ticks_us(), deadline)
            if verspaetung > periode_us // 4:
                raise RuntimeError("Abtastung verpasst; Abtastrate reduzieren.")
        fenster.append(sensor.read_accel())

    return fenster


def berechne_merkmale(fenster, abtastrate=200):
    """
    Berechnet zeitbasierte Vibrationsmerkmale aus einem Fenster von (x, y, z)-Werten.

    Args:
        fenster: Folge von Beschleunigungs-Tupeln, vorzugsweise in g.
        abtastrate: Abtastrate des Fensters in Hz fuer die Nulldurchgangsfrequenz.

    Returns:
        list: RMS der Wechselkomponente, Spitze-Spitze und Crest-Faktor je Achse.
    """
    if len(fenster) < 2:
        raise ValueError("Ein Messfenster braucht mindestens zwei Samples.")
    if abtastrate <= 0:
        raise ValueError("Die Abtastrate muss groesser als null sein.")

    achsen = [[], [], []]
    for messung in fenster:
        if len(messung) != 3:
            raise ValueError("Jedes Sample muss genau drei Achsen enthalten.")
        for index in range(3):
            achsen[index].append(float(messung[index]))

    merkmale = []
    for werte in achsen:
        mittelwert = sum(werte) / len(werte)
        wechselwerte = [wert - mittelwert for wert in werte]
        rms = math.sqrt(sum(wert * wert for wert in wechselwerte) / len(wechselwerte))
        spitze = max(abs(wert) for wert in wechselwerte)
        spitze_spitze = max(werte) - min(werte)
        crest_factor = spitze / rms if rms > 0 else 0.0
        nulldurchgaenge = 0
        vorher_positiv = wechselwerte[0] >= 0
        for wert in wechselwerte[1:]:
            positiv = wert >= 0
            if positiv != vorher_positiv:
                nulldurchgaenge += 1
            vorher_positiv = positiv
        frequenz = nulldurchgaenge * abtastrate / (2 * (len(wechselwerte) - 1))
        merkmale.extend((rms, spitze_spitze, crest_factor, frequenz))

    return merkmale


class VibrationsReferenz:
    """
    Bewertet Schwingungsmerkmale relativ zu einer gesunden Motorreferenz.

    Unterstuetzte Hardware:
    - ADXL345 oder andere Sensoren mit Beschleunigungswerten auf drei Achsen

    Schnittstelle: Dateisystem (JSON)
    """

    def __init__(self, motor_id, schwelle=3.0, mindest_streuung=0.000001):
        self.motor_id = str(motor_id)
        self.schwelle = float(schwelle)
        self.mindest_streuung = float(mindest_streuung)
        if self.schwelle <= 0 or self.mindest_streuung <= 0:
            raise ValueError("Schwelle und Mindeststreuung muessen groesser als null sein.")
        self.mittelwerte = None
        self.streuungen = None

    def einlernen(self, feature_fenster):
        """Erstellt das Referenzprofil aus mindestens zwei gesunden Feature-Vektoren."""
        if len(feature_fenster) < 2:
            raise ValueError("Zum Einlernen sind mindestens zwei gesunde Fenster noetig.")

        breite = len(feature_fenster[0])
        if breite != len(FEATURE_NAMES):
            raise ValueError("Feature-Vektoren muessen zum aktuellen Vibrationsformat passen.")

        daten = []
        for vektor in feature_fenster:
            if len(vektor) != breite:
                raise ValueError("Alle Feature-Vektoren muessen gleich lang sein.")
            daten.append([float(wert) for wert in vektor])

        self.mittelwerte = []
        self.streuungen = []
        for index in range(breite):
            werte = [vektor[index] for vektor in daten]
            mittelwert = sum(werte) / len(werte)
            varianz = sum((wert - mittelwert) ** 2 for wert in werte) / len(werte)
            self.mittelwerte.append(mittelwert)
            self.streuungen.append(max(math.sqrt(varianz), self.mindest_streuung))

    def abweichung(self, merkmale):
        """Gibt die mittlere standardisierte Abweichung zum gesunden Profil zurueck."""
        if self.mittelwerte is None:
            raise ValueError("Vor der Bewertung muss ein Referenzprofil eingelernt werden.")
        if len(merkmale) != len(self.mittelwerte):
            raise ValueError("Feature-Anzahl passt nicht zum Referenzprofil.")

        quadrate = []
        for index, wert in enumerate(merkmale):
            z_wert = (float(wert) - self.mittelwerte[index]) / self.streuungen[index]
            quadrate.append(z_wert * z_wert)
        return math.sqrt(sum(quadrate) / len(quadrate))

    def ist_abweichend(self, merkmale):
        """Prueft, ob der Abweichungswert die konfigurierte Schwelle ueberschreitet."""
        return self.abweichung(merkmale) > self.schwelle

    def speichern(self, dateiname):
        """Speichert das eingelehrte Motorprofil als JSON-Datei."""
        if self.mittelwerte is None:
            raise ValueError("Es gibt noch kein eingelerntes Referenzprofil.")
        profil = {
            "version": 1,
            "motor_id": self.motor_id,
            "schwelle": self.schwelle,
            "mindest_streuung": self.mindest_streuung,
            "feature_names": list(FEATURE_NAMES),
            "mittelwerte": self.mittelwerte,
            "streuungen": self.streuungen,
        }
        with open(dateiname, "w") as datei:
            json.dump(profil, datei)

    @classmethod
    def laden(cls, dateiname):
        """Laedt ein zuvor gespeichertes Motorprofil aus einer JSON-Datei."""
        with open(dateiname, "r") as datei:
            profil = json.load(datei)
        if profil.get("version") != 1:
            raise ValueError("Unbekannte Version des Referenzprofils.")
        if profil.get("feature_names") != list(FEATURE_NAMES):
            raise ValueError("Das Referenzprofil verwendet ein anderes Feature-Format.")

        referenz = cls(
            profil["motor_id"],
            schwelle=profil["schwelle"],
            mindest_streuung=profil["mindest_streuung"],
        )
        referenz.mittelwerte = [float(wert) for wert in profil["mittelwerte"]]
        referenz.streuungen = [float(wert) for wert in profil["streuungen"]]
        if not referenz.mittelwerte or len(referenz.mittelwerte) != len(referenz.streuungen):
            raise ValueError("Das Referenzprofil enthaelt ungueltige Feature-Daten.")
        if any(wert <= 0 for wert in referenz.streuungen):
            raise ValueError("Das Referenzprofil enthaelt ungueltige Streuungen.")
        return referenz