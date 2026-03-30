"""
NIT Bibliothek: AS7262 - 6-Kanal Spektralsensor ueber I2C
Fuer ESP32 mit MicroPython

Version:    2.0.0
Autor:      Volker Rust / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Steuert den AS7262 Spektralsensor ueber I2C an. Der Sensor misst
Lichtintensitaeten in sechs Spektralkanaelen (Violett bis Rot).
Die Kommunikation erfolgt ueber ein virtuelles Registerinterface.
"""

from machine import I2C
import time


class AS7262:
    """
    Liest 6 Spektralkanaele (Violett, Blau, Gruen, Gelb, Orange, Rot)
    vom AS7262 ueber I2C aus.

    Unterstuetzte Hardware:
    - AS7262 (6-Kanal sichtbares Licht)

    Schnittstelle: I2C
    """

    # ---------------------------------------------------------------
    # I2C-Adresse und Register
    # ---------------------------------------------------------------
    _ADDR = 0x49

    # Virtuelles Register-Interface:
    # Man schreibt/liest nicht direkt, sondern ueber STATUS/WRITE/READ.
    _STATUS_REG = 0x00
    _WRITE_REG  = 0x01
    _READ_REG   = 0x02

    # Virtuelle Register des AS7262
    _HW_VERSION     = 0x00
    _CONTROL_SETUP  = 0x04
    _INT_TIME       = 0x05
    _DEVICE_TEMP    = 0x06
    _LED_CONTROL    = 0x07

    # Rohdaten-Register (je 2 Bytes, High + Low)
    _RAW_V_HIGH = 0x08  # Violett (450 nm)
    _RAW_B_HIGH = 0x0A  # Blau    (500 nm)
    _RAW_G_HIGH = 0x0C  # Gruen   (550 nm)
    _RAW_Y_HIGH = 0x0E  # Gelb    (570 nm)
    _RAW_O_HIGH = 0x10  # Orange  (600 nm)
    _RAW_R_HIGH = 0x12  # Rot     (650 nm)

    # Kalibrierte Daten (je 4 Bytes float, IEEE 754)
    _CAL_V = 0x14
    _CAL_B = 0x18
    _CAL_G = 0x1C
    _CAL_Y = 0x20
    _CAL_O = 0x24
    _CAL_R = 0x28

    # Kanalnamen in Reihenfolge des Sensors
    KANALNAMEN = ('violett', 'blau', 'gruen', 'gelb', 'orange', 'rot')

    # ---------------------------------------------------------------
    # Initialisierung
    # ---------------------------------------------------------------

    def __init__(self, i2c, led='messen',
                 integrationszeit=50, gain=1):
        """
        Initialisiert den AS7262 Spektralsensor.

        Args:
            i2c:    Initialisiertes I2C-Objekt.
            led:    LED-Standardmodus fuer Messungen:
                - 'messen' = LED nur waehrend Messung (Standard)
                - 'aus' = LED bleibt aus
                - 'an' = LED bleibt dauerhaft ein
            integrationszeit: Messzeit in Einheiten von 2.8 ms (1-255).
                              Hoehere Werte = laengere Messung, weniger Rauschen.
            gain:   Verstaerkung: 0 = 1x, 1 = 3.7x, 2 = 16x, 3 = 64x
        """
        if not isinstance(i2c, I2C):
            raise TypeError("i2c muss ein initialisiertes machine.I2C Objekt sein")
        self._i2c = i2c

        # Pruefen, ob der Sensor antwortet
        geraete = self._i2c.scan()
        if self._ADDR not in geraete:
            raise OSError("AS7262 nicht gefunden auf I2C-Adresse 0x{:02X}".format(
                self._ADDR))

        # Sensor konfigurieren
        self.set_integrationszeit(integrationszeit)
        self.set_gain(gain)
        self._led_standardmodus = self._normalisiere_led_modus(led)
        if self._led_standardmodus == 'an':
            self.set_led(True)
        else:
            self.set_led(False)

    # ---------------------------------------------------------------
    # Virtuelles Register-Interface
    # Der AS7262 nutzt ein spezielles Protokoll:
    # Man liest/schreibt NICHT direkt auf I2C-Register,
    # sondern ueber einen Status/Read/Write-Mechanismus.
    # ---------------------------------------------------------------

    def _warte_auf_schreibbereit(self):
        """Wartet, bis der Sensor bereit ist, ein Byte zu empfangen."""
        for _ in range(100):
            status = self._i2c.readfrom_mem(self._ADDR, self._STATUS_REG, 1)[0]
            # Bit 1 = TX_VALID: Wenn 0, ist der Schreibpuffer frei
            if (status & 0x02) == 0:
                return
            time.sleep_ms(1)
        raise OSError("AS7262 Schreibbereitschaft Timeout")

    def _warte_auf_lesebereit(self):
        """Wartet, bis ein Byte zum Lesen bereit liegt."""
        for _ in range(100):
            status = self._i2c.readfrom_mem(self._ADDR, self._STATUS_REG, 1)[0]
            # Bit 0 = RX_VALID: Wenn 1, liegt ein Byte bereit
            if (status & 0x01) != 0:
                return
            time.sleep_ms(1)
        raise OSError("AS7262 Lesebereitschaft Timeout")

    def _virt_read(self, reg):
        """
        Liest ein Byte aus einem virtuellen Register.

        Der Ablauf:
        1) Warten bis Schreibpuffer frei
        2) Registeradresse in WRITE_REG schreiben
        3) Warten bis Antwort bereit
        4) Byte aus READ_REG lesen
        """
        self._warte_auf_schreibbereit()
        self._i2c.writeto_mem(self._ADDR, self._WRITE_REG, bytes([reg]))
        self._warte_auf_lesebereit()
        return self._i2c.readfrom_mem(self._ADDR, self._READ_REG, 1)[0]

    def _virt_write(self, reg, wert):
        """
        Schreibt ein Byte in ein virtuelles Register.

        Der Ablauf:
        1) Warten bis Schreibpuffer frei
        2) Registeradresse mit gesetztem Bit 7 schreiben
        3) Warten bis Schreibpuffer wieder frei
        4) Datenbyte schreiben
        """
        self._warte_auf_schreibbereit()
        self._i2c.writeto_mem(self._ADDR, self._WRITE_REG, bytes([reg | 0x80]))
        self._warte_auf_schreibbereit()
        self._i2c.writeto_mem(self._ADDR, self._WRITE_REG, bytes([wert]))

    # ---------------------------------------------------------------
    # Konfiguration
    # ---------------------------------------------------------------

    def set_integrationszeit(self, wert):
        """
        Stellt die Integrationszeit ein.

        Die tatsaechliche Messzeit in Millisekunden betraegt: wert * 2.8 ms.
        Hoehere Werte ergeben stabilere Messungen, brauchen aber laenger.

        Args:
            wert: 1 bis 255 (Standard: 50 = ca. 140 ms Messzeit)
        """
        if wert < 1 or wert > 255:
            raise ValueError("Integrationszeit muss zwischen 1 und 255 liegen")
        self._integrationszeit = wert
        self._virt_write(self._INT_TIME, wert)

    def set_gain(self, gain):
        """
        Stellt die Verstaerkung ein.

        Hoehere Verstaerkung macht den Sensor empfindlicher,
        kann aber bei hellem Licht zu Uebersteuerung fuehren.

        Args:
            gain: 0 = 1x, 1 = 3.7x, 2 = 16x, 3 = 64x
        """
        if gain not in (0, 1, 2, 3):
            raise ValueError("Gain muss 0, 1, 2 oder 3 sein")
        self._gain = gain
        # Gain steht in Bits 4:5 des CONTROL_SETUP-Registers
        ctrl = self._virt_read(self._CONTROL_SETUP)
        ctrl = (ctrl & 0xCF) | ((gain & 0x03) << 4)
        self._virt_write(self._CONTROL_SETUP, ctrl)

    def set_led(self, an):
        """
        Schaltet die eingebaute LED des Sensors ein oder aus.

        Die LED beleuchtet das Messobjekt und verbessert die Ergebnisse
        bei kurzen Abstaenden deutlich.

        Diese Methode ist fuer manuelle Steuerung (Dauerlicht)
        gedacht. Fuer LED nur waehrend Messungen den Konstruktor mit
        led='messen' verwenden.

        Args:
            an: True = LED ein, False = LED aus
        """
        led_reg = self._virt_read(self._LED_CONTROL)
        if an:
            led_reg |= 0x08   # Bit 3 = LED Enable
        else:
            led_reg &= ~0x08
        self._virt_write(self._LED_CONTROL, led_reg)

    def _normalisiere_led_modus(self, led):
        """
        Vereinheitlicht LED-Modi auf: 'messen', 'an', 'aus'.

        Erlaubt bewusst auch bool fuer Rueckwaertskompatibilitaet.
        """
        if led is True:
            return 'messen'
        if led is False:
            return 'aus'

        if isinstance(led, str):
            modus = led.lower()
            if modus in ('messen', 'an', 'aus'):
                return modus

        raise ValueError("LED-Modus muss 'messen', 'an' oder 'aus' sein")

    def _mess_led_start(self, led=None):
        """
        Aktiviert den gewuenschten LED-Modus fuer eine Messung.

        Returns:
            int|None: Vorheriger LED-Registerwert fuer Restore,
                      oder None wenn kein Restore noetig ist.
        """
        if led is None:
            modus = self._led_standardmodus
        else:
            modus = self._normalisiere_led_modus(led)

        if modus == 'aus':
            self.set_led(False)
            return None

        if modus == 'an':
            self.set_led(True)
            return None

        led_reg_vorher = self._virt_read(self._LED_CONTROL)
        if (led_reg_vorher & 0x08) == 0:
            self._virt_write(self._LED_CONTROL, led_reg_vorher | 0x08)
        return led_reg_vorher

    def _mess_led_ende(self, led_reg_vorher):
        """Stellt den LED-Zustand nach einer Messung wieder her."""
        if led_reg_vorher is not None:
            self._virt_write(self._LED_CONTROL, led_reg_vorher)

    def temperatur(self):
        """
        Liest die Sensortemperatur in Grad Celsius.

        Returns:
            int: Temperatur in Grad Celsius
        """
        return self._virt_read(self._DEVICE_TEMP)

    # ---------------------------------------------------------------
    # Messung starten
    # ---------------------------------------------------------------

    def _starte_messung(self):
        """
        Startet eine Einzelmessung (Mode 3 = One-Shot).

        Nach dem Start muss man warten, bis DATA_RDY gesetzt ist.
        """
        # CONTROL_SETUP: Bank=0, Gain beibehalten, Modus=3 (One-Shot)
        ctrl = self._virt_read(self._CONTROL_SETUP)
        # Modus in Bits 2:3 setzen (Modus 3 = One-Shot alle 6 Kanaele)
        ctrl = (ctrl & 0xF3) | (0x03 << 2)
        self._virt_write(self._CONTROL_SETUP, ctrl)

    def _warte_auf_daten(self):
        """Wartet, bis die Messung abgeschlossen ist (DATA_RDY Bit)."""
        # Maximale Wartezeit: Integrationszeit * 2.8 ms * 2 (Sicherheit)
        max_ms = int(self._integrationszeit * 2.8 * 2) + 100
        for _ in range(max_ms):
            ctrl = self._virt_read(self._CONTROL_SETUP)
            if ctrl & 0x02:  # Bit 1 = DATA_RDY
                return
            time.sleep_ms(1)
        raise OSError("AS7262 Messung Timeout")

    # ---------------------------------------------------------------
    # Rohdaten lesen (Integer-Werte, 16 Bit pro Kanal)
    # ---------------------------------------------------------------

    def _lies_rohkanal(self, reg_high):
        """Liest einen 16-Bit-Rohwert (High-Byte zuerst)."""
        high = self._virt_read(reg_high)
        low = self._virt_read(reg_high + 1)
        return (high << 8) | low

    def messen_roh(self, led=None):
        """
        Fuehrt eine Messung durch und gibt die 6 Rohwerte zurueck.

        Die Rohwerte sind 16-Bit-Zahlen ohne physikalische Einheit.
        Gut geeignet fuer ML-Training, da sie den vollen Wertebereich nutzen.

        Args:
            led: Optionaler LED-Modus nur fuer diese Messung:
                 'messen', 'aus' oder 'an'.

        Returns:
            dict: Rohwerte fuer 'violett', 'blau', 'gruen',
                  'gelb', 'orange', 'rot'
        """
        led_reg_vorher = self._mess_led_start(led)
        try:
            self._starte_messung()
            self._warte_auf_daten()

            register = [self._RAW_V_HIGH, self._RAW_B_HIGH, self._RAW_G_HIGH,
                         self._RAW_Y_HIGH, self._RAW_O_HIGH, self._RAW_R_HIGH]

            ergebnis = {}
            for name, reg in zip(self.KANALNAMEN, register):
                ergebnis[name] = self._lies_rohkanal(reg)
            return ergebnis
        finally:
            self._mess_led_ende(led_reg_vorher)

    def messen_roh_liste(self, led=None):
        """
        Wie messen_roh(), gibt aber eine Liste statt dict zurueck.

        Reihenfolge: [violett, blau, gruen, gelb, orange, rot]
        Praktisch fuer ML-Algorithmen, die Feature-Listen erwarten.

        Args:
            led: Optionaler LED-Modus nur fuer diese Messung.

        Returns:
            list: 6 Rohwerte als Integer-Liste
        """
        roh = self.messen_roh(led=led)
        return [roh[name] for name in self.KANALNAMEN]

    # ---------------------------------------------------------------
    # Kalibrierte Daten lesen (Float-Werte, IEEE 754)
    # ---------------------------------------------------------------

    def _lies_float(self, reg):
        """
        Liest einen 32-Bit-Float aus vier aufeinanderfolgenden Registern.

        Der AS7262 speichert kalibrierte Werte als IEEE-754-Floats.
        """
        import struct
        raw = bytes([self._virt_read(reg + i) for i in range(4)])
        return struct.unpack('>f', raw)[0]

    def messen_kalibriert(self, led=None):
        """
        Fuehrt eine Messung durch und gibt die kalibrierten Float-Werte zurueck.

        Diese Werte sind vom Sensor intern korrigiert und haben die
        Einheit uW/cm2. Sie sind besser vergleichbar zwischen verschiedenen
        Sensoren, aber fuer ML-Training reichen oft die Rohwerte.

        Args:
            led: Optionaler LED-Modus nur fuer diese Messung:
                 'messen', 'aus' oder 'an'.

        Returns:
            dict: Kalibrierte Werte fuer alle 6 Kanaele
        """
        led_reg_vorher = self._mess_led_start(led)
        try:
            self._starte_messung()
            self._warte_auf_daten()

            register = [self._CAL_V, self._CAL_B, self._CAL_G,
                         self._CAL_Y, self._CAL_O, self._CAL_R]

            ergebnis = {}
            for name, reg in zip(self.KANALNAMEN, register):
                ergebnis[name] = round(self._lies_float(reg), 2)
            return ergebnis
        finally:
            self._mess_led_ende(led_reg_vorher)

    def messen_kalibriert_liste(self, led=None):
        """
        Wie messen_kalibriert(), gibt aber eine Liste zurueck.

        Reihenfolge: [violett, blau, gruen, gelb, orange, rot]

        Args:
            led: Optionaler LED-Modus nur fuer diese Messung.

        Returns:
            list: 6 kalibrierte Float-Werte
        """
        kal = self.messen_kalibriert(led=led)
        return [kal[name] for name in self.KANALNAMEN]

    # ---------------------------------------------------------------
    # Hilfsfunktionen
    # ---------------------------------------------------------------

    def dominanter_kanal(self, led=None):
        """
        Gibt den Kanal mit dem hoechsten Rohwert zurueck.

        Args:
            led: Optionaler LED-Modus nur fuer diese Messung.

        Returns:
            str: Kanalname ('violett', 'blau', 'gruen', 'gelb', 'orange', 'rot')
        """
        roh = self.messen_roh(led=led)
        return max(roh, key=roh.get)
