"""
NIT Bibliothek: REGLER - Einfache Regler fuer den Unterricht
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      NIT Team / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Enthaelt Zweipunkt-, P-, I-, D- und PID-Regler inklusive PI/PD-Kombination.
Erweitert um Sensor-/Aktor-Adapter fuer direkten Hardwareeinsatz mit PWM (8-10 Bit).
Zusaetzlich kann ein didaktischer Monitor Regelgroessen sammeln und als Texttrend darstellen.
"""


try:
    from machine import Pin, PWM
except ImportError:
    Pin = None
    PWM = None


class _BasisRegler:
    """Gemeinsame Grundfunktionen fuer alle Regler."""

    def __init__(
        self,
        sollwert=0.0,
        ausgang_min=0.0,
        ausgang_max=100.0,
        bias=0.0,
        eingang_min=None,
        eingang_max=None,
    ):
        self.sollwert = float(sollwert)
        self.ausgang_min = float(ausgang_min)
        self.ausgang_max = float(ausgang_max)
        self.bias = float(bias)
        self.eingang_min = eingang_min
        self.eingang_max = eingang_max

        self.istwert = 0.0
        self.fehler = 0.0
        self.ausgang = 0.0

    def set_sollwert(self, sollwert):
        self.sollwert = float(sollwert)

    def set_ausgangsgrenzen(self, minimum, maximum):
        self.ausgang_min = float(minimum)
        self.ausgang_max = float(maximum)

    def set_eingangsgrenzen(self, minimum=None, maximum=None):
        self.eingang_min = minimum
        self.eingang_max = maximum

    def reset(self):
        self.istwert = 0.0
        self.fehler = 0.0
        self.ausgang = 0.0

    def status(self):
        return {
            "sollwert": self.sollwert,
            "istwert": self.istwert,
            "fehler": self.fehler,
            "ausgang": self.ausgang,
        }

    def _clip(self, wert):
        if wert < self.ausgang_min:
            return self.ausgang_min
        if wert > self.ausgang_max:
            return self.ausgang_max
        return wert

    def _clip_input(self, istwert):
        wert = float(istwert)
        if self.eingang_min is not None and wert < self.eingang_min:
            wert = float(self.eingang_min)
        if self.eingang_max is not None and wert > self.eingang_max:
            wert = float(self.eingang_max)
        return wert


class Zweipunktregler(_BasisRegler):
    """
    Zweipunktregler mit Schaltbreite und Hysterese.

    Typischer Einsatz: Heizung, Kuehlung oder EIN/AUS-Aktoren.
    """

    def __init__(
        self,
        sollwert=0.0,
        breite=0.0,
        hysterese=1.0,
        ausgang_min=0.0,
        ausgang_max=100.0,
        invertiert=False,
        eingang_min=None,
        eingang_max=None,
    ):
        super().__init__(
            sollwert=sollwert,
            ausgang_min=ausgang_min,
            ausgang_max=ausgang_max,
            eingang_min=eingang_min,
            eingang_max=eingang_max,
        )
        self.breite = float(breite)
        self.hysterese = float(hysterese)
        self.invertiert = bool(invertiert)
        self._ein = False

    def set_breite(self, breite):
        self.breite = float(breite)

    def set_hysterese(self, hysterese):
        self.hysterese = float(hysterese)

    def reset(self):
        super().reset()
        self._ein = False

    def update(self, istwert):
        self.istwert = self._clip_input(istwert)
        self.fehler = self.sollwert - self.istwert

        untere_grenze = self.sollwert - (self.breite / 2.0)
        obere_grenze = self.sollwert + (self.breite / 2.0)

        ein_schwelle = untere_grenze - (self.hysterese / 2.0)
        aus_schwelle = obere_grenze + (self.hysterese / 2.0)

        if not self.invertiert:
            if self.istwert <= ein_schwelle:
                self._ein = True
            elif self.istwert >= aus_schwelle:
                self._ein = False
        else:
            if self.istwert >= aus_schwelle:
                self._ein = True
            elif self.istwert <= ein_schwelle:
                self._ein = False

        self.ausgang = self.ausgang_max if self._ein else self.ausgang_min
        return self.ausgang

    def status(self):
        s = super().status()
        s.update({
            "typ": "Zweipunkt",
            "breite": self.breite,
            "hysterese": self.hysterese,
            "ein": self._ein,
        })
        return s


