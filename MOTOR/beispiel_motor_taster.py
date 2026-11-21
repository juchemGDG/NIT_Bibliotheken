"""
Beispiel fuer NIT Bibliothek: Motor (Taster-Steuerung)
Zeigt: Geschwindigkeit mit Taster A in Stufen schalten, Richtung mit Taster B umkehren (ohne blockierende Pausen)
Hardware: L298N (Kanal A) mit DC-Motor, 2 Taster an GPIO 4 und GPIO 13 (jeweils nach 3.3 V)
"""

from machine import Pin
from nitbw_motor import Motor, VOR
import time


# --- Initialisierung ---
# Motor wie in beispiel_motor.py: ENA=23 (Jumper abziehen), IN1=16, IN2=17
motor = Motor(in1=16, in2=17, en=23)

STUFEN = (0, 25, 50, 75, 100)   # Geschwindigkeitsstufen in Prozent
ENTPRELL_MS = 30                # so lange muss ein Tasterzustand stabil sein
PAUSE_WECHSEL_MS = 300          # kurzer Stillstand beim Richtungswechsel


class Taster:
    """Erkennt Tastendruecke ohne zu blockieren (mit Entprellung)."""

    def __init__(self, pin_nr):
        # Taster schaltet nach 3.3 V, der interne Pull-Down haelt sonst LOW
        self.pin = Pin(pin_nr, Pin.IN, Pin.PULL_DOWN)
        self.roh = 0          # zuletzt gelesener Pegel
        self.stabil = 0       # entprellter Pegel
        self.zeit = time.ticks_ms()

    def gedrueckt(self):
        """Liefert genau einmal pro Tastendruck True (steigende Flanke)."""
        wert = self.pin.value()
        jetzt = time.ticks_ms()
        if wert != self.roh:
            # Pegel hat sich geaendert (evtl. Prellen): Zeit neu starten
            self.roh = wert
            self.zeit = jetzt
            return False
        if wert != self.stabil and time.ticks_diff(jetzt, self.zeit) >= ENTPRELL_MS:
            # Pegel ist lange genug stabil: als neuen Zustand uebernehmen
            self.stabil = wert
            return wert == 1
        return False


taster_a = Taster(4)    # Geschwindigkeit weiterschalten
taster_b = Taster(13)   # Richtung umkehren

stufe = 0
richtung = VOR
wechsel_aktiv = False   # True, solange die Pause beim Richtungswechsel laeuft
wechsel_ende = 0


def richtung_text(r):
    """Wandelt die Richtung in einen Text um."""
    if r == VOR:
        return "VOR"
    return "ZURUECK"


def motor_setzen():
    """Uebertraegt Stufe und Richtung auf den Motor und zeigt den Zustand an."""
    motor.drehen(STUFEN[stufe], richtung)
    print("Geschwindigkeit: {:3d} %   Richtung: {}".format(
        STUFEN[stufe], richtung_text(richtung)))


# --- Hauptprogramm ---
print("=== Motor mit Tastern ===")
print("Taster A (GPIO 4):  Geschwindigkeit 0 -> 25 -> 50 -> 75 -> 100 -> 0 %")
print("Taster B (GPIO 13): Richtung umkehren")
motor_setzen()

try:
    while True:
        jetzt = time.ticks_ms()

        # Taster A: naechste Geschwindigkeitsstufe
        if taster_a.gedrueckt():
            stufe = (stufe + 1) % len(STUFEN)
            wechsel_aktiv = False
            motor_setzen()

        # Taster B: Richtung umkehren
        if taster_b.gedrueckt():
            richtung = -richtung
            if STUFEN[stufe] > 0:
                # Laufenden Motor erst kurz anhalten (schont Motor und Treiber).
                # Statt zu warten, merken wir uns nur, wann die Pause endet.
                motor.stopp()
                wechsel_aktiv = True
                wechsel_ende = time.ticks_add(jetzt, PAUSE_WECHSEL_MS)
                print("Richtungswechsel nach {} ...".format(richtung_text(richtung)))
            else:
                motor_setzen()

        # Pause beim Richtungswechsel vorbei? Dann wieder anlaufen.
        if wechsel_aktiv and time.ticks_diff(jetzt, wechsel_ende) >= 0:
            wechsel_aktiv = False
            motor_setzen()

        time.sleep_ms(5)   # sehr kurze Pause, die Schleife bleibt reaktionsschnell

finally:
    # Auch bei Abbruch mit Ctrl+C den Motor anhalten
    motor.aus()
    print("Motor aus.")
