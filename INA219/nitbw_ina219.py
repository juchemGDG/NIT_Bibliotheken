"""
NIT Bibliothek: INA219 - Strom-, Spannungs- und Leistungsmessung ueber I2C
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-07

Direkte Registeransteuerung des INA219 ohne Fremdbibliotheken.
Unterstuetzt Kalibrierung ueber Shunt-Widerstand sowie Messung von Shunt-, Bus- und Lastspannung.
"""


class INA219:
    """
    Misst Strom, Spannung und Leistung mit dem INA219.

    Unterstuetzte Hardware:
    - INA219 Breakout-Board
    - Shunt-basiertes Strommessmodul mit INA219 (typisch 0.1 Ohm)

    Schnittstelle: I2C
    """

    # Registeradressen
    REG_CONFIG = 0x00
    REG_SHUNT_VOLTAGE = 0x01
    REG_BUS_VOLTAGE = 0x02
    REG_POWER = 0x03
    REG_CURRENT = 0x04
    REG_CALIBRATION = 0x05

    # Konfigurationsbits
    CONFIG_RESET = 0x8000

    RANGE_16V = 0x0000
    RANGE_32V = 0x2000

    GAIN_1_40MV = 0x0000
    GAIN_2_80MV = 0x0800
    GAIN_4_160MV = 0x1000
    GAIN_8_320MV = 0x1800

    ADC_9BIT = 0x0000
    ADC_10BIT = 0x0080
    ADC_11BIT = 0x0100
    ADC_12BIT = 0x0180

    MODE_POWER_DOWN = 0x0000
    MODE_SHUNT_TRIGGERED = 0x0001
    MODE_BUS_TRIGGERED = 0x0002
    MODE_SHUNT_BUS_TRIGGERED = 0x0003
    MODE_ADC_OFF = 0x0004
    MODE_SHUNT_CONT = 0x0005
    MODE_BUS_CONT = 0x0006
    MODE_SHUNT_BUS_CONT = 0x0007

    def __init__(self, i2c, addr=0x40, shunt_ohms=0.1, max_expected_current=2.0):
        """
        Initialisiert den INA219 Sensor.

        :param i2c: I2C Bus Objekt (machine.I2C)
        :param addr: I2C Adresse (0x40 bis 0x4F, typischerweise 0x40)
        :param shunt_ohms: Wert des Shunt-Widerstands in Ohm
        :param max_expected_current: Erwarteter Maximalstrom in Ampere
        """
        self.i2c = i2c
        self.addr = addr

        self.shunt_ohms = shunt_ohms
        self.max_expected_current = max_expected_current

        self.current_lsb = 0.0
        self.power_lsb = 0.0
        self.calibration_value = 0

        self.reset()
        self.configure()
        self.calibrate(shunt_ohms=shunt_ohms, max_expected_current=max_expected_current)

    def _write_u16(self, reg, value):
        """Schreibt 16-bit Wert (Big Endian) in ein Register."""
        self.i2c.writeto_mem(self.addr, reg, bytes([(value >> 8) & 0xFF, value & 0xFF]))

    def _read_u16(self, reg):
        """Liest 16-bit Wert (Big Endian) aus einem Register."""
        data = self.i2c.readfrom_mem(self.addr, reg, 2)
        return (data[0] << 8) | data[1]

    def _read_s16(self, reg):
        """Liest 16-bit Signed-Wert aus einem Register."""
        value = self._read_u16(reg)
        if value > 0x7FFF:
            value -= 0x10000
        return value

    def reset(self):
        """Setzt den INA219 auf Werkseinstellung zurueck."""
        self._write_u16(self.REG_CONFIG, self.CONFIG_RESET)

    def configure(
        self,
        bus_range=RANGE_32V,
        gain=GAIN_8_320MV,
        bus_adc=ADC_12BIT,
        shunt_adc=ADC_12BIT,
        mode=MODE_SHUNT_BUS_CONT,
    ):
        """
        Konfiguriert Messbereich, ADC-Aufloesung und Modus.

        :param bus_range: Spannungsbereich (RANGE_16V oder RANGE_32V)
        :param gain: Shunt-Messbereich (GAIN_1_40MV bis GAIN_8_320MV)
        :param bus_adc: Bus-ADC-Aufloesung (ADC_9BIT bis ADC_12BIT)
        :param shunt_adc: Shunt-ADC-Aufloesung (ADC_9BIT bis ADC_12BIT)
        :param mode: Messmodus (MODE_...)
        """
        config = bus_range | gain | bus_adc | (shunt_adc >> 4) | mode
        self._write_u16(self.REG_CONFIG, config)

    def calibrate(self, shunt_ohms=None, max_expected_current=None):
        """
        Berechnet und schreibt die Kalibrierung fuer Strom- und Leistungsmessung.

        :param shunt_ohms: Shunt-Widerstand in Ohm
        :param max_expected_current: Erwarteter Maximalstrom in Ampere
        """
        if shunt_ohms is not None:
            self.shunt_ohms = shunt_ohms
        if max_expected_current is not None:
            self.max_expected_current = max_expected_current

        if self.shunt_ohms <= 0:
            raise ValueError("shunt_ohms muss > 0 sein")
        if self.max_expected_current <= 0:
            raise ValueError("max_expected_current muss > 0 sein")

        self.current_lsb = self.max_expected_current / 32768.0
        self.calibration_value = int(0.04096 / (self.current_lsb * self.shunt_ohms))

        if self.calibration_value < 1 or self.calibration_value > 0xFFFF:
            raise ValueError("Kalibrierungswert ausserhalb gueltigem Bereich")

        self.power_lsb = self.current_lsb * 20.0
        self._write_u16(self.REG_CALIBRATION, self.calibration_value)

    def conversion_ready(self):
        """Gibt True zurueck, wenn eine Konvertierung abgeschlossen ist."""
        raw = self._read_u16(self.REG_BUS_VOLTAGE)
        return bool(raw & 0x0002)

    def overflow(self):
        """Gibt True zurueck, wenn ein Messbereichsueberlauf auftrat."""
        raw = self._read_u16(self.REG_BUS_VOLTAGE)
        return bool(raw & 0x0001)

    def read_shunt_voltage_v(self):
        """Liest die Shunt-Spannung in Volt."""
        raw = self._read_s16(self.REG_SHUNT_VOLTAGE)
        return raw * 0.00001  # 10 uV pro Bit

    def read_shunt_voltage_mv(self):
        """Liest die Shunt-Spannung in Millivolt."""
        return self.read_shunt_voltage_v() * 1000.0

    def read_bus_voltage_v(self):
        """Liest die Bus-Spannung in Volt."""
        raw = self._read_u16(self.REG_BUS_VOLTAGE)
        return ((raw >> 3) * 0.004)  # 4 mV pro Bit

    def read_load_voltage_v(self):
        """Liest die Lastspannung in Volt (Bus + Shunt)."""
        return self.read_bus_voltage_v() + self.read_shunt_voltage_v()

    def read_current_a(self):
        """Liest den Strom in Ampere."""
        self._write_u16(self.REG_CALIBRATION, self.calibration_value)
        raw = self._read_s16(self.REG_CURRENT)
        return raw * self.current_lsb

    def read_current_ma(self):
        """Liest den Strom in Milliampere."""
        return self.read_current_a() * 1000.0

    def read_power_w(self):
        """Liest die Leistung in Watt."""
        self._write_u16(self.REG_CALIBRATION, self.calibration_value)
        raw = self._read_u16(self.REG_POWER)
        return raw * self.power_lsb

    def read_power_mw(self):
        """Liest die Leistung in Milliwatt."""
        return self.read_power_w() * 1000.0

    def read_all(self):
        """
        Liest alle relevanten Messgroessen als Tupel.

        Rueckgabe:
            (bus_v, shunt_mv, current_ma, power_mw, load_v)
        """
        bus_v = self.read_bus_voltage_v()
        shunt_mv = self.read_shunt_voltage_mv()
        current_ma = self.read_current_ma()
        power_mw = self.read_power_mw()
        load_v = bus_v + (shunt_mv / 1000.0)
        return bus_v, shunt_mv, current_ma, power_mw, load_v
