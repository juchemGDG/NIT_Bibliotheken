"""
NIT Bibliothek: Motor - Gleichstrommotoren ueber eine H-Bruecke (L298N)
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Volker Rust / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-11

Steuert Gleichstrommotoren ueber eine H-Bruecke: IN1/IN2 waehlen die
Drehrichtung, die Geschwindigkeit wird per PWM (duty_u16) am EN-Pin oder
direkt an IN1/IN2 ausgegeben. Die Klasse Fahrwerk kombiniert zwei Motoren
zu einem Differentialantrieb fuer Roboterautos.
"""

from machine import Pin, PWM
import time


# ============================================================================
# Konstanten
# ============================================================================

# Drehrichtungen (gleiche Werte wie in nitbw_stepper)
VOR = 1       # Vorwaerts
ZURUECK = -1  # Rueckwaerts

# Hoechster duty_u16-Wert (entspricht 100 % Einschaltdauer)
_DUTY_MAX = 65535


# ============================================================================
# Hilfsfunktionen
# ============================================================================

def _pwm_erstellen(pin_nr, freq):
    """
    Erstellt ein PWM-Objekt, das sofort mit 0 % startet.

    Ohne Startwert beginnt die ESP32-PWM mit 50 %, der Motor wuerde kurz
    anlaufen. Deshalb wird duty_u16=0 direkt im Konstruktor uebergeben.
    """
    try:
        return PWM(Pin(pin_nr), freq=freq, duty_u16=0)
    except TypeError:
        # Aeltere Firmware ohne Schluesselwort-Parameter im Konstruktor
        pwm = PWM(Pin(pin_nr))
        pwm.duty_u16(0)
        pwm.freq(freq)
        return pwm


def _pruefe_prozent(wert):
    """Prueft eine Geschwindigkeit ohne Vorzeichen (0 bis 100)."""
    if wert < 0 or wert > 100:
        raise ValueError("Geschwindigkeit ungueltig (erlaubt: 0 bis 100)")


def _pruefe_prozent_vorzeichen(wert, seite):
    """Prueft eine Geschwindigkeit mit Vorzeichen (-100 bis 100)."""
    if wert < -100 or wert > 100:
        raise ValueError(
            "Geschwindigkeit {} ungueltig (erlaubt: -100 bis 100)".format(seite))


# ============================================================================
# Klasse: Motor (ein Gleichstrommotor an einer H-Bruecke)
# ============================================================================

