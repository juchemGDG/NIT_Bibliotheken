"""
NIT Bibliothek: SDKarte - microSD-Karte ueber SPI als Datenspeicher
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Volker Rust / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-11

Eigener Blockgeraete-Treiber fuer SD-Karten im SPI-Modus (SDSC und SDHC)
nach SD-Spezifikation; die Karte wird als FAT-Dateisystem eingehaengt.
Einfache Dateifunktionen helfen beim Speichern von Messwerten (CSV).
"""

import os
import time
from machine import Pin


# ============================================================================
# Konstanten
# ============================================================================

_BLOCK = 512                 # Blockgroesse in Byte (bei SD im SPI-Modus fest)
_BAUD_INIT = 100000          # SPI-Takt waehrend der Initialisierung (max. 400 kHz)
_BAUD_BETRIEB = 1320000      # SPI-Takt im Betrieb (ca. 1,32 MHz, sicher mit Steckkabeln)

_TOKEN_START = 0xFE          # Daten-Token: Einzelblock und Mehrfach-Lesen
_TOKEN_MEHRFACH = 0xFC       # Daten-Token: Mehrfach-Schreiben (CMD25)
_TOKEN_STOPP = 0xFD          # Stopp-Token: Mehrfach-Schreiben beenden

_R1_IDLE = 0x01              # R1-Antwort: Karte im Leerlauf (Initialisierung laeuft)
_R1_ILLEGAL = 0x04           # R1-Antwort: Befehl unbekannt (z. B. CMD8 bei SD-Version 1)
_KEINE_ANTWORT = 0xFF

_NCR_MAX = 10                # max. Wartebytes bis zur Befehlsantwort
_TIMEOUT_INIT_MS = 2000      # ACMD41: so lange darf die Karte zum Starten brauchen
_TIMEOUT_BEREIT_MS = 500     # Warten, bis die Karte nicht mehr beschaeftigt ist
_TIMEOUT_LESEN_MS = 300      # Warten auf das Daten-Token beim Lesen
_TIMEOUT_SCHREIBEN_MS = 600  # Warten, bis ein geschriebener Block gespeichert ist

_FF = b'\xff'
_FFFF = b'\xff\xff'

# Fehlernummern (errno) von MicroPython
_EPERM = 1
_ENOENT = 2
_EEXIST = 17
_ENODEV = 19

# Bit im st_mode von os.stat() fuer Ordner
_S_IFDIR = 0x4000

_FEHLER_KEINE_ANTWORT = (
    "SD-Karte antwortet nicht. Bitte pruefen: Karte eingesteckt? "
    "Verkabelung SCK/MOSI/MISO und CS-Pin richtig? Versorgung des Moduls "
    "(Module mit Spannungsregler brauchen VCC = 5 V)? Gemeinsames GND?")
_FEHLER_INKOMPATIBEL = (
    "SD-Karte wird nicht unterstuetzt oder antwortet fehlerhaft. "
    "microSD-Karte (SDHC, max. 32 GB) verwenden und Verkabelung pruefen.")
_FEHLER_INIT_TIMEOUT = (
    "SD-Karte startet nicht (Zeitueberschreitung bei der Initialisierung). "
    "Versorgung pruefen oder andere Karte versuchen.")
_FEHLER_BESCHAEFTIGT = (
    "SD-Karte bleibt beschaeftigt (MISO dauerhaft LOW). "
    "Verkabelung von MISO pruefen.")
_FEHLER_KEIN_FAT = (
    "Kein FAT-Dateisystem auf der SD-Karte gefunden. Karte am PC mit "
    "FAT32 formatieren (max. 32 GB; groessere Karten sind meist exFAT).")
_FEHLER_NICHT_EINGEHAENGT = (
    "SD-Karte ist nicht eingehaengt. Zuerst einhaengen() aufrufen.")


# ============================================================================
# Hilfsfunktionen
# ============================================================================

def _crc7(daten, anzahl):
    """
    Berechnet die CRC7-Pruefsumme eines SD-Befehls (Polynom x^7 + x^3 + 1).

    Liefert das letzte Befehlsbyte: CRC7 in den oberen 7 Bit, Endbit = 1.
    """
    crc = 0
    for i in range(anzahl):
        b = daten[i]
        for _ in range(8):
            crc <<= 1
            # Hoechstes CRC-Bit mit dem naechsten Datenbit vergleichen
            if (b ^ crc) & 0x80:
                crc ^= 0x09
            b <<= 1
        crc &= 0x7F
    return (crc << 1) | 1


