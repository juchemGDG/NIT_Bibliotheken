"""
NIT Bibliothek: GY61 - 3-Achsen Beschleunigungssensor (ADXL335)
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-07

Liest die drei analogen Achsen des GY-61 (ADXL335) ueber ADC ein und
rechnet Rohdaten in Spannung, g und m/s^2 um. Enthalten sind Kalibrierung,
Neigungswinkel (Pitch/Roll) und einfache Bewegungsdetektion.
"""

from machine import ADC, Pin
import math


class GY61:
    """
    Liest Beschleunigung und Neigung mit dem GY-61 (ADXL335) aus.

    Unterstuetzte Hardware:
    - GY-61 Breakout mit ADXL335
    - ADXL335-kompatible 3-Achsen Analogmodule

    Schnittstelle: 3x ADC (XOUT, YOUT, ZOUT)
    """

    ERDBESCHLEUNIGUNG = 9.81

    def __init__(
        self,
        x_pin,
        y_pin,
        z_pin,
        adc_bits=12,
        vref=3.3,
        sensitivitaet_v_g=0.3,
        attenuation="11db",
    ):
        """
        Initialisiert den GY-61 Sensor.

        Args:
            x_pin: GPIO fuer XOUT (ADC)
            y_pin: GPIO fuer YOUT (ADC)
            z_pin: GPIO fuer ZOUT (ADC)
            adc_bits: ADC-Aufloesung (9-12, ESP32 typisch 12)
            vref: Referenzspannung des ADC in Volt (typisch 3.3)
            sensitivitaet_v_g: Empfindlichkeit in Volt pro g (typisch ca. 0.3)
            attenuation: ADC-Daempfung ("0db", "2.5db", "6db", "11db")
        """
        self._adc_bits = max(9, min(12, int(adc_bits)))
        self._vref = float(vref)
        self._max_raw = (1 << self._adc_bits) - 1

        self._x_adc = ADC(Pin(x_pin))
        self._y_adc = ADC(Pin(y_pin))
        self._z_adc = ADC(Pin(z_pin))

        self._konfiguriere_adc(self._x_adc, attenuation)
        self._konfiguriere_adc(self._y_adc, attenuation)
        self._konfiguriere_adc(self._z_adc, attenuation)

        # Offset ist bei 0 g ungefaher mittig bei Vref/2.
        halbe_ref = self._vref / 2.0
        self._offset_x = halbe_ref
        self._offset_y = halbe_ref
        self._offset_z = halbe_ref

        self._sens_x = float(sensitivitaet_v_g)
        self._sens_y = float(sensitivitaet_v_g)
        self._sens_z = float(sensitivitaet_v_g)

    def _konfiguriere_adc(self, adc, attenuation):
        """Setzt ADC-Breite und Daempfung robust fuer verschiedene Builds."""
        try:
            width_const = getattr(ADC, "WIDTH_{}BIT".format(self._adc_bits))
            adc.width(width_const)
        except Exception:
            pass

        try:
            mapping = {
                "0db": ADC.ATTN_0DB,
                "2.5db": ADC.ATTN_2_5DB,
                "6db": ADC.ATTN_6DB,
                "11db": ADC.ATTN_11DB,
            }
            att = mapping.get(str(attenuation).lower(), ADC.ATTN_11DB)
            adc.atten(att)
        except Exception:
            pass

    def _roh_zu_spannung(self, rohwert):
        return (rohwert / self._max_raw) * self._vref

    def _spannung_zu_g(self, spannung, offset, sensitivitaet):
        if sensitivitaet == 0:
            raise ValueError("Sensitivitaet darf nicht 0 sein")
        return (spannung - offset) / sensitivitaet

    def lesen_roh(self):
        """
        Liest die ADC-Rohwerte aller drei Achsen.

        Returns:
            tuple: (x_raw, y_raw, z_raw)
        """
        return self._x_adc.read(), self._y_adc.read(), self._z_adc.read()

    def lesen_spannung(self):
        """
        Liest die Achsen als Spannung in Volt.

        Returns:
            tuple: (vx, vy, vz)
        """
        x_raw, y_raw, z_raw = self.lesen_roh()
        return (
            self._roh_zu_spannung(x_raw),
            self._roh_zu_spannung(y_raw),
            self._roh_zu_spannung(z_raw),
        )

    def lesen_g(self):
        """
        Liest die Beschleunigung in g.

        Returns:
            tuple: (ax, ay, az) in g
        """
        vx, vy, vz = self.lesen_spannung()
        return (
            self._spannung_zu_g(vx, self._offset_x, self._sens_x),
            self._spannung_zu_g(vy, self._offset_y, self._sens_y),
            self._spannung_zu_g(vz, self._offset_z, self._sens_z),
        )

    def lesen_ms2(self):
        """
        Liest die Beschleunigung in m/s^2.

        Returns:
            tuple: (ax, ay, az) in m/s^2
        """
        ax, ay, az = self.lesen_g()
        faktor = self.ERDBESCHLEUNIGUNG
        return ax * faktor, ay * faktor, az * faktor

    def betrag_g(self):
        """
        Berechnet den Betrag des Beschleunigungsvektors in g.

        Returns:
            float: Betrag in g
        """
        ax, ay, az = self.lesen_g()
        return math.sqrt(ax * ax + ay * ay + az * az)

    def neigung_grad(self):
        """
        Berechnet Pitch- und Roll-Winkel in Grad aus den Achsenwerten.

        Diese Berechnung ist fuer statische oder langsam bewegte Lagen geeignet.

        Returns:
            tuple: (pitch_grad, roll_grad)
        """
        ax, ay, az = self.lesen_g()
        pitch = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))
        roll = math.degrees(math.atan2(ay, az))
        return pitch, roll

    def ist_bewegt(self, schwelle_g=0.15):
        """
        Erkennt Bewegung ueber Abweichung vom erwarteten 1g-Betrag.

        Args:
            schwelle_g: Abweichung vom 1g-Ruhewert fuer True

        Returns:
            bool: True bei erkannter Bewegung
        """
        return abs(self.betrag_g() - 1.0) > float(schwelle_g)

    def set_offsets(self, offset_x, offset_y, offset_z):
        """
        Setzt die Offsets in Volt explizit.

        Args:
            offset_x: Offset X in Volt
            offset_y: Offset Y in Volt
            offset_z: Offset Z in Volt
        """
        self._offset_x = float(offset_x)
        self._offset_y = float(offset_y)
        self._offset_z = float(offset_z)

    def set_sensitivitaet(self, sens_x, sens_y, sens_z):
        """
        Setzt die Sensitivitaet je Achse in Volt pro g.

        Args:
            sens_x: Sensitivitaet X in V/g
            sens_y: Sensitivitaet Y in V/g
            sens_z: Sensitivitaet Z in V/g
        """
        self._sens_x = float(sens_x)
        self._sens_y = float(sens_y)
        self._sens_z = float(sens_z)

    def kalibrieren_ruhelage(self, samples=200, erwartung_g=(0.0, 0.0, 1.0)):
        """
        Kalibriert die Offset-Spannungen in einer definierten Ruhelage.

        Lege den Sensor waehrend der Kalibrierung ruhig auf den Tisch,
        typischerweise mit Z-Achse nach oben (erwartung_g=(0, 0, 1)).

        Args:
            samples: Anzahl Messungen fuer Mittelwert
            erwartung_g: Erwartete Achsenwerte in g als Tuple (x, y, z)

        Returns:
            tuple: (offset_x, offset_y, offset_z) in Volt
        """
        n = max(20, int(samples))
        sum_x = 0.0
        sum_y = 0.0
        sum_z = 0.0

        for _ in range(n):
            vx, vy, vz = self.lesen_spannung()
            sum_x += vx
            sum_y += vy
            sum_z += vz

        mx = sum_x / n
        my = sum_y / n
        mz = sum_z / n

        ex, ey, ez = erwartung_g
        self._offset_x = mx - float(ex) * self._sens_x
        self._offset_y = my - float(ey) * self._sens_y
        self._offset_z = mz - float(ez) * self._sens_z

        return self._offset_x, self._offset_y, self._offset_z

    def daten(self):
        """
        Liefert eine kompakte Gesamtausgabe.

        Returns:
            dict mit Rohwerten, Spannung, g, m/s^2, Betrag und Neigung
        """
        x_raw, y_raw, z_raw = self.lesen_roh()
        vx, vy, vz = self.lesen_spannung()
        ax, ay, az = self.lesen_g()
        mx, my, mz = self.lesen_ms2()
        pitch, roll = self.neigung_grad()

        return {
            "x_raw": x_raw,
            "y_raw": y_raw,
            "z_raw": z_raw,
            "vx": vx,
            "vy": vy,
            "vz": vz,
            "ax": ax,
            "ay": ay,
            "az": az,
            "mx": mx,
            "my": my,
            "mz": mz,
            "betrag_g": math.sqrt(ax * ax + ay * ay + az * az),
            "pitch": pitch,
            "roll": roll,
        }
