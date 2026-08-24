"""
NIT Bibliothek: Stepper - Ansteuerung von Schrittmotoren
Fuer ESP32 mit MicroPython

Version:    1.2.0
Autor:      Volker Rust / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-05

Steuert 4-Draht-Schrittmotoren (28BYJ-48 am ULN2003-Board) im Halbschritt-
Betrieb sowie bipolare Schrittmotoren (NEMA 17 u.a.) ueber STEP/DIR-Treiber
wie A4988 oder DRV8825.

Beide Klassen bieten blockierende Bewegungsbefehle (Schritte, Winkel,
Umdrehungen) sowie einen nicht-blockierenden Poll-Modus (starte / ausfuehren).
"""

from machine import Pin
import time


# ============================================================================
# Konstanten
# ============================================================================

# Bewegungsrichtungen
VOR = 1       # Vorwaerts (Uhrzeigersinn von der Motorachse betrachtet)
ZURUECK = -1  # Rueckwaerts (Gegenuhrzeigersinn)

# Halbschritt-Sequenz fuer 28BYJ-48 (8 Phasen, IN1..IN4)
# Halbschritt liefert mehr Aufloesung und sanfteren Lauf als Vollschritt.
_HALBSCHRITT = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1],
]

_HALBSCHRITT_PHASEN = len(_HALBSCHRITT)  # 8


# ============================================================================
# Klasse: StepperULN (28BYJ-48 + ULN2003-Treiberplatine)
# ============================================================================

