"""
NIT Bibliothek: COMPASS - Kompass und Magnetfeldmessung fuer GY-261
Fuer ESP32 mit MicroPython

Version:    1.1.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Unterstuetzt QMC5883L und HMC5883L mit Heading-Berechnung und Kalibrierung.
Erweitert durch ADXL345 Beschleunigungssensor fuer Lageerfassung und
neigungskompensiertes Heading (Sensorfusion).
Optimiert fuer den Einsatz im Unterricht mit klarer API fuer Richtungsdaten.
"""

from machine import I2C
import math


class Accelerometer:
    """
    ADXL345 Beschleunigungssensor fuer den GY-261 Baustein.

    Misst Beschleunigung in drei Achsen, berechnet Neigungswinkel
    (Pitch/Roll) und liefert Lage-Informationen.

    Wird vom Compass-Objekt automatisch fuer Neigungskompensation genutzt,
    kann aber auch eigenstaendig verwendet werden.

    Schnittstelle: I2C
    Standard-Adresse: 0x53 (SDO-Pin auf GND/LOW)
    Alt-Adresse:      0x1D (SDO-Pin auf VCC/HIGH)
    """

    ADDRESS     = 0x53   # SDO-Pin LOW (Standard)
    ADDRESS_ALT = 0x1D   # SDO-Pin HIGH
    DEVICE_ID   = 0xE5   # Erwarteter Chip-ID-Wert

    # Register-Adressen
    REG_DEVID       = 0x00  # Chip-ID (Read-Only)
    REG_BW_RATE     = 0x2C  # Bandbreite / Abtastrate
    REG_POWER_CTL   = 0x2D  # Power-Steuerung (Standby / Messen)
    REG_DATA_FORMAT = 0x31  # Datenformat (Range, Full-Resolution)
    REG_DATAX0      = 0x32  # Start der 6 Datenbytes (X, Y, Z je LSB+MSB)

    # Messbereiche (DATA_FORMAT Register, Bits 1-0)
    RANGE_2G  = 0x00
    RANGE_4G  = 0x01
    RANGE_8G  = 0x02
    RANGE_16G = 0x03

    # Empfindlichkeit im Full-Resolution-Modus: konstant 3.9 mg/LSB
    SENSITIVITY = 0.0039  # g pro LSB (gilt fuer alle Ranges)

    # Abtastraten (BW_RATE Register, Bits 3-0)
    RATE_25HZ  = 0x08
    RATE_50HZ  = 0x09
    RATE_100HZ = 0x0A   # Standard
    RATE_200HZ = 0x0B
    RATE_400HZ = 0x0C

    def __init__(self, i2c, addr=ADDRESS):
        """
        ADXL345 initialisieren.

        Args:
            i2c:  I2C Bus Objekt
            addr: I2C-Adresse (Standard 0x53)
        """
        self.i2c  = i2c
        self.addr = addr

        # Kalibrierungs-Offsets in g
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.offset_z = 0.0

        self._initialize()

    # -----------------------------------------------------------------------
    # Interne Hilfsmethoden
    # -----------------------------------------------------------------------

    def _write_register(self, reg, value):
        self.i2c.writeto_mem(self.addr, reg, bytes([value]))

    def _read_register(self, reg):
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]

    def _read_registers(self, reg, count):
        return self.i2c.readfrom_mem(self.addr, reg, count)

    def _initialize(self):
        """ADXL345 in kontinuierlichen Messmodus versetzen."""
        # Measurement-Mode aktivieren (Bit 3 = Measure)
        self._write_register(self.REG_POWER_CTL, 0x08)
        # Full-Resolution-Modus, +/-2 g Bereich
        self._write_register(self.REG_DATA_FORMAT, 0x08)
        # Abtastrate 100 Hz
        self._write_register(self.REG_BW_RATE, self.RATE_100HZ)

    # -----------------------------------------------------------------------
    # Diagnose
    # -----------------------------------------------------------------------

    def get_device_id(self):
        """
        Chip-ID auslesen (zur Verifikation: ADXL345 gibt 0xE5 zurueck).

        Returns:
            int - Chip-ID
        """
        return self._read_register(self.REG_DEVID)

    def is_available(self):
        """
        Pruefen ob ADXL345 antwortet und die richtige ID hat.

        Returns:
            bool - True wenn Sensor gefunden und identifiziert
        """
        try:
            return self.get_device_id() == self.DEVICE_ID
        except OSError:
            return False

    # -----------------------------------------------------------------------
    # Messwerte
    # -----------------------------------------------------------------------

    def read_raw(self):
        """
        Rohdaten aus allen 6 Datenregistern lesen (Little-Endian, signed).

        Returns:
            Tuple (x, y, z) - vorzeichenbehaftete 16-bit ADC-Werte
        """
        data = self._read_registers(self.REG_DATAX0, 6)

        x = (data[1] << 8) | data[0]
        y = (data[3] << 8) | data[2]
        z = (data[5] << 8) | data[4]

        if x > 32767: x -= 65536
        if y > 32767: y -= 65536
        if z > 32767: z -= 65536

        return x, y, z

    def read_accel(self):
        """
        Kalibrierte Beschleunigung in g lesen.
        (1 g entspricht ca. 9.81 m/s²)

        Returns:
            Tuple (ax, ay, az) - Beschleunigung in g
        """
        x, y, z = self.read_raw()
        ax = x * self.SENSITIVITY - self.offset_x
        ay = y * self.SENSITIVITY - self.offset_y
        az = z * self.SENSITIVITY - self.offset_z
        return ax, ay, az

    def read_accel_ms2(self):
        """
        Kalibrierte Beschleunigung in m/s2 lesen.

        Returns:
            Tuple (ax, ay, az) - Beschleunigung in m/s2
        """
        ax, ay, az = self.read_accel()
        return ax * 9.81, ay * 9.81, az * 9.81

    def read_pitch(self):
        """
        Nickwinkel (Pitch) berechnen: Neigung um die Y-Achse.

        Returns:
            float - Pitch in Grad
                     0°   = waagerecht
                    +90° = Vorderseite hoch
                    -90° = Vorderseite unten
        """
        ax, ay, az = self.read_accel()
        pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az))
        return math.degrees(pitch)

    def read_roll(self):
        """
        Rollwinkel berechnen: Neigung um die X-Achse.

        Returns:
            float - Roll in Grad
                     0°   = waagerecht
                    +90°  = rechte Seite nach unten
                    -90°  = linke Seite nach unten
        """
        ax, ay, az = self.read_accel()
        roll = math.atan2(ay, az)
        return math.degrees(roll)

    def read_pitch_roll(self):
        """
        Pitch und Roll mit einer einzigen I2C-Messung bestimmen.

        Returns:
            Tuple (pitch, roll) - beide Winkel in Grad
        """
        ax, ay, az = self.read_accel()
        pitch = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))
        roll  = math.degrees(math.atan2(ay, az))
        return pitch, roll

    def read_tilt_angle(self):
        """
        Gesamtneigungswinkel gegenueber der Waagerechten bestimmen.

        Returns:
            float - Neigung in Grad (0° = perfekt waagerecht)
        """
        ax, ay, az = self.read_accel()
        magnitude = math.sqrt(ax * ax + ay * ay + az * az)
        if magnitude < 0.001:
            return 0.0
        cos_val = min(abs(az) / magnitude, 1.0)
        return math.degrees(math.acos(cos_val))

    def is_level(self, threshold=5.0):
        """
        Pruefen ob der Sensor ausreichend waagerecht liegt.

        Args:
            threshold: Toleranzwinkel in Grad (Standard: 5°)

        Returns:
            bool - True wenn Neigung innerhalb der Toleranz
        """
        return self.read_tilt_angle() <= threshold

    def read_orientation_text(self):
        """
        Lage des Sensors als lesbaren Text ausgeben.

        Returns:
            str - eine von: "waagerecht", "leicht geneigt",
                            "stark geneigt", "hochkant"
        """
        tilt = self.read_tilt_angle()
        if tilt <= 15:
            return "waagerecht"
        elif tilt <= 45:
            return "leicht geneigt"
        elif tilt <= 75:
            return "stark geneigt"
        else:
            return "hochkant"

    # -----------------------------------------------------------------------
    # Kalibrierung
    # -----------------------------------------------------------------------

    def calibrate(self, samples=50):
        """
        Automatische Offset-Kalibrierung.
        Sensor muss dabei waagerecht und ruhig liegen!

        Nach der Kalibrierung gilt: X ca. 0 g, Y ca. 0 g, Z ca. 1 g.

        Args:
            samples: Anzahl der Mittelwertmessungen (mehr = genauer)
        """
        print(f"Beschleunigungssensor kalibrieren ({samples} Messungen)...")
        print("Sensor waagerecht und ruhig halten!")

        sum_x = sum_y = sum_z = 0.0
        for _ in range(samples):
            x, y, z = self.read_raw()
            sum_x += x * self.SENSITIVITY
            sum_y += y * self.SENSITIVITY
            sum_z += z * self.SENSITIVITY

        avg_x = sum_x / samples
        avg_y = sum_y / samples
        avg_z = sum_z / samples

        self.offset_x = avg_x           # X soll 0 g
        self.offset_y = avg_y           # Y soll 0 g
        self.offset_z = avg_z - 1.0     # Z soll 1 g (Schwerkraft)

        print("Kalibrierung abgeschlossen!")
        print(f"  Offsets: X={self.offset_x:.4f} g, Y={self.offset_y:.4f} g, Z={self.offset_z:.4f} g")

    def set_offset(self, x_offset, y_offset, z_offset=0.0):
        """
        Offset-Kalibrierung mit vorbekannten Werten setzen.

        Args:
            x_offset: X-Offset in g
            y_offset: Y-Offset in g
            z_offset: Z-Offset in g
        """
        self.offset_x = x_offset
        self.offset_y = y_offset
        self.offset_z = z_offset


