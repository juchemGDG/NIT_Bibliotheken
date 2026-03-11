"""
NIT Bibliothek: Ultraschall - Entfernungsmessung mit HC-SR04
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Volker Rust / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Misst Entfernungen ueber Ultraschall-Laufzeit (Trigger/Echo).
Bietet Filterfunktionen, Temperaturkompensation und Schwellenwertlogik.
"""

from machine import Pin, time_pulse_us
import time


class Ultraschall:
    """
    Misst Entfernungen mit dem HC-SR04 Ultraschallsensor.

    Unterstuetzte Hardware:
    - HC-SR04 (5 V Logik, mit Spannungsteiler am Echo-Pin)
    - HC-SR04P (3.3 V kompatibel, direkt am ESP32 nutzbar)

    Schnittstelle: 2 GPIO-Pins (Trigger + Echo)
    """

    # Schallgeschwindigkeit bei 20 °C in cm/us (halber Weg: hin und zurueck)
    _SCHALL_CM_US_HALBER_WEG = 0.01715

    # Sensorlimits laut Datenblatt
    _MIN_CM = 2
    _MAX_CM = 400
    _TIMEOUT_US = 30000  # ca. 5 m (grosszuegig)

    def __init__(self, trigger, echo, temperatur=20.0):
        """
        Initialisiert den Ultraschallsensor.

        Args:
            trigger: GPIO-Pin-Nummer fuer den Trigger-Ausgang
            echo: GPIO-Pin-Nummer fuer den Echo-Eingang
            temperatur: Umgebungstemperatur in °C fuer Schallgeschwindigkeit (Standard: 20.0)
        """
        self._trigger = Pin(trigger, Pin.OUT)
        self._echo = Pin(echo, Pin.IN)
        self._trigger.value(0)
        self._offset_cm = 0.0
        self.set_temperatur(temperatur)

    # ========================================================================
    # Temperaturkompensation
    # ========================================================================

    def set_temperatur(self, grad_c):
        """
        Setzt die Umgebungstemperatur fuer die Schallgeschwindigkeitsberechnung.

        Die Schallgeschwindigkeit in Luft betraegt ca. 331.3 + 0.606 * T (m/s).
        Ideal in Kombination mit einem BME280-Sensor.

        Args:
            grad_c: Temperatur in Grad Celsius
        """
        v_m_s = 331.3 + 0.606 * grad_c
        self._cm_pro_us_halber_weg = v_m_s / 20000.0

    # ========================================================================
    # Grundmessungen
    # ========================================================================

    def messen_laufzeit(self):
        """
        Misst die Signallaufzeit (hin und zurueck) in Mikrosekunden.

        Returns:
            float: Laufzeit in Mikrosekunden oder -1 bei Timeout
        """
        self._trigger.value(0)
        time.sleep_us(5)
        self._trigger.value(1)
        time.sleep_us(10)
        self._trigger.value(0)

        laufzeit = time_pulse_us(self._echo, 1, self._TIMEOUT_US)
        return laufzeit if laufzeit > 0 else -1

    def messen_cm(self):
        """
        Misst die Entfernung in Zentimetern.

        Returns:
            float: Entfernung in cm oder -1 bei Timeout/Fehler
        """
        laufzeit = self.messen_laufzeit()
        if laufzeit < 0:
            return -1
        distanz = laufzeit * self._cm_pro_us_halber_weg + self._offset_cm
        if distanz < self._MIN_CM or distanz > self._MAX_CM:
            return -1
        return round(distanz, 1)

    def messen_mm(self):
        """
        Misst die Entfernung in Millimetern.

        Returns:
            float: Entfernung in mm oder -1 bei Timeout/Fehler
        """
        cm = self.messen_cm()
        if cm < 0:
            return -1
        return round(cm * 10, 0)

    def messen_inch(self):
        """
        Misst die Entfernung in Zoll (Inch).

        Returns:
            float: Entfernung in Zoll oder -1 bei Timeout/Fehler
        """
        cm = self.messen_cm()
        if cm < 0:
            return -1
        return round(cm / 2.54, 1)

    # ========================================================================
    # Filterfunktionen
    # ========================================================================

    def messen_mittelwert(self, n=5):
        """
        Fuehrt n Messungen durch und gibt den Mittelwert zurueck.
        Ungueltige Messungen (-1) werden dabei verworfen.

        Args:
            n: Anzahl der Messungen (Standard: 5)

        Returns:
            float: Mittelwert in cm oder -1 wenn keine gueltige Messung
        """
        werte = []
        for _ in range(n):
            cm = self.messen_cm()
            if cm > 0:
                werte.append(cm)
            time.sleep_ms(30)
        if not werte:
            return -1
        return round(sum(werte) / len(werte), 1)

    def messen_median(self, n=5):
        """
        Fuehrt n Messungen durch und gibt den Median zurueck.
        Der Median ist robuster gegenueber Ausreissern als der Mittelwert.

        Args:
            n: Anzahl der Messungen (Standard: 5)

        Returns:
            float: Median in cm oder -1 wenn keine gueltige Messung
        """
        werte = []
        for _ in range(n):
            cm = self.messen_cm()
            if cm > 0:
                werte.append(cm)
            time.sleep_ms(30)
        if not werte:
            return -1
        werte.sort()
        mitte = len(werte) // 2
        if len(werte) % 2 == 0:
            return round((werte[mitte - 1] + werte[mitte]) / 2, 1)
        return werte[mitte]

    def messen_bereich(self, n=5):
        """
        Fuehrt n Messungen durch und gibt Minimum, Maximum und Mittelwert zurueck.
        Zeigt anschaulich die Streuung der Messwerte.

        Args:
            n: Anzahl der Messungen (Standard: 5)

        Returns:
            tuple: (minimum, maximum, mittelwert) in cm oder (-1, -1, -1) bei Fehler
        """
        werte = []
        for _ in range(n):
            cm = self.messen_cm()
            if cm > 0:
                werte.append(cm)
            time.sleep_ms(30)
        if not werte:
            return (-1, -1, -1)
        return (
            round(min(werte), 1),
            round(max(werte), 1),
            round(sum(werte) / len(werte), 1)
        )

    # ========================================================================
    # Schwellenwertlogik
    # ========================================================================

    def ist_naeher_als(self, cm):
        """
        Prueft ob ein Objekt naeher als der angegebene Schwellenwert ist.

        Args:
            cm: Schwellenwert in Zentimetern

        Returns:
            bool: True wenn Objekt naeher, False wenn weiter entfernt oder Fehler
        """
        distanz = self.messen_cm()
        if distanz < 0:
            return False
        return distanz < cm

    def zone(self, nah=10, mittel=50):
        """
        Ordnet die aktuelle Entfernung in eine von drei Zonen ein.

        Args:
            nah: Grenze fuer Zone 'nah' in cm (Standard: 10)
            mittel: Grenze fuer Zone 'mittel' in cm (Standard: 50)

        Returns:
            str: 'nah', 'mittel', 'fern' oder 'fehler'
        """
        distanz = self.messen_cm()
        if distanz < 0:
            return 'fehler'
        if distanz < nah:
            return 'nah'
        if distanz < mittel:
            return 'mittel'
        return 'fern'

    # ========================================================================
    # Geschwindigkeit
    # ========================================================================

    def geschwindigkeit(self, intervall_ms=500):
        """
        Berechnet die Geschwindigkeit eines Objekts aus zwei Messungen.

        Fuehrt zwei Messungen im angegebenen Zeitabstand durch und
        berechnet daraus die Annaeherungs-/Entfernungsgeschwindigkeit.

        Args:
            intervall_ms: Zeitabstand zwischen den Messungen in ms (Standard: 500)

        Returns:
            float: Geschwindigkeit in cm/s (positiv = naehert sich,
                   negativ = entfernt sich) oder 0 bei Fehler
        """
        d1 = self.messen_cm()
        time.sleep_ms(intervall_ms)
        d2 = self.messen_cm()
        if d1 < 0 or d2 < 0:
            return 0
        delta_cm = d1 - d2
        delta_s = intervall_ms / 1000.0
        return round(delta_cm / delta_s, 1)

    # ========================================================================
    # Kalibrierung
    # ========================================================================

    def kalibrieren(self, bekannte_distanz_cm, n=10):
        """
        Kalibriert den Sensor anhand eines bekannten Abstands.
        Fuehrt mehrere Messungen durch und berechnet einen Offset.

        Aufbau: Sensor auf bekannten Abstand zu einer Wand/Flaeche ausrichten.

        Args:
            bekannte_distanz_cm: Der tatsaechliche Abstand in cm
            n: Anzahl Messungen fuer die Kalibrierung (Standard: 10)
        """
        # Offset zuruecksetzen fuer Rohmessung
        alter_offset = self._offset_cm
        self._offset_cm = 0.0

        mittel = self.messen_mittelwert(n)

        if mittel < 0:
            self._offset_cm = alter_offset
            print("Kalibrierung fehlgeschlagen: keine gueltigen Messwerte")
            return

        self._offset_cm = bekannte_distanz_cm - mittel
        print("Kalibrierung abgeschlossen.")
        print("Gemessen: {:.1f} cm, Soll: {:.1f} cm, Offset: {:+.1f} cm".format(
            mittel, bekannte_distanz_cm, self._offset_cm))

    # ========================================================================
    # Ueberwachung
    # ========================================================================

    def ueberwachen(self, schwelle_cm, callback, intervall_ms=200):
        """
        Ueberwacht dauerhaft die Entfernung und ruft eine Callback-Funktion
        auf, sobald ein Objekt naeher als der Schwellenwert kommt.

        Hinweis: Diese Funktion blockiert! Beenden mit Ctrl+C.

        Args:
            schwelle_cm: Ausloese-Abstand in cm
            callback: Funktion, die bei Unterschreitung aufgerufen wird.
                      Erhaelt die gemessene Distanz als Parameter.
            intervall_ms: Messintervall in ms (Standard: 200)
        """
        print("Ueberwachung aktiv (Schwelle: {} cm)".format(schwelle_cm))
        print("Beenden mit Ctrl+C")
        try:
            while True:
                distanz = self.messen_cm()
                if 0 < distanz < schwelle_cm:
                    callback(distanz)
                time.sleep_ms(intervall_ms)
        except KeyboardInterrupt:
            print("Ueberwachung beendet.")
