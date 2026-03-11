"""
NIT Bibliothek: BME280 - Umweltmessung mit Temperatur, Luftdruck und Feuchte
Fuer ESP32 mit MicroPython

Version:    1.1.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Direkte Registeransteuerung nach Bosch-Datenblatt ohne Fremdbibliotheken.
Unterstuetzt Messung, Kalibrierung und Betriebsmodi fuer stromsparende Anwendungen.
"""

from machine import I2C
from time import sleep_ms
import struct

class BME280:
    """
    Liest Temperatur, Luftdruck und Luftfeuchtigkeit vom BME280 aus.

    Unterstuetzte Hardware:
    - Bosch BME280 Sensor
    - BME280-Breakout-Module mit Adresse 0x76 oder 0x77

    Schnittstelle: I2C
    """
    
    # BME280 Register Adressen
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
    REG_DIG_H1 = 0xA1
    REG_DIG_H2 = 0xE1
    REG_DIG_H3 = 0xE3
    REG_DIG_H4 = 0xE4
    REG_DIG_H5 = 0xE5
    REG_DIG_H6 = 0xE7
    
    REG_CHIPID = 0xD0
    REG_VERSION = 0xD1
    REG_SOFTRESET = 0xE0
    REG_CONTROL_HUM = 0xF2
    REG_STATUS = 0xF3
    REG_CONTROL = 0xF4
    REG_CONFIG = 0xF5
    REG_PRESSURE_DATA = 0xF7
    REG_TEMP_DATA = 0xFA
    REG_HUMIDITY_DATA = 0xFD
    
    # Chip ID Wert
    CHIP_ID = 0x60
    
    # Oversampling Optionen
    OVERSAMPLE_X1 = 0x01
    OVERSAMPLE_X2 = 0x02
    OVERSAMPLE_X4 = 0x03
    OVERSAMPLE_X8 = 0x04
    OVERSAMPLE_X16 = 0x05
    
    # Betriebsmodi
    MODE_SLEEP = 0x00
    MODE_FORCED = 0x01
    MODE_NORMAL = 0x03
    
    # Standby Zeit (nur Normal Mode)
    STANDBY_0_5 = 0x00   # 0.5 ms
    STANDBY_62_5 = 0x01  # 62.5 ms
    STANDBY_125 = 0x02   # 125 ms
    STANDBY_250 = 0x03   # 250 ms
    STANDBY_500 = 0x04   # 500 ms
    STANDBY_1000 = 0x05  # 1000 ms
    STANDBY_10 = 0x06    # 10 ms
    STANDBY_20 = 0x07    # 20 ms
    
    # Filter Koeffizienten
    FILTER_OFF = 0x00
    FILTER_2 = 0x01
    FILTER_4 = 0x02
    FILTER_8 = 0x03
    FILTER_16 = 0x04
    
    def __init__(self, i2c, addr=0x76):
        """
        Initialisiert den BME280 Sensor
        
        :param i2c: I2C Bus Objekt (machine.I2C)
        :param addr: I2C Adresse (0x76 oder 0x77)
        """
        self.i2c = i2c
        self.addr = addr
        
        # Prüfe Chip ID
        chip_id = self._read_u8(self.REG_CHIPID)
        if chip_id != self.CHIP_ID:
            raise RuntimeError(f"BME280 nicht gefunden! Chip ID: 0x{chip_id:02X}, erwartet: 0x{self.CHIP_ID:02X}")
        
        # Soft Reset
        self._write_u8(self.REG_SOFTRESET, 0xB6)
        sleep_ms(10)
        
        # Kalibrierungsdaten auslesen
        self._load_calibration()
        
        # Standardkonfiguration
        self.sea_level_pressure = 1013.25  # hPa auf Meereshöhe
        
        # Sensor konfigurieren mit Standardwerten
        self.configure(
            mode=self.MODE_NORMAL,
            osrs_t=self.OVERSAMPLE_X2,
            osrs_p=self.OVERSAMPLE_X16,
            osrs_h=self.OVERSAMPLE_X1,
            filter_coef=self.FILTER_OFF,
            standby=self.STANDBY_500
        )
    
    def _read_u8(self, reg):
        """Liest ein unsigned 8-bit Register"""
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]
    
    def _read_s8(self, reg):
        """Liest ein signed 8-bit Register"""
        val = self._read_u8(reg)
        return val if val < 128 else val - 256
    
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
        """Lädt die Kalibrierungswerte aus dem Sensor"""
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
        
        # Feuchtigkeit Kalibrierung
        self.dig_H1 = self._read_u8(self.REG_DIG_H1)
        self.dig_H2 = self._read_s16_le(self.REG_DIG_H2)
        self.dig_H3 = self._read_u8(self.REG_DIG_H3)
        
        e4 = self._read_s8(self.REG_DIG_H4)
        e5 = self._read_u8(self.REG_DIG_H5)
        e6 = self._read_u8(self.REG_DIG_H5 + 1)
        e7 = self._read_s8(self.REG_DIG_H6)
        
        self.dig_H4 = (e4 << 4) | (e5 & 0x0F)
        self.dig_H5 = (e6 << 4) | (e5 >> 4)
        self.dig_H6 = e7
    
    def configure(self, mode=MODE_NORMAL, osrs_t=OVERSAMPLE_X2, osrs_p=OVERSAMPLE_X16,
                  osrs_h=OVERSAMPLE_X1, filter_coef=FILTER_OFF, standby=STANDBY_500):
        """
        Konfiguriert den BME280 Sensor
        
        :param mode: Betriebsmodus (MODE_SLEEP, MODE_FORCED, MODE_NORMAL)
        :param osrs_t: Temperatur Oversampling (OVERSAMPLE_X1 bis OVERSAMPLE_X16)
        :param osrs_p: Druck Oversampling (OVERSAMPLE_X1 bis OVERSAMPLE_X16)
        :param osrs_h: Feuchtigkeit Oversampling (OVERSAMPLE_X1 bis OVERSAMPLE_X16)
        :param filter_coef: IIR Filter Koeffizient (FILTER_OFF bis FILTER_16)
        :param standby: Standby Zeit im Normal Mode (STANDBY_0_5 bis STANDBY_1000)
        """
        # Sensor in Sleep Mode versetzen
        self._write_u8(self.REG_CONTROL, self.MODE_SLEEP)
        
        # Feuchtigkeit Oversampling konfigurieren
        self._write_u8(self.REG_CONTROL_HUM, osrs_h)
        
        # Config Register (Standby Zeit und Filter)
        config = (standby << 5) | (filter_coef << 2)
        self._write_u8(self.REG_CONFIG, config)
        
        # Control Register (Temperatur und Druck Oversampling, Modus)
        ctrl = (osrs_t << 5) | (osrs_p << 2) | mode
        self._write_u8(self.REG_CONTROL, ctrl)
        
        # Warte auf erste Messung
        if mode != self.MODE_SLEEP:
            sleep_ms(10)
    
    def _read_raw_data(self):
        """Liest die Rohdaten vom Sensor"""
        # Warte bis Messung verfügbar ist
        while self._read_u8(self.REG_STATUS) & 0x08:
            sleep_ms(1)
        
        # Lese alle 8 Bytes (Druck, Temperatur, Feuchtigkeit)
        data = self.i2c.readfrom_mem(self.addr, self.REG_PRESSURE_DATA, 8)
        
        adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        adc_h = (data[6] << 8) | data[7]
        
        return adc_t, adc_p, adc_h
    
    def _compensate_temperature(self, adc_t):
        """
        Kompensiert die Rohdaten der Temperatur
        Gibt Temperatur in 0.01°C zurück und setzt t_fine für Druck/Feuchte
        """
        var1 = ((adc_t >> 3) - (self.dig_T1 << 1)) * self.dig_T2 >> 11
        var2 = (((((adc_t >> 4) - self.dig_T1) * ((adc_t >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = var1 + var2
        return (self.t_fine * 5 + 128) >> 8
    
    def _compensate_pressure(self, adc_p):
        """
        Kompensiert die Rohdaten des Drucks
        Gibt Druck in Pa zurück
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
    
    def _compensate_humidity(self, adc_h):
        """
        Kompensiert die Rohdaten der Feuchtigkeit
        Gibt relative Feuchtigkeit in %RH zurück
        """
        h = self.t_fine - 76800
        h = ((((adc_h << 14) - (self.dig_H4 << 20) - (self.dig_H5 * h)) + 16384) >> 15) * \
            (((((((h * self.dig_H6) >> 10) * (((h * self.dig_H3) >> 11) + 32768)) >> 10) + 2097152) * \
            self.dig_H2 + 8192) >> 14)
        h = h - (((((h >> 15) * (h >> 15)) >> 7) * self.dig_H1) >> 4)
        h = 0 if h < 0 else h
        h = 419430400 if h > 419430400 else h
        
        return (h >> 12) / 1024.0
    
    def read_raw(self):
        """
        Liest die Rohdaten vom Sensor
        
        :return: Tupel (adc_t, adc_p, adc_h)
        """
        return self._read_raw_data()
    
    def read_temperature(self):
        """
        Liest die Temperatur in °C
        
        :return: Temperatur in °C
        """
        adc_t, _, _ = self._read_raw_data()
        t = self._compensate_temperature(adc_t)
        return t / 100.0
    
    def read_pressure(self):
        """
        Liest den Luftdruck in hPa
        
        :return: Luftdruck in hPa
        """
        adc_t, adc_p, _ = self._read_raw_data()
        self._compensate_temperature(adc_t)  # t_fine wird benötigt
        p = self._compensate_pressure(adc_p)
        return p / 100.0  # Pa zu hPa
    
    def read_humidity(self):
        """
        Liest die relative Feuchtigkeit in %
        
        :return: Relative Feuchtigkeit in %
        """
        adc_t, _, adc_h = self._read_raw_data()
        self._compensate_temperature(adc_t)  # t_fine wird benötigt
        h = self._compensate_humidity(adc_h)
        return h
    
    def read_all(self):
        """
        Liest Temperatur, Druck und Feuchtigkeit in einem Durchgang
        
        :return: Tupel (temperatur, druck, feuchtigkeit)
        """
        adc_t, adc_p, adc_h = self._read_raw_data()
        
        t = self._compensate_temperature(adc_t) / 100.0
        p = self._compensate_pressure(adc_p) / 100.0
        h = self._compensate_humidity(adc_h)
        
        return t, p, h
    
    def read_compensated_data(self):
        """
        Alias für read_all()
        
        :return: Tupel (temperatur, druck, feuchtigkeit)
        """
        return self.read_all()
    
    def calculate_altitude(self, pressure=None, sea_level_pressure=None):
        """
        Berechnet die Höhe über dem Meeresspiegel aus dem Luftdruck
        Verwendet die barometrische Höhenformel
        
        :param pressure: Luftdruck in hPa (None = aktuelle Messung)
        :param sea_level_pressure: Referenzdruck auf Meereshöhe in hPa (None = gespeicherter Wert)
        :return: Höhe in Metern
        """
        if pressure is None:
            pressure = self.read_pressure()
        
        if sea_level_pressure is None:
            sea_level_pressure = self.sea_level_pressure
        
        # Barometrische Höhenformel
        altitude = 44330.0 * (1.0 - pow(pressure / sea_level_pressure, 0.1903))
        return altitude
    
    def calculate_sea_level_pressure(self, altitude, pressure=None):
        """
        Berechnet den Luftdruck auf Meereshöhe aus der aktuellen Höhe
        Nützlich für die Kalibrierung
        
        :param altitude: Aktuelle Höhe über dem Meeresspiegel in Metern
        :param pressure: Luftdruck in hPa (None = aktuelle Messung)
        :return: Luftdruck auf Meereshöhe in hPa
        """
        if pressure is None:
            pressure = self.read_pressure()
        
        sea_level = pressure / pow(1.0 - (altitude / 44330.0), 5.255)
        return sea_level
    
    def set_sea_level_pressure(self, pressure):
        """
        Setzt den Referenzdruck auf Meereshöhe für Höhenberechnungen
        
        :param pressure: Luftdruck auf Meereshöhe in hPa
        """
        self.sea_level_pressure = pressure
    
    def calibrate_altitude(self, known_altitude):
        """
        Kalibriert die Höhenmessung basierend auf einer bekannten Höhe
        
        :param known_altitude: Bekannte Höhe über dem Meeresspiegel in Metern
        """
        current_pressure = self.read_pressure()
        self.sea_level_pressure = self.calculate_sea_level_pressure(known_altitude, current_pressure)
    
    def calculate_dew_point(self, temperature=None, humidity=None):
        """
        Berechnet den Taupunkt aus Temperatur und Feuchtigkeit
        Verwendet die Magnus-Formel
        
        :param temperature: Temperatur in °C (None = aktuelle Messung)
        :param humidity: Relative Feuchtigkeit in % (None = aktuelle Messung)
        :return: Taupunkt in °C
        """
        if temperature is None or humidity is None:
            t, _, h = self.read_all()
            if temperature is None:
                temperature = t
            if humidity is None:
                humidity = h
        
        # Magnus-Formel Konstanten
        a = 17.27
        b = 237.7
        
        alpha = ((a * temperature) / (b + temperature)) + (humidity / 100.0)
        dew_point = (b * alpha) / (a - alpha)
        
        return dew_point
    
    def calculate_heat_index(self, temperature=None, humidity=None):
        """
        Berechnet den Hitzeindex (gefühlte Temperatur bei Wärme)
        Verwendet die NOAA Formel für Temperaturen > 27°C
        
        :param temperature: Temperatur in °C (None = aktuelle Messung)
        :param humidity: Relative Feuchtigkeit in % (None = aktuelle Messung)
        :return: Hitzeindex in °C
        """
        if temperature is None or humidity is None:
            t, _, h = self.read_all()
            if temperature is None:
                temperature = t
            if humidity is None:
                humidity = h
        
        # Umrechnung in Fahrenheit für die Formel
        t_f = temperature * 9.0 / 5.0 + 32.0
        
        if t_f < 80:  # < 26.7°C
            return temperature
        
        # NOAA Hitzeindex Formel
        hi = -42.379 + 2.04901523 * t_f + 10.14333127 * humidity
        hi -= 0.22475541 * t_f * humidity
        hi -= 0.00683783 * t_f * t_f
        hi -= 0.05481717 * humidity * humidity
        hi += 0.00122874 * t_f * t_f * humidity
        hi += 0.00085282 * t_f * humidity * humidity
        hi -= 0.00000199 * t_f * t_f * humidity * humidity
        
        # Zurück in Celsius
        return (hi - 32.0) * 5.0 / 9.0
    
    def forced_measurement(self):
        """
        Führt eine Einzelmessung im Forced Mode durch
        Nützlich für Energiesparen zwischen Messungen
        
        :return: Tupel (temperatur, druck, feuchtigkeit)
        """
        # Setze Forced Mode
        ctrl = self._read_u8(self.REG_CONTROL)
        ctrl = (ctrl & 0xFC) | self.MODE_FORCED
        self._write_u8(self.REG_CONTROL, ctrl)
        
        # Warte auf Messung
        sleep_ms(10)
        
        return self.read_all()
    
    def sleep(self):
        """Versetzt den Sensor in den Sleep Mode (niedrigster Stromverbrauch)"""
        ctrl = self._read_u8(self.REG_CONTROL)
        ctrl = (ctrl & 0xFC) | self.MODE_SLEEP
        self._write_u8(self.REG_CONTROL, ctrl)
    
    def reset(self):
        """Führt einen Soft Reset des Sensors durch"""
        self._write_u8(self.REG_SOFTRESET, 0xB6)
        sleep_ms(10)
        self._load_calibration()
    
    def get_chip_id(self):
        """
        Liest die Chip ID
        
        :return: Chip ID (sollte 0x60 sein)
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
        """String Repräsentation mit aktuellen Messwerten"""
        try:
            t, p, h = self.read_all()
            alt = self.calculate_altitude(p)
            return f"BME280: {t:.2f}°C, {p:.2f}hPa, {h:.2f}%RH, {alt:.2f}m"
        except:
            return f"BME280 @ 0x{self.addr:02X}"
