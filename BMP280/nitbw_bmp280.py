"""
NIT Bibliothek: BMP280 - Umweltmessung mit Temperatur und Luftdruck
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-09

Direkte Registeransteuerung nach Bosch-Datenblatt ohne Fremdbibliotheken.
Aufbau und Methoden entsprechen der BME280-Bibliothek (ohne Luftfeuchte),
inklusive Hoehenberechnung, Kalibrierung und stromsparender Betriebsmodi.
"""

from machine import I2C
from time import sleep_ms


class BMP280:
    """
    Liest Temperatur und Luftdruck vom BMP280 aus.

    Unterstuetzte Hardware:
    - Bosch BMP280 Sensor
    - BMP280-Breakout-Module (z. B. GY-BMP280) mit Adresse 0x76 oder 0x77

    Schnittstelle: I2C
    """

    # BMP280 Register Adressen
    REG_DIG_T1 = 0x88
    REG_DIG_T2 = 0x8A
    REG_DIG_T3 = 0x8C
    REG_DIG_P1 = 0x8E
    REG_DIG_P2 = 0x90
    REG_DIG_P3 = 0x92
    REG_DIG_P4 = 0x94
    REG_DIG_P5 = 0x96
    REG_DIG_P6 = 0x98
    REG_DIG_P7 = 0x9A
    REG_DIG_P8 = 0x9C
    REG_DIG_P9 = 0x9E

    REG_CHIPID = 0xD0
    REG_SOFTRESET = 0xE0
    REG_STATUS = 0xF3
    REG_CONTROL = 0xF4
    REG_CONFIG = 0xF5
    REG_PRESSURE_DATA = 0xF7
    REG_TEMP_DATA = 0xFA

    # Chip ID Werte (0x58 = Serienchip, 0x56/0x57 = Vorserienmuster)
    CHIP_ID = 0x58
    CHIP_IDS = (0x56, 0x57, 0x58)
    CHIP_ID_BME280 = 0x60

    # Oversampling Optionen
    OVERSAMPLE_SKIP = 0x00
    OVERSAMPLE_X1 = 0x01
    OVERSAMPLE_X2 = 0x02
    OVERSAMPLE_X4 = 0x03
    OVERSAMPLE_X8 = 0x04
    OVERSAMPLE_X16 = 0x05

    # Betriebsmodi
    MODE_SLEEP = 0x00
    MODE_FORCED = 0x01
    MODE_NORMAL = 0x03

    # Standby Zeit (nur Normal Mode) - weicht bei 0x06/0x07 vom BME280 ab!
    STANDBY_0_5 = 0x00   # 0.5 ms
    STANDBY_62_5 = 0x01  # 62.5 ms
    STANDBY_125 = 0x02   # 125 ms
    STANDBY_250 = 0x03   # 250 ms
    STANDBY_500 = 0x04   # 500 ms
    STANDBY_1000 = 0x05  # 1000 ms
    STANDBY_2000 = 0x06  # 2000 ms
    STANDBY_4000 = 0x07  # 4000 ms

    # Filter Koeffizienten
    FILTER_OFF = 0x00
    FILTER_2 = 0x01
    FILTER_4 = 0x02
    FILTER_8 = 0x03
    FILTER_16 = 0x04

    def __init__(self, i2c, addr=0x76):
        """
        Initialisiert den BMP280 Sensor

        :param i2c: I2C Bus Objekt (machine.I2C)
        :param addr: I2C Adresse (0x76 oder 0x77)
        """
        self.i2c = i2c
        self.addr = addr

        # Pruefe Chip ID
        chip_id = self._read_u8(self.REG_CHIPID)
        if chip_id == self.CHIP_ID_BME280:
            raise RuntimeError("BME280 erkannt (Chip ID 0x60)! Bitte nitbw_bme280 verwenden.")
        if chip_id not in self.CHIP_IDS:
            raise RuntimeError(f"BMP280 nicht gefunden! Chip ID: 0x{chip_id:02X}, erwartet: 0x{self.CHIP_ID:02X}")

        # Soft Reset
        self._write_u8(self.REG_SOFTRESET, 0xB6)
        sleep_ms(10)

        # Kalibrierungsdaten auslesen
        self._load_calibration()

        # Standardkonfiguration
        self.sea_level_pressure = 1013.25  # hPa auf Meereshoehe
        self.t_fine = 0

        # Sensor konfigurieren mit Standardwerten
        self.configure(
            mode=self.MODE_NORMAL,
            osrs_t=self.OVERSAMPLE_X2,
            osrs_p=self.OVERSAMPLE_X16,
            filter_coef=self.FILTER_OFF,
            standby=self.STANDBY_500
        )

    def _read_u8(self, reg):
        """Liest ein unsigned 8-bit Register"""
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]

    def _read_u16_le(self, reg):
        """Liest ein unsigned 16-bit Register (Little Endian)"""
        data = self.i2c.readfrom_mem(self.addr, reg, 2)
        return data[0] | (data[1] << 8)

    def _read_s16_le(self, reg):
        """Liest ein signed 16-bit Register (Little Endian)"""
        val = self._read_u16_le(reg)
        return val if val < 32768 else val - 65536

    def _write_u8(self, reg, value):
        """Schreibt ein 8-bit Register"""
        self.i2c.writeto_mem(self.addr, reg, bytes([value]))

    def _load_calibration(self):
        """Laedt die Kalibrierungswerte aus dem Sensor"""
        # Temperatur Kalibrierung
        self.dig_T1 = self._read_u16_le(self.REG_DIG_T1)
        self.dig_T2 = self._read_s16_le(self.REG_DIG_T2)
        self.dig_T3 = self._read_s16_le(self.REG_DIG_T3)

        # Druck Kalibrierung
        self.dig_P1 = self._read_u16_le(self.REG_DIG_P1)
        self.dig_P2 = self._read_s16_le(self.REG_DIG_P2)
        self.dig_P3 = self._read_s16_le(self.REG_DIG_P3)
        self.dig_P4 = self._read_s16_le(self.REG_DIG_P4)
        self.dig_P5 = self._read_s16_le(self.REG_DIG_P5)
        self.dig_P6 = self._read_s16_le(self.REG_DIG_P6)
        self.dig_P7 = self._read_s16_le(self.REG_DIG_P7)
        self.dig_P8 = self._read_s16_le(self.REG_DIG_P8)
        self.dig_P9 = self._read_s16_le(self.REG_DIG_P9)

    def configure(self, mode=MODE_NORMAL, osrs_t=OVERSAMPLE_X2, osrs_p=OVERSAMPLE_X16,
                  filter_coef=FILTER_OFF, standby=STANDBY_500):
        """
        Konfiguriert den BMP280 Sensor

        :param mode: Betriebsmodus (MODE_SLEEP, MODE_FORCED, MODE_NORMAL)
        :param osrs_t: Temperatur Oversampling (OVERSAMPLE_X1 bis OVERSAMPLE_X16)
        :param osrs_p: Druck Oversampling (OVERSAMPLE_SKIP bis OVERSAMPLE_X16)
        :param filter_coef: IIR Filter Koeffizient (FILTER_OFF bis FILTER_16)
        :param standby: Standby Zeit im Normal Mode (STANDBY_0_5 bis STANDBY_4000)
        """
        self._osrs_t = osrs_t
        self._osrs_p = osrs_p

        # Sensor in Sleep Mode versetzen (Config nur im Sleep Mode sicher schreibbar)
        self._write_u8(self.REG_CONTROL, self.MODE_SLEEP)

        # Config Register (Standby Zeit und Filter)
        config = (standby << 5) | (filter_coef << 2)
        self._write_u8(self.REG_CONFIG, config)

        # Control Register (Temperatur und Druck Oversampling, Modus)
        ctrl = (osrs_t << 5) | (osrs_p << 2) | mode
        self._write_u8(self.REG_CONTROL, ctrl)

        # Warte auf erste Messung
        if mode != self.MODE_SLEEP:
            sleep_ms(self._measurement_time_ms())

    def _measurement_time_ms(self):
        """
        Berechnet die maximale Messdauer nach Datenblatt (Kap. 3.8.1)

        :return: Messdauer in ms (aufgerundet)
        """
        samples = (0, 1, 2, 4, 8, 16, 16, 16)
        t_us = 1250 + 2300 * samples[self._osrs_t]
        if self._osrs_p:
            t_us += 2300 * samples[self._osrs_p] + 575
        return t_us // 1000 + 1

    def _read_raw_data(self):
        """Liest die Rohdaten vom Sensor"""
        # Warte bis Messung verfuegbar ist
        while self._read_u8(self.REG_STATUS) & 0x08:
            sleep_ms(1)

        # Lese alle 6 Bytes (Druck, Temperatur)
        data = self.i2c.readfrom_mem(self.addr, self.REG_PRESSURE_DATA, 6)

        adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)

        return adc_t, adc_p

    def _compensate_temperature(self, adc_t):
        """
        Kompensiert die Rohdaten der Temperatur
        Gibt Temperatur in 0.01 C zurueck und setzt t_fine fuer den Druck
        """
        var1 = ((adc_t >> 3) - (self.dig_T1 << 1)) * self.dig_T2 >> 11
        var2 = (((((adc_t >> 4) - self.dig_T1) * ((adc_t >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = var1 + var2
        return (self.t_fine * 5 + 128) >> 8

    def _compensate_pressure(self, adc_p):
        """
        Kompensiert die Rohdaten des Drucks
        Gibt Druck in Pa zurueck
        """
        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33

        if var1 == 0:
            return 0

        p = 1048576 - adc_p
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.dig_P8 * p) >> 19
        p = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)

        return p / 256

    def read_raw(self):
        """
        Liest die Rohdaten vom Sensor

        :return: Tupel (adc_t, adc_p)
        """
        return self._read_raw_data()

    def read_temperature(self):
        """
        Liest die Temperatur in C

        :return: Temperatur in C
        """
        adc_t, _ = self._read_raw_data()
        t = self._compensate_temperature(adc_t)
        return t / 100.0

    def read_pressure(self):
        """
        Liest den Luftdruck in hPa

        :return: Luftdruck in hPa
        """
        adc_t, adc_p = self._read_raw_data()
        self._compensate_temperature(adc_t)  # t_fine wird benoetigt
        p = self._compensate_pressure(adc_p)
        return p / 100.0  # Pa zu hPa

    def read_all(self):
        """
        Liest Temperatur und Druck in einem Durchgang

        :return: Tupel (temperatur, druck)
        """
        adc_t, adc_p = self._read_raw_data()

        t = self._compensate_temperature(adc_t) / 100.0
        p = self._compensate_pressure(adc_p) / 100.0

        return t, p

    def read_compensated_data(self):
        """
        Alias fuer read_all()

        :return: Tupel (temperatur, druck)
        """
        return self.read_all()

    def read_averaged(self, n=10, delay_ms=0):
        """
        Liest Temperatur und Druck als Mittelwert ueber mehrere Messungen
        Nuetzlich fuer stabile Hoehenwerte (z. B. Stockwerkserkennung)

        :param n: Anzahl der Messungen
        :param delay_ms: Pause zwischen den Messungen in ms
        :return: Tupel (temperatur, druck)
        """
        n = max(1, int(n))
        sum_t = 0.0
        sum_p = 0.0
        for i in range(n):
            t, p = self.read_all()
            sum_t += t
            sum_p += p
            if delay_ms and i < n - 1:
                sleep_ms(delay_ms)
        return sum_t / n, sum_p / n

    def calculate_altitude(self, pressure=None, sea_level_pressure=None):
        """
        Berechnet die Hoehe ueber dem Meeresspiegel aus dem Luftdruck
        Verwendet die barometrische Hoehenformel

        :param pressure: Luftdruck in hPa (None = aktuelle Messung)
        :param sea_level_pressure: Referenzdruck auf Meereshoehe in hPa (None = gespeicherter Wert)
        :return: Hoehe in Metern
        """
        if pressure is None:
            pressure = self.read_pressure()

        if sea_level_pressure is None:
            sea_level_pressure = self.sea_level_pressure

        # Barometrische Hoehenformel
        altitude = 44330.0 * (1.0 - pow(pressure / sea_level_pressure, 0.1903))
        return altitude

    def calculate_sea_level_pressure(self, altitude, pressure=None):
        """
        Berechnet den Luftdruck auf Meereshoehe aus der aktuellen Hoehe
        Nuetzlich fuer die Kalibrierung

        :param altitude: Aktuelle Hoehe ueber dem Meeresspiegel in Metern
        :param pressure: Luftdruck in hPa (None = aktuelle Messung)
        :return: Luftdruck auf Meereshoehe in hPa
        """
        if pressure is None:
            pressure = self.read_pressure()

        sea_level = pressure / pow(1.0 - (altitude / 44330.0), 5.255)
        return sea_level

    def set_sea_level_pressure(self, pressure):
        """
        Setzt den Referenzdruck auf Meereshoehe fuer Hoehenberechnungen

        :param pressure: Luftdruck auf Meereshoehe in hPa
        """
        self.sea_level_pressure = pressure

    def calibrate_altitude(self, known_altitude):
        """
        Kalibriert die Hoehenmessung basierend auf einer bekannten Hoehe

        :param known_altitude: Bekannte Hoehe ueber dem Meeresspiegel in Metern
        """
        current_pressure = self.read_pressure()
        self.sea_level_pressure = self.calculate_sea_level_pressure(known_altitude, current_pressure)

    def forced_measurement(self):
        """
        Fuehrt eine Einzelmessung im Forced Mode durch
        Nuetzlich fuer Energiesparen zwischen Messungen

        :return: Tupel (temperatur, druck)
        """
        # Setze Forced Mode
        ctrl = self._read_u8(self.REG_CONTROL)
        ctrl = (ctrl & 0xFC) | self.MODE_FORCED
        self._write_u8(self.REG_CONTROL, ctrl)

        # Warte auf Messung (abhaengig vom Oversampling)
        sleep_ms(self._measurement_time_ms())

        return self.read_all()

    def sleep(self):
        """Versetzt den Sensor in den Sleep Mode (niedrigster Stromverbrauch)"""
        ctrl = self._read_u8(self.REG_CONTROL)
        ctrl = (ctrl & 0xFC) | self.MODE_SLEEP
        self._write_u8(self.REG_CONTROL, ctrl)

    def reset(self):
        """Fuehrt einen Soft Reset des Sensors durch (danach Sleep Mode, configure() aufrufen)"""
        self._write_u8(self.REG_SOFTRESET, 0xB6)
        sleep_ms(10)
        self._load_calibration()

    def get_chip_id(self):
        """
        Liest die Chip ID

        :return: Chip ID (sollte 0x58 sein)
        """
        return self._read_u8(self.REG_CHIPID)

    def get_status(self):
        """
        Liest das Status Register

        :return: Tupel (measuring, im_update)
        """
        status = self._read_u8(self.REG_STATUS)
        measuring = bool(status & 0x08)
        im_update = bool(status & 0x01)
        return measuring, im_update

    def __str__(self):
        """String Repraesentation mit aktuellen Messwerten"""
        try:
            t, p = self.read_all()
            alt = self.calculate_altitude(p)
            return f"BMP280: {t:.2f}C, {p:.2f}hPa, {alt:.2f}m"
        except:
            return f"BMP280 @ 0x{self.addr:02X}"