class PRegler(_BasisRegler):
    """Proportionalregler: u = bias + Kp * e"""

    def __init__(
        self,
        kp=1.0,
        sollwert=0.0,
        ausgang_min=0.0,
        ausgang_max=100.0,
        bias=0.0,
        eingang_min=None,
        eingang_max=None,
    ):
        super().__init__(
            sollwert=sollwert,
            ausgang_min=ausgang_min,
            ausgang_max=ausgang_max,
            bias=bias,
            eingang_min=eingang_min,
            eingang_max=eingang_max,
        )
        self.kp = float(kp)
        self.p_anteil = 0.0

    def set_kp(self, kp):
        self.kp = float(kp)

    def update(self, istwert):
        self.istwert = self._clip_input(istwert)
        self.fehler = self.sollwert - self.istwert

        self.p_anteil = self.kp * self.fehler
        self.ausgang = self._clip(self.bias + self.p_anteil)
        return self.ausgang

    def status(self):
        s = super().status()
        s.update({"typ": "P", "kp": self.kp, "p": self.p_anteil})
        return s


class IRegler(_BasisRegler):
    """Integralregler: u = bias + Integral(Ki * e * dt)"""

    def __init__(
        self,
        ki=0.1,
        sollwert=0.0,
        ausgang_min=0.0,
        ausgang_max=100.0,
        bias=0.0,
        i_min=-1000.0,
        i_max=1000.0,
        eingang_min=None,
        eingang_max=None,
    ):
        super().__init__(
            sollwert=sollwert,
            ausgang_min=ausgang_min,
            ausgang_max=ausgang_max,
            bias=bias,
            eingang_min=eingang_min,
            eingang_max=eingang_max,
        )
        self.ki = float(ki)
        self.i_min = float(i_min)
        self.i_max = float(i_max)
        self.i_anteil = 0.0

    def set_ki(self, ki):
        self.ki = float(ki)

    def reset(self):
        super().reset()
        self.i_anteil = 0.0

    def update(self, istwert, dt=1.0):
        dt = 1.0 if dt <= 0 else float(dt)

        self.istwert = self._clip_input(istwert)
        self.fehler = self.sollwert - self.istwert

        self.i_anteil += self.ki * self.fehler * dt
        if self.i_anteil < self.i_min:
            self.i_anteil = self.i_min
        if self.i_anteil > self.i_max:
            self.i_anteil = self.i_max

        self.ausgang = self._clip(self.bias + self.i_anteil)
        return self.ausgang

    def status(self):
        s = super().status()
        s.update({"typ": "I", "ki": self.ki, "i": self.i_anteil})
        return s


class DRegler(_BasisRegler):
    """Differentialregler: u = bias + Kd * de/dt"""

    def __init__(
        self,
        kd=0.1,
        sollwert=0.0,
        ausgang_min=0.0,
        ausgang_max=100.0,
        bias=0.0,
        alpha=0.0,
        eingang_min=None,
        eingang_max=None,
    ):
        super().__init__(
            sollwert=sollwert,
            ausgang_min=ausgang_min,
            ausgang_max=ausgang_max,
            bias=bias,
            eingang_min=eingang_min,
            eingang_max=eingang_max,
        )
        self.kd = float(kd)
        self.alpha = float(alpha)
        self._letzter_fehler = None
        self.d_anteil = 0.0

    def set_kd(self, kd):
        self.kd = float(kd)

    def reset(self):
        super().reset()
        self._letzter_fehler = None
        self.d_anteil = 0.0

    def update(self, istwert, dt=1.0):
        dt = 1.0 if dt <= 0 else float(dt)

        self.istwert = self._clip_input(istwert)
        self.fehler = self.sollwert - self.istwert

        if self._letzter_fehler is None:
            roh_d = 0.0
        else:
            roh_d = self.kd * (self.fehler - self._letzter_fehler) / dt

        self.d_anteil = (self.alpha * self.d_anteil) + ((1.0 - self.alpha) * roh_d)
        self._letzter_fehler = self.fehler

        self.ausgang = self._clip(self.bias + self.d_anteil)
        return self.ausgang

    def status(self):
        s = super().status()
        s.update({"typ": "D", "kd": self.kd, "d": self.d_anteil})
        return s


