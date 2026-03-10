"""
NIT Bibliothek: RTC - Echtzeituhr (Real Time Clock)
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Volker Rust
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Unterstuetzt DS1307 und DS3231 Echtzeituhr-Module ueber I2C.
Automatische Chip-Auswahl ueber Factory-Funktion RTC().
"""

from machine import I2C, Pin
import time


# ============================================================================
# Hilfsfunktionen
# ============================================================================

def _bcd_zu_dez(bcd):
    """Konvertiert BCD-Wert in Dezimalzahl"""
    return (bcd >> 4) * 10 + (bcd & 0x0F)


def _dez_zu_bcd(dez):
    """Konvertiert Dezimalzahl in BCD-Wert"""
    return ((dez // 10) << 4) | (dez % 10)


# Englische Monatsnamen (Kurzform)
_MONATE = ('Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun',
           'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez')

# Deutsche Tagesnamen (Kurzform, 1=Montag)
_TAGE = ('Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So')


# ============================================================================
# Basisklasse
# ============================================================================

class RTCBasis:
    """
    Basisklasse fuer Echtzeituhr-Module (RTC).

    Unterstuetzte Hardware:
    - DS1307
    - DS3231

    Schnittstelle: I2C
    """

    def __init__(self, i2c=None, addr=0x68, scl=22, sda=21, i2c_id=0):
        """
        Initialisiert die RTC.

        Args:
            i2c: Optionales I2C-Objekt. Falls None, wird eines erstellt.
            addr: I2C-Adresse (Standard: 0x68)
            scl: GPIO-Pin fuer SCL (Standard: 22)
            sda: GPIO-Pin fuer SDA (Standard: 21)
            i2c_id: I2C-Bus-ID (Standard: 0)
        """
        if i2c is None:
            self.i2c = I2C(i2c_id, scl=Pin(scl), sda=Pin(sda), freq=100000)
        else:
            self.i2c = i2c
        self.addr = addr

        # Pruefen ob Geraet erreichbar
        geraete = self.i2c.scan()
        if self.addr not in geraete:
            raise RuntimeError(
                "RTC nicht gefunden an Adresse 0x{:02X}. "
                "Gefundene Geraete: {}".format(
                    self.addr,
                    ['0x{:02X}'.format(g) for g in geraete]))

    # --- I2C-Zugriff --------------------------------------------------------

    def _lese_register(self, reg, laenge=1):
        """Liest Bytes ab einem Register"""
        return self.i2c.readfrom_mem(self.addr, reg, laenge)

    def _schreibe_register(self, reg, daten):
        """Schreibt Bytes ab einem Register"""
        self.i2c.writeto_mem(self.addr, reg, daten)

    def _lese_byte(self, reg):
        """Liest ein einzelnes Byte"""
        return self._lese_register(reg, 1)[0]

    def _schreibe_byte(self, reg, wert):
        """Schreibt ein einzelnes Byte"""
        self._schreibe_register(reg, bytes([wert]))

    # --- Kernfunktionen -----------------------------------------------------

    def aktuelleDaten(self):
        """
        Liest alle aktuellen Datums- und Zeitdaten von der RTC.

        Returns:
            dict: Woerterbuch mit:
                - 'sekunden': int (0-59)
                - 'minuten': int (0-59)
                - 'stunden': int (0-23)
                - 'wochentag': int (1-7, 1=Montag)
                - 'tag': int (1-31)
                - 'monat': int (1-12)
                - 'jahr': int (2000-2099)
        """
        raise NotImplementedError("Muss in Unterklasse implementiert werden")

    def set(self, jahr=None, monat=None, tag=None,
            stunden=None, minuten=None, sekunden=None, wochentag=None):
        """
        Stellt die RTC auf die angegebenen Werte.
        Nicht angegebene Werte bleiben unveraendert.

        Args:
            jahr: Jahr (2000-2099)
            monat: Monat (1-12)
            tag: Tag (1-31)
            stunden: Stunde (0-23)
            minuten: Minute (0-59)
            sekunden: Sekunde (0-59)
            wochentag: Wochentag (1=Mo, 7=So)
        """
        raise NotImplementedError("Muss in Unterklasse implementiert werden")

    # --- Einzelwerte lesen --------------------------------------------------

    def stunden(self):
        """Gibt die aktuelle Stunde zurueck (0-23)"""
        return self.aktuelleDaten()['stunden']

    def minuten(self):
        """Gibt die aktuelle Minute zurueck (0-59)"""
        return self.aktuelleDaten()['minuten']

    def sekunden(self):
        """Gibt die aktuelle Sekunde zurueck (0-59)"""
        return self.aktuelleDaten()['sekunden']

    def tag(self):
        """Gibt den aktuellen Tag zurueck (1-31)"""
        return self.aktuelleDaten()['tag']

    def monat(self):
        """Gibt den aktuellen Monat zurueck (1-12)"""
        return self.aktuelleDaten()['monat']

    def jahr(self):
        """Gibt das aktuelle Jahr zurueck (z.B. 2026)"""
        return self.aktuelleDaten()['jahr']

    def wochentag(self):
        """Gibt den aktuellen Wochentag zurueck (1=Mo, 7=So)"""
        return self.aktuelleDaten()['wochentag']

    def wochentagName(self):
        """Gibt den deutschen Kurznamen des Wochentags zurueck (Mo-So)"""
        return _TAGE[self.wochentag() - 1]

    def monatsName(self):
        """Gibt den deutschen Kurznamen des Monats zurueck (Jan-Dez)"""
        return _MONATE[self.monat() - 1]

    # --- Formatierung -------------------------------------------------------

    def toString(self, fmt):
        """
        Gibt die aktuelle Zeit als formatierten String zurueck.

        Unterstuetzte Platzhalter:
            hh   - Stunde mit fuehrender Null (00-23)
            mm   - Minute mit fuehrender Null (00-59)
            ss   - Sekunde mit fuehrender Null (00-59)
            YYYY - Jahr vierstellig (z.B. 2026)
            YY   - Jahr zweistellig (00-99)
            MM   - Monat mit fuehrender Null (01-12)
            MMM  - Deutscher Monatsname (Jan-Dez)
            DD   - Tag mit fuehrender Null (01-31)
            DDD  - Deutscher Tagesname (Mo-So)

        Beispiel:
            rtc.toString("DD.MM.YYYY hh:mm:ss")
            -> "10.03.2026 14:30:00"

        Args:
            fmt: Format-String mit Platzhaltern

        Returns:
            str: Formatierter Datums-/Zeitstring
        """
        d = self.aktuelleDaten()

        # Token-Tabelle: laengste zuerst, damit z.B. YYYY vor YY und MMM vor MM
        tokens = [
            ('YYYY', "{:04d}".format(d['jahr'])),
            ('MMM',  _MONATE[d['monat'] - 1]),
            ('DDD',  _TAGE[d['wochentag'] - 1]),
            ('YY',   "{:02d}".format(d['jahr'] % 100)),
            ('MM',   "{:02d}".format(d['monat'])),
            ('DD',   "{:02d}".format(d['tag'])),
            ('hh',   "{:02d}".format(d['stunden'])),
            ('mm',   "{:02d}".format(d['minuten'])),
            ('ss',   "{:02d}".format(d['sekunden'])),
        ]

        ergebnis = []
        i = 0
        while i < len(fmt):
            gefunden = False
            for token, wert in tokens:
                if fmt[i:i + len(token)] == token:
                    ergebnis.append(wert)
                    i += len(token)
                    gefunden = True
                    break
            if not gefunden:
                ergebnis.append(fmt[i])
                i += 1

        return ''.join(ergebnis)

    # --- Setzen ueber String ------------------------------------------------

    def setVonString(self, zeitstring):
        """
        Stellt die RTC aus einem String im Format 'YYYY-MM-DD hh:mm:ss'.

        Args:
            zeitstring: Datums-/Zeitstring (z.B. '2026-03-10 14:30:00')
        """
        teile = zeitstring.strip().split(' ')
        datum = teile[0].split('-')
        zeit = teile[1].split(':') if len(teile) > 1 else ['0', '0', '0']

        j = int(datum[0])
        m = int(datum[1])
        t = int(datum[2])
        h = int(zeit[0])
        mi = int(zeit[1])
        s = int(zeit[2]) if len(zeit) > 2 else 0

        wt = self._berechneWochentag(j, m, t)
        self.set(jahr=j, monat=m, tag=t, stunden=h, minuten=mi,
                 sekunden=s, wochentag=wt)

    # --- Serielles Stellen --------------------------------------------------

    def stellenSeriell(self):
        """
        Ermoeglicht das Stellen der Uhr ueber die serielle Schnittstelle.
        Erwartet Eingabe im Format: YYYY-MM-DD hh:mm:ss

        Beispiel im Seriellen Monitor:
            2026-03-10 14:30:00

        Returns:
            bool: True wenn erfolgreich gestellt
        """
        print("=== RTC stellen ===")
        print("Bitte Datum und Uhrzeit eingeben im Format:")
        print("YYYY-MM-DD hh:mm:ss")
        print("Beispiel: 2026-03-10 14:30:00")
        print()

        eingabe = input("Eingabe: ").strip()

        if not eingabe:
            print("Keine Eingabe. Abbruch.")
            return False

        try:
            self.setVonString(eingabe)
            print("RTC gestellt auf: " + self.toString("DD.MM.YYYY hh:mm:ss"))
            return True
        except Exception as e:
            print("Fehler: {}".format(e))
            print("Format muss sein: YYYY-MM-DD hh:mm:ss")
            return False

    # --- Interaktives Stellen mit Display und Tastern -----------------------

    def stellenInteraktiv(self, display, pin_hoch, pin_runter, pin_enter):
        """
        Stellt die Uhr interaktiv mit einem Display und 3 Tastern.
        Kompatibel mit LCD- und OLED-Objekten der NIT-Bibliotheken.

        Args:
            display: Display-Objekt (LCD oder OLED) mit print/clear Methoden
            pin_hoch: GPIO-Pin-Nummer fuer Taster 'Hoch'
            pin_runter: GPIO-Pin-Nummer fuer Taster 'Runter'
            pin_enter: GPIO-Pin-Nummer fuer Taster 'Enter/Bestaetigen'
        """
        btn_hoch = Pin(pin_hoch, Pin.IN, Pin.PULL_DOWN)
        btn_runter = Pin(pin_runter, Pin.IN, Pin.PULL_DOWN)
        btn_enter = Pin(pin_enter, Pin.IN, Pin.PULL_DOWN)

        d = self.aktuelleDaten()
        werte = [d['tag'], d['monat'], d['jahr'],
                 d['stunden'], d['minuten'], d['sekunden']]
        bezeichnungen = ['Tag', 'Monat', 'Jahr', 'Stunde', 'Minute', 'Sekunde']
        min_werte = [1, 1, 2000, 0, 0, 0]
        max_werte = [31, 12, 2099, 23, 59, 59]

        position = 0
        hat_oled = hasattr(display, 'show') and hasattr(display, 'fill')

        def anzeige():
            datum = "{:02d}.{:02d}.{:04d}".format(werte[0], werte[1], werte[2])
            zeit = "{:02d}:{:02d}:{:02d}".format(werte[3], werte[4], werte[5])
            zeile = "> {}: {}".format(bezeichnungen[position], werte[position])

            if hat_oled:
                display.fill(0)
                display.text("RTC stellen", 0, 0)
                display.text(datum, 0, 16)
                display.text(zeit, 0, 28)
                display.text(zeile, 0, 44)
                display.show()
            else:
                display.clear()
                display.print("RTC stellen", 0, 0)
                display.print(datum, 0, 1)
                display.print(zeit, 0, 2)
                display.print(zeile, 0, 3)

        anzeige()

        while position < 6:
            time.sleep_ms(150)

            if btn_hoch.value():
                werte[position] = min(werte[position] + 1, max_werte[position])
                if position <= 1:
                    max_werte[0] = self.tageImMonat(werte[1], werte[2])
                    werte[0] = min(werte[0], max_werte[0])
                anzeige()
                while btn_hoch.value():
                    time.sleep_ms(50)

            elif btn_runter.value():
                werte[position] = max(werte[position] - 1, min_werte[position])
                anzeige()
                while btn_runter.value():
                    time.sleep_ms(50)

            elif btn_enter.value():
                position += 1
                if position < 6:
                    max_werte[0] = self.tageImMonat(werte[1], werte[2])
                    werte[0] = min(werte[0], max_werte[0])
                    anzeige()
                while btn_enter.value():
                    time.sleep_ms(50)

        wt = self._berechneWochentag(werte[2], werte[1], werte[0])
        self.set(jahr=werte[2], monat=werte[1], tag=werte[0],
                 stunden=werte[3], minuten=werte[4], sekunden=werte[5],
                 wochentag=wt)

        if hat_oled:
            display.fill(0)
            display.text("RTC gestellt!", 0, 20)
            display.text(self.toString("DD.MM.YYYY"), 0, 36)
            display.text(self.toString("hh:mm:ss"), 0, 48)
            display.show()
        else:
            display.clear()
            display.print("RTC gestellt!", 0, 0)
            display.print(self.toString("DD.MM.YYYY"), 0, 1)
            display.print(self.toString("hh:mm:ss"), 0, 2)

        time.sleep(2)

    # --- Stell-Pin pruefen beim Boot ----------------------------------------

    def pruefeStellPin(self, pin_nr, display=None, pin_hoch=None,
                       pin_runter=None, pin_enter=None):
        """
        Prueft beim Boot ob ein Pin auf HIGH steht und startet
        ggf. das interaktive Stellen oder das serielle Stellen.

        Args:
            pin_nr: GPIO-Pin-Nummer des Stell-Tasters
            display: Optionales Display-Objekt (LCD/OLED)
            pin_hoch: GPIO-Pin fuer Taster 'Hoch' (nur mit Display)
            pin_runter: GPIO-Pin fuer Taster 'Runter' (nur mit Display)
            pin_enter: GPIO-Pin fuer Taster 'Enter' (nur mit Display)

        Returns:
            bool: True wenn Uhr gestellt wurde
        """
        stell_pin = Pin(pin_nr, Pin.IN, Pin.PULL_DOWN)

        if stell_pin.value():
            print("Stell-Modus erkannt!")
            if display is not None and pin_hoch is not None:
                self.stellenInteraktiv(display, pin_hoch, pin_runter, pin_enter)
                return True
            else:
                return self.stellenSeriell()
        return False

    # --- Hilfsfunktionen ----------------------------------------------------

    def _berechneWochentag(self, jahr, monat, tag):
        """
        Berechnet den Wochentag nach dem Tomohiko-Sakamoto-Algorithmus.

        Returns:
            int: 1=Montag, 7=Sonntag
        """
        t_tabelle = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4]
        j = jahr
        if monat < 3:
            j -= 1
        wt = (j + j // 4 - j // 100 + j // 400 + t_tabelle[monat - 1] + tag) % 7
        # 0=Sonntag -> 1=Montag, 7=Sonntag
        return 7 if wt == 0 else wt

    def istSchaltjahr(self, jahr=None):
        """
        Prueft ob ein Jahr ein Schaltjahr ist.

        Args:
            jahr: Zu pruefendes Jahr. Falls None: aktuelles Jahr.

        Returns:
            bool: True wenn Schaltjahr
        """
        if jahr is None:
            jahr = self.jahr()
        return (jahr % 4 == 0 and jahr % 100 != 0) or (jahr % 400 == 0)

    def tageImMonat(self, monat=None, jahr=None):
        """
        Gibt die Anzahl der Tage im angegebenen Monat zurueck.

        Args:
            monat: Monat (1-12). Falls None: aktueller Monat.
            jahr: Jahr. Falls None: aktuelles Jahr.

        Returns:
            int: Anzahl der Tage
        """
        if monat is None:
            monat = self.monat()
        if jahr is None:
            jahr = self.jahr()
        tage = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if monat == 2 and self.istSchaltjahr(jahr):
            return 29
        return tage[monat - 1]

    def zeitTuple(self):
        """
        Gibt die aktuelle Zeit als Tuple zurueck.
        Kompatibel mit time.localtime() Format.

        Returns:
            tuple: (jahr, monat, tag, stunden, minuten, sekunden, wochentag, jahrestag)
        """
        d = self.aktuelleDaten()
        jahrestag = d['tag']
        for m in range(1, d['monat']):
            jahrestag += self.tageImMonat(m, d['jahr'])
        return (d['jahr'], d['monat'], d['tag'],
                d['stunden'], d['minuten'], d['sekunden'],
                d['wochentag'] - 1, jahrestag)

    def unixZeit(self):
        """
        Gibt die aktuelle Zeit als Sekunden seit 2000-01-01 00:00:00 zurueck.
        (MicroPython-Epoche)

        Returns:
            int: Sekunden seit 2000-01-01 00:00:00
        """
        d = self.aktuelleDaten()
        tage = 0
        for y in range(2000, d['jahr']):
            tage += 366 if self.istSchaltjahr(y) else 365
        for m in range(1, d['monat']):
            tage += self.tageImMonat(m, d['jahr'])
        tage += d['tag'] - 1
        return tage * 86400 + d['stunden'] * 3600 + d['minuten'] * 60 + d['sekunden']


# ============================================================================
# DS1307
# ============================================================================

class DS1307(RTCBasis):
    """
    Treiber fuer das DS1307 Echtzeituhr-Modul.

    Unterstuetzte Hardware:
    - DS1307 RTC mit 56 Byte batterigestuetztem RAM

    Schnittstelle: I2C (Standard-Adresse: 0x68)
    """

    # Register
    _REG_SEKUNDEN = 0x00
    _REG_MINUTEN  = 0x01
    _REG_STUNDEN  = 0x02
    _REG_WOCHENTAG = 0x03
    _REG_TAG      = 0x04
    _REG_MONAT    = 0x05
    _REG_JAHR     = 0x06
    _REG_CONTROL  = 0x07
    _REG_RAM      = 0x08

    def __init__(self, i2c=None, addr=0x68, scl=22, sda=21, i2c_id=0):
        super().__init__(i2c=i2c, addr=addr, scl=scl, sda=sda, i2c_id=i2c_id)

    def aktuelleDaten(self):
        """
        Liest alle aktuellen Datums- und Zeitdaten von der DS1307.

        Returns:
            dict: Woerterbuch mit sekunden, minuten, stunden, wochentag,
                  tag, monat, jahr
        """
        daten = self._lese_register(self._REG_SEKUNDEN, 7)
        return {
            'sekunden':  _bcd_zu_dez(daten[0] & 0x7F),
            'minuten':   _bcd_zu_dez(daten[1] & 0x7F),
            'stunden':   _bcd_zu_dez(daten[2] & 0x3F),
            'wochentag': daten[3] & 0x07,
            'tag':       _bcd_zu_dez(daten[4] & 0x3F),
            'monat':     _bcd_zu_dez(daten[5] & 0x1F),
            'jahr':      _bcd_zu_dez(daten[6]) + 2000
        }

    def set(self, jahr=None, monat=None, tag=None,
            stunden=None, minuten=None, sekunden=None, wochentag=None):
        """Stellt die DS1307. Nicht angegebene Werte bleiben unveraendert."""
        d = self.aktuelleDaten()

        s  = sekunden  if sekunden  is not None else d['sekunden']
        mi = minuten   if minuten   is not None else d['minuten']
        h  = stunden   if stunden   is not None else d['stunden']
        wt = wochentag if wochentag is not None else d['wochentag']
        t  = tag       if tag       is not None else d['tag']
        m  = monat     if monat     is not None else d['monat']
        j  = (jahr - 2000) if jahr  is not None else (d['jahr'] - 2000)

        self._schreibe_register(self._REG_SEKUNDEN, bytes([
            _dez_zu_bcd(s),       # Sekunden (CH=0 -> Oszillator laeuft)
            _dez_zu_bcd(mi),      # Minuten
            _dez_zu_bcd(h),       # Stunden (24h-Modus)
            wt,                   # Wochentag
            _dez_zu_bcd(t),       # Tag
            _dez_zu_bcd(m),       # Monat
            _dez_zu_bcd(j)        # Jahr (00-99)
        ]))

    def laueft(self):
        """
        Prueft ob der Oszillator der DS1307 laeuft.

        Returns:
            bool: True wenn der Oszillator laeuft (CH-Bit = 0)
        """
        return not bool(self._lese_byte(self._REG_SEKUNDEN) & 0x80)

    def start(self):
        """Startet den Oszillator der DS1307"""
        sek = self._lese_byte(self._REG_SEKUNDEN)
        self._schreibe_byte(self._REG_SEKUNDEN, sek & 0x7F)

    def stop(self):
        """Stoppt den Oszillator der DS1307"""
        sek = self._lese_byte(self._REG_SEKUNDEN)
        self._schreibe_byte(self._REG_SEKUNDEN, sek | 0x80)

    def schreibeRAM(self, adresse, daten):
        """
        Schreibt Daten in den DS1307 RAM (56 Bytes, Adresse 0-55).

        Args:
            adresse: RAM-Offset (0-55)
            daten: Bytes zum Schreiben
        """
        if adresse < 0 or adresse + len(daten) > 56:
            raise ValueError("RAM-Adresse ausserhalb des gueltigen Bereichs (0-55)")
        self._schreibe_register(self._REG_RAM + adresse, daten)

    def leseRAM(self, adresse, laenge=1):
        """
        Liest Daten aus dem DS1307 RAM.

        Args:
            adresse: RAM-Offset (0-55)
            laenge: Anzahl der zu lesenden Bytes

        Returns:
            bytes: Gelesene Daten
        """
        if adresse < 0 or adresse + laenge > 56:
            raise ValueError("RAM-Adresse ausserhalb des gueltigen Bereichs (0-55)")
        return self._lese_register(self._REG_RAM + adresse, laenge)

    def squareWave(self, frequenz=None):
        """
        Konfiguriert den Square-Wave-Ausgang (SQW/OUT Pin).

        Args:
            frequenz: None=aus, 1=1Hz, 4096=4.096kHz,
                      8192=8.192kHz, 32768=32.768kHz
        """
        freq_map = {None: 0x00, 1: 0x10, 4096: 0x11,
                    8192: 0x12, 32768: 0x13}
        if frequenz not in freq_map:
            raise ValueError("Gueltige Frequenzen: None, 1, 4096, 8192, 32768")
        self._schreibe_byte(self._REG_CONTROL, freq_map[frequenz])


# ============================================================================
# DS3231
# ============================================================================

class DS3231(RTCBasis):
    """
    Treiber fuer das DS3231 Echtzeituhr-Modul.

    Unterstuetzte Hardware:
    - DS3231 RTC mit integriertem Temperatursensor und Alarm-Funktion

    Schnittstelle: I2C (Standard-Adresse: 0x68)
    """

    # Register
    _REG_SEKUNDEN   = 0x00
    _REG_MINUTEN    = 0x01
    _REG_STUNDEN    = 0x02
    _REG_WOCHENTAG  = 0x03
    _REG_TAG        = 0x04
    _REG_MONAT      = 0x05
    _REG_JAHR       = 0x06
    _REG_ALARM1_SEK = 0x07
    _REG_ALARM1_MIN = 0x08
    _REG_ALARM1_STD = 0x09
    _REG_ALARM1_TAG = 0x0A
    _REG_ALARM2_MIN = 0x0B
    _REG_ALARM2_STD = 0x0C
    _REG_ALARM2_TAG = 0x0D
    _REG_CONTROL    = 0x0E
    _REG_STATUS     = 0x0F
    _REG_TEMPERATUR = 0x11

    def __init__(self, i2c=None, addr=0x68, scl=22, sda=21, i2c_id=0):
        super().__init__(i2c=i2c, addr=addr, scl=scl, sda=sda, i2c_id=i2c_id)

    def aktuelleDaten(self):
        """
        Liest alle aktuellen Datums- und Zeitdaten von der DS3231.

        Returns:
            dict: Woerterbuch mit sekunden, minuten, stunden, wochentag,
                  tag, monat, jahr
        """
        daten = self._lese_register(self._REG_SEKUNDEN, 7)
        return {
            'sekunden':  _bcd_zu_dez(daten[0] & 0x7F),
            'minuten':   _bcd_zu_dez(daten[1] & 0x7F),
            'stunden':   _bcd_zu_dez(daten[2] & 0x3F),
            'wochentag': daten[3] & 0x07,
            'tag':       _bcd_zu_dez(daten[4] & 0x3F),
            'monat':     _bcd_zu_dez(daten[5] & 0x1F),
            'jahr':      _bcd_zu_dez(daten[6]) + 2000
        }

    def set(self, jahr=None, monat=None, tag=None,
            stunden=None, minuten=None, sekunden=None, wochentag=None):
        """Stellt die DS3231. Nicht angegebene Werte bleiben unveraendert."""
        d = self.aktuelleDaten()

        s  = sekunden  if sekunden  is not None else d['sekunden']
        mi = minuten   if minuten   is not None else d['minuten']
        h  = stunden   if stunden   is not None else d['stunden']
        wt = wochentag if wochentag is not None else d['wochentag']
        t  = tag       if tag       is not None else d['tag']
        m  = monat     if monat     is not None else d['monat']
        j  = (jahr - 2000) if jahr  is not None else (d['jahr'] - 2000)

        self._schreibe_register(self._REG_SEKUNDEN, bytes([
            _dez_zu_bcd(s),
            _dez_zu_bcd(mi),
            _dez_zu_bcd(h),
            wt,
            _dez_zu_bcd(t),
            _dez_zu_bcd(m),
            _dez_zu_bcd(j)
        ]))

    def temperatur(self):
        """
        Liest die Temperatur vom integrierten Sensor der DS3231.

        Returns:
            float: Temperatur in Grad Celsius (Aufloesung: 0.25 C)
        """
        daten = self._lese_register(self._REG_TEMPERATUR, 2)
        msb = daten[0]
        lsb = daten[1]
        temp = msb if msb < 128 else msb - 256
        temp += (lsb >> 6) * 0.25
        return temp

    def laueft(self):
        """
        Prueft ob der Oszillator der DS3231 laeuft.

        Returns:
            bool: True wenn der Oszillator laeuft (OSF-Bit = 0)
        """
        return not bool(self._lese_byte(self._REG_STATUS) & 0x80)

    def start(self):
        """Startet den Oszillator der DS3231"""
        ctrl = self._lese_byte(self._REG_CONTROL)
        self._schreibe_byte(self._REG_CONTROL, ctrl & 0x7F)
        status = self._lese_byte(self._REG_STATUS)
        self._schreibe_byte(self._REG_STATUS, status & 0x7F)

    def stop(self):
        """Stoppt den Oszillator der DS3231"""
        ctrl = self._lese_byte(self._REG_CONTROL)
        self._schreibe_byte(self._REG_CONTROL, ctrl | 0x80)

    # --- Alarm-Funktionen ---------------------------------------------------

    def alarm1(self, stunden=None, minuten=None, sekunden=0,
               tag=None, wochentag=None):
        """
        Setzt Alarm 1 der DS3231.

        Args:
            stunden: Stunde (0-23) oder None
            minuten: Minute (0-59) oder None
            sekunden: Sekunde (0-59, Standard: 0)
            tag: Tag des Monats (1-31) oder None
            wochentag: Wochentag (1-7) oder None
        """
        if stunden is None and minuten is None:
            a1m1, a1m2, a1m3, a1m4 = 0x80, 0x80, 0x80, 0x80
        elif stunden is None:
            a1m1, a1m2, a1m3, a1m4 = 0x00, 0x00, 0x80, 0x80
        else:
            a1m1, a1m2, a1m3, a1m4 = 0x00, 0x00, 0x00, 0x80

        if tag is not None:
            a1m4 = 0x00
        elif wochentag is not None:
            a1m4 = 0x40

        self._schreibe_register(self._REG_ALARM1_SEK, bytes([
            _dez_zu_bcd(sekunden) | a1m1,
            _dez_zu_bcd(minuten if minuten is not None else 0) | a1m2,
            _dez_zu_bcd(stunden if stunden is not None else 0) | a1m3,
            (_dez_zu_bcd(tag) if tag is not None else
             (wochentag if wochentag is not None else 1)) | a1m4
        ]))

        ctrl = self._lese_byte(self._REG_CONTROL)
        self._schreibe_byte(self._REG_CONTROL, ctrl | 0x05)

    def alarm2(self, stunden=None, minuten=None, tag=None, wochentag=None):
        """
        Setzt Alarm 2 der DS3231 (ohne Sekunden-Genauigkeit).

        Args:
            stunden: Stunde (0-23) oder None
            minuten: Minute (0-59) oder None
            tag: Tag des Monats (1-31) oder None
            wochentag: Wochentag (1-7) oder None
        """
        if stunden is None and minuten is None:
            a2m2, a2m3, a2m4 = 0x80, 0x80, 0x80
        elif stunden is None:
            a2m2, a2m3, a2m4 = 0x00, 0x80, 0x80
        else:
            a2m2, a2m3, a2m4 = 0x00, 0x00, 0x80

        if tag is not None:
            a2m4 = 0x00
        elif wochentag is not None:
            a2m4 = 0x40

        self._schreibe_register(self._REG_ALARM2_MIN, bytes([
            _dez_zu_bcd(minuten if minuten is not None else 0) | a2m2,
            _dez_zu_bcd(stunden if stunden is not None else 0) | a2m3,
            (_dez_zu_bcd(tag) if tag is not None else
             (wochentag if wochentag is not None else 1)) | a2m4
        ]))

        ctrl = self._lese_byte(self._REG_CONTROL)
        self._schreibe_byte(self._REG_CONTROL, ctrl | 0x06)

    def alarmStatus(self):
        """
        Prueft ob ein Alarm ausgeloest wurde.

        Returns:
            tuple: (alarm1_ausgeloest, alarm2_ausgeloest)
        """
        status = self._lese_byte(self._REG_STATUS)
        return (bool(status & 0x01), bool(status & 0x02))

    def alarmLoeschen(self, alarm_nr=None):
        """
        Loescht den Alarm-Status.

        Args:
            alarm_nr: 1 oder 2 fuer einzelnen Alarm, None fuer beide
        """
        status = self._lese_byte(self._REG_STATUS)
        if alarm_nr == 1:
            status &= 0xFE
        elif alarm_nr == 2:
            status &= 0xFD
        else:
            status &= 0xFC
        self._schreibe_byte(self._REG_STATUS, status)

    # --- Square-Wave --------------------------------------------------------

    def squareWave(self, frequenz=None):
        """
        Konfiguriert den Square-Wave-Ausgang (SQW Pin).

        Args:
            frequenz: None=aus, 1=1Hz, 1024=1.024kHz,
                      4096=4.096kHz, 8192=8.192kHz
        """
        ctrl = self._lese_byte(self._REG_CONTROL)

        if frequenz is None:
            self._schreibe_byte(self._REG_CONTROL, (ctrl | 0x04) & 0xE7)
        else:
            ctrl &= 0xE3
            freq_map = {1: 0x00, 1024: 0x08, 4096: 0x10, 8192: 0x18}
            if frequenz not in freq_map:
                raise ValueError(
                    "Gueltige Frequenzen: None, 1, 1024, 4096, 8192")
            ctrl |= freq_map[frequenz]
            self._schreibe_byte(self._REG_CONTROL, ctrl)


# ============================================================================
# Factory-Funktion
# ============================================================================

def RTC(chip='DS3231', i2c=None, addr=0x68, scl=22, sda=21, i2c_id=0):
    """
    Erzeugt ein RTC-Objekt fuer den angegebenen Chip-Typ.

    Args:
        chip: 'DS1307' oder 'DS3231' (Standard: 'DS3231')
        i2c: Optionales I2C-Objekt
        addr: I2C-Adresse (Standard: 0x68)
        scl: GPIO-Pin fuer SCL (Standard: 22)
        sda: GPIO-Pin fuer SDA (Standard: 21)
        i2c_id: I2C-Bus-ID (Standard: 0)

    Returns:
        DS1307 oder DS3231 Objekt
    """
    chip_upper = chip.upper()
    if chip_upper == 'DS1307':
        return DS1307(i2c=i2c, addr=addr, scl=scl, sda=sda, i2c_id=i2c_id)
    elif chip_upper == 'DS3231':
        return DS3231(i2c=i2c, addr=addr, scl=scl, sda=sda, i2c_id=i2c_id)
    else:
        raise ValueError(
            "Unbekannter Chip-Typ: {}. Unterstuetzt: DS1307, DS3231".format(chip))
