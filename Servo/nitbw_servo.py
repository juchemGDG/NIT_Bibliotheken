"""
NIT Bibliothek: Servo - Ansteuerung von Standard- und Continuous-Servos
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Volker Rust
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Steuert Standard-Servos (Winkelposition 0-180°) und Continuous-Rotation-Servos
(Drehzahl in Prozent + Drehrichtung) ueber PWM-Signale am ESP32.
"""

from machine import Pin, PWM


# ============================================================================
# Konstanten
# ============================================================================

# PWM-Frequenz fuer Servos (50 Hz = 20 ms Periodendauer, Servo-Standard)
_PWM_FREQ = 50

# Pulsbreiten in Mikrosekunden (typische Werte fuer SG90 / MG996R)
_PULS_MIN_US = 500       # 0.5 ms -> 0°
_PULS_MAX_US = 2500      # 2.5 ms -> 180°
_PULS_MITTE_US = 1500    # 1.5 ms -> 90° / Stillstand bei Continuous

# ESP32 PWM-Aufloesung: duty wird in 0-1023 angegeben (10-Bit)
_DUTY_MAX = 1023

# Periodendauer in Mikrosekunden bei 50 Hz
_PERIOD_US = 20000  # 1 / 50 Hz = 20 ms = 20 000 us


# ============================================================================
# Hilfsfunktionen
# ============================================================================

def _us_zu_duty(puls_us):
    """Rechnet eine Pulsbreite (Mikrosekunden) in einen PWM-Duty-Wert um."""
    return int(puls_us / _PERIOD_US * _DUTY_MAX)


# ============================================================================
# Klasse: Servo (Standard-Servo, 0-180°)
# ============================================================================

class Servo:
    """
    Steuert einen Standard-Servo (Winkelposition 0-180°).

    Unterstuetzte Hardware:
    - SG90, SG92R, MG90S, MG996R und kompatible PWM-Servos

    Schnittstelle: PWM (ein GPIO-Pin)
    """

    def __init__(self, pin, puls_min_us=_PULS_MIN_US, puls_max_us=_PULS_MAX_US,
                 winkel_min=0, winkel_max=180):
        """
        Initialisiert den Standard-Servo.

        Args:
            pin: GPIO-Pin-Nummer (z. B. 13)
            puls_min_us: Pulsbreite fuer Minimalwinkel in us (Standard: 500)
            puls_max_us: Pulsbreite fuer Maximalwinkel in us (Standard: 2500)
            winkel_min: Minimaler Winkel in Grad (Standard: 0)
            winkel_max: Maximaler Winkel in Grad (Standard: 180)
        """
        self._pin_nr = pin
        self._pwm = PWM(Pin(pin))
        self._pwm.freq(_PWM_FREQ)
        self._puls_min = puls_min_us
        self._puls_max = puls_max_us
        self._winkel_min = winkel_min
        self._winkel_max = winkel_max
        self._aktueller_winkel = None

    # --- Kernfunktionen -----------------------------------------------------

    def winkel(self, grad):
        """
        Faehrt den Servo auf einen bestimmten Winkel.

        Args:
            grad: Zielwinkel in Grad (Standard: 0-180)

        Raises:
            ValueError: Wenn der Winkel ausserhalb des gueltigen Bereichs liegt.
        """
        if grad < self._winkel_min or grad > self._winkel_max:
            raise ValueError(
                "Winkel {} ausserhalb des Bereichs ({}-{})".format(
                    grad, self._winkel_min, self._winkel_max))

        # Linear interpolieren: Winkel -> Pulsbreite
        anteil = (grad - self._winkel_min) / (self._winkel_max - self._winkel_min)
        puls_us = self._puls_min + anteil * (self._puls_max - self._puls_min)
        self._pwm.duty(_us_zu_duty(puls_us))
        self._aktueller_winkel = grad

    def mitte(self):
        """Faehrt den Servo auf die Mittelposition (90° bei 0-180°)."""
        mitte = (self._winkel_min + self._winkel_max) // 2
        self.winkel(mitte)

    def minimum(self):
        """Faehrt den Servo auf den Minimalwinkel."""
        self.winkel(self._winkel_min)

    def maximum(self):
        """Faehrt den Servo auf den Maximalwinkel."""
        self.winkel(self._winkel_max)

    def puls(self, puls_us):
        """
        Setzt die Pulsbreite direkt (fuer Feinabstimmung).

        Args:
            puls_us: Pulsbreite in Mikrosekunden (z. B. 500-2500)
        """
        self._pwm.duty(_us_zu_duty(puls_us))

    def lese_winkel(self):
        """
        Gibt den zuletzt gesetzten Winkel zurueck.

        Returns:
            int/float oder None, falls noch kein Winkel gesetzt wurde.
        """
        return self._aktueller_winkel

    def aus(self):
        """Schaltet das PWM-Signal ab (Servo wird stromlos)."""
        self._pwm.duty(0)

    def deinit(self):
        """Gibt den PWM-Pin wieder frei."""
        self._pwm.deinit()


