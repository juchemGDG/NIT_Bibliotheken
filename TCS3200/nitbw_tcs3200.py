"""
NIT Bibliothek: TCS3200 - Farbsensor mit Frequenzausgang
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Stephan Juchem mit Hilfe von GitHub Copilot / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Misst Farbintensitaeten ueber den Frequenzausgang OUT des TCS3200/TCS230.
Bietet Rohmessung, RGB-Umrechnung, Kalibrierung und einfache Farberkennung.
"""

from machine import Pin, time_pulse_us
import time


class TCS3200:
    """
    Misst Farben mit dem TCS3200/TCS230 ueber den digitalen Frequenzausgang.

    Unterstuetzte Hardware:
    - TCS3200
    - TCS230

    Schnittstelle: GPIO (OUT + S2/S3, optional S0/S1 und OE)
    """

    _FILTER = {
        'rot': (0, 0),
        'blau': (0, 1),
        'klar': (1, 0),
        'gruen': (1, 1),
    }

    _SKALIERUNG = {
        0: (0, 0),
        2: (0, 1),
        20: (1, 0),
        100: (1, 1),
    }

    _KANAELE = ('rot', 'gruen', 'blau', 'klar')

    def __init__(self, out, s2, s3, s0=None, s1=None, oe=None, frequenzskalierung=2):
        """
        Initialisiert den Farbsensor.

        Args:
            out: GPIO-Pin-Nummer fuer den OUT-Ausgang des Sensors
            s2: GPIO-Pin-Nummer fuer S2 (Filterauswahl)
            s3: GPIO-Pin-Nummer fuer S3 (Filterauswahl)
            s0: Optionaler GPIO-Pin fuer S0 (Frequenzskalierung)
            s1: Optionaler GPIO-Pin fuer S1 (Frequenzskalierung)
            oe: Optionaler GPIO-Pin fuer OE (Output Enable, aktiv LOW)
            frequenzskalierung: 0, 2, 20 oder 100 Prozent
        """
        self._out = Pin(out, Pin.IN)
        self._s2 = Pin(s2, Pin.OUT)
        self._s3 = Pin(s3, Pin.OUT)
        self._s0 = Pin(s0, Pin.OUT) if s0 is not None else None
        self._s1 = Pin(s1, Pin.OUT) if s1 is not None else None
        self._oe = Pin(oe, Pin.OUT) if oe is not None else None

        self._aktueller_filter = 'klar'
        self._frequenzskalierung = frequenzskalierung
        self._kalibrierung_weiss = None
        self._kalibrierung_schwarz = None

        self.aktivieren()
        self.set_frequenzskalierung(frequenzskalierung)
        self.set_filter('klar')

    # ======================================================================
    # Sensorsteuerung
    # ======================================================================

    def aktivieren(self):
        """
        Aktiviert den Sensorausgang, falls OE angeschlossen ist.
        """
        if self._oe is not None:
            self._oe.value(0)

    def deaktivieren(self):
        """
        Deaktiviert den Sensorausgang, falls OE angeschlossen ist.
        """
        if self._oe is not None:
            self._oe.value(1)

    def set_frequenzskalierung(self, prozent):
        """
        Stellt die Frequenzskalierung des Sensors ein.

        Gueltige Werte sind 0, 2, 20 und 100 Prozent.
        Fuer den Unterricht ist 2 % meist am stabilsten messbar.

        Args:
            prozent: 0, 2, 20 oder 100
        """
        if prozent not in self._SKALIERUNG:
            raise ValueError('Frequenzskalierung muss 0, 2, 20 oder 100 sein')

        self._frequenzskalierung = prozent
        if self._s0 is not None and self._s1 is not None:
            s0_wert, s1_wert = self._SKALIERUNG[prozent]
            self._s0.value(s0_wert)
            self._s1.value(s1_wert)
            time.sleep_ms(2)

    def frequenzskalierung(self):
        """
        Gibt die aktuell eingestellte Frequenzskalierung zurueck.

        Returns:
            int: 0, 2, 20 oder 100
        """
        return self._frequenzskalierung

    def set_filter(self, farbe):
        """
        Waehlt den aktiven Farbfilter des Sensors.

        Args:
            farbe: 'rot', 'gruen', 'blau' oder 'klar'
        """
        if farbe not in self._FILTER:
            raise ValueError("Farbe muss 'rot', 'gruen', 'blau' oder 'klar' sein")

        s2_wert, s3_wert = self._FILTER[farbe]
        self._s2.value(s2_wert)
        self._s3.value(s3_wert)
        self._aktueller_filter = farbe
        time.sleep_ms(2)

    def filter(self):
        """
        Gibt den aktuell ausgewaehlten Filter zurueck.

        Returns:
            str: 'rot', 'gruen', 'blau' oder 'klar'
        """
        return self._aktueller_filter

    # ======================================================================
    # Grundmessungen
    # ======================================================================

    def _messen_periode_us(self, timeout_us):
        """Misst eine komplette Periode des Ausgangssignals in Mikrosekunden."""
        high = time_pulse_us(self._out, 1, timeout_us)
        if high <= 0:
            return -1

        low = time_pulse_us(self._out, 0, timeout_us)
        if low <= 0:
            return -1

        return high + low

    def messen_periode_us(self, farbe=None, messungen=10, timeout_us=100000):
        """
        Misst die mittlere Periodendauer des Sensorsignals.

        Args:
            farbe: Optionaler Filter ('rot', 'gruen', 'blau', 'klar')
            messungen: Anzahl der Einzelmessungen
            timeout_us: Timeout pro Puls in Mikrosekunden

        Returns:
            float: Mittlere Periodendauer in us oder -1 bei Fehler
        """
        if farbe is not None:
            self.set_filter(farbe)

        perioden = []
        for _ in range(messungen):
            periode = self._messen_periode_us(timeout_us)
            if periode > 0:
                perioden.append(periode)

        if not perioden:
            return -1

        return round(sum(perioden) / len(perioden), 1)

    def messen_frequenz(self, farbe=None, messungen=10, timeout_us=100000):
        """
        Misst die Ausgangsfrequenz des Sensors in Hertz.

        Args:
            farbe: Optionaler Filter ('rot', 'gruen', 'blau', 'klar')
            messungen: Anzahl der Einzelmessungen
            timeout_us: Timeout pro Puls in Mikrosekunden

        Returns:
            float: Frequenz in Hz oder -1 bei Fehler
        """
        periode = self.messen_periode_us(
            farbe=farbe,
            messungen=messungen,
            timeout_us=timeout_us
        )
        if periode <= 0:
            return -1
        return round(1000000.0 / periode, 1)

    def messen_rohwerte(self, messungen=10, timeout_us=100000):
        """
        Liest die Rohfrequenzen aller vier Filterkanaele aus.

        Args:
            messungen: Anzahl der Einzelmessungen je Kanal
            timeout_us: Timeout pro Puls in Mikrosekunden

        Returns:
            dict: Frequenzen fuer 'rot', 'gruen', 'blau' und 'klar'
        """
        rohwerte = {}
        for kanal in self._KANAELE:
            rohwerte[kanal] = self.messen_frequenz(
                farbe=kanal,
                messungen=messungen,
                timeout_us=timeout_us
            )
        return rohwerte

    def messen_helligkeit(self, messungen=10, timeout_us=100000):
        """
        Misst die Helligkeit ueber den klaren Kanal.

        Mit Kalibrierung wird ein Prozentwert von 0 bis 100 geliefert,
        sonst direkt die Frequenz des klaren Kanals in Hertz.

        Args:
            messungen: Anzahl der Einzelmessungen
            timeout_us: Timeout pro Puls in Mikrosekunden

        Returns:
            float: Prozentwert 0-100 oder Frequenz in Hz, bei Fehler -1
        """
        klar = self.messen_frequenz('klar', messungen=messungen, timeout_us=timeout_us)
        if klar <= 0:
            return -1

        if self._kalibrierung_weiss and self._kalibrierung_schwarz:
            wert = self._normiere_kanal('klar', klar)
            return round(wert * 100.0, 1)

        return klar

    # ======================================================================
    # RGB und Farberkennung
    # ======================================================================

    def _normiere_kanal(self, kanal, frequenz):
        """Normiert einen Kanal mit Schwarz-/Weisskalibrierung auf 0.0 bis 1.0."""
        schwarz = self._kalibrierung_schwarz[kanal]
        weiss = self._kalibrierung_weiss[kanal]
        delta = weiss - schwarz

        if delta <= 0:
            return 0.0

        wert = (frequenz - schwarz) / delta
        if wert < 0.0:
            return 0.0
        if wert > 1.0:
            return 1.0
        return wert

    def _rgb_anteile_aus_rohwerten(self, rohwerte):
        """Berechnet normierte RGB-Anteile aus Rohwerten oder Kalibrierung."""
        if self._kalibrierung_weiss and self._kalibrierung_schwarz:
            return {
                'rot': self._normiere_kanal('rot', rohwerte['rot']),
                'gruen': self._normiere_kanal('gruen', rohwerte['gruen']),
                'blau': self._normiere_kanal('blau', rohwerte['blau']),
            }

        gesamt = rohwerte['rot'] + rohwerte['gruen'] + rohwerte['blau']
        if gesamt <= 0:
            return {'rot': 0.0, 'gruen': 0.0, 'blau': 0.0}

        return {
            'rot': rohwerte['rot'] / gesamt,
            'gruen': rohwerte['gruen'] / gesamt,
            'blau': rohwerte['blau'] / gesamt,
        }

    def messen_rgb(self, messungen=10, timeout_us=100000):
        """
        Liefert RGB-Werte im Bereich 0 bis 255.

        Mit Schwarz-/Weisskalibrierung entsprechen die Werte einer groben
        8-Bit-Darstellung. Ohne Kalibrierung werden relative Farbanteile
        auf 0 bis 255 umgerechnet.

        Args:
            messungen: Anzahl der Einzelmessungen je Kanal
            timeout_us: Timeout pro Puls in Mikrosekunden

        Returns:
            tuple: (rot, gruen, blau) mit Werten von 0 bis 255
        """
        rohwerte = self.messen_rohwerte(messungen=messungen, timeout_us=timeout_us)
        if rohwerte['rot'] <= 0 or rohwerte['gruen'] <= 0 or rohwerte['blau'] <= 0:
            return (0, 0, 0)

        anteile = self._rgb_anteile_aus_rohwerten(rohwerte)
        return (
            int(round(anteile['rot'] * 255)),
            int(round(anteile['gruen'] * 255)),
            int(round(anteile['blau'] * 255)),
        )

    def messen_hex(self, messungen=10, timeout_us=100000):
        """
        Liefert die gemessene Farbe als Hex-String.

        Args:
            messungen: Anzahl der Einzelmessungen je Kanal
            timeout_us: Timeout pro Puls in Mikrosekunden

        Returns:
            str: Farbe im Format '#RRGGBB'
        """
        rot, gruen, blau = self.messen_rgb(
            messungen=messungen,
            timeout_us=timeout_us
        )
        return '#{:02X}{:02X}{:02X}'.format(rot, gruen, blau)

    def dominante_farbe(self, messungen=10, timeout_us=100000, mindestabstand=0.08):
        """
        Bestimmt die dominante Grundfarbe.

        Args:
            messungen: Anzahl der Einzelmessungen je Kanal
            timeout_us: Timeout pro Puls in Mikrosekunden
            mindestabstand: Minimaler Abstand zwischen Platz 1 und Platz 2

        Returns:
            str: 'rot', 'gruen', 'blau' oder 'unbekannt'
        """
        rohwerte = self.messen_rohwerte(messungen=messungen, timeout_us=timeout_us)
        anteile = self._rgb_anteile_aus_rohwerten(rohwerte)
        sortiert = sorted(anteile.items(), key=lambda eintrag: eintrag[1], reverse=True)

        if sortiert[0][1] <= 0:
            return 'unbekannt'

        if (sortiert[0][1] - sortiert[1][1]) < mindestabstand:
            return 'unbekannt'

        return sortiert[0][0]

    def ist_farbe(self, farbe, messungen=10, timeout_us=100000,
                  mindestanteil=0.45, mindestabstand=0.08):
        """
        Prueft, ob eine bestimmte Grundfarbe erkannt wird.

        Args:
            farbe: 'rot', 'gruen' oder 'blau'
            messungen: Anzahl der Einzelmessungen je Kanal
            timeout_us: Timeout pro Puls in Mikrosekunden
            mindestanteil: Mindestanteil der gewuenschten Farbe (0.0-1.0)
            mindestabstand: Minimaler Abstand zur zweitstaerksten Farbe

        Returns:
            bool: True wenn Farbe erkannt wurde, sonst False
        """
        if farbe not in ('rot', 'gruen', 'blau'):
            raise ValueError("Farbe muss 'rot', 'gruen' oder 'blau' sein")

        rohwerte = self.messen_rohwerte(messungen=messungen, timeout_us=timeout_us)
        anteile = self._rgb_anteile_aus_rohwerten(rohwerte)
        zielwert = anteile[farbe]
        rest = [anteile[kanal] for kanal in ('rot', 'gruen', 'blau') if kanal != farbe]

        if zielwert < mindestanteil:
            return False

        return zielwert - max(rest) >= mindestabstand

    # ======================================================================
    # Kalibrierung
    # ======================================================================

    def kalibrieren_weiss(self, messungen=20, timeout_us=100000):
        """
        Speichert die aktuelle Messung als Weissreferenz.

        Args:
            messungen: Anzahl der Einzelmessungen je Kanal
            timeout_us: Timeout pro Puls in Mikrosekunden

        Returns:
            dict: Gespeicherte Weissreferenz
        """
        self._kalibrierung_weiss = self.messen_rohwerte(
            messungen=messungen,
            timeout_us=timeout_us
        )
        return self._kalibrierung_weiss.copy()

    def kalibrieren_schwarz(self, messungen=20, timeout_us=100000):
        """
        Speichert die aktuelle Messung als Schwarzreferenz.

        Args:
            messungen: Anzahl der Einzelmessungen je Kanal
            timeout_us: Timeout pro Puls in Mikrosekunden

        Returns:
            dict: Gespeicherte Schwarzreferenz
        """
        self._kalibrierung_schwarz = self.messen_rohwerte(
            messungen=messungen,
            timeout_us=timeout_us
        )
        return self._kalibrierung_schwarz.copy()

    def reset_kalibrierung(self):
        """
        Loescht beide Kalibrierungen.
        """
        self._kalibrierung_weiss = None
        self._kalibrierung_schwarz = None

    def kalibrierung(self):
        """
        Gibt die aktuell gespeicherten Kalibrierdaten zurueck.

        Returns:
            dict: {'weiss': ..., 'schwarz': ...}
        """
        return {
            'weiss': self._kalibrierung_weiss.copy() if self._kalibrierung_weiss else None,
            'schwarz': self._kalibrierung_schwarz.copy() if self._kalibrierung_schwarz else None,
        }