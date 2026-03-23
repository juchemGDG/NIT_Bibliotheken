"""
NIT Bibliothek: KY023 - Analoges Joystick-Modul mit Taster
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      NIT / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Direkte Auswertung der beiden Analogachsen (VRx/VRy) und des Tasters (SW)
ueber ADC- und GPIO-Pins. Enthaelt Kalibrierung, Normierung und Richtungslogik.
"""

from machine import ADC, Pin
import math


class KY023:
    """
    Liest ein KY-023 Joystick-Modul mit zwei Analogachsen und Taster aus.

    Unterstuetzte Hardware:
    - KY-023 Joystick-Modul
    - Kompatible 2-Achsen Analog-Joysticks mit Taster

    Schnittstelle: 2x ADC + 1x GPIO
    """

    def __init__(
        self,
        vrx_pin,
        vry_pin,
        sw_pin,
        adc_bits=12,
        deadzone=0.12,
        invert_x=False,
        invert_y=False,
        button_active_low=True,
    ):
        """
        Initialisiert den Joystick.

        Args:
            vrx_pin: GPIO fuer X-Achse (ADC)
            vry_pin: GPIO fuer Y-Achse (ADC)
            sw_pin: GPIO fuer Taster
            adc_bits: ADC-Aufloesung (9-12, ESP32 typisch 12)
            deadzone: Totzone fuer Richtungs- und Bewegungslogik (0.0-1.0)
            invert_x: X-Achse invertieren
            invert_y: Y-Achse invertieren
            button_active_low: True bei Pull-up und Taster nach GND
        """
        self.vrx = ADC(Pin(vrx_pin))
        self.vry = ADC(Pin(vry_pin))

        self.sw = Pin(sw_pin, Pin.IN, Pin.PULL_UP if button_active_low else None)
        self.button_active_low = button_active_low

        # ADC-Konfiguration robust fuer verschiedene MicroPython-Builds setzen.
        self.adc_bits = max(9, min(12, int(adc_bits)))
        try:
            self.vrx.width(getattr(ADC, "WIDTH_{}BIT".format(self.adc_bits)))
            self.vry.width(getattr(ADC, "WIDTH_{}BIT".format(self.adc_bits)))
        except Exception:
            pass

        try:
            self.vrx.atten(ADC.ATTN_11DB)
            self.vry.atten(ADC.ATTN_11DB)
        except Exception:
            pass

        self.max_raw = (1 << self.adc_bits) - 1
        self.center_x = self.max_raw // 2
        self.center_y = self.max_raw // 2

        self.deadzone = float(deadzone)
        self.invert_x = bool(invert_x)
        self.invert_y = bool(invert_y)

    def _clamp(self, value, min_value, max_value):
        return max(min_value, min(max_value, value))

    def _normalize_axis(self, raw, center):
        if raw >= center:
            den = max(1, self.max_raw - center)
            value = (raw - center) / den
        else:
            den = max(1, center)
            value = (raw - center) / den
        return self._clamp(value, -1.0, 1.0)

    def lesen_roh(self):
        """
        Liest Rohwerte.

        Returns:
            dict mit x_raw, y_raw und sw (True = gedrueckt)
        """
        x_raw = self.vrx.read()
        y_raw = self.vry.read()
        sw_raw = self.sw.value()
        gedrueckt = (sw_raw == 0) if self.button_active_low else (sw_raw == 1)

        return {
            "x_raw": x_raw,
            "y_raw": y_raw,
            "sw": gedrueckt,
        }

    def lesen_normiert(self):
        """
        Liest normierte Achswerte.

        Returns:
            dict mit x, y im Bereich -1.0..1.0 sowie sw
        """
        raw = self.lesen_roh()
        x = self._normalize_axis(raw["x_raw"], self.center_x)
        y = self._normalize_axis(raw["y_raw"], self.center_y)

        if self.invert_x:
            x = -x
        if self.invert_y:
            y = -y

        return {
            "x": x,
            "y": y,
            "sw": raw["sw"],
            "x_raw": raw["x_raw"],
            "y_raw": raw["y_raw"],
        }

    def kalibrieren_mitte(self, samples=100):
        """
        Kalibriert die Mittelstellung durch Mittelwertbildung.

        Args:
            samples: Anzahl Samples in Ruheposition

        Returns:
            tuple (center_x, center_y)
        """
        samples = max(10, int(samples))
        sum_x = 0
        sum_y = 0

        for _ in range(samples):
            sum_x += self.vrx.read()
            sum_y += self.vry.read()

        self.center_x = sum_x // samples
        self.center_y = sum_y // samples
        return self.center_x, self.center_y

    def set_deadzone(self, deadzone):
        """Setzt die Totzone fuer Bewegungsdetektion."""
        self.deadzone = self._clamp(float(deadzone), 0.0, 0.95)

    def gedrueckt(self):
        """True wenn der Taster gedrueckt ist."""
        sw_raw = self.sw.value()
        return (sw_raw == 0) if self.button_active_low else (sw_raw == 1)

    def betrag(self):
        """Liefert den Bewegungsbetrag 0.0..1.0 aus x/y."""
        n = self.lesen_normiert()
        return self._clamp(math.sqrt(n["x"] * n["x"] + n["y"] * n["y"]), 0.0, 1.0)

    def winkel_grad(self):
        """
        Liefert den Winkel in Grad.

        0 Grad = rechts, 90 Grad = oben, 180 Grad = links, 270 Grad = unten.
        """
        n = self.lesen_normiert()
        angle = math.degrees(math.atan2(n["y"], n["x"]))
        if angle < 0:
            angle += 360
        return angle

    def richtung(self):
        """
        Gibt die 8-Wege-Richtung oder MITTE zurueck.

        Returns:
            str: MITTE, RECHTS, LINKS, OBEN, UNTEN,
                 RECHTS_OBEN, RECHTS_UNTEN, LINKS_OBEN, LINKS_UNTEN
        """
        n = self.lesen_normiert()
        x = n["x"]
        y = n["y"]

        if abs(x) < self.deadzone and abs(y) < self.deadzone:
            return "MITTE"

        x_state = 0
        y_state = 0

        if x > self.deadzone:
            x_state = 1
        elif x < -self.deadzone:
            x_state = -1

        if y > self.deadzone:
            y_state = 1
        elif y < -self.deadzone:
            y_state = -1

        mapping = {
            (0, 0): "MITTE",
            (1, 0): "RECHTS",
            (-1, 0): "LINKS",
            (0, 1): "OBEN",
            (0, -1): "UNTEN",
            (1, 1): "RECHTS_OBEN",
            (1, -1): "RECHTS_UNTEN",
            (-1, 1): "LINKS_OBEN",
            (-1, -1): "LINKS_UNTEN",
        }
        return mapping[(x_state, y_state)]

    def daten(self):
        """
        Kompakte Statusausgabe.

        Returns:
            dict mit Rohdaten, normierten Werten, Richtung, Winkel und Taster
        """
        n = self.lesen_normiert()
        return {
            "x_raw": n["x_raw"],
            "y_raw": n["y_raw"],
            "x": n["x"],
            "y": n["y"],
            "richtung": self.richtung(),
            "winkel": self.winkel_grad(),
            "betrag": self._clamp(math.sqrt(n["x"] * n["x"] + n["y"] * n["y"]), 0.0, 1.0),
            "sw": n["sw"],
        }
