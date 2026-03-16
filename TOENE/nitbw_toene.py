"""
NIT Bibliothek: TOENE - Melodien aus Notenlisten mit englischer Notation
Fuer ESP32 mit MicroPython

Version:    1.2.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Spielt einzelne Noten und komplette Lied-Listen im Format (note, dauer).
Verwendet Notennamen wie C4, F#4 oder P (Pause) mit frei waehlbarer BPM.
"""

from machine import PWM
from time import sleep


class TOENE:
    """
    Spielt Melodien aus Tupel-Listen ueber einen PWM-Lautsprecher.

    Unterstuetzte Hardware:
    - Passiver Piezo-Lautsprecher
    - PWM-faehige GPIO-Pins am ESP32

    Schnittstelle: PWM
    """

    _FREQ = {
        "C1": 33, "C#1": 35, "D1": 37, "D#1": 39, "E1": 41, "F1": 44,
        "F#1": 46, "G1": 49, "G#1": 52, "A1": 55, "A#1": 58, "B1": 62,
        "C2": 65, "C#2": 69, "D2": 73, "D#2": 78, "E2": 82, "F2": 87,
        "F#2": 93, "G2": 98, "G#2": 104, "A2": 110, "A#2": 117, "B2": 123,
        "C3": 131, "C#3": 139, "D3": 147, "D#3": 156, "E3": 165, "F3": 175,
        "F#3": 185, "G3": 196, "G#3": 208, "A3": 220, "A#3": 233, "B3": 247,
        "C4": 262, "C#4": 277, "D4": 294, "D#4": 311, "E4": 330, "F4": 349,
        "F#4": 370, "G4": 392, "G#4": 415, "A4": 440, "A#4": 466, "B4": 494,
        "C5": 523, "C#5": 554, "D5": 587, "D#5": 622, "E5": 659, "F5": 698,
        "F#5": 740, "G5": 784, "G#5": 831, "A5": 880, "A#5": 932, "B5": 988,
        "C6": 1047, "C#6": 1109, "D6": 1175, "D#6": 1245, "E6": 1319,
        "F6": 1397, "F#6": 1480, "G6": 1568, "G#6": 1661, "A6": 1760,
        "A#6": 1865, "B6": 1976, "C7": 2093, "C#7": 2217, "D7": 2349,
        "D#7": 2489, "E7": 2637, "F7": 2794, "F#7": 2960, "G7": 3136,
        "G#7": 3322, "A7": 3520, "A#7": 3729, "B7": 3951,
        "P": 1,
    }

    def __init__(self, pin, geschwindigkeit=60):
        self._pwm = PWM(pin)
        self._pwm.freq(1)
        self._set_duty_off()
        self._geschwindigkeit = int(geschwindigkeit)

    def _set_duty_on(self):
        try:
            self._pwm.duty_u16(32768)
        except AttributeError:
            self._pwm.duty(512)

    def _set_duty_off(self):
        try:
            self._pwm.duty_u16(0)
        except AttributeError:
            self._pwm.duty(0)

    def set_geschwindigkeit(self, bpm):
        """Setzt das Tempo in BPM."""
        bpm = int(bpm)
        self._geschwindigkeit = bpm if 20 <= bpm <= 300 else 60

    def get_geschwindigkeit(self):
        """Liefert das aktuelle Tempo in BPM."""
        return self._geschwindigkeit

    def ton(self, note):
        """Spielt ein Tupel (notenname, dauer_anteil)."""
        hoehe, dauer = note
        if hoehe not in self._FREQ:
            raise ValueError("Unbekannte Note: {}".format(hoehe))

        self._pwm.freq(self._FREQ[hoehe])
        if hoehe == "P":
            self._set_duty_off()
        else:
            self._set_duty_on()

        sleep(float(dauer) * 60.0 / self._geschwindigkeit)
        self._set_duty_off()
        sleep(0.01)

    def spiele_lied(self, lied):
        """Spielt eine Liste aus Noten-Tupeln nacheinander ab."""
        for note in lied:
            self.ton(note)

    def stop(self):
        """Schaltet den Lautsprecher stumm."""
        self._set_duty_off()

    # Rueckwaertskompatible Aliase zur alten Music-API
    def tone(self, note):
        self.ton(note)

    def noTone(self):
        self.stop()


class Music(TOENE):
    """Kompatibilitaetsklasse zur alten TOENE/music.py API."""


__all__ = ["TOENE", "Music"]