def _vfs_funktion(name):
    """
    Liefert mount, umount oder VfsFat.

    Bis MicroPython 1.22 liegen sie im Modul os, ab 1.23 im Modul vfs.
    """
    funktion = getattr(os, name, None)
    if funktion is None:
        try:
            import vfs
            funktion = getattr(vfs, name, None)
        except ImportError:
            funktion = None
    if funktion is None:
        raise OSError(
            "Diese MicroPython-Firmware kennt '{}' nicht (FAT-Unterstuetzung fehlt).".format(name))
    return funktion


def _fehlernummer(fehler):
    """Liefert die errno eines OSError (oder None)."""
    if fehler.args and isinstance(fehler.args[0], int):
        return fehler.args[0]
    return None


# ============================================================================
# Klasse: _SDBlock (Blockgeraete-Treiber fuer SD-Karten im SPI-Modus)
# ============================================================================

class _SDBlock:
    """
    Blockgeraet fuer eine SD-Karte im SPI-Modus (wird intern von SDKarte genutzt).

    Stellt readblocks(), writeblocks() und ioctl() bereit, wie es
    os.VfsFat von einem Blockgeraet erwartet. Unterstuetzt SDSC-Karten
    (Version 1 und 2, Byte-Adressierung) und SDHC/SDXC-Karten
    (Block-Adressierung).
    """

    def __init__(self, spi, cs, baudrate=_BAUD_BETRIEB):
        """
        Initialisiert die SD-Karte.

        Args:
            spi: machine.SPI-Objekt (ausserhalb erstellt)
            cs: GPIO-Pin-Nummer fuer Chip Select (oder fertiges Pin-Objekt)
            baudrate: SPI-Takt nach der Initialisierung in Hz (Standard: 1320000)

        Raises:
            OSError: Wenn die Karte nicht antwortet oder nicht unterstuetzt wird.
        """
        self._spi = spi
        if isinstance(cs, int):
            self._cs = Pin(cs, Pin.OUT, value=1)
        else:
            self._cs = cs
            self._cs.init(Pin.OUT, value=1)
        self._baudrate = baudrate
        self._byte = bytearray(1)
        self._kmd = bytearray(6)
        self._crc = bytearray(2)
        self._token = bytearray(1)
        self._stopp = bytes([_TOKEN_STOPP])
        self._sdhc = False
        self._bloecke = 0
        self.initialisieren()

    # --- Initialisierung ----------------------------------------------------

    def initialisieren(self):
        """
        Initialisiert die Karte nach SD-Spezifikation (SPI-Modus).

        Ablauf: Einschalttakte, CMD0 (Reset), CMD8 (Version),
        ACMD41 (Start), CMD58 (Adressierungsart), CMD9 (Kapazitaet),
        CMD16 (Blockgroesse), danach hoeherer SPI-Takt.

        Raises:
            OSError: Wenn die Karte nicht antwortet oder nicht unterstuetzt wird.
        """
        self._spi.init(baudrate=_BAUD_INIT, polarity=0, phase=0)

        # Mindestens 74 Takte mit CS = HIGH, damit die Karte startklar wird
        self._cs.value(1)
        for _ in range(16):
            self._spi.write(_FF)

        # CMD0: Reset, die Karte wechselt in den SPI-Modus (Antwort: Idle)
        bereit = False
        for _ in range(5):
            if self._befehl(0, 0, warten=False) == _R1_IDLE:
                bereit = True
                break
        if not bereit:
            raise OSError(_FEHLER_KEINE_ANTWORT)

        # CMD8: Nur Karten ab SD-Version 2 kennen diesen Befehl
        r7 = bytearray(4)
        r1 = self._befehl(8, 0x1AA, r7)
        if r1 == _R1_IDLE:
            # Karte muss 2,7-3,6 V bestaetigen und das Pruefmuster 0xAA zuruecksenden
            if (r7[2] & 0x0F) != 0x01 or r7[3] != 0xAA:
                raise OSError(_FEHLER_INKOMPATIBEL)
            version2 = True
        elif r1 != _KEINE_ANTWORT and (r1 & _R1_ILLEGAL):
            version2 = False
        else:
            raise OSError(_FEHLER_KEINE_ANTWORT)

        # ACMD41 (= CMD55 + CMD41): Karte starten, bis sie den Leerlauf verlaesst.
        # Bei Version 2 wird HCS gesetzt: "Host kann SDHC".
        argument = 0x40000000 if version2 else 0
        start = time.ticks_ms()
        while True:
            self._befehl(55, 0)
            r1 = self._befehl(41, argument)
            if r1 == 0:
                break
            if r1 == _KEINE_ANTWORT:
                raise OSError(_FEHLER_KEINE_ANTWORT)
            if r1 != _R1_IDLE:
                raise OSError(_FEHLER_INKOMPATIBEL)
            if time.ticks_diff(time.ticks_ms(), start) > _TIMEOUT_INIT_MS:
                raise OSError(_FEHLER_INIT_TIMEOUT)
            time.sleep_ms(10)

        # CMD58: OCR lesen, das CCS-Bit zeigt Block-Adressierung (SDHC/SDXC)
        self._sdhc = False
        if version2:
            ocr = bytearray(4)
            if self._befehl(58, 0, ocr) != 0:
                raise OSError(_FEHLER_INKOMPATIBEL)
            self._sdhc = bool(ocr[0] & 0x40)

        # CMD9: CSD-Register lesen und daraus die Anzahl der Bloecke berechnen
        self._bloecke = self._lese_kapazitaet()

        # CMD16: Blockgroesse 512 Byte festlegen (SDHC hat immer 512 Byte)
        if not self._sdhc:
            if self._befehl(16, _BLOCK) != 0:
                raise OSError(_FEHLER_INKOMPATIBEL)

        # Initialisierung fertig: auf den Betriebstakt umschalten
        self._spi.init(baudrate=self._baudrate, polarity=0, phase=0)

    def _lese_kapazitaet(self):
        """Liest das CSD-Register (CMD9) und berechnet die Anzahl der 512-Byte-Bloecke."""
        csd = bytearray(16)
        self._auswaehlen()
        try:
            if self._sende_befehl(9, 0) != 0:
                raise OSError(_FEHLER_INKOMPATIBEL)
            self._lese_daten(csd)
        finally:
            self._freigeben()

        struktur = csd[0] >> 6
        if struktur == 1:
            # CSD Version 2.0 (SDHC/SDXC): Kapazitaet = (C_SIZE + 1) * 512 KiB
            c_size = ((csd[7] & 0x3F) << 16) | (csd[8] << 8) | csd[9]
            return (c_size + 1) * 1024
        if struktur == 0:
            # CSD Version 1.0 (SDSC):
            # Kapazitaet = (C_SIZE + 1) * 2^(C_SIZE_MULT + 2) * 2^READ_BL_LEN Byte
            read_bl_len = csd[5] & 0x0F
            c_size = ((csd[6] & 0x03) << 10) | (csd[7] << 2) | (csd[8] >> 6)
            c_size_mult = ((csd[9] & 0x03) << 1) | (csd[10] >> 7)
            if read_bl_len < 9:
                raise OSError(_FEHLER_INKOMPATIBEL)
            return (c_size + 1) << (c_size_mult + 2 + read_bl_len - 9)
        raise OSError(_FEHLER_INKOMPATIBEL)

    # --- SPI-Grundfunktionen ------------------------------------------------

    def _auswaehlen(self, warten=True):
        """Setzt CS auf LOW und wartet (optional), bis die Karte bereit ist."""
        self._cs.value(0)
        if warten and not self._warte_bereit(_TIMEOUT_BEREIT_MS):
            self._freigeben()
            raise OSError(_FEHLER_BESCHAEFTIGT)

    def _freigeben(self):
        """Setzt CS auf HIGH und sendet 8 Takte, damit die Karte MISO freigibt."""
        self._cs.value(1)
        self._spi.write(_FF)

    def _warte_bereit(self, timeout_ms):
        """Liest Bytes, bis die Karte 0xFF sendet (nicht beschaeftigt). True = bereit."""
        start = time.ticks_ms()
        while True:
            self._spi.readinto(self._byte, 0xFF)
            if self._byte[0] == 0xFF:
                return True
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                return False

    def _sende_befehl(self, kmd, argument, fuellbyte=False):
        """
        Sendet einen 6-Byte-Befehl (CS muss LOW sein) und liefert die R1-Antwort.

        Aufbau: 01 + Befehlsnummer, 32-Bit-Argument, CRC7 + Endbit.
        Rueckgabe 0xFF bedeutet: keine Antwort.
        """
        k = self._kmd
        k[0] = 0x40 | kmd
        k[1] = (argument >> 24) & 0xFF
        k[2] = (argument >> 16) & 0xFF
        k[3] = (argument >> 8) & 0xFF
        k[4] = argument & 0xFF
        k[5] = _crc7(k, 5)
        self._spi.write(k)
        if fuellbyte:
            # Nach CMD12 folgt ein Fuellbyte, das keine Antwort ist
            self._spi.readinto(self._byte, 0xFF)
        # Die Antwort kommt nach 0 bis 8 Bytes; sie beginnt mit Bit 7 = 0
        for _ in range(_NCR_MAX):
            self._spi.readinto(self._byte, 0xFF)
            if not (self._byte[0] & 0x80):
                return self._byte[0]
        return _KEINE_ANTWORT

    def _befehl(self, kmd, argument, antwort=None, warten=True):
        """
        Sendet einen Befehl als eigene Uebertragung (CS LOW ... CS HIGH).

        Args:
            kmd: Befehlsnummer (z. B. 8 fuer CMD8)
            argument: 32-Bit-Argument
            antwort: optionaler Puffer fuer weitere Antwortbytes (R3/R7)
            warten: vorher warten, bis die Karte bereit ist

        Returns:
            int: R1-Antwort (0xFF = keine Antwort)
        """
        self._auswaehlen(warten)
        try:
            r1 = self._sende_befehl(kmd, argument)
            if antwort is not None and r1 != _KEINE_ANTWORT:
                self._spi.readinto(antwort, 0xFF)
        finally:
            self._freigeben()
        return r1

    def _lese_daten(self, puffer):
        """Wartet auf das Start-Token und liest einen Datenblock in puffer."""
        start = time.ticks_ms()
        while True:
            self._spi.readinto(self._byte, 0xFF)
            token = self._byte[0]
            if token == _TOKEN_START:
                break
            if token != 0xFF:
                raise OSError("SD-Karte: Lesefehler (Fehler-Token 0x{:02X})".format(token))
            if time.ticks_diff(time.ticks_ms(), start) > _TIMEOUT_LESEN_MS:
                raise OSError("SD-Karte: Zeitueberschreitung beim Lesen")
        self._spi.readinto(puffer, 0xFF)
        # Die CRC wird im SPI-Modus nicht geprueft, nur abgeholt
        self._spi.readinto(self._crc, 0xFF)

    def _schreibe_daten(self, token, daten):
        """
        Sendet einen Datenblock mit Token und Dummy-CRC.

        Returns:
            None bei Erfolg, sonst eine Fehlermeldung (str)
        """
        self._spi.write(_FF)                # Abstand zwischen Antwort und Token
        self._token[0] = token
        self._spi.write(self._token)
        self._spi.write(daten)
        self._spi.write(_FFFF)              # Dummy-CRC
        self._spi.readinto(self._byte, 0xFF)
        antwort = self._byte[0] & 0x1F
        if antwort != 0x05:
            # 0x05 = angenommen, 0x0B = CRC-Fehler, 0x0D = Schreibfehler
            return "SD-Karte: Schreibfehler (Datenantwort 0x{:02X})".format(antwort)
        if not self._warte_bereit(_TIMEOUT_SCHREIBEN_MS):
            return "SD-Karte: Zeitueberschreitung beim Schreiben"
        return None

    def _adresse(self, block_nr):
        """SDHC wird blockweise adressiert, SDSC byteweise."""
        if self._sdhc:
            return block_nr
        return block_nr * _BLOCK

    @staticmethod
    def _anzahl_bloecke(puffer):
        """Prueft die Puffergroesse und liefert die Anzahl der Bloecke."""
        anzahl = len(puffer) // _BLOCK
        if anzahl == 0 or len(puffer) % _BLOCK:
            raise ValueError("Puffergroesse muss ein Vielfaches von 512 Byte sein")
        return anzahl

    # --- Blockgeraete-Schnittstelle (fuer os.VfsFat) ------------------------

    def readblocks(self, block_nr, puffer):
        """
        Liest einen oder mehrere 512-Byte-Bloecke.

        Args:
            block_nr: Nummer des ersten Blocks
            puffer: bytearray, Groesse = Anzahl Bloecke * 512
        """
        anzahl = self._anzahl_bloecke(puffer)
        mv = memoryview(puffer)
        self._auswaehlen()
        try:
            if anzahl == 1:
                # CMD17: einen Block lesen
                if self._sende_befehl(17, self._adresse(block_nr)) != 0:
                    raise OSError("SD-Karte: Lesebefehl abgelehnt (Block {})".format(block_nr))
                self._lese_daten(mv)
            else:
                # CMD18: mehrere Bloecke lesen, CMD12 beendet die Uebertragung
                if self._sende_befehl(18, self._adresse(block_nr)) != 0:
                    raise OSError("SD-Karte: Lesebefehl abgelehnt (Block {})".format(block_nr))
                try:
                    for i in range(anzahl):
                        self._lese_daten(mv[i * _BLOCK:(i + 1) * _BLOCK])
                finally:
                    # CMD12 beendet die Uebertragung (auch nach einem Lesefehler)
                    self._sende_befehl(12, 0, fuellbyte=True)
                    bereit = self._warte_bereit(_TIMEOUT_BEREIT_MS)
                if not bereit:
                    raise OSError(_FEHLER_BESCHAEFTIGT)
        finally:
            self._freigeben()

    def writeblocks(self, block_nr, puffer):
        """
        Schreibt einen oder mehrere 512-Byte-Bloecke.

        Args:
            block_nr: Nummer des ersten Blocks
            puffer: Daten, Groesse = Anzahl Bloecke * 512
        """
        anzahl = self._anzahl_bloecke(puffer)
        mv = memoryview(puffer)
        self._auswaehlen()
        try:
            if anzahl == 1:
                # CMD24: einen Block schreiben
                if self._sende_befehl(24, self._adresse(block_nr)) != 0:
                    raise OSError("SD-Karte: Schreibbefehl abgelehnt (Block {})".format(block_nr))
                fehler = self._schreibe_daten(_TOKEN_START, mv)
            else:
                # CMD25: mehrere Bloecke schreiben, Stopp-Token beendet
                if self._sende_befehl(25, self._adresse(block_nr)) != 0:
                    raise OSError("SD-Karte: Schreibbefehl abgelehnt (Block {})".format(block_nr))
                fehler = None
                for i in range(anzahl):
                    fehler = self._schreibe_daten(
                        _TOKEN_MEHRFACH, mv[i * _BLOCK:(i + 1) * _BLOCK])
                    if fehler:
                        break
                self._spi.write(self._stopp)
                self._spi.readinto(self._byte, 0xFF)   # Karte meldet "busy" erst nach 1 Byte
                if not self._warte_bereit(_TIMEOUT_SCHREIBEN_MS) and fehler is None:
                    fehler = "SD-Karte: Zeitueberschreitung beim Schreiben"
            if fehler:
                raise OSError(fehler)
        finally:
            self._freigeben()

    def ioctl(self, op, arg):
        """
        Steuerfunktionen fuer os.VfsFat.

        Args:
            op: 1 = Init, 2 = Deinit, 3 = Sync, 4 = Anzahl Bloecke, 5 = Blockgroesse
            arg: wird nicht verwendet

        Returns:
            int: Ergebnis (0 = OK) oder None bei unbekannter Operation
        """
        if op == 4:
            return self._bloecke
        if op == 5:
            return _BLOCK
        if op in (1, 2, 3):
            return 0
        return None


