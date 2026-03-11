"""
NIT Bibliothek: COMPASS - Kompass und Magnetfeldmessung fuer GY-261
Fuer ESP32 mit MicroPython

Version:    1.1.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Unterstuetzt QMC5883L und HMC5883L mit Heading-Berechnung und Kalibrierung.
Optimiert fuer den Einsatz im Unterricht mit klarer API fuer Richtungsdaten.
"""

from machine import I2C, Pin
import math


class Compass:
    """
    Berechnet Kompassrichtung aus den Magnetfelddaten des GY-261 Moduls.

    Unterstuetzte Hardware:
    - GY-261 mit QMC5883L (0x0D)
    - GY-261 mit HMC5883L (0x1E)

    Schnittstelle: I2C
    """
    
    # I2C Adressen
    ADDRESS_HMC5883L = 0x1E  # Standard I2C Adresse für HMC5883L
    ADDRESS_QMC5883L = 0x0D  # I2C Adresse für QMC5883L (neuere Version)
    ADDRESS = 0x0D           # Standard: QMC5883L (häufiger in GY-261)
    
    # QMC5883L Register
    REG_DATA_X_LSB = 0x00
    REG_DATA_X_MSB = 0x01
    REG_DATA_Y_LSB = 0x02
    REG_DATA_Y_MSB = 0x03
    REG_DATA_Z_LSB = 0x04
    REG_DATA_Z_MSB = 0x05
    REG_STATUS = 0x06
    REG_TEMP_LSB = 0x07
    REG_TEMP_MSB = 0x08
    REG_CONFIG_1 = 0x09
    REG_CONFIG_2 = 0x0A
    REG_SET_RESET = 0x0B
    REG_RESERVED = 0x0C
    REG_CHIP_ID = 0x0D
    
    # Betriebsmodi (QMC5883L)
    MODE_STANDBY = 0x00
    MODE_CONTINUOUS = 0x01
    
    # Messbereich/Range Optionen (QMC5883L)
    # In Config 1: Bits 7-6
    RANGE_2G = 0x00      # ±2 Gauss (best resolution)
    RANGE_8G = 0x01      # ±8 Gauss
    RANGE_12G = 0x02     # ±12 Gauss
    RANGE_30G = 0x03     # ±30 Gauss (largest range)
    
    # Sample Rate Optionen (QMC5883L)
    # In Config 1: Bits 3-2
    RATE_10HZ = 0x00
    RATE_25HZ = 0x01
    RATE_50HZ = 0x02
    RATE_100HZ = 0x03
    
    # Oversample Optionen (QMC5883L)
    # In Config 1: Bits 5-4
    OVERSAMPLE_512 = 0x00
    OVERSAMPLE_256 = 0x01
    OVERSAMPLE_128 = 0x02
    OVERSAMPLE_64 = 0x03
    
    # Empfindlichkeiten für verschiedene Ranges (in mG)
    RANGE_SENSITIVITY = {
        RANGE_2G: 0.00833,    # 2 Gauss = 2000 mG, 16-bit = 0.061 mG/LSB
        RANGE_8G: 0.03333,    # 8 Gauss
        RANGE_12G: 0.05,      # 12 Gauss
        RANGE_30G: 0.12083    # 30 Gauss
    }
    
    def __init__(self, i2c, addr=ADDRESS, scl=22, sda=21):
        """
        Kompass initialisieren
        
        Args:
            i2c: I2C Bus Objekt (oder None zum Auto-Erstellen)
            addr: I2C Adresse (Standard: 0x0D für QMC5883L, 0x1E für HMC5883L)
            scl: SCL Pin falls i2c=None
            sda: SDA Pin falls i2c=None
        """
        if i2c is None:
            self.i2c = I2C(0, scl=Pin(scl), sda=Pin(sda), freq=400000)
        else:
            self.i2c = i2c
        
        self.addr = addr
        self.range = self.RANGE_2G  # Standard: ±2 Gauss
        self.sample_rate = self.RATE_25HZ
        self.oversample = self.OVERSAMPLE_512
        self.declination = 0  # Lokale Deklination in Grad
        
        # Kalibrierungswerte
        self.calibration_x = 0
        self.calibration_y = 0
        self.calibration_z = 0
        
        # Rohdaten
        self.x_raw = 0
        self.y_raw = 0
        self.z_raw = 0
        
        # Sensorinitialisierung
        self._initialize()
    
    def _write_register(self, reg, value):
        """Register schreiben"""
        self.i2c.writeto_mem(self.addr, reg, bytes([value]))
    
    def _read_register(self, reg):
        """Register lesen"""
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]
    
    def _read_registers(self, reg, count):
        """Mehrere Register lesen"""
        return self.i2c.readfrom_mem(self.addr, reg, count)
    
    def _initialize(self):
        """Sensor initialisieren (QMC5883L)"""
        # Reset: Set/Reset Strobe
        self._write_register(self.REG_SET_RESET, 0x01)
        
        # Config 1: Range, Sample Rate, Oversample
        # Bits 7-6: Range (0x00 = ±2G)
        # Bits 5-4: Oversample (0x00 = 512)
        # Bits 3-2: Sample Rate (0x01 = 25 Hz)
        # Bit 1-0: Mode (0x01 = Continuous)
        config1 = (self.range << 6) | (self.oversample << 4) | (self.sample_rate << 2) | self.MODE_CONTINUOUS
        self._write_register(self.REG_CONFIG_1, config1)
        
        # Config 2: keine kritischen Settings (default OK)
        self._write_register(self.REG_CONFIG_2, 0x00)
    
    def set_range(self, range_val):
        """
        Messbereich einstellen
        
        Args:
            range_val: RANGE_2G, RANGE_8G, RANGE_12G, oder RANGE_30G
        """
        self.range = range_val
        config1 = self._read_register(self.REG_CONFIG_1)
        new_config = (config1 & 0x3F) | (range_val << 6)
        self._write_register(self.REG_CONFIG_1, new_config)
    
    def set_oversample(self, oversample):
        """
        Oversample Rate einstellen (mehr = bessere Auflösung, langsamer)
        
        Args:
            oversample: OVERSAMPLE_512, OVERSAMPLE_256, OVERSAMPLE_128, oder OVERSAMPLE_64
        """
        self.oversample = oversample
        config1 = self._read_register(self.REG_CONFIG_1)
        new_config = (config1 & 0xCF) | (oversample << 4)
        self._write_register(self.REG_CONFIG_1, new_config)
    
    def set_sample_rate(self, rate):
        """
        Sample Rate einstellen (QMC5883L)
        
        Args:
            rate: RATE_10HZ, RATE_25HZ, RATE_50HZ, oder RATE_100HZ
        """
        self.sample_rate = rate
        config1 = self._read_register(self.REG_CONFIG_1)
        new_config = (config1 & 0xF3) | (rate << 2)
        self._write_register(self.REG_CONFIG_1, new_config)
    
    def set_mode(self, mode):
        """
        Betriebsmodus einstellen (QMC5883L)
        
        Args:
            mode: MODE_STANDBY oder MODE_CONTINUOUS
        """
        config1 = self._read_register(self.REG_CONFIG_1)
        new_config = (config1 & 0xFE) | mode
        self._write_register(self.REG_CONFIG_1, new_config)
    
    def set_declination(self, degrees, minutes=0):
        """
        Lokalen Deklinationswinkel setzen
        (Unterschied zwischen magnetischem und geographischem Nord)
        
        Args:
            degrees: Grad
            minutes: Minuten (optional)
        """
        self.declination = degrees + minutes / 60.0
    
    def read_raw(self):
        """
        Rohdaten auslesen (QMC5883L Format)
        
        Returns:
            Tuple (x, y, z) - rohe ADC-Werte
        """
        # QMC5883L: Register mit LSB zuerst
        data = self._read_registers(self.REG_DATA_X_LSB, 6)
        
        # 16-Bit Werte zusammensetzen (Little-Endian)
        x = (data[1] << 8) | data[0]
        y = (data[3] << 8) | data[2]
        z = (data[5] << 8) | data[4]
        
        # Als signed int interpretieren
        if x > 32767:
            x -= 65536
        if y > 32767:
            y -= 65536
        if z > 32767:
            z -= 65536
        
        self.x_raw = x
        self.y_raw = y
        self.z_raw = z
        
        return x, y, z
    
    def read_field(self):
        """
        Magnetisches Feld auslesen (in mG)
        
        Returns:
            Tuple (x, y, z) - Feldstärke in Milligauss + Kalibrierung
        """
        x, y, z = self.read_raw()
        
        # QMC5883L: Empfindlichkeit abhängig vom Range
        # LSB = 1 mG pro LSB bei ±2G, proportional für andere Ranges
        sensitivity = self.RANGE_SENSITIVITY[self.range]
        
        x_mg = (x + self.calibration_x) * sensitivity
        y_mg = (y + self.calibration_y) * sensitivity
        z_mg = (z + self.calibration_z) * sensitivity
        
        return x_mg, y_mg, z_mg
    
    def read_heading(self):
        """
        Kompassrichtung berechnen (Heading in Grad von Nord)
        
        Returns:
            float - Winkel in Grad (0°=Nord, 90°=Ost, 180°=Süd, 270°=West)
        """
        x, y, z = self.read_field()
        
        # Heading aus X und Y berechnen (Z wird ignoriert)
        # atan2 gibt Winkel in Radiant -> zu Grad konvertieren
        heading = math.atan2(y, x)
        heading = math.degrees(heading)
        
        # Deklinationswinkel addieren
        heading += self.declination
        
        # Normalisieren auf 0-360 Grad
        if heading < 0:
            heading += 360
        elif heading >= 360:
            heading -= 360
        
        return heading
    
    def read_heading_direction(self):
        """
        Kompassrichtung als Text (N, NE, E, SE, S, SW, W, NW)
        
        Returns:
            str - Himmelsrichtung
        """
        heading = self.read_heading()
        
        directions = [
            "N", "NNE", "NE", "ENE",
            "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW",
            "W", "WNW", "NW", "NNW"
        ]
        
        # heading / 22.5 = Sektor 0-15
        sector = int((heading + 11.25) / 22.5) % 16
        
        return directions[sector]
    
    def calibrate_with_bias(self, x_bias, y_bias, z_bias=0):
        """
        Manuelle Kalibrierung mit bekannten Offset-Werten
        
        Args:
            x_bias: X-Achsen Offset
            y_bias: Y-Achsen Offset
            z_bias: Z-Achsen Offset (optional)
        """
        self.calibration_x = x_bias
        self.calibration_y = y_bias
        self.calibration_z = z_bias
    
    def auto_calibrate(self, samples=100):
        """
        Automatische Offset-Kalibrierung durchführen
        Sensor während Kalibrierung in alle Richtungen drehen
        
        Args:
            samples: Anzahl der Messwerte
        """
        x_min, x_max = 0, 0
        y_min, y_max = 0, 0
        z_min, z_max = 0, 0
        
        print(f"Kalibrierung wird durchgeführt ({samples} Messungen)...")
        print("Sensor bitte in alle Richtungen drehen...")
        
        for i in range(samples):
            x, y, z = self.read_raw()
            
            if x < x_min:
                x_min = x
            if x > x_max:
                x_max = x
            if y < y_min:
                y_min = y
            if y > y_max:
                y_max = y
            if z < z_min:
                z_min = z
            if z > z_max:
                z_max = z
            
            if (i + 1) % 25 == 0:
                print(f"  {i + 1}/{samples} Messungen...")
        
        # Mittelpunkte als Offset speichern
        self.calibration_x = -(x_max + x_min) // 2
        self.calibration_y = -(y_max + y_min) // 2
        self.calibration_z = -(z_max + z_min) // 2
        
        print("Kalibrierung abgeschlossen!")
        print(f"Offsets: X={self.calibration_x}, Y={self.calibration_y}, Z={self.calibration_z}")
    
    def read_strength(self):
        """
        Größe des Magnetvektors berechnen
        
        Returns:
            float - Feldstärke in mG
        """
        x, y, z = self.read_field()
        strength = math.sqrt(x*x + y*y + z*z)
        return strength
    
    def is_ready(self):
        """
        Prüfen ob neue Daten verfügbar sind (QMC5883L)
        
        Returns:
            bool - True wenn Messung bereit
        """
        status = self._read_register(self.REG_STATUS)
        return (status & 0x01) == 1  # Bit 0: DRDY (Data Ready)
    
    def calculate_rotation(self, start_heading, end_heading):
        """
        Drehwinkel zwischen zwei Kompassrichtungen berechnen
        
        Args:
            start_heading: Start-Heading in Grad (0-360)
            end_heading: End-Heading in Grad (0-360)
        
        Returns:
            float - Drehwinkel in Grad
                    positiv = Drehung im Uhrzeigersinn (rechts)
                    negativ = Drehung gegen Uhrzeigersinn (links)
                    Bereich: -180° bis +180°
        
        Beispiele:
            von 10° nach 90°  -> +80°  (80° im Uhrzeigersinn)
            von 90° nach 10°  -> -80°  (80° gegen Uhrzeigersinn)
            von 350° nach 10° -> +20°  (20° im Uhrzeigersinn über 0°)
            von 10° nach 350° -> -20°  (20° gegen Uhrzeigersinn über 0°)
        """
        # Differenz berechnen
        rotation = end_heading - start_heading
        
        # Auf kürzesten Weg normalisieren (-180 bis +180)
        if rotation > 180:
            rotation -= 360
        elif rotation < -180:
            rotation += 360
        
        return rotation
    
    def get_rotation_direction(self, start_heading, end_heading):
        """
        Drehrichtung als Text ausgeben
        
        Args:
            start_heading: Start-Heading in Grad (0-360)
            end_heading: End-Heading in Grad (0-360)
        
        Returns:
            str - "rechts" (im Uhrzeigersinn) oder "links" (gegen Uhrzeigersinn)
        """
        rotation = self.calculate_rotation(start_heading, end_heading)
        
        if rotation > 0:
            return "rechts"
        elif rotation < 0:
            return "links"
        else:
            return "keine Drehung"