# ============================================================================
# Klasse: ContinuousServo (Endlos-Drehung)
# ============================================================================

class ContinuousServo:
    """
    Steuert einen Continuous-Rotation-Servo (endlose Drehung).

    Steuerung ueber Geschwindigkeit in Prozent (0-100 %) und Drehrichtung.
    Intern wird die Pulsbreite symmetrisch um den Stillstandspunkt (1500 us)
    nach oben oder unten verschoben.

    Unterstuetzte Hardware:
    - FS90R, SM-S4303R und kompatible 360°-Servos

    Schnittstelle: PWM (ein GPIO-Pin)
    """

    # Drehrichtungs-Konstanten
    RECHTS = 1    # Uhrzeigersinn (von vorne betrachtet)
    LINKS = -1    # Gegen Uhrzeigersinn (von vorne betrachtet)

    def __init__(self, pin, puls_mitte_us=_PULS_MITTE_US,
                 puls_min_us=_PULS_MIN_US, puls_max_us=_PULS_MAX_US):
        """
        Initialisiert den Continuous-Rotation-Servo.

        Args:
            pin: GPIO-Pin-Nummer (z. B. 14)
            puls_mitte_us: Pulsbreite fuer Stillstand in us (Standard: 1500)
            puls_min_us: Pulsbreite fuer volle Drehzahl rueckwaerts (Standard: 500)
            puls_max_us: Pulsbreite fuer volle Drehzahl vorwaerts (Standard: 2500)
        """
        self._pin_nr = pin
        self._pwm = PWM(Pin(pin))
        self._pwm.freq(_PWM_FREQ)
        self._puls_mitte = puls_mitte_us
        self._puls_min = puls_min_us
        self._puls_max = puls_max_us

    # --- Kernfunktionen -----------------------------------------------------

    def drehen(self, geschwindigkeit, richtung=None):
        """
        Dreht den Servo mit einer bestimmten Geschwindigkeit.

        Args:
            geschwindigkeit: Drehzahl in Prozent (-100 bis 100).
                             Positive Werte = RECHTS, negative = LINKS.
                             0 = Stillstand.
                             Wenn richtung separat angegeben wird, nur 0-100.
            richtung: Optionale Drehrichtung (Standard: RECHTS).
                      ContinuousServo.RECHTS ( 1) = Uhrzeigersinn
                      ContinuousServo.LINKS  (-1) = Gegen Uhrzeigersinn
                      Wird automatisch aus dem Vorzeichen von geschwindigkeit
                      ermittelt, falls nicht angegeben.

        Beispiele:
            drehen(50)          # 50 % nach rechts (Standard)
            drehen(-50)         # 50 % nach links  (Vorzeichen)
            drehen(50, RECHTS)  # 50 % nach rechts (explizit)
            drehen(50, -1)      # 50 % nach links  (explizit)
        """
        # Richtung aus Vorzeichen ableiten, wenn nicht explizit angegeben
        if richtung is None:
            if geschwindigkeit < 0:
                richtung = self.LINKS
                geschwindigkeit = -geschwindigkeit
            else:
                richtung = self.RECHTS

        if geschwindigkeit < 0 or geschwindigkeit > 100:
            raise ValueError(
                "Geschwindigkeit ungueltig (erlaubt: -100 bis 100 oder 0-100 mit Richtung)")
        if richtung not in (self.RECHTS, self.LINKS):
            raise ValueError(
                "Richtung ungueltig (erlaubt: RECHTS=1, LINKS=-1)")

        if geschwindigkeit == 0:
            self.stopp()
            return

        # Anteil berechnen (0.0 - 1.0)
        anteil = geschwindigkeit / 100.0

        if richtung == self.RECHTS:
            # Uhrzeigersinn: Puls von Mitte Richtung Maximum
            puls_us = self._puls_mitte + anteil * (self._puls_max - self._puls_mitte)
        else:
            # Gegen Uhrzeigersinn: Puls von Mitte Richtung Minimum
            puls_us = self._puls_mitte - anteil * (self._puls_mitte - self._puls_min)

        self._pwm.duty(_us_zu_duty(puls_us))

    def stopp(self):
        """Haelt den Servo an (setzt Puls auf den Stillstandspunkt)."""
        self._pwm.duty(_us_zu_duty(self._puls_mitte))

    def puls(self, puls_us):
        """
        Setzt die Pulsbreite direkt (fuer Feinabstimmung / Totpunkt-Kalibrierung).

        Args:
            puls_us: Pulsbreite in Mikrosekunden
        """
        self._pwm.duty(_us_zu_duty(puls_us))

    def aus(self):
        """Schaltet das PWM-Signal ab (Servo wird stromlos)."""
        self._pwm.duty(0)

    def deinit(self):
        """Gibt den PWM-Pin wieder frei."""
        self._pwm.deinit()
