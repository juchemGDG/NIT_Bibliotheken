"""
NIT Bibliothek: MP3 - Wiedergabe mit MP3-TF-16P (DFPlayer-kompatibel)
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-07

Steuert das MP3-TF-16P Modul ueber UART mit dem ueblichen 10-Byte-Protokoll.
Unterstuetzt Wiedergabe, Lautstaerke, Ordnertracks und zentrale Player-Befehle.
"""

from time import sleep_ms


class MP3TF16P:
    """
    Steuert einen MP3-TF-16P Mini MP3 Player ueber serielle Befehle.

    Unterstuetzte Hardware:
    - MP3-TF-16P V3.0 (DFPlayer-Mini kompatibel)
    - MicroSD-Karte (FAT16/FAT32)

    Schnittstelle: UART
    """

    DEVICE_U_DISK = 1
    DEVICE_TF = 2
    DEVICE_AUX = 3
    DEVICE_SLEEP = 4
    DEVICE_FLASH = 5

    EQ_NORMAL = 0
    EQ_POP = 1
    EQ_ROCK = 2
    EQ_JAZZ = 3
    EQ_CLASSIC = 4
    EQ_BASS = 5

    def __init__(self, uart, ack=False):
        """
        Initialisiert den Player.

        Args:
            uart: Vorgefertigtes UART-Objekt (machine.UART)
            ack: True, wenn Rueckmeldungen vom Modul angefordert werden sollen
        """
        self.uart = uart
        self._ack = 1 if ack else 0
        self._volume = 20

    def _checksum(self, cmd, param):
        """Berechnet die 16-bit Checksumme fuer einen DFPlayer-Frame."""
        param_high = (param >> 8) & 0xFF
        param_low = param & 0xFF
        total = 0xFF + 0x06 + cmd + self._ack + param_high + param_low
        checksum = (0xFFFF - total + 1) & 0xFFFF
        return (checksum >> 8) & 0xFF, checksum & 0xFF

    def _send_command(self, cmd, param=0):
        """Sendet einen 10-Byte-Befehl an das Modul."""
        param_high = (param >> 8) & 0xFF
        param_low = param & 0xFF
        chk_high, chk_low = self._checksum(cmd, param)
        frame = bytearray([
            0x7E,
            0xFF,
            0x06,
            cmd,
            self._ack,
            param_high,
            param_low,
            chk_high,
            chk_low,
            0xEF,
        ])
        self.uart.write(frame)
        sleep_ms(30)

    def next(self):
        """Spielt den naechsten Titel."""
        self._send_command(0x01)

    def previous(self):
        """Spielt den vorherigen Titel."""
        self._send_command(0x02)

    def play(self, track):
        """
        Spielt einen globalen Titelindex (typisch 1..2999).

        Args:
            track: Titelnummer
        """
        if track < 1:
            raise ValueError("track muss >= 1 sein")
        self._send_command(0x03, track)

    def volume_up(self):
        """Erhoeht die Lautstaerke um 1 Schritt."""
        self._send_command(0x04)
        if self._volume < 30:
            self._volume += 1

    def volume_down(self):
        """Verringert die Lautstaerke um 1 Schritt."""
        self._send_command(0x05)
        if self._volume > 0:
            self._volume -= 1

    def set_volume(self, value):
        """
        Setzt die Lautstaerke von 0 bis 30.

        Args:
            value: Lautstaerke 0..30
        """
        if value < 0 or value > 30:
            raise ValueError("Lautstaerke muss zwischen 0 und 30 liegen")
        self._send_command(0x06, value)
        self._volume = value

    def get_volume(self):
        """Gibt den zuletzt gesetzten Lautstaerkewert zurueck."""
        return self._volume

    def set_eq(self, mode):
        """
        Setzt den Equalizer-Modus.

        Args:
            mode: 0=normal, 1=pop, 2=rock, 3=jazz, 4=classic, 5=bass
        """
        if mode < 0 or mode > 5:
            raise ValueError("EQ-Modus muss zwischen 0 und 5 liegen")
        self._send_command(0x07, mode)

    def set_source(self, device):
        """
        Waehlt die Audioquelle.

        Args:
            device: DEVICE_U_DISK, DEVICE_TF, DEVICE_AUX, DEVICE_SLEEP, DEVICE_FLASH
        """
        if device < 1 or device > 5:
            raise ValueError("Ungueltige Quelle")
        self._send_command(0x09, device)

    def sleep(self):
        """Versetzt das Modul in den Sleep-Modus."""
        self._send_command(0x0A)

    def reset(self):
        """Fuehrt einen Soft-Reset des Moduls aus."""
        self._send_command(0x0C)
        sleep_ms(1000)

    def resume(self):
        """Setzt eine pausierte Wiedergabe fort."""
        self._send_command(0x0D)

    def pause(self):
        """Pausiert die Wiedergabe."""
        self._send_command(0x0E)

    def play_folder(self, folder, track):
        """
        Spielt Datei in numerischem Ordner (01..99, Datei 001..255).

        Args:
            folder: Ordnernummer 1..99
            track: Titelnummer im Ordner 1..255
        """
        if folder < 1 or folder > 99:
            raise ValueError("folder muss zwischen 1 und 99 liegen")
        if track < 1 or track > 255:
            raise ValueError("track muss zwischen 1 und 255 liegen")
        param = (folder << 8) | track
        self._send_command(0x0F, param)

    def loop_all(self, enable=True):
        """
        Aktiviert oder deaktiviert Endlosschleife ueber alle Titel.

        Args:
            enable: True fuer ein, False fuer aus
        """
        self._send_command(0x11, 1 if enable else 0)

    def play_mp3(self, track):
        """
        Spielt Datei aus dem MP3-Ordner (Dateien 0001.mp3 ...).

        Args:
            track: Titelnummer 1..3000
        """
        if track < 1 or track > 3000:
            raise ValueError("track muss zwischen 1 und 3000 liegen")
        self._send_command(0x12, track)

    def advert_play(self, track):
        """
        Spielt einen Prioritaetstitel (Werbeeinspieler) aus dem ADVERT-Ordner.

        Args:
            track: Titelnummer 1..3000
        """
        if track < 1 or track > 3000:
            raise ValueError("track muss zwischen 1 und 3000 liegen")
        self._send_command(0x13, track)

    def advert_stop(self):
        """Beendet den Prioritaetstitel und kehrt zur vorherigen Wiedergabe zurueck."""
        self._send_command(0x15)

    def stop(self):
        """Stoppt die Wiedergabe."""
        self._send_command(0x16)

    def loop_folder(self, folder):
        """
        Startet Endlosschleife innerhalb eines Ordners.

        Args:
            folder: Ordnernummer 1..99
        """
        if folder < 1 or folder > 99:
            raise ValueError("folder muss zwischen 1 und 99 liegen")
        self._send_command(0x17, folder)

    def random_all(self):
        """Startet Zufallswiedergabe ueber alle Dateien."""
        self._send_command(0x18)

    def repeat_current(self, enable=True):
        """
        Aktiviert oder deaktiviert Wiederholung des aktuellen Titels.

        Args:
            enable: True fuer ein, False fuer aus
        """
        self._send_command(0x19, 1 if enable else 0)
