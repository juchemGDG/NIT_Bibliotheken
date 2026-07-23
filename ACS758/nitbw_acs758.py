"""
NIT Bibliothek: ACS758 - Hall-Stromsensor fuer Gleich- und Wechselstrom
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-07

Liest die Analogspannung des ACS758 ueber einen ADC ein und rechnet sie
ratiometrisch in Stromstaerke um. Alle Umrechnungsfaktoren werden vorab
berechnet, damit pro Messwert nur eine Multiplikation und eine Subtraktion
noetig sind (schnelle Burst-Messung). Enthalten sind Varianten-Presets,
Nullpunkt- und Referenzkalibrierung sowie Mittelwert-, Median-,
Effektivwert- und Spitzenwertauswertung.
"""

from machine import ADC, Pin
from time import ticks_us, ticks_ms, ticks_diff, sleep_us


class ACS758:
    """
    Misst Stromstaerke in mA und A mit dem Hall-Sensor ACS758.

    Unterstuetzte Hardware:
    - ACS758LCB-050B / 050U (50 A)
    - ACS758LCB-100B / 100U (100 A)
    - ACS758KCB-150B / 150U (150 A)
    - ACS758ECB-200B / 200U (200 A)

    Schnittstelle: 1x ADC (analoger Ausgang VIOUT, meist ueber Spannungsteiler)
    """

    # Varianten-Presets: Name -> (Empfindlichkeit in mV/A bei Vcc = 5 V,
    #                             bidirektional, Nennstrom in A)
    VARIANTEN = {
        "50B": (40.0, True, 50),
        "50U": (60.0, False, 50),
        "100B": (20.0, True, 100),
        "100U": (40.0, False, 100),
        "150B": (13.3, True, 150),
        "150U": (26.7, False, 150),
        "200B": (10.0, True, 200),
        "200U": (20.0, False, 200),
    }

    # Nullpunkt als Anteil der Versorgungsspannung
    NULL_BIDIREKTIONAL = 0.5
    NULL_UNIDIREKTIONAL = 0.12

    # Referenzspannung, fuer die die Datenblattwerte gelten
    VCC_NENN = 5.0

    def __init__(
        self,
        pin,
        variante="50B",
        vcc=5.0,
        teiler=1.0,
        adc_bits=12,
        vref=3.3,
        attenuation="11db",
        messungen=8,
        glaettung=0.0,
        totzone_ma=0.0,
        invertiert=False,
    ):
        """
        Initialisiert den ACS758 Stromsensor.

        Args:
            pin: GPIO fuer VIOUT (ADC-faehiger Pin, z. B. 34/35/32/33)
            variante: Sensortyp aus VARIANTEN ("50B", "100U", ...)
            vcc: Versorgungsspannung des Sensors in Volt (typisch 5.0)
            teiler: Teilerfaktor Vsensor/Vadc des Spannungsteilers
                    (1.0 = direkt, 2.0 = Teiler 1:2 mit z. B. 10k/10k)
            adc_bits: ADC-Aufloesung (9-12, ESP32 typisch 12)
            vref: Referenzspannung des ADC in Volt (typisch 3.3)
            attenuation: ADC-Daempfung ("0db", "2.5db", "6db", "11db")
            messungen: Standard-Anzahl Einzelmessungen pro Messwert
            glaettung: EMA-Glaettung 0.0 (aus) bis 0.99 (sehr traege)
            totzone_ma: Betraege unter dieser Grenze werden als 0 mA gemeldet
            invertiert: True dreht das Vorzeichen (Stromrichtung getauscht)
        """
        self._adc_bits = max(9, min(12, int(adc_bits)))
        self._max_raw = (1 << self._adc_bits) - 1
        self._vref = float(vref)

        self._adc = ADC(Pin(pin))
        self._daempfung = str(attenuation).lower()
        self._konfiguriere_adc()

        # read_uv() liefert werkskalibrierte Mikrovolt und ist deutlich
        # genauer als der lineare Rohwert. Nur nutzen, wenn im Build vorhanden.
        self._hat_uv = self._pruefe_uv()

        self._vcc = float(vcc)
        self._teiler = float(teiler)
        self._messungen = max(1, int(messungen))
        self._invertiert = bool(invertiert)
        self._totzone_ma = abs(float(totzone_ma))

        self._glaettung = 0.0
        self._ema = None
        self.set_glaettung(glaettung)

        self._variante = None
        self._empf_mv_a = 40.0
        self._bidirektional = True
        self._nennstrom_a = 50
        self._nullpunkt_v = self._vcc * self.NULL_BIDIREKTIONAL
        self.set_variante(variante)

    # ------------------------------------------------------------------
    # Interne Hilfsfunktionen
    # ------------------------------------------------------------------

    def _konfiguriere_adc(self):
        """Setzt ADC-Breite und Daempfung robust fuer verschiedene Builds."""
        try:
            width_const = getattr(ADC, "WIDTH_{}BIT".format(self._adc_bits))
            self._adc.width(width_const)
        except Exception:
            pass

        try:
            mapping = {
                "0db": ADC.ATTN_0DB,
                "2.5db": ADC.ATTN_2_5DB,
                "6db": ADC.ATTN_6DB,
                "11db": ADC.ATTN_11DB,
            }
            self._adc.atten(mapping.get(self._daempfung, ADC.ATTN_11DB))
        except Exception:
            pass

    def _pruefe_uv(self):
        """Prueft, ob der ADC kalibrierte Mikrovolt liefern kann."""
        try:
            self._adc.read_uv()
            return True
        except Exception:
            return False

    def _aktualisieren(self):
        """
        Berechnet alle Umrechnungsfaktoren neu.

        Danach gilt fuer jeden Rohwert:
            strom_a = rohwert * _faktor_a - _null_a
        """
        empf_v_a = self._empf_mv_a / 1000.0
        if empf_v_a == 0:
            raise ValueError("Empfindlichkeit darf nicht 0 sein")

        # Rohwert -> Spannung am ADC-Pin
        if self._hat_uv:
            faktor_v = 1e-6
        else:
            faktor_v = self._vref / self._max_raw

        self._faktor_a = faktor_v * self._teiler / empf_v_a
        self._null_a = self._nullpunkt_v / empf_v_a
        self._ema = None

    def _roh(self):
        """Liest einen ADC-Wert (Rohwert oder Mikrovolt, je nach Build)."""
        if self._hat_uv:
            return self._adc.read_uv()
        return self._adc.read()

    def _roh_mittel(self, n):
        """Liest n ADC-Werte moeglichst schnell und mittelt sie."""
        if n <= 1:
            return self._roh()
        summe = 0
        for _ in range(n):
            summe += self._roh()
        return summe / n

    def _roh_zu_strom_a(self, wert):
        """Rechnet einen ADC-Wert in Ampere um (Nullpunkt bereits enthalten)."""
        strom = wert * self._faktor_a - self._null_a
        if self._invertiert:
            strom = -strom
        return strom

    def _nachbearbeiten(self, strom_a, glaetten=True):
        """Wendet Glaettung und Totzone auf einen Stromwert an."""
        if glaetten and self._glaettung > 0.0:
            if self._ema is None:
                self._ema = strom_a
            else:
                self._ema = self._ema + (1.0 - self._glaettung) * (strom_a - self._ema)
            strom_a = self._ema

        if self._totzone_ma > 0.0 and abs(strom_a) * 1000.0 < self._totzone_ma:
            return 0.0
        return strom_a

    # ------------------------------------------------------------------
    # Rohwerte und Spannung
    # ------------------------------------------------------------------

    def lesen_roh(self, n=1):
        """
        Liest den ADC-Rohwert (bzw. Mikrovolt bei kalibriertem ADC).

        Args:
            n: Anzahl Einzelmessungen fuer den Mittelwert

        Returns:
            float: gemittelter ADC-Wert
        """
        return self._roh_mittel(max(1, int(n)))

    def lesen_spannung(self, n=None):
        """
        Liest die Ausgangsspannung des Sensors in Volt.

        Der Teilerfaktor ist bereits herausgerechnet, der Wert entspricht
        also der Spannung an VIOUT.

        Args:
            n: Anzahl Einzelmessungen (None -> Standardwert)

        Returns:
            float: Spannung an VIOUT in Volt
        """
        if n is None:
            n = self._messungen
        wert = self._roh_mittel(max(1, int(n)))
        if self._hat_uv:
            return wert * 1e-6 * self._teiler
        return wert * (self._vref / self._max_raw) * self._teiler

    # ------------------------------------------------------------------
    # Strommessung
    # ------------------------------------------------------------------

    def messen_a(self, n=None):
        """
        Misst die Stromstaerke in Ampere.

        Args:
            n: Anzahl Einzelmessungen (None -> Standardwert aus set_messungen)

        Returns:
            float: Strom in A (negativ bei umgekehrter Flussrichtung)
        """
        if n is None:
            n = self._messungen
        strom = self._roh_zu_strom_a(self._roh_mittel(max(1, int(n))))
        return self._nachbearbeiten(strom)

    def messen_ma(self, n=None):
        """
        Misst die Stromstaerke in Milliampere.

        Args:
            n: Anzahl Einzelmessungen (None -> Standardwert)

        Returns:
            float: Strom in mA
        """
        return self.messen_a(n) * 1000.0

    def messen_schnell_a(self):
        """
        Misst mit einer einzigen ADC-Wandlung ohne Glaettung.

        Schnellster Weg zu einem Messwert, dafuer mit dem hoechsten Rauschen.

        Returns:
            float: Strom in A
        """
        return self._roh_zu_strom_a(self._roh())

    def messen_schnell_ma(self):
        """
        Misst mit einer einzigen ADC-Wandlung ohne Glaettung.

        Returns:
            float: Strom in mA
        """
        return self.messen_schnell_a() * 1000.0

    def messen_median_a(self, n=9):
        """
        Misst den Median aus n Einzelmessungen (robust gegen Ausreisser).

        Args:
            n: Anzahl Einzelmessungen (ungerade Werte empfohlen)

        Returns:
            float: Strom in A
        """
        n = max(1, int(n))
        werte = [self._roh() for _ in range(n)]
        werte.sort()

        mitte = n // 2
        if n % 2 == 0:
            wert = (werte[mitte - 1] + werte[mitte]) / 2.0
        else:
            wert = werte[mitte]

        return self._nachbearbeiten(self._roh_zu_strom_a(wert))

    def messen_median_ma(self, n=9):
        """
        Misst den Median aus n Einzelmessungen in Milliampere.

        Returns:
            float: Strom in mA
        """
        return self.messen_median_a(n) * 1000.0

    def messen_serie_a(self, anzahl=100, intervall_us=0):
        """
        Nimmt schnell hintereinander mehrere Messwerte auf.

        Die Umrechnung erfolgt erst nach der Aufnahme, damit die Abtastung
        so schnell und gleichmaessig wie moeglich bleibt.

        Args:
            anzahl: Anzahl der Messwerte
            intervall_us: Pause zwischen zwei Messungen in Mikrosekunden

        Returns:
            list: Stromwerte in A
        """
        anzahl = max(1, int(anzahl))
        intervall_us = max(0, int(intervall_us))

        rohwerte = []
        for _ in range(anzahl):
            rohwerte.append(self._roh())
            if intervall_us:
                sleep_us(intervall_us)

        return [self._roh_zu_strom_a(w) for w in rohwerte]

    def messen_serie_ma(self, anzahl=100, intervall_us=0):
        """
        Nimmt schnell hintereinander mehrere Messwerte in mA auf.

        Returns:
            list: Stromwerte in mA
        """
        return [i * 1000.0 for i in self.messen_serie_a(anzahl, intervall_us)]

    def messen_effektivwert_a(self, dauer_ms=200):
        """
        Misst den Effektivwert (RMS) ueber ein Zeitfenster.

        Geeignet fuer Wechselstrom. Bei 50 Hz sollte das Fenster ein
        Vielfaches von 20 ms sein (z. B. 200 ms).

        Args:
            dauer_ms: Messdauer in Millisekunden

        Returns:
            float: Effektivwert in A
        """
        return self.messen_statistik(dauer_ms)["effektiv_a"]

    def messen_effektivwert_ma(self, dauer_ms=200):
        """
        Misst den Effektivwert (RMS) ueber ein Zeitfenster in mA.

        Returns:
            float: Effektivwert in mA
        """
        return self.messen_effektivwert_a(dauer_ms) * 1000.0

    def messen_spitze_a(self, dauer_ms=200):
        """
        Ermittelt kleinsten und groessten Strom in einem Zeitfenster.

        Args:
            dauer_ms: Messdauer in Millisekunden

        Returns:
            tuple: (min_a, max_a)
        """
        werte = self.messen_statistik(dauer_ms)
        return werte["min_a"], werte["max_a"]

    def messen_statistik(self, dauer_ms=200):
        """
        Tastet den Sensor ein Zeitfenster lang ab und wertet es aus.

        Args:
            dauer_ms: Messdauer in Millisekunden

        Returns:
            dict: min_a, max_a, mittel_a, effektiv_a, spitze_spitze_a,
                  anzahl, rate_hz
        """
        dauer_ms = max(1, int(dauer_ms))

        summe = 0.0
        summe_quadrat = 0.0
        kleinster = None
        groesster = None
        anzahl = 0

        start = ticks_ms()
        start_us = ticks_us()
        while ticks_diff(ticks_ms(), start) < dauer_ms:
            strom = self._roh_zu_strom_a(self._roh())
            summe += strom
            summe_quadrat += strom * strom
            if kleinster is None or strom < kleinster:
                kleinster = strom
            if groesster is None or strom > groesster:
                groesster = strom
            anzahl += 1
        laufzeit_us = ticks_diff(ticks_us(), start_us)

        mittel = summe / anzahl
        effektiv = (summe_quadrat / anzahl) ** 0.5
        rate = anzahl * 1000000.0 / laufzeit_us if laufzeit_us > 0 else 0.0

        return {
            "min_a": kleinster,
            "max_a": groesster,
            "mittel_a": mittel,
            "effektiv_a": effektiv,
            "spitze_spitze_a": groesster - kleinster,
            "anzahl": anzahl,
            "rate_hz": rate,
        }

    def messrate(self, anzahl=200):
        """
        Ermittelt, wie viele Einzelmessungen pro Sekunde moeglich sind.

        Args:
            anzahl: Anzahl der Testmessungen

        Returns:
            float: Messrate in Hz
        """
        anzahl = max(1, int(anzahl))
        start = ticks_us()
        for _ in range(anzahl):
            self._roh()
        dauer_us = ticks_diff(ticks_us(), start)
        if dauer_us <= 0:
            return 0.0
        return anzahl * 1000000.0 / dauer_us

    def ist_stromfluss(self, schwelle_ma=200.0):
        """
        Prueft, ob nennenswert Strom fliesst.

        Args:
            schwelle_ma: Ansprechschwelle in mA

        Returns:
            bool: True wenn der Betrag ueber der Schwelle liegt
        """
        return abs(self.messen_ma()) > abs(float(schwelle_ma))

    def richtung(self, schwelle_ma=200.0):
        """
        Ermittelt die Stromrichtung.

        Args:
            schwelle_ma: Ansprechschwelle in mA

        Returns:
            int: 1 (vorwaerts), -1 (rueckwaerts) oder 0 (kein Stromfluss)
        """
        strom_ma = self.messen_ma()
        if abs(strom_ma) <= abs(float(schwelle_ma)):
            return 0
        return 1 if strom_ma > 0 else -1

    # ------------------------------------------------------------------
    # Kalibrierung
    # ------------------------------------------------------------------

    def nullpunkt_kalibrieren(self, n=200):
        """
        Kalibriert den Nullpunkt (Offset) bei stromlosem Leiter.

        Waehrend der Messung darf kein Strom durch den Sensor fliessen.
        Damit werden Toleranzen von Sensor, Versorgungsspannung und
        Spannungsteiler gemeinsam ausgeglichen.

        Args:
            n: Anzahl Einzelmessungen fuer den Mittelwert

        Returns:
            float: Neuer Nullpunkt in Volt
        """
        n = max(10, int(n))
        self._nullpunkt_v = self.lesen_spannung(n=n)
        self._aktualisieren()
        return self._nullpunkt_v

    def kalibrieren(self, referenz_strom_a, n=200):
        """
        Kalibriert die Empfindlichkeit mit einem bekannten Referenzstrom.

        Ablauf:
        1) Ohne Strom `nullpunkt_kalibrieren()` aufrufen
        2) Bekannten Strom einschalten (z. B. mit Multimeter gemessen)
        3) Diese Methode mit dem gemessenen Strom aufrufen

        Args:
            referenz_strom_a: Tatsaechlich fliessender Strom in A
            n: Anzahl Einzelmessungen fuer den Mittelwert

        Returns:
            float: Neue Empfindlichkeit in mV/A
        """
        referenz_strom_a = float(referenz_strom_a)
        if referenz_strom_a == 0:
            raise ValueError("referenz_strom_a darf nicht 0 sein")

        spannung = self.lesen_spannung(n=max(10, int(n)))
        delta_v = spannung - self._nullpunkt_v
        if self._invertiert:
            delta_v = -delta_v

        empf_mv_a = (delta_v * 1000.0) / referenz_strom_a
        if empf_mv_a == 0:
            raise ValueError("Keine Spannungsaenderung messbar - Aufbau pruefen")

        self._empf_mv_a = empf_mv_a
        self._aktualisieren()
        return self._empf_mv_a

    def kalibrieren_referenz_ma(self, referenz_strom_ma, n=200):
        """
        Kalibriert die Empfindlichkeit mit einem Referenzstrom in mA.

        Args:
            referenz_strom_ma: Tatsaechlich fliessender Strom in mA
            n: Anzahl Einzelmessungen

        Returns:
            float: Neue Empfindlichkeit in mV/A
        """
        return self.kalibrieren(float(referenz_strom_ma) / 1000.0, n=n)

    def set_nullpunkt_v(self, spannung):
        """Setzt den Nullpunkt (Ausgangsspannung bei 0 A) in Volt."""
        self._nullpunkt_v = float(spannung)
        self._aktualisieren()

    def get_nullpunkt_v(self):
        """Gibt den aktuellen Nullpunkt in Volt zurueck."""
        return self._nullpunkt_v

    def set_empfindlichkeit_mv_a(self, mv_pro_a):
        """Setzt die Empfindlichkeit in mV pro Ampere."""
        mv_pro_a = float(mv_pro_a)
        if mv_pro_a == 0:
            raise ValueError("Empfindlichkeit darf nicht 0 sein")
        self._empf_mv_a = mv_pro_a
        self._aktualisieren()

    def get_empfindlichkeit_mv_a(self):
        """Gibt die aktuelle Empfindlichkeit in mV pro Ampere zurueck."""
        return self._empf_mv_a

    # ------------------------------------------------------------------
    # Einstellungen
    # ------------------------------------------------------------------

    def set_variante(self, variante):
        """
        Waehlt ein Varianten-Preset und setzt Empfindlichkeit und Nullpunkt.

        Gueltige Namen: siehe ACS758.VARIANTEN
        (z. B. "50B", "50U", "100B", "100U", "150B", "150U", "200B", "200U")
        """
        name = str(variante).upper().replace("ACS758", "").strip()
        if name not in self.VARIANTEN:
            raise ValueError("Unbekannte Variante: {}".format(variante))

        mv_a, bidirektional, nennstrom = self.VARIANTEN[name]
        self._variante = name
        self._bidirektional = bidirektional
        self._nennstrom_a = nennstrom

        # Empfindlichkeit und Nullpunkt sind ratiometrisch zur Versorgung
        self._empf_mv_a = mv_a * (self._vcc / self.VCC_NENN)
        anteil = self.NULL_BIDIREKTIONAL if bidirektional else self.NULL_UNIDIREKTIONAL
        self._nullpunkt_v = self._vcc * anteil
        self._aktualisieren()

    def get_variante(self):
        """Gibt den Namen der eingestellten Variante zurueck."""
        return self._variante

    def set_vcc(self, vcc):
        """
        Setzt die Versorgungsspannung des Sensors in Volt.

        Empfindlichkeit und Nullpunkt werden aus dem Varianten-Preset
        neu berechnet. Eine vorherige Kalibrierung geht dabei verloren.
        """
        self._vcc = float(vcc)
        self.set_variante(self._variante)

    def get_vcc(self):
        """Gibt die eingestellte Versorgungsspannung zurueck."""
        return self._vcc

    def set_teiler(self, teiler):
        """
        Setzt den Teilerfaktor Vsensor/Vadc des Spannungsteilers.

        Beispiel: 10k/10k halbiert die Spannung -> teiler = 2.0
        """
        teiler = float(teiler)
        if teiler <= 0:
            raise ValueError("teiler muss groesser 0 sein")
        self._teiler = teiler
        self._aktualisieren()

    def get_teiler(self):
        """Gibt den eingestellten Teilerfaktor zurueck."""
        return self._teiler

    def set_messungen(self, n):
        """Setzt die Standard-Anzahl Einzelmessungen pro Messwert."""
        self._messungen = max(1, int(n))

    def get_messungen(self):
        """Gibt die Standard-Anzahl Einzelmessungen zurueck."""
        return self._messungen

    def set_glaettung(self, faktor):
        """
        Setzt die EMA-Glaettung.

        Args:
            faktor: 0.0 = aus, 0.8 = mittel, 0.95 = sehr traege (max. 0.99)
        """
        faktor = float(faktor)
        if faktor < 0.0 or faktor > 0.99:
            raise ValueError("glaettung muss zwischen 0.0 und 0.99 liegen")
        self._glaettung = faktor
        self._ema = None

    def get_glaettung(self):
        """Gibt den Glaettungsfaktor zurueck."""
        return self._glaettung

    def set_totzone_ma(self, totzone_ma):
        """Setzt die Totzone in mA (kleine Betraege werden zu 0 mA)."""
        self._totzone_ma = abs(float(totzone_ma))

    def get_totzone_ma(self):
        """Gibt die eingestellte Totzone in mA zurueck."""
        return self._totzone_ma

    def set_invertiert(self, invertiert=True):
        """Dreht das Vorzeichen der Messung (vertauschte Stromrichtung)."""
        self._invertiert = bool(invertiert)
        self._ema = None

    def ist_invertiert(self):
        """Gibt zurueck, ob das Vorzeichen gedreht wird."""
        return self._invertiert

    def set_daempfung(self, attenuation):
        """
        Setzt die ADC-Daempfung neu ("0db", "2.5db", "6db", "11db").

        Fuer den vollen Eingangsbereich bis ca. 3.1 V ist "11db" noetig.
        """
        self._daempfung = str(attenuation).lower()
        self._konfiguriere_adc()
        self._ema = None

    def zuruecksetzen(self):
        """Setzt Glaettungsspeicher und internen Filterzustand zurueck."""
        self._ema = None

    def messbereich_a(self):
        """
        Gibt den nominalen Messbereich der Variante zurueck.

        Returns:
            tuple: (min_a, max_a)
        """
        if self._bidirektional:
            return -float(self._nennstrom_a), float(self._nennstrom_a)
        return 0.0, float(self._nennstrom_a)

    def aufloesung_ma(self):
        """
        Schaetzt die kleinste unterscheidbare Stromaenderung in mA.

        Entspricht einem ADC-Schritt und ist damit die theoretische
        Aufloesung ohne Rauschen und ohne Mittelwertbildung.

        Returns:
            float: Aufloesung in mA pro ADC-Schritt
        """
        schritt_v = (self._vref / self._max_raw) * self._teiler
        return schritt_v * 1000000.0 / self._empf_mv_a

    def info(self):
        """
        Gibt die aktuellen Einstellungen als dict zurueck.

        Returns:
            dict mit Variante, Empfindlichkeit, Nullpunkt, Teiler, Filter
        """
        return {
            "variante": self._variante,
            "bidirektional": self._bidirektional,
            "nennstrom_a": self._nennstrom_a,
            "empfindlichkeit_mv_a": self._empf_mv_a,
            "nullpunkt_v": self._nullpunkt_v,
            "vcc": self._vcc,
            "teiler": self._teiler,
            "vref": self._vref,
            "adc_bits": self._adc_bits,
            "kalibrierter_adc": self._hat_uv,
            "messungen": self._messungen,
            "glaettung": self._glaettung,
            "totzone_ma": self._totzone_ma,
            "invertiert": self._invertiert,
        }

    def daten(self, n=None):
        """
        Liefert eine kompakte Gesamtausgabe einer Messung.

        Args:
            n: Anzahl Einzelmessungen (None -> Standardwert)

        Returns:
            dict mit Rohwert, Spannung, Strom in A und mA
        """
        if n is None:
            n = self._messungen
        n = max(1, int(n))

        wert = self._roh_mittel(n)
        if self._hat_uv:
            spannung = wert * 1e-6 * self._teiler
        else:
            spannung = wert * (self._vref / self._max_raw) * self._teiler

        strom_a = self._nachbearbeiten(self._roh_zu_strom_a(wert))

        return {
            "roh": wert,
            "spannung_v": spannung,
            "strom_a": strom_a,
            "strom_ma": strom_a * 1000.0,
        }
