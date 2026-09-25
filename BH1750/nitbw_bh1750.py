"""
NIT Bibliothek: BH1750 - Digitaler Lichtsensor (Beleuchtungsstaerke in Lux) ueber I2C
Fuer ESP32 mit MicroPython

Version:    1.1.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-09
Geaendert:  2026-09 - Transmission/Extinktion (Fotometer-Funktionen) integriert

Direkte Befehlsansteuerung des BH1750 (ROHM) ohne Fremdbibliotheken.
Unterstuetzt kontinuierliche und einmalige Messungen in hoher/niedriger
Aufloesung sowie eine einstellbare Messzeit (MTreg) zur Anpassung der
Empfindlichkeit an sehr helle oder sehr dunkle Umgebungen.

Zusaetzlich enthaelt die Klasse Fotometer-Funktionen: Nach einer
Referenzmessung (Leerwert/Blank, z. B. mit Wasser oder leerem
Strahlengang) koennen Transmission (%) und Extinktion/Absorbanz nach
dem Beer-Lambert-Gesetz berechnet werden. Diese Groessen sind
unabhaengig von LED-Alterung, Abstand und Umgebungslicht und eignen
sich besser als Feature fuer die ML-Algorithmen als der rohe Lux-Wert.
"""

from time import sleep_ms
import math


