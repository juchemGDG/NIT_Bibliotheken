"""
GY-261 Kompass Sensor Bibliothek für MicroPython auf ESP32
Basiert auf HMC5883L 3-Achsen Magnetfeld-Sensor
Keine externen Abhängigkeiten (außer machine.I2C)
"""

from machine import I2C, Pin
import math


class Compass:
    """
    Kompass-Sensor Treiber für GY-261 (HMC5883L)
    
    Auslesen des Magnetfeldes in 3 Achsen (X, Y, Z)
    Berechnung des Heading (Kompassrichtung) in Grad
    Kalibrierung und Deklinationswinkelverwaltung
    """
    
    # I2C Adresse
    ADDRESS = 0x1E  # Standard I2C Adresse für HMC5883L
    
    # Register
    REG_CONFIG_A = 0x00
    REG_CONFIG_B = 0x01
    REG_MODE = 0x02
    REG_DATA_X_MSB = 0x03
    REG_DATA_X_LSB = 0x04
    REG_DATA_Z_MSB = 0x05
    REG_DATA_Z_LSB = 0x06
    REG_DATA_Y_MSB = 0x07
    REG_DATA_Y_LSB = 0x08
    REG_STATUS = 0x09
    REG_IDENT_A = 0x0A
    
    # Betriebsmodi
    MODE_CONTINUOUS = 0x00
    MODE_SINGLE = 0x01
    MODE_IDLE = 0x02
    
    # Messbereich/Gain Optionen
    GAIN_1370 = 0x00  # 0.73 mG/LSB (Standardbereich)
    GAIN_1090 = 0x01  # 0.92 mG/LSB
    GAIN_820 = 0x02   # 1.22 mG/LSB
    GAIN_660 = 0x03   # 1.52 mG/LSB
    GAIN_440 = 0x04   # 2.27 mG/LSB
    GAIN_330 = 0x05   # 3.03 mG/LSB
    GAIN_220 = 0x06   # 4.35 mG/LSB
    GAIN_165 = 0x07   # 5.80 mG/LSB
    
    # Sample Rate Optionen
    RATE_0_75HZ = 0x00
    RATE_1_5HZ = 0x01
    RATE_3HZ = 0x02
    RATE_7_5HZ = 0x03
    RATE_15HZ = 0x04       # Standard
    RATE_30HZ = 0x05
    RATE_75HZ = 0x06
    
    # Messbereiche für verschiedene Gains
    RANGE_LSBS = [0.73, 0.92, 1.22, 1.52, 2.27, 3.03, 4.35, 5.80]
    
    def __init__(self, i2c, addr=ADDRESS, scl=22, sda=21):
        """
        Kompass initialisieren
        
        Args:
            i2c: I2C Bus Objekt (oder None zum Auto-Erstellen)
            addr: I2C Adresse (Standard: 0x1E)
            scl: SCL Pin falls i2c=None
            sda: SDA Pin falls i2c=None
        """
        if i2c is None:
            self.i2c = I2C(0, scl=Pin(scl), sda=Pin(sda), freq=400000)
        else:
            self.i2c = i2c
        
        self.addr = addr
        self.gain = self.GAIN_1370  # Standardbereich
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
        """Sensor initialisieren"""
        # Config A: Sample Rate und Measurement Mode
        # Bits 7:5 = Sample Rate (default 15 Hz)
        # Bits 4:3 = Measurement Mode (normal)
        config_a = (self.RATE_15HZ << 2) | 0x00
        self._write_register(self.REG_CONFIG_A, config_a)
        
        # Config B: Gain/Range
        self._write_register(self.REG_CONFIG_B, self.gain << 5)
        
        # Mode: Continuous Measurement
        self._write_register(self.REG_MODE, self.MODE_CONTINUOUS)
    
    def set_gain(self, gain):
        """
        Messbereich einstellen
        Höhere Gains = höhere Auflösung, kleinerer Messbereich
        
        Args:
            gain: GAIN_1370 bis GAIN_165
        """
        self.gain = gain
        self._write_register(self.REG_CONFIG_B, gain << 5)
    
    def set_sample_rate(self, rate):
        """
        Sample Rate einstellen
        
        Args:
            rate: RATE_0_75HZ bis RATE_75HZ
        """
        current = self._read_register(self.REG_CONFIG_A)
        new_config = (current & 0xE3) | (rate << 2)
        self._write_register(self.REG_CONFIG_A, new_config)
    
    def set_mode(self, mode):
        """
        Betriebsmodus einstellen
        
        Args:
            mode: MODE_CONTINUOUS, MODE_SINGLE, oder MODE_IDLE
        """
        self._write_register(self.REG_MODE, mode)
    
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
        Rohdaten auslesen
        
        Returns:
            Tuple (x, y, z) - rohe ADC-Werte
        """
        # Daten lesen: X(MSB,LSB), Z(MSB,LSB), Y(MSB,LSB)
        data = self._read_registers(self.REG_DATA_X_MSB, 6)
        
        # 16-Bit Werte zusammensetzen (Big-Endian)
        x = (data[0] << 8) | data[1]
        z = (data[2] << 8) | data[3]
        y = (data[4] << 8) | data[5]
        
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
        
        # Rohdaten mit mG/LSB Wert umrechnen
        lsb = self.RANGE_LSBS[self.gain]
        
        x_mg = (x + self.calibration_x) * lsb
        y_mg = (y + self.calibration_y) * lsb
        z_mg = (z + self.calibration_z) * lsb
        
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
        Prüfen ob neue Daten verfügbar sind
        
        Returns:
            bool - True wenn Messung bereit
        """
        status = self._read_register(self.REG_STATUS)
        return (status & 0x01) == 0  # Bit 0: Data Ready
