"""
NIT Bibliothek: DS18B20 - OneWire Temperatursensor
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      NIT / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Direkte OneWire-Registeransteuerung nach Maxim/Dallas-Datenblatt.
Unterstuetzt Einzelsensor und Multiple-Sensoren-Konfiguration mit ROM-Suche,
Aufloesung (9/10/11/12 Bit), Alarmfunktion (TH/TL) und CRC8-Abfrage.
"""

from machine import Pin
from time import sleep_ms, sleep_us


class DS18B20:
    """
    Liest Temperatur vom DS18B20 OneWire Temperatursensor aus.

    Unterstuetzte Hardware:
    - Maxim/Dallas DS18B20 OneWire Temperatursensor
    - DS18S20 (aelteres Modell mit 9-Bit-Aufloesung)
    
    Schnittstelle: OneWire (ein digitaler Pin mit Pull-up Widerstand, z.B. 4.7 kOhm)
    """
    
    # OneWire ROM Commands
    CMD_SEARCH_ROM = 0xF0
    CMD_READ_ROM = 0x33
    CMD_MATCH_ROM = 0x55
    CMD_SKIP_ROM = 0xCC
    
    # OneWire Function Commands
    CMD_CONVERT_T = 0x44
    CMD_READ_SCRATCHPAD = 0xBE
    CMD_WRITE_SCRATCHPAD = 0x4E
    CMD_COPY_SCRATCHPAD = 0x48
    CMD_RECALL_E2 = 0xB8
    CMD_READ_POWER_SUPPLY = 0xB4
    
    # Aufloesung (in Bit)
    RESOLUTION_9BIT = 0
    RESOLUTION_10BIT = 1
    RESOLUTION_11BIT = 2
    RESOLUTION_12BIT = 3
    
    # CRC8 Polynom
    CRC8_POLY = 0x8C
    
    def __init__(self, pin):
        """
        Initialisieren Sie den DS18B20 Sensor.
        
        Args:
            pin: GPIO-Pin-Nummer fuer OneWire Bus (z.B. Pin(4) fuer GPIO4)
        """
        self.pin = pin if hasattr(pin, 'init') else Pin(pin)
        self.pin.init(Pin.OPEN_DRAIN, Pin.PULL_UP)
        self.roms = []
        self.resolution = self.RESOLUTION_12BIT  # Default 12-Bit
        self._crc8_LUT = self._init_crc8_table()
    
    def _init_crc8_table(self):
        """Initialisiere CRC8 Lookup-Tabelle."""
        lut = []
        for i in range(256):
            crc = i
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0x8C
                else:
                    crc >>= 1
            lut.append(crc)
        return lut
    
    def _crc8(self, data):
        """Berechne CRC8 fuer Bytearray."""
        if isinstance(data, list) or isinstance(data, bytes):
            crc = 0
            for byte in data:
                crc = self._crc8_LUT[crc ^ byte]
            return crc
        return 0
    
    def _reset(self):
        """
        Setze OneWire Bus zurueck und pruefe auf Geraete-Praesenz.
        
        Returns:
            True wenn Geraet antwortet, False sonst
        """
        # Reset-Puls: Master zieht Bus fuer mindestens 480 us auf Low.
        self.pin.value(0)
        sleep_us(480)
        
        # Bus freigeben und auf Presence-Puls warten.
        self.pin.value(1)
        sleep_us(70)
        presence = (self.pin.value() == 0)
        # Rest des Reset-Slots abwarten (insgesamt min. 960 us).
        sleep_us(410)
        return presence
    
    def _write_bit(self, bit):
        """Schreibe ein Bit (0 oder 1) auf den Bus."""
        if bit:
            # Bit 1: kurzer Low-Impuls, dann freigeben.
            self.pin.value(0)
            sleep_us(6)
            self.pin.value(1)
            sleep_us(64)
        else:
            # Bit 0: langer Low-Impuls.
            self.pin.value(0)
            sleep_us(60)
            self.pin.value(1)
            sleep_us(10)
    
    def _read_bit(self):
        """Lese ein Bit vom Bus."""
        self.pin.value(0)
        sleep_us(6)
        self.pin.value(1)
        sleep_us(9)
        bit = self.pin.value()
        sleep_us(55)
        return bit
    
    def _write_byte(self, byte):
        """Schreibe ein Byte (LSB first)."""
        for i in range(8):
            bit = (byte >> i) & 1
            self._write_bit(bit)
    
    def _read_byte(self):
        """Lese ein Byte (LSB first)."""
        byte = 0
        for i in range(8):
            byte |= self._read_bit() << i
        return byte
    
    def search_roms(self):
        """
        Durchsuche Bus nach allen angeschlossenen Geraeten.
        
        Returns:
            Liste mit ROM-Adressen (jeweils als Bytearray)
        """
        self.roms = []
        last_discrepancy = 0
        last_device_flag = False
        rom_no = bytearray(8)

        while not last_device_flag:
            id_bit_number = 1
            last_zero = 0
            rom_byte_number = 0
            rom_byte_mask = 0x01

            if not self._reset():
                break

            self._write_byte(self.CMD_SEARCH_ROM)

            while rom_byte_number < 8:
                id_bit = self._read_bit()
                cmp_id_bit = self._read_bit()

                if id_bit == 1 and cmp_id_bit == 1:
                    break

                if id_bit != cmp_id_bit:
                    search_direction = id_bit
                else:
                    if id_bit_number < last_discrepancy:
                        search_direction = 1 if (rom_no[rom_byte_number] & rom_byte_mask) else 0
                    else:
                        search_direction = 1 if id_bit_number == last_discrepancy else 0

                    if search_direction == 0:
                        last_zero = id_bit_number

                if search_direction == 1:
                    rom_no[rom_byte_number] |= rom_byte_mask
                else:
                    rom_no[rom_byte_number] &= (~rom_byte_mask) & 0xFF

                self._write_bit(search_direction)

                id_bit_number += 1
                rom_byte_mask <<= 1

                if rom_byte_mask > 0x80:
                    rom_byte_number += 1
                    rom_byte_mask = 0x01

            if id_bit_number >= 65:
                last_discrepancy = last_zero
                if last_discrepancy == 0:
                    last_device_flag = True

                rom = bytes(rom_no)
                if self._crc8(rom[:7]) == rom[7]:
                    self.roms.append(rom)
                else:
                    break
            else:
                break

        return self.roms
    
    def convert_temperature(self, rom=None):
        """
        Starte Temperaturkonvertierung (Messung).
        
        Args:
            rom: ROM-Adresse zum Ansprechen (None = SKIP ROM fuer einzelnen Sensor)
        """
        if not self._reset():
            return False
        
        if rom:
            self._write_byte(self.CMD_MATCH_ROM)
            for byte in rom:
                self._write_byte(byte)
        else:
            self._write_byte(self.CMD_SKIP_ROM)
        
        self._write_byte(self.CMD_CONVERT_T)
        return True

    def sensor_vorhanden(self):
        """
        Prueft, ob mindestens ein OneWire-Geraet auf dem Bus antwortet.

        Returns:
            True bei Presence-Puls, sonst False
        """
        return self._reset()

    def read_scratchpad(self, rom=None):
        """
        Liest die 9 Scratchpad-Bytes inklusive CRC.

        Args:
            rom: ROM-Adresse zum Ansprechen (None = SKIP ROM)

        Returns:
            bytes mit 9 Bytes oder None bei Kommunikationsfehler
        """
        if not self._reset():
            return None

        if rom:
            self._write_byte(self.CMD_MATCH_ROM)
            for byte in rom:
                self._write_byte(byte)
        else:
            self._write_byte(self.CMD_SKIP_ROM)

        self._write_byte(self.CMD_READ_SCRATCHPAD)
        data = bytearray(9)
        for i in range(9):
            data[i] = self._read_byte()
        return bytes(data)
    
    def read_temperature(self, rom=None):
        """
        Lese Temperaturwert nach erfolgter Konvertierung.
        
        Args:
            rom: ROM-Adresse zum Ansprechen (None = SKIP ROM fuer einzelnen Sensor)
        
        Returns:
            Temperatur in Celsius als float oder None wenn CRC-Fehler
        """
        data = self.read_scratchpad(rom)
        if data is None:
            return None
        
        # Pruefe CRC8
        if self._crc8(data[:8]) != data[8]:
            return None
        
        # Temperatur ist als signed 16-bit Wert mit LSB = 1/16 °C kodiert.
        raw = (data[1] << 8) | data[0]
        if raw & 0x8000:
            raw -= 0x10000

        return raw / 16.0
    
    def messen(self, rom=None):
        """
        Fuehre Temperaturmessung aus (Konvertierung + Lesen).
        
        Args:
            rom: ROM-Adresse (None = einzelner Sensor)
        
        Returns:
            Temperatur in Celsius oder None
        """
        if self.convert_temperature(rom):
            # Wartezeit gemaess Datenblatt (9-12 Bit: 94/188/375/750 ms).
            wait_ms = {
                self.RESOLUTION_9BIT: 100,
                self.RESOLUTION_10BIT: 200,
                self.RESOLUTION_11BIT: 400,
                self.RESOLUTION_12BIT: 800,
            }.get(self.resolution, 800)
            sleep_ms(wait_ms)
            return self.read_temperature(rom)
        return None
    
    def set_resolution(self, bits):
        """
        Setze Temperaturaufloesung.
        
        Args:
            bits: 9, 10, 11 oder 12 (Default: 12)
        """
        if bits == 9:
            self.resolution = self.RESOLUTION_9BIT
        elif bits == 10:
            self.resolution = self.RESOLUTION_10BIT
        elif bits == 11:
            self.resolution = self.RESOLUTION_11BIT
        else:
            self.resolution = self.RESOLUTION_12BIT
    
    def write_scratchpad(self, th, tl, resolution=None, rom=None):
        """
        Schreibe Alarm-Schwellwerte und Aufloesung.
        
        Args:
            th: Alarm High Temperatur (max) als Integer
            tl: Alarm Low Temperatur (min) als Integer
            resolution: 9, 10, 11 oder 12 Bit (None = aktuell)
            rom: ROM-Adresse (None = SKIP ROM)
        """
        if resolution is None:
            res_bits = self.resolution
        else:
            if resolution == 9:
                res_bits = self.RESOLUTION_9BIT
            elif resolution == 10:
                res_bits = self.RESOLUTION_10BIT
            elif resolution == 11:
                res_bits = self.RESOLUTION_11BIT
            else:
                res_bits = self.RESOLUTION_12BIT
        
        if not self._reset():
            return False
        
        if rom:
            self._write_byte(self.CMD_MATCH_ROM)
            for byte in rom:
                self._write_byte(byte)
        else:
            self._write_byte(self.CMD_SKIP_ROM)
        
        self._write_byte(self.CMD_WRITE_SCRATCHPAD)
        self._write_byte(th & 0xFF)
        self._write_byte(tl & 0xFF)
        
        # Config Byte: Bits 5-6 fuer Aufloesung
        cfg = (res_bits << 5) | 0x1F  # Default config
        self._write_byte(cfg)
        
        return True
    
    def get_rom_list(self):
        """Gebe Liste mit allen gefundenen ROM-Adressen zurueck."""
        return self.roms
    
    def rom_to_string(self, rom):
        """Konvertiere ROM-Adresse zu Hex-String."""
        return "".join(["{:02X}".format(b) for b in rom])