class PIDRegler(_BasisRegler):
    """PID-Regler mit optionalen PI- und PD-Kombinationen ueber Parameter."""

    def __init__(
        self,
        kp=1.0,
        ki=0.0,
        kd=0.0,
        sollwert=0.0,
        ausgang_min=0.0,
        ausgang_max=100.0,
        bias=0.0,
        i_min=-1000.0,
        i_max=1000.0,
        alpha=0.0,
        eingang_min=None,
        eingang_max=None,
    ):
        super().__init__(
            sollwert=sollwert,
            ausgang_min=ausgang_min,
            ausgang_max=ausgang_max,
            bias=bias,
            eingang_min=eingang_min,
            eingang_max=eingang_max,
        )
        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)
        self.i_min = float(i_min)
        self.i_max = float(i_max)
        self.alpha = float(alpha)

        self.p_anteil = 0.0
        self.i_anteil = 0.0
        self.d_anteil = 0.0
        self._letzter_fehler = None

    def set_parameter(self, kp=None, ki=None, kd=None):
        if kp is not None:
            self.kp = float(kp)
        if ki is not None:
            self.ki = float(ki)
        if kd is not None:
            self.kd = float(kd)

    def reset(self):
        super().reset()
        self.p_anteil = 0.0
        self.i_anteil = 0.0
        self.d_anteil = 0.0
        self._letzter_fehler = None

    def update(self, istwert, dt=1.0):
        dt = 1.0 if dt <= 0 else float(dt)

        self.istwert = self._clip_input(istwert)
        self.fehler = self.sollwert - self.istwert

        self.p_anteil = self.kp * self.fehler

        self.i_anteil += self.ki * self.fehler * dt
        if self.i_anteil < self.i_min:
            self.i_anteil = self.i_min
        if self.i_anteil > self.i_max:
            self.i_anteil = self.i_max

        if self._letzter_fehler is None:
            roh_d = 0.0
        else:
            roh_d = self.kd * (self.fehler - self._letzter_fehler) / dt

        self.d_anteil = (self.alpha * self.d_anteil) + ((1.0 - self.alpha) * roh_d)
        self._letzter_fehler = self.fehler

        self.ausgang = self._clip(self.bias + self.p_anteil + self.i_anteil + self.d_anteil)
        return self.ausgang

    def status(self):
        s = super().status()
        s.update({
            "typ": "PID",
            "kp": self.kp,
            "ki": self.ki,
            "kd": self.kd,
            "p": self.p_anteil,
            "i": self.i_anteil,
            "d": self.d_anteil,
        })
        return s


class PIRegler(PIDRegler):
    """PI-Regler als PID-Spezialisierung (Kd=0)."""

    def __init__(
        self,
        kp=1.0,
        ki=0.1,
        sollwert=0.0,
        ausgang_min=0.0,
        ausgang_max=100.0,
        bias=0.0,
        i_min=-1000.0,
        i_max=1000.0,
        eingang_min=None,
        eingang_max=None,
    ):
        super().__init__(
            kp=kp,
            ki=ki,
            kd=0.0,
            sollwert=sollwert,
            ausgang_min=ausgang_min,
            ausgang_max=ausgang_max,
            bias=bias,
            i_min=i_min,
            i_max=i_max,
            alpha=0.0,
            eingang_min=eingang_min,
            eingang_max=eingang_max,
        )

    def status(self):
        s = super().status()
        s["typ"] = "PI"
        return s


class PDRegler(PIDRegler):
    """PD-Regler als PID-Spezialisierung (Ki=0)."""

    def __init__(
        self,
        kp=1.0,
        kd=0.1,
        sollwert=0.0,
        ausgang_min=0.0,
        ausgang_max=100.0,
        bias=0.0,
        alpha=0.0,
        eingang_min=None,
        eingang_max=None,
    ):
        super().__init__(
            kp=kp,
            ki=0.0,
            kd=kd,
            sollwert=sollwert,
            ausgang_min=ausgang_min,
            ausgang_max=ausgang_max,
            bias=bias,
            i_min=0.0,
            i_max=0.0,
            alpha=alpha,
            eingang_min=eingang_min,
            eingang_max=eingang_max,
        )

    def status(self):
        s = super().status()
        s["typ"] = "PD"
        return s