class StepperULN:
    """
    Steuert einen 28BYJ-48 Schrittmotor ueber ein ULN2003-Treiberboard.

    Der Motor wird im Halbschritt-Betrieb angesteuert (8 Phasen pro Zyklus),
    was einen ruhigeren Lauf und hoehere Aufloesung gegenueber Vollschritt
    erzielt.

    Unterstuetzte Hardware:
    - 28BYJ-48 (5 V oder 12 V Version)
    - ULN2003-Treiberplatine (IN1..IN4 direkt an ESP32-GPIO)

    Schnittstelle: 4 digitale GPIO-Ausgaenge (IN1, IN2, IN3, IN4)
    """

    def __init__(self, in1, in2, in3, in4,
                 schritte_pro_umdrehung=4096, geschwindigkeit=10):
        """
        Initialisiert den Stepper.

        Args:
            in1..in4: GPIO-Pin-Nummern fuer die vier Motorleitungen
            schritte_pro_umdrehung: Schritte fuer eine volle Umdrehung
                                    (28BYJ-48 Halbschritt: typ. 4096,
                                    praxisnah oft ~4076)
            geschwindigkeit: Startgeschwindigkeit in Schritten/Sekunde
                             (28BYJ-48 sinnvoll: 5 - 200 sps)
        """
        self._pins = [
            Pin(in1, Pin.OUT),
            Pin(in2, Pin.OUT),
            Pin(in3, Pin.OUT),
            Pin(in4, Pin.OUT),
        ]
        self._schritte_pro_umdrehung = schritte_pro_umdrehung
        self._phase = 0           # aktuelle Phasenposition in _HALBSCHRITT
        self._position = 0        # absolute Schrittposition (Vorzeichen = Richtung)
        self._ziel = 0            # Zielschritte fuer nicht-blockierenden Modus
        self._laufend = False     # True wenn nicht-blockierende Bewegung aktiv
        self._richtung = VOR
        self._naechster_schritt_us = 0  # Timestamp naechster erlaubter Schritt

        self.geschwindigkeit(geschwindigkeit)
        self._spulen_aus()

    # --- Interne Helfer -----------------------------------------------------

    def _schritt_setzen(self, richtung):
        """Fuehrt genau einen Halbschritt in der gegebenen Richtung aus."""
        self._phase = (self._phase + richtung) % _HALBSCHRITT_PHASEN
        seq = _HALBSCHRITT[self._phase]
        for i, pin in enumerate(self._pins):
            pin.value(seq[i])
        self._position += richtung

    def _spulen_aus(self):
        """Schaltet alle Spulen stromlos (kein Haltemoment)."""
        for pin in self._pins:
            pin.value(0)

    # --- Blockierende Bewegungsbefehle --------------------------------------

    def schritte(self, n, richtung=VOR):
        """
        Faehrt n Schritte in der angegebenen Richtung (blockierend).

        Args:
            n: Anzahl Schritte (positiv)
            richtung: VOR (1) oder ZURUECK (-1)
        """
        if n < 0:
            raise ValueError("n muss positiv sein. Richtung ueber 'richtung' angeben.")
        for _ in range(n):
            self._schritt_setzen(richtung)
            time.sleep_us(self._intervall_us)

    def winkel(self, grad, richtung=VOR):
        """
        Dreht den Motor um den angegebenen Winkel in Grad (blockierend).

        Args:
            grad: Winkel in Grad (kann auch Kommazahl sein)
            richtung: VOR (1) oder ZURUECK (-1)
        """
        n = int(round(abs(grad) / 360.0 * self._schritte_pro_umdrehung))
        self.schritte(n, richtung)

    def umdrehungen(self, n, richtung=VOR):
        """
        Dreht den Motor um n volle Umdrehungen (blockierend).

        Args:
            n: Anzahl Umdrehungen (kann auch Kommazahl sein)
            richtung: VOR (1) oder ZURUECK (-1)
        """
        schritte = int(round(abs(n) * self._schritte_pro_umdrehung))
        self.schritte(schritte, richtung)

    # --- Nicht-blockierender Modus ------------------------------------------

    def starte(self, n, richtung=VOR):
        """
        Startet eine Bewegung von n Schritten ohne zu blockieren.

        Danach regelmaessig ausfuehren() im Hauptloop aufrufen.

        Args:
            n: Anzahl Schritte (positiv)
            richtung: VOR (1) oder ZURUECK (-1)
        """
        if n < 0:
            raise ValueError("n muss positiv sein. Richtung ueber 'richtung' angeben.")
        self._ziel = n
        self._richtung = richtung
        self._laufend = True
        self._naechster_schritt_us = time.ticks_us()

    def ausfuehren(self):
        """
        Fuehrt den naechsten faelligen Schritt aus (nicht-blockierend).

        Muss im Hauptloop regelmaessig aufgerufen werden. Gibt True zurueck,
        wenn in diesem Aufruf ein Schritt ausgefuehrt wurde.

        Returns:
            True wenn ein Schritt ausgefuehrt wurde, False sonst.
        """
        if not self._laufend or self._ziel <= 0:
            return False

        jetzt = time.ticks_us()
        if time.ticks_diff(jetzt, self._naechster_schritt_us) >= 0:
            self._schritt_setzen(self._richtung)
            self._ziel -= 1
            if self._ziel <= 0:
                self._laufend = False
                self._spulen_aus()
            else:
                self._naechster_schritt_us = time.ticks_add(
                    self._naechster_schritt_us, self._intervall_us)
            return True

        return False

    def ist_fertig(self):
        """
        Gibt True zurueck, wenn keine nicht-blockierende Bewegung mehr laeuft.

        Returns:
            bool: True wenn fertig oder keine Bewegung gestartet.
        """
        return not self._laufend

    def stopp(self):
        """Bricht eine laufende nicht-blockierende Bewegung sofort ab."""
        self._laufend = False
        self._ziel = 0
        self._spulen_aus()

    # --- Konfiguration & Status ---------------------------------------------

    def geschwindigkeit(self, sps):
        """
        Setzt die Motorgeschwindigkeit.

        Args:
            sps: Schritte pro Sekunde (z. B. 10 fuer 28BYJ-48 Standard,
                 max. ca. 900 sps bei 5 V)

        Raises:
            ValueError: Wenn sps <= 0.
        """
        if sps <= 0:
            raise ValueError("Geschwindigkeit muss groesser 0 sein.")
        self._intervall_us = int(1_000_000 / sps)

    def lese_position(self):
        """
        Gibt die aktuelle absolute Schrittposition zurueck.

        Die Position wird bei jedem Schritt um +1 (VOR) oder -1 (ZURUECK)
        veraendert. Beim Initialisieren startet sie bei 0.

        Returns:
            int: aktuelle Schrittposition
        """
        return self._position

    def aus(self):
        """Schaltet alle Motorspulen stromlos (kein Haltemoment)."""
        self._spulen_aus()

    def deinit(self):
        """Schaltet Spulen aus. (Pins werden in MicroPython nicht explizit freigegeben.)"""
        self._spulen_aus()


