"""
NIT Bibliothek: HX711AD - Waegedrucksensor fuer Waegezellen
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-07

Direkte Bit-Bang-Ansteuerung des HX711AD ueber DT und SCK.
Unterstuetzt Rohwertmessung, Tara, Kalibrierung und Gewichtsausgabe in frei waehlbaren Einheiten.
"""

from machine import Pin, disable_irq, enable_irq
from time import sleep_ms, sleep_us, ticks_ms, ticks_diff


class HX711AD:
    """
    Liest Waegezellenwerte ueber den HX711AD aus.

    Unterstuetzte Hardware:
    - HX711 / HX711AD Verstaerker-Module
    - Waegezellen (z. B. 1 kg, 5 kg, 20 kg) mit Wheatstone-Bruecke

    Schnittstelle: 2 GPIO-Pins (DT + SCK)
    """

    KANAL_A = "A"
    KANAL_B = "B"

    # Pulse nach 24 Datenbits zur Kanal/Gain-Auswahl der naechsten Messung
    # 1 Puls: Kanal A Gain 128
    # 2 Pulse: Kanal B Gain 32
    # 3 Pulse: Kanal A Gain 64
    _GAIN_PULSE_MAP = {
        (KANAL_A, 128): 1,
        (KANAL_B, 32): 2,
        (KANAL_A, 64): 3,
    }

    def __init__(self, dt_pin, sck_pin, kanal=KANAL_A, gain=128, timeout_ms=1000):
        """
        Initialisiert den HX711AD.

        :param dt_pin: GPIO fuer DT (DOUT)
        :param sck_pin: GPIO fuer SCK (PD_SCK)
        :param kanal: Startkanal ('A' oder 'B')
        :param gain: Verstaerkung (A: 128/64, B: 32)
        :param timeout_ms: Timeout fuer warten_bereit in Millisekunden
        """
        self._dt = Pin(dt_pin, Pin.IN)
        self._sck = Pin(sck_pin, Pin.OUT)
        self._sck.value(0)

        self._offset = 0
        self._scale = 1.0
        self._timeout_ms = timeout_ms

        self._kanal = self.KANAL_A
        self._gain = 128
        self._gain_pulses = 1
        self.set_kanal_gain(kanal=kanal, gain=gain)

        # Erste gueltige Konfiguration in den HX711 takten
        self.messen_roh()

    def ist_bereit(self):
        """Prueft, ob ein neuer Messwert bereitsteht (DT = LOW)."""
        return self._dt.value() == 0

    def warten_bereit(self, timeout_ms=None, poll_ms=1):
        """
        Wartet, bis der Sensor messbereit ist.

        :param timeout_ms: Timeout in ms (None -> Standard aus Konstruktor)
        :param poll_ms: Warteintervall zwischen Polls in ms
        :return: True wenn bereit, sonst False bei Timeout
        """
        if timeout_ms is None:
            timeout_ms = self._timeout_ms

        start = ticks_ms()
        while not self.ist_bereit():
            if ticks_diff(ticks_ms(), start) >= timeout_ms:
                return False
            sleep_ms(poll_ms)
        return True

    def set_timeout(self, timeout_ms):
        """Setzt den Standard-Timeout fuer warten_bereit()."""
        self._timeout_ms = int(timeout_ms)

    def set_kanal_gain(self, kanal=KANAL_A, gain=128):
        """
        Setzt Kanal und Gain fuer folgende Messungen.

        Gueltige Kombinationen:
        - Kanal A, Gain 128
        - Kanal A, Gain 64
        - Kanal B, Gain 32
        """
        kanal = str(kanal).upper()
        key = (kanal, int(gain))
        if key not in self._GAIN_PULSE_MAP:
            raise ValueError("Ungueltige Kombination aus kanal/gain")

        self._kanal = kanal
        self._gain = int(gain)
        self._gain_pulses = self._GAIN_PULSE_MAP[key]

    def get_kanal_gain(self):
        """Gibt aktuelles (kanal, gain)-Tupel zurueck."""
        return self._kanal, self._gain

    def _clock_pulse(self):
        """Erzeugt einen SCK-Taktimpuls."""
        self._sck.value(1)
        sleep_us(1)
        self._sck.value(0)
        sleep_us(1)

    def messen_roh(self):
        """
        Liest einen 24-bit Rohwert (signed) vom HX711.

        :return: Messwert als signed int
        :raises RuntimeError: Bei Timeout
        """
        if not self.warten_bereit():
            raise RuntimeError("HX711 Timeout: kein Messwert bereit")

        state = disable_irq()
        try:
            value = 0
            for _ in range(24):
                self._sck.value(1)
                value = (value << 1) | self._dt.value()
                self._sck.value(0)

            for _ in range(self._gain_pulses):
                self._clock_pulse()
        finally:
            enable_irq(state)

        if value & 0x800000:
            value -= 1 << 24
        return value

    def messen_mittelwert(self, n=10, delay_ms=5):
        """
        Liest n Rohwerte und bildet den Mittelwert.

        :param n: Anzahl Messungen
        :param delay_ms: Pause zwischen Messungen
        :return: Mittelwert als int
        """
        if n <= 0:
            raise ValueError("n muss > 0 sein")

        total = 0
        for i in range(n):
            total += self.messen_roh()
            if i < n - 1:
                sleep_ms(delay_ms)
        return total // n

    def messen_median(self, n=7, delay_ms=5):
        """
        Liest n Rohwerte und gibt den Median zurueck.

        :param n: Anzahl Messungen
        :param delay_ms: Pause zwischen Messungen
        :return: Median als int
        """
        if n <= 0:
            raise ValueError("n muss > 0 sein")

        werte = []
        for i in range(n):
            werte.append(self.messen_roh())
            if i < n - 1:
                sleep_ms(delay_ms)
        werte.sort()

        mitte = len(werte) // 2
        if len(werte) % 2 == 0:
            return (werte[mitte - 1] + werte[mitte]) // 2
        return werte[mitte]

    def tara(self, n=20, delay_ms=5, median=False):
        """
        Fuehrt eine Tara-Messung durch und setzt den Offset.

        :param n: Anzahl Messungen fuer Tara
        :param delay_ms: Pause zwischen Messungen
        :param median: True fuer Median statt Mittelwert
        :return: Gesetzter Offset
        """
        if median:
            self._offset = self.messen_median(n=n, delay_ms=delay_ms)
        else:
            self._offset = self.messen_mittelwert(n=n, delay_ms=delay_ms)
        return self._offset

    def set_offset(self, offset):
        """Setzt den Rohdaten-Offset manuell."""
        self._offset = int(offset)

    def get_offset(self):
        """Gibt den aktuellen Rohdaten-Offset zurueck."""
        return self._offset

    def set_skala(self, scale):
        """
        Setzt den Kalibrierfaktor (Rohwert pro Einheit).

        Einheit ist frei waehlbar (z. B. g, kg, N), sofern konsistent genutzt.
        Der konkrete Wert ist immer systemabhaengig und haengt von Waegezelle,
        Mechanik, Hebelverhaeltnis, Montage und Verstärkung ab.
        """
        scale = float(scale)
        if scale == 0:
            raise ValueError("scale darf nicht 0 sein")
        self._scale = scale

    def get_skala(self):
        """Gibt den aktuellen Kalibrierfaktor zurueck."""
        return self._scale

    def messen_wert(self, n=5, delay_ms=5, median=False):
        """
        Liest den offset-korrigierten Rohwert.

        :return: Rohwert nach Tara-Korrektur
        """
        if median:
            raw = self.messen_median(n=n, delay_ms=delay_ms)
        else:
            raw = self.messen_mittelwert(n=n, delay_ms=delay_ms)
        return raw - self._offset

    def messen_gewicht(self, n=5, delay_ms=5, median=False):
        """
        Liest das Gewicht in kalibrierter Einheit.

        :return: Gewicht (float)
        """
        return self.messen_wert(n=n, delay_ms=delay_ms, median=median) / self._scale

    def kalibrieren(self, referenz_gewicht, n=20, delay_ms=5, median=True):
        """
        Berechnet den Kalibrierfaktor mit bekanntem Referenzgewicht.

        Ablauf:
        1) Waage tarieren (ohne Last)
        2) Referenzgewicht auflegen
        3) Methode aufrufen

        :param referenz_gewicht: Bekanntes Gewicht in Ziel-Einheit (z. B. Gramm)
        :param n: Anzahl Messungen fuer Kalibrierung
        :param delay_ms: Pause zwischen Messungen
        :param median: True fuer robustere Median-Auswertung
        :return: Neuer Kalibrierfaktor
        """
        referenz_gewicht = float(referenz_gewicht)
        if referenz_gewicht == 0:
            raise ValueError("referenz_gewicht darf nicht 0 sein")

        netto = self.messen_wert(n=n, delay_ms=delay_ms, median=median)
        self._scale = netto / referenz_gewicht
        return self._scale

    def power_down(self):
        """Versetzt den HX711 in den Stromsparmodus."""
        self._sck.value(0)
        self._sck.value(1)
        sleep_us(70)

    def power_up(self):
        """Weckt den HX711 aus dem Stromsparmodus auf."""
        self._sck.value(0)