class ReglerMonitor:
    """
    Sammelt Regelgroessen und erzeugt eine einfache Textdarstellung.

    Kann direkt im Unterricht genutzt werden, auch ohne Grafikbibliothek.
    """

    def __init__(self, max_punkte=120):
        self.max_punkte = int(max_punkte)
        self.punkte = []

    def reset(self):
        self.punkte = []

    def add(self, zeit, sollwert, istwert, ausgang, fehler=None):
        if fehler is None:
            fehler = float(sollwert) - float(istwert)

        eintrag = {
            "zeit": float(zeit),
            "soll": float(sollwert),
            "ist": float(istwert),
            "fehler": float(fehler),
            "ausgang": float(ausgang),
        }
        self.punkte.append(eintrag)

        if len(self.punkte) > self.max_punkte:
            self.punkte = self.punkte[-self.max_punkte:]

    def letzte_werte(self):
        if not self.punkte:
            return None
        return self.punkte[-1]

    def als_tabelle(self, start=-10):
        if not self.punkte:
            return "(keine Daten)"

        daten = self.punkte[start:]
        zeilen = [" t[s] |   soll |    ist | fehler | ausgang"]
        zeilen.append("-------------------------------------------")
        for p in daten:
            zeilen.append("{:5.1f} | {:6.2f} | {:6.2f} | {:6.2f} | {:7.2f}".format(
                p["zeit"], p["soll"], p["ist"], p["fehler"], p["ausgang"]
            ))
        return "\n".join(zeilen)

    def trend(self, signal="ist", breite=60):
        if not self.punkte:
            return "(keine Daten)"

        if signal not in ("soll", "ist", "fehler", "ausgang"):
            return "(ungueltiges Signal)"

        werte = [p[signal] for p in self.punkte]
        if len(werte) > breite:
            schritt = len(werte) / float(breite)
            kompakt = []
            index = 0.0
            while int(index) < len(werte) and len(kompakt) < breite:
                kompakt.append(werte[int(index)])
                index += schritt
            werte = kompakt

        minimum = min(werte)
        maximum = max(werte)

        if abs(maximum - minimum) < 1e-9:
            return signal + ": " + ("-" * len(werte)) + "  min=max={:.2f}".format(minimum)

        palette = " .:-=+*#%@"
        skala = len(palette) - 1

        chars = []
        for v in werte:
            norm = (v - minimum) / (maximum - minimum)
            idx = int(norm * skala)
            chars.append(palette[idx])

        return "{}: {}  min={:.2f} max={:.2f}".format(signal, "".join(chars), minimum, maximum)


class SensorAdapter:
    """
    Kapselt den Zugriff auf einen Sensorwert.

    Der Sensor wird als Funktion uebergeben, die bei jedem Aufruf einen float liefert.
    """

    def __init__(self, read_func, minimum=None, maximum=None):
        self.read_func = read_func
        self.minimum = minimum
        self.maximum = maximum

    def lesen(self):
        wert = float(self.read_func())
        if self.minimum is not None and wert < self.minimum:
            wert = float(self.minimum)
        if self.maximum is not None and wert > self.maximum:
            wert = float(self.maximum)
        return wert


