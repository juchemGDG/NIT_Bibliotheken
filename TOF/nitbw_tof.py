"""
NIT Bibliothek: TOF - Entfernungsmessung mit VL53L0X (Time-of-Flight Laser)
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Volker Rust / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Misst Entfernungen per Laser-Laufzeit (Time-of-Flight) ueber I2C.
Bietet vier Messmodi, Filterfunktionen und Mehrfachsensor-Unterstuetzung.
"""

from machine import Pin, I2C
import time


class TOF:
    """
    Misst Entfernungen mit dem VL53L0X Time-of-Flight Lasersensor.

    Unterstuetzte Hardware:
    - VL53L0X Breakout-Module (GY-530 und kompatible)
    - Mehrere Sensoren am selben I2C-Bus (ueber XSHUT-Pins)

    Schnittstelle: I2C
    """

    # Messmodi
    SCHNELL = 1
    STANDARD = 2
    GENAU = 3
    LANGSTRECKE = 4

    _DEFAULT_ADDR = 0x29

    # Register
    _SYSRANGE_START = 0x00
    _SYSTEM_SEQUENCE_CONFIG = 0x01
    _SYSTEM_INTERRUPT_CONFIG_GPIO = 0x0A
    _SYSTEM_INTERRUPT_CLEAR = 0x0B
    _RESULT_INTERRUPT_STATUS = 0x13
    _RESULT_RANGE_STATUS = 0x14
    _I2C_SLAVE_DEVICE_ADDRESS = 0x8A
    _MSRC_CONFIG_CONTROL = 0x60
    _SIGNAL_RATE_LIMIT = 0x44
    _PRE_RANGE_CONFIG_VCSEL_PERIOD = 0x50
    _PRE_RANGE_CONFIG_TIMEOUT_MACROP_HI = 0x51
    _FINAL_RANGE_CONFIG_VCSEL_PERIOD = 0x70
    _FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI = 0x71
    _MSRC_CONFIG_TIMEOUT_MACROP = 0x46
    _GPIO_HV_MUX_ACTIVE_HIGH = 0x84
    _IDENTIFICATION_MODEL_ID = 0xC0
    _ALGO_PHASECAL_CONFIG_TIMEOUT = 0x30

    # Modus-Namen
    _MODI_NAMEN = {
        SCHNELL: 'schnell',
        STANDARD: 'standard',
        GENAU: 'genau',
        LANGSTRECKE: 'langstrecke'
    }

    # Timing-Budget Overhead-Konstanten (Mikrosekunden)
    _START_OVERHEAD = 1910
    _END_OVERHEAD = 960
    _MSRC_OVERHEAD = 660
    _TCC_OVERHEAD = 590
    _DSS_OVERHEAD = 690
    _PRE_RANGE_OVERHEAD = 660
    _FINAL_RANGE_OVERHEAD = 550

    # Phasecal-Limits abhaengig von Pre-Range VCSEL-Periode
    _PHASECAL_LIMITS = {12: 0x18, 14: 0x30, 16: 0x40, 18: 0x50}

    # Status-Texte
    _STATUS_TEXTE = {
        0: 'gueltig',
        1: 'Sigma zu hoch',
        2: 'Signal zu schwach',
        3: 'minimaler Abstand unterschritten',
        4: 'Phase ausserhalb Limit',
        5: 'Hardware-Fehler',
        7: 'Wrap-Around',
        11: 'gueltig',
    }

    def __init__(self, i2c, addr=0x29, xshut=None):
        """
        Initialisiert den VL53L0X Sensor.

        Args:
            i2c: I2C-Bus-Objekt (z. B. I2C(0, scl=Pin(22), sda=Pin(21)))
            addr: I2C-Adresse (Standard: 0x29). Bei Mehrfachsensoren
                  jedem Sensor eine eigene Adresse geben.
            xshut: GPIO-Pin-Nummer fuer XSHUT (optional, fuer Mehrfachsensoren).
                   Wird HIGH gesetzt, um den Sensor aufzuwecken.
        """
        self._i2c = i2c
        self._addr = self._DEFAULT_ADDR
        self._modus = self.STANDARD
        self._timing_budget_us = 33000
        self._letzter_status = 0

        # XSHUT-Pin: Sensor aufwecken
        if xshut is not None:
            self._xshut = Pin(xshut, Pin.OUT)
            self._xshut.value(1)
            time.sleep_ms(50)
        else:
            self._xshut = None

        # Warten bis Sensor bereit ist (Bootzeit ~1.2 ms laut Datenblatt,
        # in der Praxis bis zu 50 ms bei manchen Modulen)
        time.sleep_ms(50)

        # Pruefen ob Sensor am Bus erreichbar ist
        if self._addr not in self._i2c.scan():
            raise OSError(
                "VL53L0X nicht gefunden an Adresse 0x{:02X}. "
                "Verkabelung pruefen (SDA/SCL vertauscht?)".format(self._addr))

        # Adresse aendern falls gewuenscht (Sensor startet immer bei 0x29)
        if addr != self._DEFAULT_ADDR:
            self._reg_schreiben(self._I2C_SLAVE_DEVICE_ADDRESS, addr & 0x7F)
            self._addr = addr
            time.sleep_ms(10)

        # Sensor initialisieren
        self._init_sensor()
        self.set_modus(self.STANDARD)

    # ================================================================
    # I2C Hilfsfunktionen
    # ================================================================

    def _reg_schreiben(self, reg, wert):
        """Schreibt ein Byte in ein Register."""
        self._i2c.writeto_mem(self._addr, reg, bytes([wert]))

    def _reg_schreiben_16(self, reg, wert):
        """Schreibt ein 16-Bit-Wort (Big Endian)."""
        self._i2c.writeto_mem(self._addr, reg, bytes([wert >> 8, wert & 0xFF]))

    def _reg_lesen(self, reg):
        """Liest ein Byte aus einem Register."""
        return self._i2c.readfrom_mem(self._addr, reg, 1)[0]

    def _reg_lesen_16(self, reg):
        """Liest ein 16-Bit-Wort (Big Endian)."""
        daten = self._i2c.readfrom_mem(self._addr, reg, 2)
        return (daten[0] << 8) | daten[1]

    # ================================================================
    # Sensor-Initialisierung
    # ================================================================

    def _init_sensor(self):
        """Fuehrt die komplette Initialisierungssequenz durch."""
        # Sensor-ID pruefen
        if self._reg_lesen(self._IDENTIFICATION_MODEL_ID) != 0xEE:
            raise OSError("VL53L0X nicht gefunden an Adresse 0x{:02X}".format(
                self._addr))

        # I2C Standard-Modus
        self._reg_schreiben(0x88, 0x00)

        # Stopp-Variable lesen (wird fuer Einzelmessungen benoetigt)
        self._reg_schreiben(0x80, 0x01)
        self._reg_schreiben(0xFF, 0x01)
        self._reg_schreiben(0x00, 0x00)
        self._stop_variable = self._reg_lesen(0x91)
        self._reg_schreiben(0x00, 0x01)
        self._reg_schreiben(0xFF, 0x00)
        self._reg_schreiben(0x80, 0x00)

        # MSRC-Konfiguration: Minimum-Count-Rate-Check aktivieren
        config = self._reg_lesen(self._MSRC_CONFIG_CONTROL)
        self._reg_schreiben(self._MSRC_CONFIG_CONTROL, config | 0x12)

        # Standard Signal Rate Limit: 0.25 MCPS
        self._set_signal_rate_limit(0.25)

        # Sequenz-Konfiguration: alle Schritte aktiv
        self._reg_schreiben(self._SYSTEM_SEQUENCE_CONFIG, 0xFF)

        # SPAD-Kalibrierung
        self._spad_init()

        # Tuning-Einstellungen laden
        self._tuning_laden()

        # GPIO-Interrupt konfigurieren
        self._reg_schreiben(self._SYSTEM_INTERRUPT_CONFIG_GPIO, 0x04)
        gpio_hv = self._reg_lesen(self._GPIO_HV_MUX_ACTIVE_HIGH)
        self._reg_schreiben(self._GPIO_HV_MUX_ACTIVE_HIGH, gpio_hv & ~0x10)
        self._reg_schreiben(self._SYSTEM_INTERRUPT_CLEAR, 0x01)

        # Referenz-Kalibrierung (VHV + Phase)
        self._ref_kalibrierung()

    def _spad_init(self):
        """SPAD-Referenz-Kalibrierung (Single Photon Avalanche Diodes)."""
        self._reg_schreiben(0x80, 0x01)
        self._reg_schreiben(0xFF, 0x01)
        self._reg_schreiben(0x00, 0x00)
        self._reg_schreiben(0xFF, 0x06)
        val = self._reg_lesen(0x83)
        self._reg_schreiben(0x83, val | 0x04)
        self._reg_schreiben(0xFF, 0x07)
        self._reg_schreiben(0x81, 0x01)
        self._reg_schreiben(0x80, 0x01)
        self._reg_schreiben(0x94, 0x6B)
        self._reg_schreiben(0x83, 0x00)

        timeout = 100
        while self._reg_lesen(0x83) == 0x00:
            timeout -= 1
            if timeout == 0:
                break
            time.sleep_ms(1)

        self._reg_schreiben(0x83, 0x01)
        val = self._reg_lesen(0x92)
        spad_count = val & 0x7F
        spad_is_aperture = (val >> 7) & 0x01

        self._reg_schreiben(0x81, 0x00)
        self._reg_schreiben(0xFF, 0x06)
        val = self._reg_lesen(0x83)
        self._reg_schreiben(0x83, val & ~0x04)
        self._reg_schreiben(0xFF, 0x01)
        self._reg_schreiben(0x00, 0x01)
        self._reg_schreiben(0xFF, 0x00)
        self._reg_schreiben(0x80, 0x00)

        # SPAD-Map lesen und konfigurieren
        ref_spad_map = bytearray(self._i2c.readfrom_mem(self._addr, 0xB0, 6))
        self._reg_schreiben(0xFF, 0x01)
        self._reg_schreiben(self._SYSRANGE_START, 0x00)
        self._reg_schreiben(0xFF, 0x00)
        self._reg_schreiben(0x09, 0x00)
        self._reg_schreiben(0x10, 0x00)

        first_spad = 12 if spad_is_aperture else 0
        spads_enabled = 0
        for i in range(48):
            if i < first_spad or spads_enabled >= spad_count:
                ref_spad_map[i // 8] &= ~(1 << (i % 8))
            elif ref_spad_map[i // 8] & (1 << (i % 8)):
                spads_enabled += 1

        self._i2c.writeto_mem(self._addr, 0xB0, ref_spad_map)

    def _tuning_laden(self):
        """Laedt die Standard-Tuning-Einstellungen (Register-Sequenz vom Hersteller)."""
        tuning = [
            (0xFF, 0x01), (0x00, 0x00), (0xFF, 0x00), (0x09, 0x00),
            (0x10, 0x00), (0x11, 0x00), (0x24, 0x01), (0x25, 0xFF),
            (0x75, 0x00), (0xFF, 0x01), (0x4E, 0x2C), (0x48, 0x00),
            (0x30, 0x20), (0xFF, 0x00), (0x30, 0x09), (0x54, 0x00),
            (0x31, 0x04), (0x32, 0x03), (0x40, 0x83), (0x46, 0x25),
            (0x60, 0x00), (0x27, 0x00), (0x50, 0x06), (0x51, 0x00),
            (0x52, 0x96), (0x56, 0x08), (0x57, 0x30), (0x61, 0x00),
            (0x62, 0x00), (0x64, 0x00), (0x65, 0x00), (0x66, 0xA0),
            (0xFF, 0x01), (0x22, 0x32), (0x47, 0x14), (0x49, 0xFF),
            (0x4A, 0x00), (0xFF, 0x00), (0x7A, 0x0A), (0x7B, 0x00),
            (0x78, 0x21), (0xFF, 0x01), (0x23, 0x34), (0x42, 0x00),
            (0x44, 0xFF), (0x45, 0x26), (0x46, 0x05), (0x40, 0x40),
            (0x0E, 0x06), (0x20, 0x1A), (0x43, 0x40), (0xFF, 0x00),
            (0x34, 0x03), (0x35, 0x44), (0xFF, 0x01), (0x31, 0x04),
            (0x4B, 0x09), (0x4C, 0x05), (0x4D, 0x04), (0xFF, 0x00),
            (0x44, 0x00), (0x45, 0x20), (0x47, 0x08), (0x48, 0x28),
            (0x67, 0x00), (0x70, 0x04), (0x71, 0x01), (0x72, 0xFE),
            (0x76, 0x00), (0x77, 0x00), (0xFF, 0x01), (0x0D, 0x01),
            (0xFF, 0x00), (0x80, 0x01), (0x01, 0xF8), (0xFF, 0x01),
            (0x8E, 0x01), (0x00, 0x01), (0xFF, 0x00), (0x80, 0x00),
        ]
        for reg, val in tuning:
            self._reg_schreiben(reg, val)

    def _ref_kalibrierung(self):
        """Referenz-Kalibrierung: VHV und Phase."""
        # VHV-Kalibrierung
        self._reg_schreiben(self._SYSTEM_SEQUENCE_CONFIG, 0x01)
        self._einzelmessung()

        # Phase-Kalibrierung
        self._reg_schreiben(self._SYSTEM_SEQUENCE_CONFIG, 0x02)
        self._einzelmessung()

        # Alle Sequenz-Schritte wieder aktivieren
        self._reg_schreiben(self._SYSTEM_SEQUENCE_CONFIG, 0xFF)

    def _einzelmessung(self):
        """Fuehrt eine einzelne Messung durch (fuer Kalibrierung)."""
        self._reg_schreiben(self._SYSRANGE_START, 0x01)

        timeout = 500
        while self._reg_lesen(self._SYSRANGE_START) & 0x01:
            timeout -= 1
            if timeout == 0:
                return
            time.sleep_ms(1)

        timeout = 500
        while not (self._reg_lesen(self._RESULT_INTERRUPT_STATUS) & 0x07):
            timeout -= 1
            if timeout == 0:
                return
            time.sleep_ms(1)

        self._reg_schreiben(self._SYSTEM_INTERRUPT_CLEAR, 0x01)
        self._reg_schreiben(self._SYSRANGE_START, 0x00)

    # ================================================================
    # Timeout-Berechnungen
    # ================================================================

    @staticmethod
    def _calc_macro_period_ns(vcsel_period_pclks):
        """Berechnet die Makro-Periodendauer in Nanosekunden."""
        return ((2304 * vcsel_period_pclks * 1655) + 500) // 1000

    @staticmethod
    def _decode_timeout(reg_val):
        """Dekodiert einen 16-Bit Timeout-Registerwert in MCLKS."""
        ls_byte = reg_val & 0xFF
        ms_byte = (reg_val >> 8) & 0xFF
        return (ls_byte << ms_byte) + 1

    @staticmethod
    def _encode_timeout(timeout_mclks):
        """Kodiert MCLKS in das 16-Bit Registerformat."""
        if timeout_mclks <= 0:
            return 0
        ls_byte = timeout_mclks - 1
        ms_byte = 0
        while ls_byte > 0xFF:
            ls_byte >>= 1
            ms_byte += 1
        return (ms_byte << 8) | (ls_byte & 0xFF)

    def _timeout_mclks_to_us(self, timeout_mclks, vcsel_period_pclks):
        """Konvertiert MCLKS in Mikrosekunden."""
        macro_ns = self._calc_macro_period_ns(vcsel_period_pclks)
        return ((timeout_mclks * macro_ns) + 500) // 1000

    def _timeout_us_to_mclks(self, timeout_us, vcsel_period_pclks):
        """Konvertiert Mikrosekunden in MCLKS."""
        macro_ns = self._calc_macro_period_ns(vcsel_period_pclks)
        return ((timeout_us * 1000) + (macro_ns // 2)) // macro_ns

    # ================================================================
    # Signal-Rate und VCSEL Konfiguration
    # ================================================================

    def _set_signal_rate_limit(self, mcps):
        """Setzt das Signal Rate Limit in MCPS (Mega Counts Per Second)."""
        wert = int(mcps * (1 << 7))  # Fixed-point 9.7 Format
        self._reg_schreiben_16(self._SIGNAL_RATE_LIMIT, wert)

    def _get_vcsel_period(self, typ):
        """Liest die VCSEL-Pulsperiode in PCLKS."""
        if typ == 'pre':
            return (self._reg_lesen(self._PRE_RANGE_CONFIG_VCSEL_PERIOD) + 1) << 1
        else:
            return (self._reg_lesen(self._FINAL_RANGE_CONFIG_VCSEL_PERIOD) + 1) << 1

    def _get_sequence_step_enables(self):
        """Liest welche Sequenz-Schritte aktiviert sind."""
        config = self._reg_lesen(self._SYSTEM_SEQUENCE_CONFIG)
        return {
            'tcc': bool(config & 0x10),
            'dss': bool(config & 0x08),
            'msrc': bool(config & 0x04),
            'pre_range': bool(config & 0x40),
            'final_range': bool(config & 0x80),
        }

    def _get_sequence_step_timeouts(self):
        """Liest die Timeout-Werte aller Sequenz-Schritte."""
        pre_vcsel = self._get_vcsel_period('pre')
        final_vcsel = self._get_vcsel_period('final')

        msrc_mclks = self._reg_lesen(self._MSRC_CONFIG_TIMEOUT_MACROP) + 1
        msrc_us = self._timeout_mclks_to_us(msrc_mclks, pre_vcsel)

        pre_mclks = self._decode_timeout(
            self._reg_lesen_16(self._PRE_RANGE_CONFIG_TIMEOUT_MACROP_HI))
        pre_us = self._timeout_mclks_to_us(pre_mclks, pre_vcsel)

        final_mclks = self._decode_timeout(
            self._reg_lesen_16(self._FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI))
        final_us = self._timeout_mclks_to_us(final_mclks, final_vcsel)

        return {
            'msrc_us': msrc_us,
            'pre_us': pre_us,
            'final_us': final_us,
            'pre_vcsel': pre_vcsel,
            'final_vcsel': final_vcsel,
        }

    def _set_vcsel_periode(self, typ, period_pclks):
        """
        Setzt die VCSEL-Pulsperiode und passt Timeouts an.

        Args:
            typ: 'pre' oder 'final'
            period_pclks: Periode in PCLKS (gerade Zahl: pre 12-18, final 8-14)
        """
        timeouts = self._get_sequence_step_timeouts()
        encoded_vcsel = (period_pclks >> 1) - 1

        if typ == 'pre':
            # Phasecal-Timeout anpassen
            self._reg_schreiben(self._ALGO_PHASECAL_CONFIG_TIMEOUT,
                                self._PHASECAL_LIMITS.get(period_pclks, 0x30))

            # VCSEL-Periode schreiben
            self._reg_schreiben(self._PRE_RANGE_CONFIG_VCSEL_PERIOD, encoded_vcsel)

            # MSRC-Timeout umrechnen auf neue Periode
            new_msrc = self._timeout_us_to_mclks(timeouts['msrc_us'], period_pclks)
            self._reg_schreiben(self._MSRC_CONFIG_TIMEOUT_MACROP,
                                min(max(new_msrc - 1, 0), 255))

            # Pre-Range-Timeout umrechnen
            new_pre = self._timeout_us_to_mclks(timeouts['pre_us'], period_pclks)
            self._reg_schreiben_16(self._PRE_RANGE_CONFIG_TIMEOUT_MACROP_HI,
                                   self._encode_timeout(new_pre))

        elif typ == 'final':
            # VCSEL-Periode schreiben
            self._reg_schreiben(self._FINAL_RANGE_CONFIG_VCSEL_PERIOD, encoded_vcsel)

            # Final-Range-Timeout umrechnen
            new_final = self._timeout_us_to_mclks(timeouts['final_us'], period_pclks)
            self._reg_schreiben_16(self._FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI,
                                   self._encode_timeout(new_final))

        # Timing Budget beibehalten
        self._set_timing_budget_us(self._timing_budget_us)

    def _set_timing_budget_us(self, budget_us):
        """Setzt das Measurement Timing Budget in Mikrosekunden."""
        enables = self._get_sequence_step_enables()
        timeouts = self._get_sequence_step_timeouts()

        used_us = self._START_OVERHEAD + self._END_OVERHEAD

        if enables['tcc']:
            used_us += timeouts['msrc_us'] + self._TCC_OVERHEAD
        if enables['dss']:
            used_us += 2 * (timeouts['msrc_us'] + self._DSS_OVERHEAD)
        elif enables['msrc']:
            used_us += timeouts['msrc_us'] + self._MSRC_OVERHEAD
        if enables['pre_range']:
            used_us += timeouts['pre_us'] + self._PRE_RANGE_OVERHEAD
        if enables['final_range']:
            used_us += self._FINAL_RANGE_OVERHEAD

            # Verbleibende Zeit fuer Final Range
            remaining = budget_us - used_us
            if remaining <= 0:
                return

            # In MCLKS umrechnen und schreiben
            final_mclks = self._timeout_us_to_mclks(
                remaining, timeouts['final_vcsel'])
            self._reg_schreiben_16(
                self._FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI,
                self._encode_timeout(final_mclks))

        self._timing_budget_us = budget_us

    # ================================================================
    # Messmodi
    # ================================================================

    def set_modus(self, modus):
        """
        Setzt den Messmodus des Sensors.

        Verfuegbare Modi:
            TOF.SCHNELL:      20 ms, ~60 cm Reichweite, schnelle Hinderniserkennung
            TOF.STANDARD:     33 ms, ~120 cm Reichweite, allgemeine Messung (Default)
            TOF.GENAU:        200 ms, ~120 cm Reichweite, hohe Praezision
            TOF.LANGSTRECKE:  33 ms, ~200 cm Reichweite, maximale Distanz

        Args:
            modus: TOF.SCHNELL, TOF.STANDARD, TOF.GENAU oder TOF.LANGSTRECKE
        """
        if modus not in self._MODI_NAMEN:
            print("Ungueltiger Modus. Verwende TOF.SCHNELL/STANDARD/GENAU/LANGSTRECKE")
            return

        if modus == self.LANGSTRECKE:
            # Langstrecke: niedrigere Signalschwelle + laengere VCSEL-Pulse
            self._set_signal_rate_limit(0.1)
            self._set_vcsel_periode('pre', 18)
            self._set_vcsel_periode('final', 14)
            self._set_timing_budget_us(33000)
        else:
            # Standard-VCSEL wiederherstellen (falls vorher Langstrecke aktiv)
            if self._modus == self.LANGSTRECKE:
                self._set_signal_rate_limit(0.25)
                self._set_vcsel_periode('pre', 14)
                self._set_vcsel_periode('final', 10)

            if modus == self.SCHNELL:
                self._set_timing_budget_us(20000)
            elif modus == self.GENAU:
                self._set_timing_budget_us(200000)
            else:  # STANDARD
                self._set_timing_budget_us(33000)

        self._modus = modus

    def lese_modus(self):
        """
        Gibt den aktuellen Messmodus als String zurueck.

        Returns:
            str: 'schnell', 'standard', 'genau' oder 'langstrecke'
        """
        return self._MODI_NAMEN.get(self._modus, 'unbekannt')

    # ================================================================
    # Grundmessungen
    # ================================================================

    def messen_mm(self):
        """
        Misst die Entfernung in Millimetern.

        Returns:
            int: Entfernung in mm oder -1 bei Fehler/Timeout
        """
        # Mess-Sequenz starten
        self._reg_schreiben(0x80, 0x01)
        self._reg_schreiben(0xFF, 0x01)
        self._reg_schreiben(0x00, 0x00)
        self._reg_schreiben(0x91, self._stop_variable)
        self._reg_schreiben(0x00, 0x01)
        self._reg_schreiben(0xFF, 0x00)
        self._reg_schreiben(0x80, 0x00)

        self._reg_schreiben(self._SYSRANGE_START, 0x01)

        # Warten bis Messung gestartet
        timeout = 500
        while self._reg_lesen(self._SYSRANGE_START) & 0x01:
            timeout -= 1
            if timeout == 0:
                return -1
            time.sleep_ms(1)

        # Warten auf Ergebnis
        timeout = 500
        while not (self._reg_lesen(self._RESULT_INTERRUPT_STATUS) & 0x07):
            timeout -= 1
            if timeout == 0:
                return -1
            time.sleep_ms(1)

        # Ergebnis lesen (12 Bytes ab RESULT_RANGE_STATUS)
        daten = self._i2c.readfrom_mem(self._addr, self._RESULT_RANGE_STATUS, 12)
        self._letzter_status = (daten[0] & 0x78) >> 3
        distanz = (daten[10] << 8) | daten[11]

        # Interrupt loeschen
        self._reg_schreiben(self._SYSTEM_INTERRUPT_CLEAR, 0x01)

        if distanz <= 0 or distanz > 2200:
            return -1

        return distanz

    def messen_cm(self):
        """
        Misst die Entfernung in Zentimetern.

        Returns:
            float: Entfernung in cm oder -1 bei Fehler
        """
        mm = self.messen_mm()
        if mm < 0:
            return -1
        return round(mm / 10.0, 1)

    def messen_laufzeit(self):
        """
        Gibt die ungefaehre Signallaufzeit in Nanosekunden zurueck.

        Die Laufzeit wird aus der Distanz zurueckgerechnet:
        Laufzeit = 2 * Distanz / Lichtgeschwindigkeit

        Returns:
            int: Laufzeit (hin und zurueck) in Nanosekunden oder -1 bei Fehler
        """
        mm = self.messen_mm()
        if mm < 0:
            return -1
        # Lichtgeschwindigkeit: ~0.2998 mm/ns, hin und zurueck
        return round(2 * mm / 0.2998)

    def status(self):
        """
        Gibt den Status der letzten Messung als lesbaren String zurueck.

        Returns:
            str: Statusbeschreibung (z. B. 'gueltig', 'Signal zu schwach')
        """
        return self._STATUS_TEXTE.get(
            self._letzter_status,
            'unbekannt ({})'.format(self._letzter_status))

    # ================================================================
    # Filterfunktionen
    # ================================================================

    def messen_mittelwert(self, n=5):
        """
        Fuehrt n Messungen durch und gibt den Mittelwert in mm zurueck.
        Ungueltige Messungen werden verworfen.

        Args:
            n: Anzahl der Messungen (Standard: 5)

        Returns:
            int: Mittelwert in mm oder -1 wenn keine gueltige Messung
        """
        werte = []
        for _ in range(n):
            mm = self.messen_mm()
            if mm > 0:
                werte.append(mm)
        if not werte:
            return -1
        return round(sum(werte) / len(werte))

    def messen_median(self, n=5):
        """
        Fuehrt n Messungen durch und gibt den Median in mm zurueck.
        Der Median ist robuster gegenueber Ausreissern als der Mittelwert.

        Args:
            n: Anzahl der Messungen (Standard: 5)

        Returns:
            int: Median in mm oder -1 wenn keine gueltige Messung
        """
        werte = []
        for _ in range(n):
            mm = self.messen_mm()
            if mm > 0:
                werte.append(mm)
        if not werte:
            return -1
        werte.sort()
        mitte = len(werte) // 2
        if len(werte) % 2 == 0:
            return round((werte[mitte - 1] + werte[mitte]) / 2)
        return werte[mitte]

    def messen_bereich(self, n=5):
        """
        Fuehrt n Messungen durch und gibt Minimum, Maximum und Mittelwert zurueck.

        Args:
            n: Anzahl der Messungen (Standard: 5)

        Returns:
            tuple: (minimum, maximum, mittelwert) in mm oder (-1, -1, -1) bei Fehler
        """
        werte = []
        for _ in range(n):
            mm = self.messen_mm()
            if mm > 0:
                werte.append(mm)
        if not werte:
            return (-1, -1, -1)
        return (
            min(werte),
            max(werte),
            round(sum(werte) / len(werte))
        )

    # ================================================================
    # Schwellenwertlogik
    # ================================================================

    def ist_naeher_als(self, mm):
        """
        Prueft ob ein Objekt naeher als der angegebene Schwellenwert ist.

        Args:
            mm: Schwellenwert in Millimetern

        Returns:
            bool: True wenn Objekt naeher, False wenn weiter entfernt oder Fehler
        """
        distanz = self.messen_mm()
        if distanz < 0:
            return False
        return distanz < mm

    def zone(self, nah=100, mittel=500):
        """
        Ordnet die aktuelle Entfernung in eine von drei Zonen ein.

        Args:
            nah: Grenze fuer Zone 'nah' in mm (Standard: 100)
            mittel: Grenze fuer Zone 'mittel' in mm (Standard: 500)

        Returns:
            str: 'nah', 'mittel', 'fern' oder 'fehler'
        """
        distanz = self.messen_mm()
        if distanz < 0:
            return 'fehler'
        if distanz < nah:
            return 'nah'
        if distanz < mittel:
            return 'mittel'
        return 'fern'

    def geschwindigkeit(self, intervall_ms=500):
        """
        Berechnet die Geschwindigkeit eines Objekts aus zwei Messungen.

        Args:
            intervall_ms: Zeitabstand zwischen den Messungen in ms (Standard: 500)

        Returns:
            float: Geschwindigkeit in mm/s (positiv = naehert sich,
                   negativ = entfernt sich) oder 0 bei Fehler
        """
        d1 = self.messen_mm()
        time.sleep_ms(intervall_ms)
        d2 = self.messen_mm()
        if d1 < 0 or d2 < 0:
            return 0
        delta_mm = d1 - d2
        delta_s = intervall_ms / 1000.0
        return round(delta_mm / delta_s, 1)

    # ================================================================
    # Sensor-Konfiguration
    # ================================================================

    def set_adresse(self, neue_adresse):
        """
        Aendert die I2C-Adresse des Sensors.

        Die Aenderung ist fluechtig und gilt nur bis zum naechsten
        Neustart (Strom aus/ein). Bei jedem Boot muss die Adresse
        erneut gesetzt werden.

        Args:
            neue_adresse: Neue 7-Bit I2C-Adresse (z. B. 0x30)
        """
        self._reg_schreiben(self._I2C_SLAVE_DEVICE_ADDRESS, neue_adresse & 0x7F)
        self._addr = neue_adresse
        print("Neue Adresse: 0x{:02X}".format(neue_adresse))

    def lese_adresse(self):
        """
        Gibt die aktuelle I2C-Adresse zurueck.

        Returns:
            int: Aktuelle I2C-Adresse
        """
        return self._addr

    def set_timing_budget(self, us):
        """
        Setzt das Timing Budget manuell in Mikrosekunden (Expertenmodus).

        Hoehere Werte = praeziser aber langsamer.
        Typische Werte: 20000, 33000, 66000, 100000, 200000.

        Args:
            us: Timing Budget in Mikrosekunden
        """
        self._set_timing_budget_us(us)

    def lese_timing_budget(self):
        """
        Gibt das aktuelle Timing Budget in Mikrosekunden zurueck.

        Returns:
            int: Timing Budget in us
        """
        return self._timing_budget_us