class Compass:
    """
    Berechnet Kompassrichtung aus den Magnetfelddaten des GY-261 Moduls.
    Optional mit ADXL345-Beschleunigungssensor fuer neigungskompensiertes
    Heading (Sensorfusion).

    Unterstuetzte Hardware:
    - GY-261 mit QMC5883L (0x0D)
    - GY-261 mit HMC5883L (0x1E)
    - GY-261 mit ADXL345  (0x53, optional fuer Sensorfusion)

    Schnittstelle: I2C
    """

    # I2C Adressen
    ADDRESS_HMC5883L = 0x1E
    ADDRESS_QMC5883L = 0x0D
    ADDRESS = 0x0D   # Standard: QMC5883L (haeufiger in GY-261)

    # QMC5883L Register
    REG_DATA_X_LSB = 0x00
    REG_DATA_X_MSB = 0x01
    REG_DATA_Y_LSB = 0x02
    REG_DATA_Y_MSB = 0x03
    REG_DATA_Z_LSB = 0x04
    REG_DATA_Z_MSB = 0x05
    REG_STATUS    = 0x06
    REG_TEMP_LSB  = 0x07
    REG_TEMP_MSB  = 0x08
    REG_CONFIG_1  = 0x09
    REG_CONFIG_2  = 0x0A
    REG_SET_RESET = 0x0B
    REG_RESERVED  = 0x0C
    REG_CHIP_ID   = 0x0D

    # Betriebsmodi (QMC5883L)
    MODE_STANDBY    = 0x00
    MODE_CONTINUOUS = 0x01

    # Messbereich/Range (QMC5883L Config 1, Bits 7-6)
    RANGE_2G  = 0x00
    RANGE_8G  = 0x01
    RANGE_12G = 0x02
    RANGE_30G = 0x03

    # Sample Rate (QMC5883L Config 1, Bits 3-2)
    RATE_10HZ  = 0x00
    RATE_25HZ  = 0x01
    RATE_50HZ  = 0x02
    RATE_100HZ = 0x03

    # Oversample (QMC5883L Config 1, Bits 5-4)
    OVERSAMPLE_512 = 0x00
    OVERSAMPLE_256 = 0x01
    OVERSAMPLE_128 = 0x02
    OVERSAMPLE_64  = 0x03

    # Empfindlichkeiten fuer verschiedene Ranges (in mG/LSB)
    RANGE_SENSITIVITY = {
        RANGE_2G:  0.00833,
        RANGE_8G:  0.03333,
        RANGE_12G: 0.05,
        RANGE_30G: 0.12083
    }

    def __init__(self, i2c, addr=ADDRESS,
                 use_accel=True, accel_addr=None):
        """
        Kompass initialisieren (optional mit Beschleunigungssensor).

        Args:
            i2c:        Initialisiertes I2C Bus Objekt
            addr:       I2C-Adresse des Magnetfeldsensors
            use_accel:  True = ADXL345 automatisch suchen und initialisieren
            accel_addr: I2C-Adresse des ADXL345 (None = Standard 0x53)
        """
        if not isinstance(i2c, I2C):
            raise TypeError("i2c muss ein initialisiertes machine.I2C Objekt sein")
        self.i2c = i2c

        self.addr        = addr
        self.range       = self.RANGE_2G
        self.sample_rate = self.RATE_25HZ
        self.oversample  = self.OVERSAMPLE_512
        self.declination = 0.0

        # Kalibrierungswerte (Magnetometer)
        self.calibration_x = 0
        self.calibration_y = 0
        self.calibration_z = 0

        # Rohdaten (Magnetometer)
        self.x_raw = 0
        self.y_raw = 0
        self.z_raw = 0

        # Magnetometer initialisieren
        self._initialize()

        # Beschleunigungssensor (ADXL345) optional aufbauen
        self.accel = None
        if use_accel:
            a_addr = accel_addr if accel_addr is not None else Accelerometer.ADDRESS
            try:
                self.accel = Accelerometer(self.i2c, addr=a_addr)
            except OSError:
                self.accel = None  # Sensor nicht gefunden - ohne ACC weiterarbeiten

    # -----------------------------------------------------------------------
    # Interne Hilfsmethoden
    # -----------------------------------------------------------------------

    def _write_register(self, reg, value):
        self.i2c.writeto_mem(self.addr, reg, bytes([value]))

    def _read_register(self, reg):
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]

    def _read_registers(self, reg, count):
        return self.i2c.readfrom_mem(self.addr, reg, count)

    def _initialize(self):
        """QMC5883L initialisieren."""
        self._write_register(self.REG_SET_RESET, 0x01)
        config1 = (self.range << 6) | (self.oversample << 4) | (self.sample_rate << 2) | self.MODE_CONTINUOUS
        self._write_register(self.REG_CONFIG_1, config1)
        
        self._write_register(self.REG_CONFIG_2, 0x00)

    def _heading_to_direction(self, heading):
        """Heading in Grad zur naechsten Himmelsrichtung (16-teilig)."""
        directions = [
            "N", "NNE", "NE", "ENE",
            "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW",
            "W", "WNW", "NW", "NNW"
        ]
        sector = int((heading + 11.25) / 22.5) % 16
        return directions[sector]

    def _normalize_heading(self, heading):
        """Heading auf 0-360 Grad normalisieren."""
        heading = heading % 360.0
        if heading < 0:
            heading += 360.0
        return heading

    # -----------------------------------------------------------------------
    # Konfiguration
    # -----------------------------------------------------------------------

    def set_range(self, range_val):
        """
        Messbereich einstellen.

        Args:
            range_val: RANGE_2G, RANGE_8G, RANGE_12G, oder RANGE_30G
        """
        self.range = range_val
        config1 = self._read_register(self.REG_CONFIG_1)
        self._write_register(self.REG_CONFIG_1, (config1 & 0x3F) | (range_val << 6))

    def set_oversample(self, oversample):
        """
        Oversample-Rate einstellen (hoeher = genauer, aber langsamer).

        Args:
            oversample: OVERSAMPLE_512, OVERSAMPLE_256, OVERSAMPLE_128, OVERSAMPLE_64
        """
        self.oversample = oversample
        config1 = self._read_register(self.REG_CONFIG_1)
        self._write_register(self.REG_CONFIG_1, (config1 & 0xCF) | (oversample << 4))

    def set_sample_rate(self, rate):
        """
        Sample-Rate einstellen.

        Args:
            rate: RATE_10HZ, RATE_25HZ, RATE_50HZ, oder RATE_100HZ
        """
        self.sample_rate = rate
        config1 = self._read_register(self.REG_CONFIG_1)
        self._write_register(self.REG_CONFIG_1, (config1 & 0xF3) | (rate << 2))

    def set_mode(self, mode):
        """
        Betriebsmodus setzen.

        Args:
            mode: MODE_STANDBY oder MODE_CONTINUOUS
        """
        config1 = self._read_register(self.REG_CONFIG_1)
        self._write_register(self.REG_CONFIG_1, (config1 & 0xFE) | mode)

    def set_declination(self, degrees, minutes=0):
        """
        Magnetische Deklination fuer den aktuellen Standort setzen.
        (Abweichung zwischen magnetischem und geografischem Nord)

        Args:
            degrees: Grad-Anteil
            minutes: Minuten-Anteil (optional)
        """
        self.declination = degrees + minutes / 60.0

    # -----------------------------------------------------------------------
    # Messwerte - Magnetometer
    # -----------------------------------------------------------------------

    def read_raw(self):
        """
        Rohdaten des Magnetometers auslesen.

        Returns:
            Tuple (x, y, z) - rohe ADC-Werte (signed 16-bit)
        """
        data = self._read_registers(self.REG_DATA_X_LSB, 6)

        x = (data[1] << 8) | data[0]
        y = (data[3] << 8) | data[2]
        z = (data[5] << 8) | data[4]

        if x > 32767: x -= 65536
        if y > 32767: y -= 65536
        if z > 32767: z -= 65536

        self.x_raw = x
        self.y_raw = y
        self.z_raw = z

        return x, y, z

    def read_field(self):
        """
        Kalibriertes Magnetfeld in Milligauss lesen.
        
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

    # -----------------------------------------------------------------------
    # Sensorfusion: Neigungskompensiertes Heading (verwendet ADXL345)
    # -----------------------------------------------------------------------

    def has_accelerometer(self):
        """
        Prueft ob der ADXL345 Beschleunigungssensor verfuegbar ist.

        Returns:
            bool - True wenn ADXL345 initialisiert und erreichbar
        """
        return self.accel is not None

    def read_heading_tilt_compensated(self):
        """
        Neigungskompensiertes Heading berechnen (Sensorfusion).

        Kombiniert Magnetometer- und Beschleunigungsdaten, um ein genaues
        Heading zu liefern, auch wenn der Sensor um bis zu ~60 Grad geneigt
        ist. Ohne ADXL345 wird automatisch auf einfaches Heading zurueckgefallen.

        Algorithmus:
            1. Pitch und Roll aus dem ADXL345 berechnen
            2. Magnetfeldvektor mit Rotationsmatrix in die Horizontalebene
               projizieren
            3. Heading aus dem kompensierten Vektor ableiten

        Returns:
            float - Kompassrichtung in Grad (0-360), neigungskompensiert
                    wenn ADXL345 vorhanden, sonst normales Heading
        """
        if self.accel is None:
            return self.read_heading()

        # Lagewinkel aus Beschleunigungssensor (in Radiant)
        ax, ay, az = self.accel.read_accel()
        pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az))
        roll  = math.atan2(ay, az)

        # Magnetfeldrohdaten
        mx, my, mz = self.read_field()

        # Magnetfeldvektor in die Horizontalebene projizieren
        # (Rotationsmatrix fuer Pitch und Roll)
        cos_p = math.cos(pitch)
        sin_p = math.sin(pitch)
        cos_r = math.cos(roll)
        sin_r = math.sin(roll)

        mx_h = mx * cos_p + mz * sin_p
        my_h = mx * sin_r * sin_p + my * cos_r - mz * sin_r * cos_p

        # Heading aus kompensiertem Vektor
        heading = math.degrees(math.atan2(-my_h, mx_h))
        heading += self.declination
        return self._normalize_heading(heading)

    def read_heading_tilt_compensated_direction(self):
        """
        Neigungskompensierte Himmelsrichtung als Text.

        Returns:
            str - Himmelsrichtung (z.B. "N", "NE", "SW", ...)
        """
        heading = self.read_heading_tilt_compensated()
        return self._heading_to_direction(heading)

    def read_all(self):
        """
        Alle verfuegbaren Sensordaten in einem Aufruf lesen.

        Gibt Magnetometer-Daten zurueck; wenn ADXL345 vorhanden, auch
        Beschleunigung, Lagewinkel und das neigungskompensierte Heading.

        Returns:
            dict mit Schluesseln:
                "heading"          - einfaches Heading in Grad
                "direction"        - Himmelsrichtung (Text)
                "mx", "my", "mz"   - Magnetfeld in mG
                "strength"         - Feldstaerke in mG
                Wenn ADXL345 vorhanden, zusaetzlich:
                "heading_tc"       - neigungskompensiertes Heading
                "direction_tc"     - kompensierte Himmelsrichtung
                "ax", "ay", "az"   - Beschleunigung in g
                "pitch"            - Nickwinkel in Grad
                "roll"             - Rollwinkel in Grad
                "tilt"             - Gesamtneigung in Grad
                "is_level"         - True wenn ausreichend waagerecht
        """
        mx, my, mz = self.read_field()
        heading    = self._normalize_heading(
            math.degrees(math.atan2(my, mx)) + self.declination
        )
        strength = math.sqrt(mx * mx + my * my + mz * mz)

        result = {
            "heading"  : heading,
            "direction": self._heading_to_direction(heading),
            "mx"       : mx,
            "my"       : my,
            "mz"       : mz,
            "strength" : strength,
        }

        if self.accel is not None:
            ax, ay, az = self.accel.read_accel()
            pitch = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))
            roll  = math.degrees(math.atan2(ay, az))
            tilt  = self.accel.read_tilt_angle()

            # Neigungskompensiertes Heading (Radiant-Werte direkt berechnen)
            pitch_r = math.radians(pitch)
            roll_r  = math.radians(roll)
            cos_p   = math.cos(pitch_r)
            sin_p   = math.sin(pitch_r)
            cos_r   = math.cos(roll_r)
            sin_r   = math.sin(roll_r)
            mx_h    = mx * cos_p + mz * sin_p
            my_h    = mx * sin_r * sin_p + my * cos_r - mz * sin_r * cos_p
            heading_tc = self._normalize_heading(
                math.degrees(math.atan2(-my_h, mx_h)) + self.declination
            )

            result.update({
                "heading_tc"  : heading_tc,
                "direction_tc": self._heading_to_direction(heading_tc),
                "ax"          : ax,
                "ay"          : ay,
                "az"          : az,
                "pitch"       : pitch,
                "roll"        : roll,
                "tilt"        : tilt,
                "is_level"    : tilt <= 5.0,
            })

        return result