class Motor:
    """
    Steuert einen Gleichstrommotor ueber eine H-Bruecke in Richtung und Geschwindigkeit.

    Zwei Betriebsarten:
    - Mit EN-Pin (en angegeben, L298N ohne ENA-Jumper): PWM am EN-Pin,
      IN1/IN2 sind normale Ausgaenge und waehlen nur die Richtung.
    - Ohne EN-Pin (en=None, L298N mit gestecktem ENA-Jumper): PWM direkt
      an IN1 (vorwaerts) oder IN2 (rueckwaerts), der andere Pin bleibt LOW.

    Unterstuetzte Hardware:
    - L298N-Modul (Dual-H-Bruecke, Kanal A oder Kanal B)
    - L9110S, DRV8833, TB6612FNG im Zwei-Pin-PWM-Betrieb (en=None)

    Schnittstelle: PWM + GPIO (IN1, IN2, optional EN)
    """

    def __init__(self, in1, in2, en=None, freq=1000, min_prozent=0):
        """
        Initialisiert den Motor. Der Motor steht danach still.

        Args:
            in1: GPIO-Pin-Nummer fuer IN1 (am zweiten L298N-Kanal: IN3)
            in2: GPIO-Pin-Nummer fuer IN2 (am zweiten L298N-Kanal: IN4)
            en: GPIO-Pin-Nummer fuer ENA bzw. ENB (optional, Standard: None).
                Ohne EN-Pin wird die PWM direkt an IN1/IN2 ausgegeben;
                beim L298N muss dann der ENA-/ENB-Jumper gesteckt sein.
            freq: PWM-Frequenz in Hz (Standard: 1000)
            min_prozent: Anlaufschwelle in Prozent (Standard: 0).
                         Jede Geschwindigkeit von 1 bis 100 % wird linear
                         auf min_prozent bis 100 % abgebildet, 0 bleibt 0.
                         So laeuft der Motor schon bei kleinen Werten an.

        Raises:
            ValueError: Wenn min_prozent oder freq ungueltig sind.
        """
        if min_prozent < 0 or min_prozent >= 100:
            raise ValueError("min_prozent ungueltig (erlaubt: 0 bis 99)")
        if freq <= 0:
            raise ValueError("PWM-Frequenz muss groesser 0 sein.")

        self._in1_nr = in1
        self._in2_nr = in2
        self._en_nr = en
        self._min_prozent = min_prozent
        self._geschwindigkeit = 0

        if en is not None:
            # Richtungspins als normale Ausgaenge, PWM nur am EN-Pin
            self._in1 = Pin(in1, Pin.OUT, value=0)
            self._in2 = Pin(in2, Pin.OUT, value=0)
            self._en = _pwm_erstellen(en, freq)
            self._pwm1 = None
            self._pwm2 = None
        else:
            # EN ist dauerhaft HIGH (Jumper): PWM direkt an IN1 und IN2
            self._in1 = None
            self._in2 = None
            self._en = None
            self._pwm1 = _pwm_erstellen(in1, freq)
            self._pwm2 = _pwm_erstellen(in2, freq)

    # --- Interne Helfer -----------------------------------------------------

    def _duty(self, prozent):
        """Rechnet 0-100 % (mit Anlaufschwelle) in einen duty_u16-Wert um."""
        if prozent <= 0:
            return 0
        wirksam = self._min_prozent + (100 - self._min_prozent) * prozent / 100.0
        duty = int(wirksam * _DUTY_MAX / 100.0 + 0.5)
        return min(duty, _DUTY_MAX)

    def _ausgeben(self, richtung, duty):
        """Setzt Richtung (VOR/ZURUECK) und PWM-Wert an der H-Bruecke."""
        if self._en is not None:
            # Erst PWM setzen, dann den alten Richtungspin loesen und
            # zuletzt den neuen setzen (nie beide IN gleichzeitig HIGH)
            self._en.duty_u16(duty)
            if richtung == VOR:
                self._in2.value(0)
                self._in1.value(1)
            else:
                self._in1.value(0)
                self._in2.value(1)
        else:
            if richtung == VOR:
                self._pwm2.duty_u16(0)
                self._pwm1.duty_u16(duty)
            else:
                self._pwm1.duty_u16(0)
                self._pwm2.duty_u16(duty)

    # --- Kernfunktionen -----------------------------------------------------

    def drehen(self, geschwindigkeit, richtung=None):
        """
        Dreht den Motor mit einer bestimmten Geschwindigkeit.

        Args:
            geschwindigkeit: Geschwindigkeit in Prozent (-100 bis 100).
                             Positive Werte = VOR, negative = ZURUECK.
                             0 = Stillstand (wie stopp()).
                             Wenn richtung separat angegeben wird, nur 0-100.
            richtung: Optionale Drehrichtung (Standard: VOR).
                      VOR ( 1) = vorwaerts
                      ZURUECK (-1) = rueckwaerts
                      Wird automatisch aus dem Vorzeichen von geschwindigkeit
                      ermittelt, falls nicht angegeben.

        Raises:
            ValueError: Wenn Geschwindigkeit oder Richtung ungueltig sind.

        Beispiele:
            drehen(50)           # 50 % vorwaerts
            drehen(-50)          # 50 % rueckwaerts (Vorzeichen)
            drehen(50, VOR)      # 50 % vorwaerts (explizit)
            drehen(50, ZURUECK)  # 50 % rueckwaerts (explizit)
        """
        # Richtung aus Vorzeichen ableiten, wenn nicht explizit angegeben
        if richtung is None:
            if geschwindigkeit < 0:
                richtung = ZURUECK
                geschwindigkeit = -geschwindigkeit
            else:
                richtung = VOR

        if geschwindigkeit < 0 or geschwindigkeit > 100:
            raise ValueError(
                "Geschwindigkeit ungueltig (erlaubt: -100 bis 100 oder 0-100 mit Richtung)")
        if richtung not in (VOR, ZURUECK):
            raise ValueError(
                "Richtung ungueltig (erlaubt: VOR=1, ZURUECK=-1)")

        if geschwindigkeit == 0:
            self.stopp()
            return

        self._ausgeben(richtung, self._duty(geschwindigkeit))
        self._geschwindigkeit = geschwindigkeit * richtung

    def vor(self, geschwindigkeit=100):
        """
        Dreht den Motor vorwaerts.

        Args:
            geschwindigkeit: Geschwindigkeit in Prozent (0-100, Standard: 100)
        """
        self.drehen(geschwindigkeit, VOR)

    def zurueck(self, geschwindigkeit=100):
        """
        Dreht den Motor rueckwaerts.

        Args:
            geschwindigkeit: Geschwindigkeit in Prozent (0-100, Standard: 100)
        """
        self.drehen(geschwindigkeit, ZURUECK)

    def stopp(self):
        """
        Haelt den Motor an: beide IN auf LOW, PWM auf 0.

        Mit EN-Pin laeuft der Motor frei aus. Hinweis: Beim L298N mit
        gestecktem ENA-Jumper (Betrieb ohne EN-Pin) bedeutet IN1 = IN2 = LOW
        laut Datenblatt bereits ein Abbremsen; freies Auslaufen gibt es dort
        nicht.
        """
        if self._en is not None:
            self._en.duty_u16(0)
            self._in1.value(0)
            self._in2.value(0)
        else:
            self._pwm1.duty_u16(0)
            self._pwm2.duty_u16(0)
        self._geschwindigkeit = 0

    def bremsen(self):
        """
        Bremst den Motor aktiv ab: beide IN auf HIGH, EN voll an.

        Dabei schliesst die H-Bruecke die Motorwicklung kurz. Die Spannung,
        die der auslaufende Motor selbst erzeugt, bremst ihn ab; kurzzeitig
        fliesst ein hoher Strom. Die Bremse deshalb nur kurz halten
        (z. B. 200-500 ms) und danach stopp() aufrufen.
        """
        if self._en is not None:
            self._in1.value(1)
            self._in2.value(1)
            self._en.duty_u16(_DUTY_MAX)
        else:
            self._pwm1.duty_u16(_DUTY_MAX)
            self._pwm2.duty_u16(_DUTY_MAX)
        self._geschwindigkeit = 0

    def rampe(self, ziel, dauer_ms=1000, schritte=20):
        """
        Aendert die Geschwindigkeit sanft vom aktuellen Wert auf einen Zielwert.

        Schont Getriebe, Motor und Treiber, z. B. beim Anfahren oder bei
        einem Richtungswechsel. Ein Wechsel ueber 0 hinweg (z. B. von 80
        auf -80) kehrt die Drehrichtung um.

        Hinweis: Diese Funktion blockiert fuer dauer_ms Millisekunden.

        Args:
            ziel: Zielgeschwindigkeit in Prozent (-100 bis 100, Vorzeichen = Richtung)
            dauer_ms: Gesamtdauer der Rampe in ms (Standard: 1000)
            schritte: Anzahl der Zwischenschritte (Standard: 20)

        Raises:
            ValueError: Wenn ziel, dauer_ms oder schritte ungueltig sind.
        """
        if ziel < -100 or ziel > 100:
            raise ValueError("Zielgeschwindigkeit ungueltig (erlaubt: -100 bis 100)")
        if schritte < 1:
            raise ValueError("schritte muss mindestens 1 sein.")
        if dauer_ms < 0:
            raise ValueError("dauer_ms darf nicht negativ sein.")

        start = self._geschwindigkeit
        pause_ms = int(dauer_ms / schritte)

        for i in range(1, schritte + 1):
            if pause_ms > 0:
                time.sleep_ms(pause_ms)
            if i == schritte:
                wert = ziel
            else:
                wert = int(round(start + (ziel - start) * i / schritte))
            self.drehen(wert)

    # --- Status -------------------------------------------------------------

    def lese_geschwindigkeit(self):
        """
        Gibt die zuletzt eingestellte Geschwindigkeit zurueck.

        Es ist der angeforderte Wert, nicht der intern berechnete PWM-Wert
        (die Anlaufschwelle min_prozent ist darin nicht enthalten).

        Returns:
            int/float: -100 bis 100 (negativ = rueckwaerts, 0 = Stillstand)
        """
        return self._geschwindigkeit

    def lese_richtung(self):
        """
        Gibt die aktuelle Drehrichtung zurueck.

        Returns:
            VOR (1), ZURUECK (-1) oder 0 bei Stillstand
        """
        if self._geschwindigkeit > 0:
            return VOR
        if self._geschwindigkeit < 0:
            return ZURUECK
        return 0

    # --- Abschalten ---------------------------------------------------------

    def aus(self):
        """Haelt den Motor an (wie stopp())."""
        self.stopp()

    def deinit(self):
        """
        Haelt den Motor an und gibt die PWM-Kanaele frei.

        Die Pins werden danach fest auf LOW gelegt. Das Motor-Objekt
        anschliessend nicht mehr verwenden.
        """
        self.stopp()
        if self._en is not None:
            self._en.deinit()
            Pin(self._en_nr, Pin.OUT, value=0)
        else:
            self._pwm1.deinit()
            self._pwm2.deinit()
            Pin(self._in1_nr, Pin.OUT, value=0)
            Pin(self._in2_nr, Pin.OUT, value=0)


