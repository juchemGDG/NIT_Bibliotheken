"""
NIT Bibliothek: ADS1015 - 12-bit ADC fuer analoge Messungen ueber I2C
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-07

Direkte Registeransteuerung des ADS1015 ohne Fremdbibliotheken.
Unterstuetzt Single-Ended- und Differenzialmessung mit einstellbarem Gain und Datenrate.
"""

from time import sleep_ms


class ADS1015:
    """
    Liest analoge Spannungen ueber den ADS1015 aus.

    Unterstuetzte Hardware:
    - ADS1015 Breakout-Board
    - ADS1015 ADC-Module mit Adresse 0x48 bis 0x4B

    Schnittstelle: I2C
    """

    # Registeradressen
    REG_CONVERSION = 0x00
    REG_CONFIG = 0x01
    REG_LO_THRESH = 0x02
    REG_HI_THRESH = 0x03

    # Kanal-Multiplexer (Single-Ended)
    MUX_SINGLE_0 = 0x4000
    MUX_SINGLE_1 = 0x5000
    MUX_SINGLE_2 = 0x6000
    MUX_SINGLE_3 = 0x7000

    # Kanal-Multiplexer (Differenzial)
    MUX_DIFF_0_1 = 0x0000
    MUX_DIFF_0_3 = 0x1000
    MUX_DIFF_1_3 = 0x2000
    MUX_DIFF_2_3 = 0x3000

    # Programmable Gain Amplifier
    PGA_6_144V = 0x0000
    PGA_4_096V = 0x0200
    PGA_2_048V = 0x0400
    PGA_1_024V = 0x0600
    PGA_0_512V = 0x0800
    PGA_0_256V = 0x0A00

    # Betriebsmodus
    MODE_CONTINUOUS = 0x0000
    MODE_SINGLE_SHOT = 0x0100

    # Datenraten ADS1015 (Samples pro Sekunde)
    DR_128 = 0x0000
    DR_250 = 0x0020
    DR_490 = 0x0040
    DR_920 = 0x0060
    DR_1600 = 0x0080
    DR_2400 = 0x00A0
    DR_3300 = 0x00C0

    # Komparator aus
    COMP_DISABLE = 0x0003

    _MUX_SINGLE_MAP = {
        0: MUX_SINGLE_0,
        1: MUX_SINGLE_1,
        2: MUX_SINGLE_2,
        3: MUX_SINGLE_3,
    }

    _PGA_FS_MAP = {
        PGA_6_144V: 6.144,
        PGA_4_096V: 4.096,
        PGA_2_048V: 2.048,
        PGA_1_024V: 1.024,
        PGA_0_512V: 0.512,
        PGA_0_256V: 0.256,
    }

    _DR_SPS_MAP = {
        DR_128: 128,
        DR_250: 250,
        DR_490: 490,
        DR_920: 920,
        DR_1600: 1600,
        DR_2400: 2400,
        DR_3300: 3300,
    }

    def __init__(self, i2c, addr=0x48, pga=PGA_4_096V, data_rate=DR_1600):
        """
        Initialisiert den ADS1015.

        :param i2c: I2C Bus Objekt (machine.I2C)
        :param addr: I2C Adresse (0x48 bis 0x4B)
        :param pga: Vollbereich des PGA (PGA_...)
        :param data_rate: Datenrate (DR_...)
        """
        self.i2c = i2c
        self.addr = addr

        self.pga = pga
        self.data_rate = data_rate
        self.mode = self.MODE_SINGLE_SHOT

        if pga not in self._PGA_FS_MAP:
            raise ValueError("Ungueltiger pga-Wert")
        if data_rate not in self._DR_SPS_MAP:
            raise ValueError("Ungueltiger data_rate-Wert")

        self._write_u16(self.REG_LO_THRESH, 0x8000)
        self._write_u16(self.REG_HI_THRESH, 0x7FFF)

    def _write_u16(self, reg, value):
        """Schreibt 16-bit Wert (Big Endian) in ein Register."""
        self.i2c.writeto_mem(self.addr, reg, bytes([(value >> 8) & 0xFF, value & 0xFF]))

    def _read_u16(self, reg):
        """Liest 16-bit Wert (Big Endian) aus einem Register."""
        data = self.i2c.readfrom_mem(self.addr, reg, 2)
        return (data[0] << 8) | data[1]

    def _build_config(self, mux):
        """Erzeugt das Config-Register fuer eine Messung."""
        return (
            0x8000  # OS-Bit: Einzelkonvertierung starten
            | mux
            | self.pga
            | self.mode
            | self.data_rate
            | self.COMP_DISABLE
        )

    def _conversion_delay_ms(self):
        """Berechnet eine passende Wartezeit auf Basis der Datenrate."""
        sps = self._DR_SPS_MAP[self.data_rate]
        return max(1, int(1000 / sps) + 1)

    def _decode_raw_12bit(self, raw):
        """Dekodiert den 12-bit Messwert aus dem 16-bit Konversionsregister."""
        value = raw >> 4
        if value & 0x0800:
            value -= 0x1000
        return value

    def set_gain(self, pga):
        """Setzt den PGA-Bereich fuer folgende Messungen."""
        if pga not in self._PGA_FS_MAP:
            raise ValueError("Ungueltiger pga-Wert")
        self.pga = pga

    def set_data_rate(self, data_rate):
        """Setzt die Datenrate fuer folgende Messungen."""
        if data_rate not in self._DR_SPS_MAP:
            raise ValueError("Ungueltiger data_rate-Wert")
        self.data_rate = data_rate

    def set_mode(self, mode):
        """Setzt den Messmodus (Single-Shot oder Continuous)."""
        if mode not in (self.MODE_SINGLE_SHOT, self.MODE_CONTINUOUS):
            raise ValueError("Ungueltiger mode-Wert")
        self.mode = mode

    def get_lsb_mv(self):
        """Gibt die Aufloesung in mV pro LSB zurueck."""
        full_scale = self._PGA_FS_MAP[self.pga]
        return (full_scale / 2048.0) * 1000.0

    def read_raw(self, channel=0):
        """
        Liest einen rohen 12-bit Single-Ended-Messwert.

        :param channel: Kanal 0 bis 3
        :return: Signed Integer im Bereich -2048 bis 2047
        """
        if channel not in self._MUX_SINGLE_MAP:
            raise ValueError("channel muss 0..3 sein")

        config = self._build_config(self._MUX_SINGLE_MAP[channel])
        self._write_u16(self.REG_CONFIG, config)
        sleep_ms(self._conversion_delay_ms())

        raw = self._read_u16(self.REG_CONVERSION)
        return self._decode_raw_12bit(raw)

    def read_voltage(self, channel=0):
        """
        Liest die Single-Ended-Spannung in Volt.

        :param channel: Kanal 0 bis 3
        :return: Spannung in Volt
        """
        raw = self.read_raw(channel=channel)
        return raw * (self.get_lsb_mv() / 1000.0)

    def read_diff_raw(self, mux=MUX_DIFF_0_1):
        """
        Liest einen rohen 12-bit Differenzialwert.

        :param mux: Einer der MUX_DIFF_... Werte
        :return: Signed Integer im Bereich -2048 bis 2047
        """
        if mux not in (
            self.MUX_DIFF_0_1,
            self.MUX_DIFF_0_3,
            self.MUX_DIFF_1_3,
            self.MUX_DIFF_2_3,
        ):
            raise ValueError("Ungueltiger Differenzial-MUX")

        config = self._build_config(mux)
        self._write_u16(self.REG_CONFIG, config)
        sleep_ms(self._conversion_delay_ms())

        raw = self._read_u16(self.REG_CONVERSION)
        return self._decode_raw_12bit(raw)

    def read_diff_voltage(self, mux=MUX_DIFF_0_1):
        """
        Liest die Differenzialspannung in Volt.

        :param mux: Einer der MUX_DIFF_... Werte
        :return: Spannung in Volt
        """
        raw = self.read_diff_raw(mux=mux)
        return raw * (self.get_lsb_mv() / 1000.0)

    def read_all(self):
        """
        Liest alle vier Single-Ended Kanaele als Tupel.

        Rueckgabe:
            (ch0, ch1, ch2, ch3) in Volt
        """
        return (
            self.read_voltage(0),
            self.read_voltage(1),
            self.read_voltage(2),
            self.read_voltage(3),
        )