class BH1750:
    """
    Liest die Beleuchtungsstaerke (Lux) ueber den BH1750 aus und kann
    optional als Fotometer verwendet werden (Transmission/Extinktion
    relativ zu einer Referenzmessung).

    Unterstuetzte Hardware:
    - BH1750 / BH1750FVI Breakout-Board (z. B. GY-302)
    - I2C-Adresse 0x23 (ADDR=GND/offen) oder 0x5C (ADDR=VCC)

    Schnittstelle: I2C
    """

    # I2C-Standardadressen
    ADDR_LOW = 0x23   # ADDR-Pin auf GND oder offen
    ADDR_HIGH = 0x5C  # ADDR-Pin auf VCC

    # Befehle (Opcodes)
    CMD_POWER_DOWN = 0x00
    CMD_POWER_ON = 0x01
    CMD_RESET = 0x07

    # Messmodi (kontinuierlich)
    CONT_HIRES = 0x10    # 1.0 lx Aufloesung, ca. 120 ms
    CONT_HIRES2 = 0x11   # 0.5 lx Aufloesung, ca. 120 ms
    CONT_LORES = 0x13    # 4.0 lx Aufloesung, ca. 16 ms

    # Messmodi (einmalig, Sensor geht danach in Power-Down)
    ONCE_HIRES = 0x20
    ONCE_HIRES2 = 0x21
    ONCE_LORES = 0x23

    # Basis-Messzeiten (ms) bei MTreg = 69, inkl. Reserve
    _BASE_TIME_HI = 180
    _BASE_TIME_LO = 24

    # MTreg-Grenzen laut Datenblatt
    MTREG_MIN = 31
    MTREG_DEFAULT = 69
    MTREG_MAX = 254

    _HIRES_MODES = (CONT_HIRES, CONT_HIRES2, ONCE_HIRES, ONCE_HIRES2)
    _HIRES2_MODES = (CONT_HIRES2, ONCE_HIRES2)
    _ONCE_MODES = (ONCE_HIRES, ONCE_HIRES2, ONCE_LORES)
    _CONT_MODES = (CONT_HIRES, CONT_HIRES2, CONT_LORES)
    _ALL_MODES = _CONT_MODES + _ONCE_MODES

    def __init__(self, i2c, addr=ADDR_LOW, mode=CONT_HIRES, mtreg=MTREG_DEFAULT,
                 n_kalibrierung=10):
        """
        Initialisiert den BH1750.

        :param i2c: I2C Bus Objekt (machine.I2C)
        :param addr: I2C Adresse (0x23 oder 0x5C)
        :param mode: Startmodus (CONT_HIRES, CONT_HIRES2, CONT_LORES,
                     ONCE_HIRES, ONCE_HIRES2, ONCE_LORES)
        :param mtreg: Messzeitregister (31..254, Standard 69)
        :param n_kalibrierung: Standard-Anzahl Messungen fuer kalibrieren()
        """
        if mode not in self._ALL_MODES:
            raise ValueError("Ungueltiger mode-Wert")
        if not (self.MTREG_MIN <= mtreg <= self.MTREG_MAX):
            raise ValueError("mtreg muss 31..254 sein")

        self.i2c = i2c
        self.addr = addr
        self.mode = mode
        self.mtreg = mtreg

        # Fotometer-Referenzwert (Leerwert) - None solange nicht kalibriert
        self.n_kalibrierung = n_kalibrierung
        self.i0 = None

        self.power_on()
        if mtreg != self.MTREG_DEFAULT:
            self.set_mtreg(mtreg)
        self._set_mode(mode)

    def _write_cmd(self, cmd):
        """Schreibt einen einzelnen Befehlsbyte an den Sensor."""
        self.i2c.writeto(self.addr, bytes([cmd]))

    def _set_mode(self, mode):
        """Sendet den Messmodus-Befehl an den Sensor."""
        self._write_cmd(mode)
        self.mode = mode
        # Nach dem Moduswechsel kurz auf die erste Wandlung warten.
        sleep_ms(self._measure_time_ms())

    def power_on(self):
        """Schaltet den Sensor aktiv (Power-On)."""
        self._write_cmd(self.CMD_POWER_ON)

    def power_down(self):
        """Versetzt den Sensor in den Stromsparmodus (Power-Down)."""
        self._write_cmd(self.CMD_POWER_DOWN)

    def reset(self):
        """Setzt das Datenregister zurueck (nur im Power-On-Zustand wirksam)."""
        self.power_on()
        self._write_cmd(self.CMD_RESET)

    def set_mode(self, mode):
        """
        Setzt den Messmodus fuer folgende Messungen.

        :param mode: CONT_HIRES, CONT_HIRES2, CONT_LORES,
                     ONCE_HIRES, ONCE_HIRES2 oder ONCE_LORES
        """
        if mode not in self._ALL_MODES:
            raise ValueError("Ungueltiger mode-Wert")
        self.power_on()
        self._set_mode(mode)

    def set_mtreg(self, mtreg):
        """
        Setzt das Messzeitregister (MTreg) und passt so die Empfindlichkeit an.

        Groesserer Wert  -> laengere Messzeit, hoehere Empfindlichkeit
                            (fuer sehr dunkle Umgebungen).
        Kleinerer Wert   -> kuerzere Messzeit, hoeherer Messbereich
                            (fuer sehr helle Umgebungen, verhindert Saettigung).

        Hinweis: Nach einer Aenderung des MTreg ist ein bereits
        gespeicherter Referenzwert (i0) nicht mehr gueltig, da sich die
        Skalierung der Rohwerte aendert. Ggf. erneut kalibrieren().

        :param mtreg: Wert von 31 bis 254 (Standard 69)
        """
        if not (self.MTREG_MIN <= mtreg <= self.MTREG_MAX):
            raise ValueError("mtreg muss 31..254 sein")

        # High-Bits: 0b01000_xxx  |  Low-Bits: 0b011_xxxxx
        self._write_cmd(0x40 | (mtreg >> 5))
        self._write_cmd(0x60 | (mtreg & 0x1F))
        self.mtreg = mtreg

        # Nach MTreg-Aenderung muss der Modus erneut gesetzt werden.
        self._set_mode(self.mode)

    def set_sensitivity(self, faktor):
        """
        Bequeme Empfindlichkeitsanpassung ueber einen Faktor.

        faktor = 1.0 entspricht dem Standard (MTreg 69). Werte > 1.0 erhoehen
        die Empfindlichkeit (dunkle Raeume), Werte < 1.0 vergroessern den
        Messbereich (helle Umgebung). Der resultierende MTreg wird auf den
        gueltigen Bereich 31..254 begrenzt.

        :param faktor: Empfindlichkeitsfaktor, z. B. 0.5 bis 3.68
        """
        wert = int(round(self.MTREG_DEFAULT * faktor))
        wert = max(self.MTREG_MIN, min(self.MTREG_MAX, wert))
        self.set_mtreg(wert)

    def _measure_time_ms(self):
        """Berechnet eine passende Wartezeit fuer den aktuellen Modus/MTreg."""
        basis = self._BASE_TIME_HI if self.mode in self._HIRES_MODES else self._BASE_TIME_LO
        skaliert = basis * self.mtreg / self.MTREG_DEFAULT
        return max(1, int(skaliert) + 1)

    def _read_raw(self):
        """Liest den 16-bit Rohwert (Big Endian) aus dem Datenregister."""
        data = self.i2c.readfrom(self.addr, 2)
        return (data[0] << 8) | data[1]

    def read_raw(self):
        """
        Liest den rohen 16-bit Messwert.

        Bei Einmal-Modi wird der Modus vor jeder Messung neu gestartet und
        anschliessend die noetige Wandlungszeit abgewartet.

        :return: Rohwert 0..65535
        """
        if self.mode in self._ONCE_MODES:
            self._write_cmd(self.mode)
            sleep_ms(self._measure_time_ms())
        return self._read_raw()

    def _raw_to_lux(self, raw):
        """Rechnet einen Rohwert unter Beruecksichtigung von MTreg/Modus in Lux um."""
        lux = raw / 1.2
        lux *= self.MTREG_DEFAULT / self.mtreg
        if self.mode in self._HIRES2_MODES:
            lux /= 2.0
        return lux

    def read_lux(self):
        """
        Liest die Beleuchtungsstaerke in Lux.

        :return: Beleuchtungsstaerke in Lux (float)
        """
        return self._raw_to_lux(self.read_raw())

    def read_averaged(self, n=5, pause_ms=10):
        """
        Liest mehrere Messungen und gibt den Mittelwert in Lux zurueck.

        Nuetzlich zur Rauschunterdbrueckung bei flackerndem Licht.

        :param n: Anzahl der Messungen (>= 1)
        :param pause_ms: Pause zwischen den Messungen in Millisekunden
        :return: Gemittelte Beleuchtungsstaerke in Lux (float)
        """
        if n < 1:
            raise ValueError("n muss >= 1 sein")
        summe = 0.0
        for i in range(n):
            summe += self.read_lux()
            if i < n - 1 and pause_ms > 0:
                sleep_ms(pause_ms)
        return summe / n

    def is_dark(self, schwelle=10.0):
        """
        Prueft, ob es dunkler als eine Schwelle ist.

        :param schwelle: Grenzwert in Lux (Standard 10 lx)
        :return: True, wenn die aktuelle Beleuchtungsstaerke < schwelle
        """
        return self.read_lux() < schwelle

    # ------------------------------------------------------------------
    # Fotometer-Funktionen: Transmission & Extinktion relativ zu i0
    # ------------------------------------------------------------------

    def kalibrieren(self, n=None):
        """
        Nimmt die aktuelle Beleuchtungsstaerke als Referenzwert (Leerwert) auf.

        Muss einmal mit Referenzfluessigkeit (z. B. Wasser) oder leerem
        Strahlengang aufgerufen werden, bevor transmission()/extinktion()
        sinnvolle Werte liefern. Nach einer Aenderung von Modus oder
        MTreg (set_mode/set_mtreg/set_sensitivity) muss erneut kalibriert
        werden, da sich sonst die Skalierung der Rohwerte veraendert.

        :param n: Anzahl Messungen zum Mitteln (Standard: n_kalibrierung)
        :return: gemessener Referenzwert I0 (in "Lux", Rohgroesse des Sensors)
        """
        anzahl = n if n is not None else self.n_kalibrierung
        self.i0 = self.read_averaged(n=anzahl)
        if self.i0 <= 0:
            self.i0 = None
            raise ValueError(
                "Referenzwert ist 0 oder negativ - Lichtquelle/Sensor pruefen"
            )
        return self.i0

    def ist_kalibriert(self):
        """Gibt True zurueck, wenn bereits eine Referenzmessung vorliegt."""
        return self.i0 is not None

    def _pruefe_kalibrierung(self):
        if self.i0 is None:
            raise RuntimeError(
                "Noch nicht kalibriert - zuerst kalibrieren() mit Referenz aufrufen"
            )

    def transmission(self, n=5):
        """
        Misst die Transmission der aktuell eingesetzten Probe relativ
        zum Referenzwert (kalibrieren() muss vorher aufgerufen worden sein).

        :param n: Anzahl Einzelmessungen zum Mitteln
        :return: Transmission T in Prozent (0..100+, >100 moeglich bei Rauschen)
        """
        self._pruefe_kalibrierung()
        i_probe = self.read_averaged(n=n)
        return (i_probe / self.i0) * 100.0

    def extinktion(self, n=5):
        """
        Misst die Extinktion (Absorbanz) der aktuell eingesetzten Probe
        nach dem Beer-Lambert-Gesetz: E = -log10(T).

        Ist linear zur Konzentration des absorbierenden Stoffs und
        eignet sich daher fuer Kalibriergeraden und als ML-Feature.

        :param n: Anzahl Einzelmessungen zum Mitteln
        :return: Extinktion E (dimensionslos, >= 0 im Normalfall)
        """
        t_prozent = self.transmission(n=n)
        t = t_prozent / 100.0
        if t <= 0:
            # voellig undurchlaessige Probe -> Extinktion waere unendlich
            return float("inf")
        return -math.log10(t)

    def messung(self, n=5):
        """
        Bequemer Sammelaufruf: liefert Rohwert, Transmission und
        Extinktion in einem Durchgang (nur eine Messreihe noetig).

        :param n: Anzahl Einzelmessungen zum Mitteln
        :return: dict mit 'lux', 'transmission' (%), 'extinktion'
        """
        self._pruefe_kalibrierung()
        i_probe = self.read_averaged(n=n)
        t_prozent = (i_probe / self.i0) * 100.0
        t = t_prozent / 100.0
        e = float("inf") if t <= 0 else -math.log10(t)
        return {
            "lux": i_probe,
            "transmission": t_prozent,
            "extinktion": e,
        }