class PWMAktor:
    """
    Einfache PWM-Ausgabe mit einstellbarer Aufloesung (typisch 8-10 Bit).

    Schnittstelle: GPIO-Pin des ESP32 mit machine.PWM
    """

    def __init__(self, pin, freq=1000, bits=10):
        if PWM is None or Pin is None:
            raise RuntimeError("machine.PWM ist nur auf MicroPython-Hardware verfuegbar")

        self.bits = int(bits)
        if self.bits < 1:
            self.bits = 1
        if self.bits > 16:
            self.bits = 16

        self.max_wert = (1 << self.bits) - 1
        self.pwm = PWM(Pin(pin), freq=int(freq))
        self.letzter_rohwert = 0

    def schreibe_roh(self, rohwert):
        wert = int(rohwert)
        if wert < 0:
            wert = 0
        if wert > self.max_wert:
            wert = self.max_wert

        self.letzter_rohwert = wert

        # Unterstuetzt alte und neue PWM-API in MicroPython.
        if hasattr(self.pwm, "duty"):
            # Bei ESP32 meist 10 Bit -> Wertebereich 0..1023.
            if self.max_wert == 1023:
                self.pwm.duty(wert)
            else:
                duty_10bit = int((wert / self.max_wert) * 1023)
                self.pwm.duty(duty_10bit)
            return

        if hasattr(self.pwm, "duty_u16"):
            duty_u16 = int((wert / self.max_wert) * 65535)
            self.pwm.duty_u16(duty_u16)

    def schreibe_prozent(self, prozent):
        p = float(prozent)
        if p < 0.0:
            p = 0.0
        if p > 100.0:
            p = 100.0
        roh = int((p / 100.0) * self.max_wert)
        self.schreibe_roh(roh)
        return roh

    def aus(self):
        self.schreibe_roh(0)


class Regelkanal:
    """
    Verbindet Regler, Sensor und Aktor zu einem kompletten Regelkreis.

    Die Reglerberechnung, Sensorabfrage und Aktoransteuerung laufen in `step()`.
    """

    def __init__(
        self,
        regler,
        sensor,
        aktor=None,
        output_mode="raw",
        output_min=0.0,
        output_max=1023.0,
    ):
        self.regler = regler
        self.sensor = sensor
        self.aktor = aktor
        self.output_mode = output_mode
        self.output_min = float(output_min)
        self.output_max = float(output_max)

        self.letzter_istwert = None
        self.letzter_reglerwert = 0.0
        self.letzter_outputwert = 0.0

    def set_output_grenzen(self, minimum, maximum):
        self.output_min = float(minimum)
        self.output_max = float(maximum)

    def _run_regler(self, istwert, dt):
        try:
            return self.regler.update(istwert, dt=dt)
        except TypeError:
            return self.regler.update(istwert)

    def _scale_output(self, reglerwert):
        # output_mode='percent': Regler liefert 0..100 Prozent.
        if self.output_mode == "percent":
            wert = float(reglerwert)
            if wert < 0.0:
                wert = 0.0
            if wert > 100.0:
                wert = 100.0
            return self.output_min + ((self.output_max - self.output_min) * (wert / 100.0))

        # output_mode='raw': Regler liefert direkt Rohwert im gewuenschten Bereich.
        wert = float(reglerwert)
        if wert < self.output_min:
            return self.output_min
        if wert > self.output_max:
            return self.output_max
        return wert

    def step(self, dt=1.0):
        istwert = self.sensor.lesen() if hasattr(self.sensor, "lesen") else float(self.sensor())

        reglerwert = self._run_regler(istwert, dt)
        outputwert = self._scale_output(reglerwert)

        self.letzter_istwert = istwert
        self.letzter_reglerwert = reglerwert
        self.letzter_outputwert = outputwert

        if self.aktor is not None:
            if hasattr(self.aktor, "schreibe_roh"):
                self.aktor.schreibe_roh(int(outputwert))
            elif hasattr(self.aktor, "write"):
                self.aktor.write(outputwert)

        status = self.regler.status()
        status.update({
            "istwert": istwert,
            "reglerwert": reglerwert,
            "output": outputwert,
        })
        return status


def format_status(status):
    """Formatiert ein Status-Dictionary als didaktische Ein-Zeilen-Ausgabe."""
    typ = status.get("typ", "?")
    return (
        "{typ:<10} Soll={sollwert:7.2f} Ist={istwert:7.2f} "
        "e={fehler:7.2f} u={ausgang:7.2f}"
    ).format(
        typ=typ,
        sollwert=status.get("sollwert", 0.0),
        istwert=status.get("istwert", 0.0),
        fehler=status.get("fehler", 0.0),
        ausgang=status.get("ausgang", 0.0),
    )