# ============================================================================
# Klasse: SDKarte (Einhaengen + einfache Dateifunktionen)
# ============================================================================

class SDKarte:
    """
    Bindet eine microSD-Karte als FAT-Dateisystem ein und bietet einfache Dateifunktionen.

    Dateinamen werden relativ zum Einhaengepunkt angegeben:
    'messung.csv' wird zu '/sd/messung.csv'.

    Unterstuetzte Hardware:
    - microSD-Kartenmodule mit SPI (meist mit 3.3-V-Regler und Pegelwandler, VCC 5 V)
    - reine 3.3-V-microSD-Adapter (VCC 3.3 V)
    - microSD-Karten SDSC und SDHC, FAT32-formatiert (max. 32 GB)

    Schnittstelle: SPI
    """

    def __init__(self, spi, cs, pfad='/sd', geraet=None, einhaengen=True):
        """
        Initialisiert die SD-Karte und haengt sie (standardmaessig) ein.

        Args:
            spi: machine.SPI-Objekt (ausserhalb erstellt), z. B.
                 SPI(2, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
            cs: GPIO-Pin-Nummer fuer Chip Select (z. B. 5)
            pfad: Einhaengepunkt im Dateisystem (Standard: '/sd')
            geraet: Optionales fertiges Blockgeraet, z. B. machine.SDCard(slot=2).
                    Dann wird der eigene SPI-Treiber nicht verwendet und
                    spi/cs duerfen None sein.
            einhaengen: True = sofort einhaengen (Standard), False = spaeter
                        mit einhaengen()

        Raises:
            ValueError: Wenn weder spi/cs noch geraet angegeben sind.
            OSError: Wenn die Karte nicht antwortet oder kein FAT hat.
        """
        if geraet is None and (spi is None or cs is None):
            raise ValueError("spi und cs angeben (oder ein fertiges Blockgeraet ueber geraet=...)")
        pfad = pfad.rstrip('/')
        if not pfad:
            raise ValueError("pfad darf nicht '/' sein (z. B. '/sd' verwenden)")

        self._spi = spi
        self._cs = cs
        self._pfad = pfad
        self._eigener_treiber = geraet is None
        self._geraet = geraet
        self._eingehaengt = False
        if einhaengen:
            self.einhaengen()

    # --- Einhaengen ---------------------------------------------------------

    def einhaengen(self):
        """
        Initialisiert die Karte und haengt sie als FAT-Dateisystem unter pfad ein.

        Wird vom Konstruktor automatisch aufgerufen (einhaengen=True).
        Nach aushaengen() und einem Kartenwechsel erneut aufrufen.

        Raises:
            OSError: Wenn die Karte nicht antwortet oder kein FAT-Dateisystem hat.
        """
        if self._eingehaengt:
            return
        if self._eigener_treiber:
            if self._geraet is None:
                self._geraet = _SDBlock(self._spi, self._cs)
            else:
                # Karte neu starten (z. B. nach einem Kartenwechsel)
                self._geraet.initialisieren()

        mount = _vfs_funktion('mount')
        dateisystem = _vfs_funktion('VfsFat')(self._geraet)
        try:
            mount(dateisystem, self._pfad)
        except OSError as e:
            nummer = _fehlernummer(e)
            if nummer == _ENODEV:
                raise OSError(_FEHLER_KEIN_FAT)
            if nummer != _EPERM:
                raise
            # Pfad ist schon belegt (z. B. Programm ohne Neustart erneut
            # gestartet): alte Einhaengung loesen und neu einhaengen
            _vfs_funktion('umount')(self._pfad)
            mount(dateisystem, self._pfad)
        self._eingehaengt = True

    def aushaengen(self):
        """
        Haengt die Karte aus. Vor dem Herausziehen der Karte aufrufen.

        Danach sind die Dateifunktionen erst nach einhaengen() wieder nutzbar.
        """
        if not self._eingehaengt:
            return
        try:
            _vfs_funktion('umount')(self._pfad)
        except OSError:
            pass   # war bereits ausgehaengt
        self._eingehaengt = False

    def ist_eingehaengt(self):
        """
        Gibt an, ob die Karte eingehaengt ist.

        Returns:
            bool: True wenn eingehaengt
        """
        return self._eingehaengt

    # --- Pfade --------------------------------------------------------------

    def pfad(self, datei):
        """
        Wandelt einen Dateinamen in einen vollstaendigen Pfad auf der Karte um.

        Args:
            datei: Dateiname, z. B. 'messung.csv' oder 'daten/messung.csv'.
                   Pfade, die schon mit dem Einhaengepunkt beginnen
                   (z. B. '/sd/messung.csv'), bleiben unveraendert.

        Returns:
            str: z. B. '/sd/messung.csv'
        """
        if datei == self._pfad or datei.startswith(self._pfad + '/'):
            return datei.rstrip('/')
        datei = datei.strip('/')
        if not datei:
            return self._pfad
        return self._pfad + '/' + datei

    # --- Interne Helfer -----------------------------------------------------

    def _pruefe_eingehaengt(self):
        """Loest einen verstaendlichen Fehler aus, wenn die Karte nicht eingehaengt ist."""
        if not self._eingehaengt:
            raise OSError(_FEHLER_NICHT_EINGEHAENGT)

    def _oeffnen(self, datei, modus):
        """Oeffnet eine Datei auf der Karte mit verstaendlicher Fehlermeldung."""
        self._pruefe_eingehaengt()
        p = self.pfad(datei)
        try:
            return open(p, modus)
        except OSError as e:
            if _fehlernummer(e) != _ENOENT:
                raise
            if modus == 'r':
                raise OSError("Datei nicht gefunden: {}".format(p))
            raise OSError(
                "Ordner nicht gefunden fuer: {} (zuerst ordner_anlegen() aufrufen)".format(p))

    def _schreibe(self, datei, text, modus):
        """Schreibt text in eine Datei (Modus 'w' oder 'a') und schliesst sie sofort."""
        with self._oeffnen(datei, modus) as f:
            f.write(text)

    def _stat_modus(self, p):
        """Liefert st_mode eines Pfads oder None, wenn er nicht existiert."""
        try:
            return os.stat(p)[0]
        except OSError:
            return None

    @staticmethod
    def _csv_feld(wert, trenner, dezimalkomma):
        """Wandelt einen Wert in ein CSV-Feld um."""
        if wert is None:
            return ''
        if isinstance(wert, float):
            text = str(wert)
            if dezimalkomma:
                text = text.replace('.', ',')
            return text
        text = str(wert)
        if trenner in text or '"' in text or '\n' in text:
            # Text mit Trennzeichen in Anfuehrungszeichen setzen
            text = '"' + text.replace('"', '""') + '"'
        return text

    # --- Schreiben ----------------------------------------------------------

    def schreiben(self, datei, text):
        """
        Schreibt Text in eine Datei. Eine vorhandene Datei wird ueberschrieben.

        Args:
            datei: Dateiname, z. B. 'notiz.txt'
            text: zu schreibender Text
        """
        self._schreibe(datei, str(text), 'w')

    def anhaengen(self, datei, text):
        """
        Haengt Text unveraendert an das Ende einer Datei an (legt sie bei Bedarf an).

        Args:
            datei: Dateiname
            text: anzuhaengender Text (ohne automatischen Zeilenumbruch)
        """
        self._schreibe(datei, str(text), 'a')

    def zeile_anhaengen(self, datei, text):
        """
        Haengt Text als neue Zeile an (mit Zeilenumbruch am Ende).

        Args:
            datei: Dateiname
            text: Inhalt der Zeile
        """
        self._schreibe(datei, str(text) + '\n', 'a')

    def csv_anhaengen(self, datei, werte, kopf=None, trenner=';', dezimalkomma=True):
        """
        Haengt eine Zeile mit Messwerten an eine CSV-Datei an.

        Die Kopfzeile wird nur geschrieben, wenn die Datei noch nicht
        existiert (oder leer ist). Kommazahlen werden mit Dezimalkomma
        geschrieben, damit eine deutsche Tabellenkalkulation sie als
        Zahlen erkennt.

        Args:
            datei: Dateiname, z. B. 'messung.csv'
            werte: Liste der Werte einer Zeile, z. B. [12.5, 23.4]
            kopf: optionale Liste mit Spaltennamen, z. B. ['Zeit_s', 'Wert']
            trenner: Spaltentrenner (Standard: ';')
            dezimalkomma: True = Kommazahlen mit ',' statt '.' (Standard: True)

        Raises:
            ValueError: Wenn dezimalkomma=True und trenner=',' kombiniert werden.
        """
        if dezimalkomma and trenner == ',':
            raise ValueError("Mit dezimalkomma=True darf der Trenner nicht ',' sein (z. B. ';' verwenden)")
        if not isinstance(werte, (list, tuple)):
            werte = [werte]

        self._pruefe_eingehaengt()
        p = self.pfad(datei)
        try:
            neu = os.stat(p)[6] == 0      # st_size: leere Datei zaehlt als neu
        except OSError:
            neu = True

        zeile = trenner.join([self._csv_feld(w, trenner, dezimalkomma) for w in werte])
        if neu and kopf is not None:
            kopfzeile = trenner.join([self._csv_feld(k, trenner, dezimalkomma) for k in kopf])
            zeile = kopfzeile + '\n' + zeile
        self._schreibe(p, zeile + '\n', 'a')

    # --- Lesen --------------------------------------------------------------

    def lesen(self, datei):
        """
        Liest den gesamten Inhalt einer Datei.

        Args:
            datei: Dateiname

        Returns:
            str: Dateiinhalt
        """
        with self._oeffnen(datei, 'r') as f:
            return f.read()

    def zeilen(self, datei):
        """
        Liest eine Datei zeilenweise.

        Args:
            datei: Dateiname

        Returns:
            list: Zeilen ohne Zeilenumbruch am Ende
        """
        ergebnis = []
        with self._oeffnen(datei, 'r') as f:
            for zeile in f:
                ergebnis.append(zeile.rstrip('\r\n'))
        return ergebnis

    # --- Dateien und Ordner -------------------------------------------------

    def dateien(self, ordner=''):
        """
        Listet die Dateien und Ordner in einem Ordner der Karte auf.

        Args:
            ordner: Unterordner (Standard: '' = Hauptverzeichnis der Karte)

        Returns:
            list: alphabetisch sortierte Namen
        """
        self._pruefe_eingehaengt()
        namen = os.listdir(self.pfad(ordner))
        namen.sort()
        return namen

    def existiert(self, datei):
        """
        Prueft, ob eine Datei oder ein Ordner existiert.

        Args:
            datei: Datei- oder Ordnername

        Returns:
            bool: True wenn vorhanden
        """
        self._pruefe_eingehaengt()
        return self._stat_modus(self.pfad(datei)) is not None

    def loeschen(self, datei):
        """
        Loescht eine Datei oder einen leeren Ordner.

        Args:
            datei: Datei- oder Ordnername

        Raises:
            OSError: Wenn die Datei nicht existiert oder der Ordner nicht leer ist.
        """
        self._pruefe_eingehaengt()
        p = self.pfad(datei)
        if p == self._pfad:
            raise ValueError("Das Hauptverzeichnis der Karte kann nicht geloescht werden.")
        modus = self._stat_modus(p)
        if modus is None:
            raise OSError("Datei nicht gefunden: {}".format(p))
        if modus & _S_IFDIR:
            try:
                os.rmdir(p)
            except OSError:
                raise OSError("Ordner kann nicht geloescht werden (nicht leer?): {}".format(p))
        else:
            os.remove(p)

    def ordner_anlegen(self, name):
        """
        Legt einen Ordner an (auch mehrere Ebenen, z. B. 'daten/2026').

        Ein bereits vorhandener Ordner ist kein Fehler.

        Args:
            name: Ordnername

        Raises:
            OSError: Wenn es bereits eine Datei mit diesem Namen gibt.
        """
        self._pruefe_eingehaengt()
        relativ = self.pfad(name)[len(self._pfad) + 1:]
        aktuell = self._pfad
        for teil in relativ.split('/'):
            if not teil:
                continue
            aktuell = aktuell + '/' + teil
            try:
                os.mkdir(aktuell)
            except OSError as e:
                if _fehlernummer(e) != _EEXIST:
                    raise
                modus = self._stat_modus(aktuell)
                if modus is None or not (modus & _S_IFDIR):
                    raise OSError("Es gibt bereits eine Datei mit diesem Namen: {}".format(aktuell))

    # --- Speicherplatz ------------------------------------------------------

    def speicher(self):
        """
        Ermittelt Gesamtgroesse und freien Speicher der Karte.

        Hinweis: Bei grossen Karten kann der erste Aufruf einige Sekunden
        dauern, wenn das Dateisystem den freien Platz erst zaehlen muss.

        Returns:
            tuple: (gesamt_mb, frei_mb), jeweils auf 0,1 MB gerundet
        """
        self._pruefe_eingehaengt()
        st = os.statvfs(self._pfad)
        blockgroesse = st[1] or st[0]   # f_frsize, sonst f_bsize
        gesamt = st[2] * blockgroesse   # f_blocks
        frei = st[4] * blockgroesse     # f_bavail
        return (round(gesamt / 1048576, 1), round(frei / 1048576, 1))