# ============================================================================
# Klasse: StepperDir (NEMA 17 u.a. + A4988 / DRV8825, STEP+DIR-Interface)
# ============================================================================

class StepperDir:
    """
    Steuert bipolare Schrittmotoren (z. B. NEMA 17) ueber einen
    STEP/DIR-Treiber wie den A4988 oder DRV8825.

    Das STEP+DIR-Interface erzeugt pro Schritt einen kurzen HIGH-Impuls
    auf dem STEP-Pin. Die Richtung wird ueber den DIR-Pin festgelegt.

    Unterstuetzte Hardware:
    - NEMA 17 (z. B. 17HS4401, 17HS2408) und andere bipolare Motoren
    - A4988, DRV8825, TMC2208 und kompatible STEP/DIR-Treiber

    Schnittstelle: STEP-Pin, DIR-Pin, optional ENABLE-Pin
    """

    # Mindestimpulsbreite STEP-Pin in Mikrosekunden (A4988: >= 1 us)
    _STEP_PULS_US = 2

    def __init__(self, step_pin, dir_pin, enable_pin=None,
                 schritte_pro_umdrehung=200, geschwindigkeit=100):
        """
        Initialisiert den STEP/DIR-Stepper.

        Args:
            step_pin: GPIO-Pin-Nummer fuer STEP
            dir_pin:  GPIO-Pin-Nummer fuer DIR
            enable_pin: GPIO-Pin-Nummer fuer ENABLE (optional).
                        Bei A4988/DRV8825 ist LOW = aktiv.
                        Falls angegeben, wird der Motor beim Initialisieren
                        sofort aktiviert.
            schritte_pro_umdrehung: Vollschritte pro Umdrehung
                                    (NEMA 17 Standard: 200)
            geschwindigkeit: Startgeschwindigkeit in Schritten/Sekunde
        """
        self._step = Pin(step_pin, Pin.OUT, value=0)
        self._dir = Pin(dir_pin, Pin.OUT, value=0)
        self._enable = None
        if enable_pin is not None:
            self._enable = Pin(enable_pin, Pin.OUT)
            self.aktivieren()

        self._schritte_pro_umdrehung = schritte_pro_umdrehung
        self._position = 0
        self._ziel = 0
        self._laufend = False
        self._richtung = VOR
        self._naechster_schritt_us = 0

        self.geschwindigkeit(geschwindigkeit)

    # --- Interne Helfer -----------------------------------------------------

    def _schritt_setzen(self, richtung):
        """Erzeugt einen STEP-Impuls und aktualisiert die Position."""
        self._dir.value(1 if richtung == VOR else 0)
        self._step.value(1)
        time.sleep_us(self._STEP_PULS_US)
        self._step.value(0)
        self._position += richtung

    # --- Blockierende Bewegungsbefehle --------------------------------------

    def schritte(self, n, richtung=VOR):
        """
        Faehrt n Schritte in der angegebenen Richtung (blockierend).

        Args:
            n: Anzahl Schritte (positiv)
            richtung: VOR (1) oder ZURUECK (-1)
        """
        if n < 0:
            raise ValueError("n muss positiv sein. Richtung ueber 'richtung' angeben.")
        for _ in range(n):
            self._schritt_setzen(richtung)
            time.sleep_us(self._intervall_us)

    def winkel(self, grad, richtung=VOR):
        """
        Dreht den Motor um den angegebenen Winkel in Grad (blockierend).

        Args:
            grad: Winkel in Grad (kann auch Kommazahl sein)
            richtung: VOR (1) oder ZURUECK (-1)
        """
        n = int(round(abs(grad) / 360.0 * self._schritte_pro_umdrehung))
        self.schritte(n, richtung)

    def umdrehungen(self, n, richtung=VOR):
        """
        Dreht den Motor um n volle Umdrehungen (blockierend).

        Args:
            n: Anzahl Umdrehungen (kann auch Kommazahl sein)
            richtung: VOR (1) oder ZURUECK (-1)
        """
        schritte = int(round(abs(n) * self._schritte_pro_umdrehung))
        self.schritte(schritte, richtung)

    # --- Nicht-blockierender Modus ------------------------------------------

    def starte(self, n, richtung=VOR):
        """
        Startet eine Bewegung von n Schritten ohne zu blockieren.

        Danach regelmaessig ausfuehren() im Hauptloop aufrufen.

        Args:
            n: Anzahl Schritte (positiv)
            richtung: VOR (1) oder ZURUECK (-1)
        """
        if n < 0:
            raise ValueError("n muss positiv sein. Richtung ueber 'richtung' angeben.")
        self._ziel = n
        self._richtung = richtung
        self._laufend = True
        self._naechster_schritt_us = time.ticks_us()

    def ausfuehren(self):
        """
        Fuehrt den naechsten faelligen Schritt aus (nicht-blockierend).

        Muss im Hauptloop regelmaessig aufgerufen werden. Gibt True zurueck,
        wenn in diesem Aufruf ein Schritt ausgefuehrt wurde.

        Returns:
            True wenn ein Schritt ausgefuehrt wurde, False sonst.
        """
        if not self._laufend or self._ziel <= 0:
            return False

        jetzt = time.ticks_us()
        if time.ticks_diff(jetzt, self._naechster_schritt_us) >= 0:
            self._schritt_setzen(self._richtung)
            self._ziel -= 1
            if self._ziel <= 0:
                self._laufend = False
            else:
                self._naechster_schritt_us = time.ticks_add(
                    self._naechster_schritt_us, self._intervall_us)
            return True

        return False

    def ist_fertig(self):
        """
        Gibt True zurueck, wenn keine nicht-blockierende Bewegung mehr laeuft.

        Returns:
            bool: True wenn fertig oder keine Bewegung gestartet.
        """
        return not self._laufend

    def stopp(self):
        """Bricht eine laufende nicht-blockierende Bewegung sofort ab."""
        self._laufend = False
        self._ziel = 0

    # --- Treiber-Verwaltung -------------------------------------------------

    def aktivieren(self):
        """
        Aktiviert den Motortreiber (ENABLE-Pin auf LOW).

        Nur wirksam, wenn ein ENABLE-Pin im Konstruktor angegeben wurde.
        """
        if self._enable is not None:
            self._enable.value(0)

    def deaktivieren(self):
        """
        Deaktiviert den Motortreiber (ENABLE-Pin auf HIGH).

        Der Motor wird stromlos; die mechanische Position bleibt erhalten
        (keine aktive Haltekraft mehr). Spart Strom und reduziert Waerme.

        Nur wirksam, wenn ein ENABLE-Pin im Konstruktor angegeben wurde.
        """
        if self._enable is not None:
            self._enable.value(1)

    # --- Konfiguration & Status ---------------------------------------------

    def geschwindigkeit(self, sps):
        """
        Setzt die Motorgeschwindigkeit.

        Args:
            sps: Schritte pro Sekunde (z. B. 200 bis 2000 fuer NEMA 17)

        Raises:
            ValueError: Wenn sps <= 0.
        """
        if sps <= 0:
            raise ValueError("Geschwindigkeit muss groesser 0 sein.")
        self._intervall_us = int(1_000_000 / sps)

    def lese_position(self):
        """
        Gibt die aktuelle absolute Schrittposition zurueck.

        Returns:
            int: aktuelle Schrittposition (0 = Startpunkt)
        """
        return self._position

    def aus(self):
        """Deaktiviert den Treiber (falls ENABLE-Pin vorhanden), STEP auf LOW."""
        self._step.value(0)
        self.deaktivieren()

    def deinit(self):
        """Schaltet STEP-Pin auf LOW und deaktiviert den Treiber."""
        self._step.value(0)
        self.deaktivieren()