# ============================================================================
# Klasse: Fahrwerk (zwei Motoren als Differentialantrieb)
# ============================================================================

class Fahrwerk:
    """
    Steuert zwei Motoren als Differentialantrieb fuer ein Roboterauto.

    Gelenkt wird ueber unterschiedliche Geschwindigkeiten links und rechts.
    Laufen beide Raeder gegeneinander, dreht sich das Fahrzeug auf der Stelle.

    Unterstuetzte Hardware:
    - Roboter-Chassis mit zwei Getriebemotoren (z. B. TT-Motoren) an einem L298N
    - Beliebige zwei Motor-Objekte dieser Bibliothek

    Schnittstelle: zwei Motor-Objekte
    """

    def __init__(self, links, rechts):
        """
        Initialisiert das Fahrwerk.

        Args:
            links: Motor-Objekt fuer das linke Rad
            rechts: Motor-Objekt fuer das rechte Rad
        """
        self.motor_links = links
        self.motor_rechts = rechts

    def fahren(self, links, rechts):
        """
        Stellt beide Raeder getrennt ein.

        Args:
            links: Geschwindigkeit linkes Rad in Prozent (-100 bis 100)
            rechts: Geschwindigkeit rechtes Rad in Prozent (-100 bis 100)

        Raises:
            ValueError: Wenn ein Wert ausserhalb von -100 bis 100 liegt.

        Beispiele:
            fahren(60, 60)    # geradeaus
            fahren(30, 70)    # Linkskurve
            fahren(-50, 50)   # auf der Stelle nach links drehen
        """
        # Erst beide Werte pruefen, damit nicht nur ein Rad umschaltet
        _pruefe_prozent_vorzeichen(links, "links")
        _pruefe_prozent_vorzeichen(rechts, "rechts")
        self.motor_links.drehen(links)
        self.motor_rechts.drehen(rechts)

    def vor(self, geschwindigkeit=100):
        """
        Faehrt geradeaus vorwaerts.

        Args:
            geschwindigkeit: Geschwindigkeit in Prozent (0-100, Standard: 100)
        """
        _pruefe_prozent(geschwindigkeit)
        self.fahren(geschwindigkeit, geschwindigkeit)

    def zurueck(self, geschwindigkeit=100):
        """
        Faehrt geradeaus rueckwaerts.

        Args:
            geschwindigkeit: Geschwindigkeit in Prozent (0-100, Standard: 100)
        """
        _pruefe_prozent(geschwindigkeit)
        self.fahren(-geschwindigkeit, -geschwindigkeit)

    def links(self, geschwindigkeit=100):
        """
        Dreht auf der Stelle nach links (linkes Rad rueckwaerts, rechtes vorwaerts).

        Args:
            geschwindigkeit: Geschwindigkeit in Prozent (0-100, Standard: 100)
        """
        _pruefe_prozent(geschwindigkeit)
        self.fahren(-geschwindigkeit, geschwindigkeit)

    def rechts(self, geschwindigkeit=100):
        """
        Dreht auf der Stelle nach rechts (linkes Rad vorwaerts, rechtes rueckwaerts).

        Args:
            geschwindigkeit: Geschwindigkeit in Prozent (0-100, Standard: 100)
        """
        _pruefe_prozent(geschwindigkeit)
        self.fahren(geschwindigkeit, -geschwindigkeit)

    def stopp(self):
        """Haelt beide Motoren an (siehe Motor.stopp())."""
        self.motor_links.stopp()
        self.motor_rechts.stopp()

    def bremsen(self):
        """Bremst beide Motoren aktiv ab (nur kurz halten, siehe Motor.bremsen())."""
        self.motor_links.bremsen()
        self.motor_rechts.bremsen()

    def aus(self):
        """Haelt beide Motoren an (wie stopp())."""
        self.motor_links.aus()
        self.motor_rechts.aus()
