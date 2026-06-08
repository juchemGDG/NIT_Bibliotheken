"""
NIT Bibliothek: MPU6050 - Beschleunigungssensor und Gyroskop
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-06

Direkte Registeransteuerung nach InvenSense-Datenblatt ohne Fremdbibliotheken.
Unterstuetzt Beschleunigung, Winkelgeschwindigkeit, Temperatur sowie
Lagewinkelberechnung (Pitch, Roll) und Gyroskop-Kalibrierung.
"""

from machine import I2C
from time import sleep_ms
import math


class MPU6050:
    """
    Liest Beschleunigung, Winkelgeschwindigkeit und Temperatur vom MPU6050 aus.

    Unterstuetzte Hardware:
    - InvenSense MPU-6050 Sensor
    - GY-521 und kompatible Breakout-Module

    Schnittstelle: I2C
    Standard-Adresse: 0x68 (AD0=LOW), alternativ 0x69 (AD0=HIGH)
    """

    # I2C Adressen
    ADDRESS     = 0x68  # AD0-Pin LOW (Standard)
    ADDRESS_ALT = 0x69  # AD0-Pin HIGH

    # Register-Adressen
    REG_WHO_AM_I     = 0x75  # Chip-ID (erwartet: 0x68)
    REG_PWR_MGMT_1   = 0x6B  # Power Management 1
    REG_PWR_MGMT_2   = 0x6C  # Power Management 2
    REG_SMPLRT_DIV   = 0x19  # Sample Rate Divider
    REG_CONFIG       = 0x1A  # Konfiguration (DLPF)
    REG_GYRO_CONFIG  = 0x1B  # Gyroskop-Konfiguration
    REG_ACCEL_CONFIG = 0x1C  # Beschleunigungssensor-Konfiguration
    REG_INT_ENABLE   = 0x38  # Interrupt Enable
    REG_INT_STATUS   = 0x3A  # Interrupt Status
    REG_ACCEL_XOUT_H = 0x3B  # Beschleunigungs-Rohdaten (Start, 6 Bytes)
    REG_TEMP_OUT_H   = 0x41  # Temperatur-Rohdaten (2 Bytes)
    REG_GYRO_XOUT_H  = 0x43  # Gyroskop-Rohdaten (Start, 6 Bytes)

    # Chip-ID Wert
    WHO_AM_I_VALUE = 0x68

    # Beschleunigungssensor Messbereiche (ACCEL_CONFIG, Bits 4-3)
    ACCEL_RANGE_2G  = 0x00  # +-2 g,  Empfindlichkeit: 16384 LSB/g
    ACCEL_RANGE_4G  = 0x01  # +-4 g,  Empfindlichkeit:  8192 LSB/g
    ACCEL_RANGE_8G  = 0x02  # +-8 g,  Empfindlichkeit:  4096 LSB/g
    ACCEL_RANGE_16G = 0x03  # +-16 g, Empfindlichkeit:  2048 LSB/g

    # Gyroskop Messbereiche (GYRO_CONFIG, Bits 4-3)
    GYRO_RANGE_250  = 0x00  # +-250  deg/s, Empfindlichkeit: 131.0 LSB/deg/s
    GYRO_RANGE_500  = 0x01  # +-500  deg/s, Empfindlichkeit:  65.5 LSB/deg/s
    GYRO_RANGE_1000 = 0x02  # +-1000 deg/s, Empfindlichkeit:  32.8 LSB/deg/s
    GYRO_RANGE_2000 = 0x03  # +-2000 deg/s, Empfindlichkeit:  16.4 LSB/deg/s

    # Digital Low-Pass Filter Bandbreiten (CONFIG, Bits 2-0)
    DLPF_260HZ = 0x00  # Kein Filter (Gyro: 256 Hz, Accel: 260 Hz)
    DLPF_184HZ = 0x01
    DLPF_94HZ  = 0x02
    DLPF_44HZ  = 0x03
    DLPF_21HZ  = 0x04
    DLPF_10HZ  = 0x05
    DLPF_5HZ   = 0x06

    # Taktquelle (PWR_MGMT_1, Bits 2-0)
    CLOCK_INTERNAL = 0x00  # Interner 8 MHz Oszillator
    CLOCK_GYRO_X   = 0x01  # PLL mit X-Achsen-Gyroskop (empfohlen)
    CLOCK_GYRO_Y   = 0x02  # PLL mit Y-Achsen-Gyroskop
    CLOCK_GYRO_Z   = 0x03  # PLL mit Z-Achsen-Gyroskop

    # Empfindlichkeiten je Messbereich
    _ACCEL_SENSITIVITY = {
        0x00: 16384.0,
        0x01:  8192.0,
        0x02:  4096.0,
        0x03:  2048.0,
    }
    _GYRO_SENSITIVITY = {
        0x00: 131.0,
        0x01:  65.5,
        0x02:  32.8,
        0x03:  16.4,
    }

    def __init__(self, i2c, addr=ADDRESS):
        """
        Initialisiert den MPU6050 Sensor.

        Args:
            i2c:  Initialisiertes I2C Bus Objekt (machine.I2C)
            addr: I2C-Adresse (0x68 oder 0x69)
        """
        self.i2c  = i2c
        self.addr = addr

        self._accel_range = self.ACCEL_RANGE_2G
        self._gyro_range  = self.GYRO_RANGE_250

        # Gyroskop-Kalibrierungsoffsets in deg/s
        self.gyro_offset_x = 0.0
        self.gyro_offset_y = 0.0
        self.gyro_offset_z = 0.0

        # Chip pruefen
        who = self._read_register(self.REG_WHO_AM_I)
        if who != self.WHO_AM_I_VALUE:
            raise RuntimeError(
                f"MPU6050 nicht gefunden! WHO_AM_I: 0x{who:02X}, erwartet: 0x{self.WHO_AM_I_VALUE:02X}"
            )

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

    def _to_signed16(self, data, offset=0):
        """Zwei Bytes Big-Endian als vorzeichenbehaftetes 16-bit Integer lesen."""
        val = (data[offset] << 8) | data[offset + 1]
        return val if val < 32768 else val - 65536

    def _initialize(self):
        """Sensor zuruecksetzen, aus Sleep-Mode holen und Standardwerte setzen."""
        # Vollstaendiger Software-Reset
        self._write_register(self.REG_PWR_MGMT_1, 0x80)
        sleep_ms(100)

        # PLL mit X-Gyroskop als Taktquelle (stabiler als interner Oszillator)
        self._write_register(self.REG_PWR_MGMT_1, self.CLOCK_GYRO_X)
        sleep_ms(10)

        # Abtastrate: Gyro-Takt / (1 + SMPLRT_DIV). Mit DLPF aktiv = 1 kHz Gyro-Takt.
        # Divider 9 -> 100 Hz Abtastrate
        self._write_register(self.REG_SMPLRT_DIV, 0x09)

        # DLPF 44 Hz: guter Kompromiss aus Rauschunterdrueckung und Reaktionszeit
        self._write_register(self.REG_CONFIG, self.DLPF_44HZ)

        # Standardmessbereiche
        self._write_register(self.REG_GYRO_CONFIG,  self._gyro_range  << 3)
        self._write_register(self.REG_ACCEL_CONFIG, self._accel_range << 3)
        sleep_ms(10)

    # -----------------------------------------------------------------------
    # Konfiguration
    # -----------------------------------------------------------------------

    def set_accel_range(self, range_val):
        """
        Messbereich des Beschleunigungssensors einstellen.

        Args:
            range_val: ACCEL_RANGE_2G, ACCEL_RANGE_4G, ACCEL_RANGE_8G, ACCEL_RANGE_16G
        """
        self._accel_range = range_val
        self._write_register(self.REG_ACCEL_CONFIG, range_val << 3)

    def set_gyro_range(self, range_val):
        """
        Messbereich des Gyroskops einstellen.

        Args:
            range_val: GYRO_RANGE_250, GYRO_RANGE_500, GYRO_RANGE_1000, GYRO_RANGE_2000
        """
        self._gyro_range = range_val
        self._write_register(self.REG_GYRO_CONFIG, range_val << 3)

    def set_dlpf(self, dlpf):
        """
        Digitales Tiefpassfilter konfigurieren.

        Args:
            dlpf: DLPF_260HZ, DLPF_184HZ, DLPF_94HZ, DLPF_44HZ, DLPF_21HZ, DLPF_10HZ, DLPF_5HZ
        """
        config = self._read_register(self.REG_CONFIG)
        self._write_register(self.REG_CONFIG, (config & 0xF8) | (dlpf & 0x07))

    def set_sample_rate_divider(self, divider):
        """
        Sample-Rate-Teiler setzen. Abtastrate = 1000 Hz / (1 + divider) bei aktivem DLPF.

        Args:
            divider: 0-255 (0 = 1 kHz, 9 = 100 Hz, 99 = 10 Hz)
        """
        self._write_register(self.REG_SMPLRT_DIV, divider & 0xFF)

    # -----------------------------------------------------------------------
    # Rohdaten
    # -----------------------------------------------------------------------

    def read_accel_raw(self):
        """
        Rohdaten des Beschleunigungssensors lesen.

        Returns:
            Tuple (x, y, z) - ADC-Rohwerte (signed 16-bit)
        """
        data = self._read_registers(self.REG_ACCEL_XOUT_H, 6)
        return (
            self._to_signed16(data, 0),
            self._to_signed16(data, 2),
            self._to_signed16(data, 4),
        )

    def read_gyro_raw(self):
        """
        Rohdaten des Gyroskops lesen.

        Returns:
            Tuple (x, y, z) - ADC-Rohwerte (signed 16-bit)
        """
        data = self._read_registers(self.REG_GYRO_XOUT_H, 6)
        return (
            self._to_signed16(data, 0),
            self._to_signed16(data, 2),
            self._to_signed16(data, 4),
        )

    def read_temp_raw(self):
        """
        Rohwert des Temperatursensors lesen.

        Returns:
            int - Rohwert (signed 16-bit)
        """
        data = self._read_registers(self.REG_TEMP_OUT_H, 2)
        return self._to_signed16(data, 0)

    # -----------------------------------------------------------------------
    # Messwerte (skaliert)
    # -----------------------------------------------------------------------

    def read_accel(self):
        """
        Beschleunigung in g lesen.
        1 g entspricht ca. 9.81 m/s².

        Returns:
            Tuple (ax, ay, az) - Beschleunigung in g
        """
        x, y, z = self.read_accel_raw()
        sens = self._ACCEL_SENSITIVITY[self._accel_range]
        return x / sens, y / sens, z / sens

    def read_accel_ms2(self):
        """
        Beschleunigung in m/s² lesen.

        Returns:
            Tuple (ax, ay, az) - Beschleunigung in m/s²
        """
        ax, ay, az = self.read_accel()
        return ax * 9.81, ay * 9.81, az * 9.81

    def read_gyro(self):
        """
        Winkelgeschwindigkeit in deg/s lesen (mit Kalibrierungs-Offset korrigiert).

        Returns:
            Tuple (gx, gy, gz) - Winkelgeschwindigkeit in deg/s
        """
        x, y, z = self.read_gyro_raw()
        sens = self._GYRO_SENSITIVITY[self._gyro_range]
        return (
            x / sens - self.gyro_offset_x,
            y / sens - self.gyro_offset_y,
            z / sens - self.gyro_offset_z,
        )

    def read_temperature(self):
        """
        Gehaeuse-Temperatur des Sensors lesen.
        Hinweis: Gibt die Chip-Temperatur an, nicht die Umgebungstemperatur.

        Returns:
            float - Temperatur in degC
        """
        return self.read_temp_raw() / 340.0 + 36.53

    def read_all(self):
        """
        Alle Messwerte in einem einzigen I2C-Lesevorgang (14 Bytes) lesen.

        Returns:
            dict mit Schluesseln:
                "ax", "ay", "az"  - Beschleunigung in g
                "gx", "gy", "gz"  - Winkelgeschwindigkeit in deg/s
                "temp"            - Temperatur in degC
        """
        data   = self._read_registers(self.REG_ACCEL_XOUT_H, 14)
        a_sens = self._ACCEL_SENSITIVITY[self._accel_range]
        g_sens = self._GYRO_SENSITIVITY[self._gyro_range]

        ax = self._to_signed16(data,  0) / a_sens
        ay = self._to_signed16(data,  2) / a_sens
        az = self._to_signed16(data,  4) / a_sens
        temp = self._to_signed16(data, 6) / 340.0 + 36.53
        gx = self._to_signed16(data,  8) / g_sens - self.gyro_offset_x
        gy = self._to_signed16(data, 10) / g_sens - self.gyro_offset_y
        gz = self._to_signed16(data, 12) / g_sens - self.gyro_offset_z

        return {"ax": ax, "ay": ay, "az": az,
                "gx": gx, "gy": gy, "gz": gz,
                "temp": temp}

    # -----------------------------------------------------------------------
    # Lagewinkel (aus Beschleunigungssensor)
    # -----------------------------------------------------------------------

    def read_pitch(self):
        """
        Nickwinkel (Pitch) aus dem Beschleunigungssensor berechnen.
        Nur bei ruhiger Lage exakt; bei Erschuetterungen kurzzeitig verzerrt.

        Returns:
            float - Pitch in Grad
                     0°  = waagerecht
                    +90° = Vorderseite hoch
                    -90° = Vorderseite unten
        """
        ax, ay, az = self.read_accel()
        return math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))

    def read_roll(self):
        """
        Rollwinkel aus dem Beschleunigungssensor berechnen.

        Returns:
            float - Roll in Grad
                     0°  = waagerecht
                    +90° = rechte Seite nach unten
                    -90° = linke Seite nach unten
        """
        ax, ay, az = self.read_accel()
        return math.degrees(math.atan2(ay, az))

    def read_pitch_roll(self):
        """
        Pitch und Roll mit einer einzigen I2C-Messung bestimmen.

        Returns:
            Tuple (pitch, roll) in Grad
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
        Lage des Sensors als lesbaren Text.

        Returns:
            str - eine von: "waagerecht", "leicht geneigt", "stark geneigt", "hochkant"
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

    def calibrate_gyro(self, samples=200):
        """
        Automatische Gyroskop-Kalibrierung durch Mittelwertbildung im Stillstand.
        Sensor muss waehrend der Kalibrierung absolut ruhig liegen!

        Nach der Kalibrierung liefert read_gyro() bei ruhigem Sensor (0, 0, 0).

        Args:
            samples: Anzahl der Mittelwertmessungen (mehr = genauer, typisch 100-500)
        """
        print(f"Gyroskop kalibrieren ({samples} Messungen)...")
        print("Sensor ruhig und bewegungslos halten!")

        self.gyro_offset_x = 0.0
        self.gyro_offset_y = 0.0
        self.gyro_offset_z = 0.0

        sum_x = sum_y = sum_z = 0.0
        sens = self._GYRO_SENSITIVITY[self._gyro_range]

        for _ in range(samples):
            x, y, z = self.read_gyro_raw()
            sum_x += x / sens
            sum_y += y / sens
            sum_z += z / sens

        self.gyro_offset_x = sum_x / samples
        self.gyro_offset_y = sum_y / samples
        self.gyro_offset_z = sum_z / samples

        print("Kalibrierung abgeschlossen!")
        print(f"  Offsets: X={self.gyro_offset_x:.3f}, Y={self.gyro_offset_y:.3f}, Z={self.gyro_offset_z:.3f} deg/s")

    def set_gyro_offset(self, offset_x, offset_y, offset_z):
        """
        Gyroskop-Offsets manuell setzen (z.B. nach gespeicherter Kalibrierung).

        Args:
            offset_x: X-Offset in deg/s
            offset_y: Y-Offset in deg/s
            offset_z: Z-Offset in deg/s
        """
        self.gyro_offset_x = offset_x
        self.gyro_offset_y = offset_y
        self.gyro_offset_z = offset_z

    # -----------------------------------------------------------------------
    # Power Management
    # -----------------------------------------------------------------------

    def sleep(self):
        """Sensor in den Sleep-Mode versetzen (niedrigster Stromverbrauch)."""
        reg = self._read_register(self.REG_PWR_MGMT_1)
        self._write_register(self.REG_PWR_MGMT_1, reg | 0x40)

    def wake(self):
        """Sensor aus dem Sleep-Mode aufwecken."""
        reg = self._read_register(self.REG_PWR_MGMT_1)
        self._write_register(self.REG_PWR_MGMT_1, reg & 0xBF)
        sleep_ms(10)

    def reset(self):
        """Software-Reset und Neuinitialisierung des Sensors."""
        self._initialize()

    # -----------------------------------------------------------------------
    # Diagnose
    # -----------------------------------------------------------------------

    def get_who_am_i(self):
        """
        WHO_AM_I-Register lesen (Verifikation: MPU6050 gibt 0x68 zurueck).

        Returns:
            int - Chip-ID
        """
        return self._read_register(self.REG_WHO_AM_I)

    def is_available(self):
        """
        Pruefen ob MPU6050 antwortet und korrekte ID liefert.

        Returns:
            bool - True wenn Sensor gefunden und identifiziert
        """
        try:
            return self.get_who_am_i() == self.WHO_AM_I_VALUE
        except OSError:
            return False

    def __str__(self):
        """String-Repraesentation mit aktuellen Messwerten."""
        try:
            d = self.read_all()
            return (
                f"MPU6050 @ 0x{self.addr:02X}: "
                f"a=({d['ax']:.2f},{d['ay']:.2f},{d['az']:.2f})g "
                f"g=({d['gx']:.1f},{d['gy']:.1f},{d['gz']:.1f})deg/s "
                f"T={d['temp']:.1f}C"
            )
        except Exception:
            return f"MPU6050 @ 0x{self.addr:02X}"
