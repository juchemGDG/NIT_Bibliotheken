"""
NIT Bibliothek: PID - Regler aus ReglerLab (P, I, D, PI, PD, PID, Zweipunkt)
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      Stephan Juchem / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-09

Rein rechnende Regler ohne Hardwarezugriff: Sie bekommen Sollwert und Istwert
und liefern die Stellgroesse. Bezeichnungen, Parameter und Rechenvorschrift
entsprechen den Reglerbloecken in ReglerLab und dem dort erzeugten
MicroPython-Code. Zusaetzlich enthalten: Takt (feste Abtastzeit) und
aus_rlab() (Reglerparameter aus einer .rlab-Datei uebernehmen).
"""

import json
from time import ticks_us, ticks_diff, ticks_add, sleep_ms, sleep_us


# Zuordnung: Parametername (wie in ReglerLab bzw. bei "@set KPR=2.5") -> Attribut
_NAMEN = {
    "KPR": "kpr", "TN": "tn", "TV": "tv", "KIR": "kir", "KDR": "kdr",
    "XSD": "xsd", "YMIN": "ymin", "YMAX": "ymax",
    "Y_MIN": "ymin", "Y_MAX": "ymax", "AW": "anti_windup",
    "ANTI_WINDUP": "anti_windup",
}


class Regler:
    """
    Basisklasse aller Regler: Zeitschritt, Zustand, Parameter aendern.

    Unterstuetzte Hardware:
    - beliebige Sensoren (Istwert) und Aktoren (Stellgroesse), die Regler
      rechnet nur

    Schnittstelle: keine (reine Berechnung)
    """

    ART = "Regler"
    PARAMETER = ()

    def __init__(self, ts=None):
        """
        :param ts: feste Abtastzeit in s (empfohlen, zusammen mit Takt).
                   None: die Zeit zwischen zwei Aufrufen wird gemessen.
        """
        if ts is not None and ts <= 0:
            raise ValueError("ts muss groesser als 0 sein")
        self.ts = ts
        self.e = 0.0          # letzte Regeldifferenz
        self.y = 0.0          # letzte Stellgroesse (begrenzt)
        self.y_roh = 0.0      # letzte Stellgroesse vor der Begrenzung
        self.p_anteil = 0.0   # Anteile der letzten Berechnung (vor Begrenzung)
        self.i_anteil = 0.0
        self.d_anteil = 0.0
        self._t_letzt = None
        self._integral = 0.0
        self._e_f = None      # verzoegertes e fuer den D-Anteil
        self.an = False       # Schaltzustand (nur Zweipunktregler)

    def reset(self):
        """Setzt Integral, D-Filter, Schaltzustand und Zeitmessung zurueck."""
        self._t_letzt = None
        self._integral = 0.0
        self._e_f = None
        self.an = False
        self.e = 0.0
        self.y = 0.0
        self.y_roh = 0.0
        self.p_anteil = 0.0
        self.i_anteil = 0.0
        self.d_anteil = 0.0

    def berechnen(self, soll, ist):
        """
        Berechnet die Stellgroesse aus Sollwert w und Istwert x (e = w - x).

        :return: Stellgroesse y
        """
        return self.berechnen_e(soll - ist)

    def berechnen_e(self, e):
        """
        Berechnet die Stellgroesse direkt aus der Regeldifferenz e.

        :return: Stellgroesse y
        """
        dt = self._zeitschritt()
        y_roh = self._rechnen(e, dt)
        self.e = e
        self.y_roh = y_roh
        self.y = self._begrenzen(y_roh)
        return self.y

    def setzen(self, name, wert):
        """
        Aendert einen Parameter ueber seinen Namen, z. B. setzen("KPR", 2.5).

        Erlaubt sind die Namen aus ReglerLab (KPR, TN, TV, KIR, KDR, XSD,
        YMIN, YMAX, AW) in beliebiger Gross-/Kleinschreibung.
        TD (Verzoegerung des D-Anteils) sendet ReglerLab mit, sie wird hier
        aber aus tv berechnet; der Wert wird daher ignoriert.
        """
        if str(name).upper() == "TD" and ("tv" in self.PARAMETER or "kdr" in self.PARAMETER):
            return
        key = _NAMEN.get(str(name).upper())
        if key is None or key not in self.PARAMETER:
            raise ValueError("Kein Parameter dieses Reglers: " + str(name))
        if key == "anti_windup":
            wert = bool(wert)
        elif wert is None and key in ("ymin", "ymax"):
            pass
        else:
            wert = float(wert)
            if key == "tn" and wert <= 0:
                raise ValueError("tn muss groesser als 0 sein")
        setattr(self, key, wert)

    def parameter(self):
        """Gibt die aktuellen Parameter als Dictionary zurueck."""
        return {k: getattr(self, k) for k in self.PARAMETER}

    def __str__(self):
        teile = ["{}={}".format(k, getattr(self, k)) for k in self.PARAMETER]
        return "{}({})".format(self.ART, ", ".join(teile))

    # --- interne Hilfen ---

    def _zeitschritt(self):
        """Schrittweite dt in s: fest (ts) oder gemessen."""
        if self.ts is not None:
            return self.ts
        jetzt = ticks_us()
        if self._t_letzt is None:
            dt = 0.0
        else:
            dt = ticks_diff(jetzt, self._t_letzt) / 1000000
        self._t_letzt = jetzt
        return dt

    def _rechnen(self, e, dt):
        raise NotImplementedError

    def _begrenzen(self, y):
        return y


class _Stetig(Regler):
    """Gemeinsame Teile von P, I, D, PI, PD und PID: Begrenzung, Anti-Windup, D-Filter."""

    def __init__(self, ymin, ymax, anti_windup, ts):
        Regler.__init__(self, ts)
        if ymin is not None and ymax is not None and ymin > ymax:
            ymin, ymax = ymax, ymin
        self.ymin = ymin
        self.ymax = ymax
        self.anti_windup = anti_windup

    def _begrenzen(self, y):
        if self.ymin is not None and y < self.ymin:
            return self.ymin
        if self.ymax is not None and y > self.ymax:
            return self.ymax
        return y

    def _integrieren(self, e, dt, y_roh):
        # Anti-Windup: nur weiter aufsummieren, solange die Stellgroesse
        # nicht an der Grenze steht und e nicht weiter hinausdrueckt
        if self.anti_windup:
            if self.ymax is not None and y_roh >= self.ymax and e > 0:
                return
            if self.ymin is not None and y_roh <= self.ymin and e < 0:
                return
        self._integral += e * dt

    def _verzoegert(self, e, td, dt):
        """e leicht verzoegert (fuer den D-Anteil); beim ersten Aufruf kein Sprung."""
        if self._e_f is None:
            self._e_f = e
        self._e_f += (e - self._e_f) * dt / (td + dt)
        return self._e_f

    def _d_teil(self, e, dt, tv):
        """D-Anteil T_V * de/dt als DT1-Glied mit der Verzoegerung T_V/10."""
        if tv <= 0:
            self._e_f = None
            return 0.0
        td = max(tv / 10, dt)
        e_f = self._verzoegert(e, td, dt)
        return tv * (e - e_f) / td


class PRegler(_Stetig):
    """
    P-Regler: y = K_PR * e

    Unterstuetzte Hardware:
    - beliebige Sensoren und Aktoren (Regler rechnet nur)

    Schnittstelle: keine (reine Berechnung)
    """

    ART = "P-Regler"
    PARAMETER = ("kpr", "ymin", "ymax")

    def __init__(self, kpr=1.0, ymin=None, ymax=None, ts=None):
        """
        :param kpr: Proportionalbeiwert K_PR (Regelverstaerkung)
        :param ymin: untere Grenze der Stellgroesse (None: keine Begrenzung)
        :param ymax: obere Grenze der Stellgroesse (None: keine Begrenzung)
        :param ts: feste Abtastzeit in s (None: wird gemessen)
        """
        _Stetig.__init__(self, ymin, ymax, False, ts)
        self.kpr = float(kpr)

    def _rechnen(self, e, dt):
        y = self.kpr * e
        self.p_anteil = y
        return y


class IRegler(_Stetig):
    """
    I-Regler: y = K_IR * Integral(e dt)

    Unterstuetzte Hardware:
    - beliebige Sensoren und Aktoren (Regler rechnet nur)

    Schnittstelle: keine (reine Berechnung)
    """

    ART = "I-Regler"
    PARAMETER = ("kir", "ymin", "ymax", "anti_windup")

    def __init__(self, kir=1.0, ymin=None, ymax=None, anti_windup=True, ts=None):
        """
        :param kir: Integrierbeiwert K_IR in 1/s
        :param ymin: untere Grenze der Stellgroesse (None: keine Begrenzung)
        :param ymax: obere Grenze der Stellgroesse (None: keine Begrenzung)
        :param anti_windup: I-Anteil anhalten, solange die Grenze erreicht ist
        :param ts: feste Abtastzeit in s (None: wird gemessen)
        """
        _Stetig.__init__(self, ymin, ymax, anti_windup, ts)
        self.kir = float(kir)

    def _rechnen(self, e, dt):
        y = self.kir * self._integral
        self.i_anteil = y
        self._integrieren(e, dt, y)
        return y


class DRegler(_Stetig):
    """
    D-Regler: y = K_DR * de/dt (mit Verzoegerung 0,05 s, siehe ReglerLab)

    Unterstuetzte Hardware:
    - beliebige Sensoren und Aktoren (Regler rechnet nur)

    Schnittstelle: keine (reine Berechnung)
    """

    ART = "D-Regler"
    PARAMETER = ("kdr", "ymin", "ymax")

    def __init__(self, kdr=0.5, ymin=None, ymax=None, ts=None):
        """
        :param kdr: Differenzierbeiwert K_DR in s
        :param ymin: untere Grenze der Stellgroesse (None: keine Begrenzung)
        :param ymax: obere Grenze der Stellgroesse (None: keine Begrenzung)
        :param ts: feste Abtastzeit in s (None: wird gemessen)
        """
        _Stetig.__init__(self, ymin, ymax, False, ts)
        self.kdr = float(kdr)

    def _rechnen(self, e, dt):
        td = max(0.05, dt)
        e_f = self._verzoegert(e, td, dt)
        y = self.kdr * (e - e_f) / td
        self.d_anteil = y
        return y


class PIRegler(_Stetig):
    """
    PI-Regler: y = K_PR * (e + 1/T_N * Integral(e dt))

    Unterstuetzte Hardware:
    - beliebige Sensoren und Aktoren (Regler rechnet nur)

    Schnittstelle: keine (reine Berechnung)
    """

    ART = "PI-Regler"
    PARAMETER = ("kpr", "tn", "ymin", "ymax", "anti_windup")

    def __init__(self, kpr=1.0, tn=1.0, ymin=None, ymax=None, anti_windup=True, ts=None):
        """
        :param kpr: Proportionalbeiwert K_PR
        :param tn: Nachstellzeit T_N in s (muss groesser als 0 sein)
        :param ymin: untere Grenze der Stellgroesse (None: keine Begrenzung)
        :param ymax: obere Grenze der Stellgroesse (None: keine Begrenzung)
        :param anti_windup: I-Anteil anhalten, solange die Grenze erreicht ist
        :param ts: feste Abtastzeit in s (None: wird gemessen)
        """
        _Stetig.__init__(self, ymin, ymax, anti_windup, ts)
        if tn <= 0:
            raise ValueError("tn muss groesser als 0 sein")
        self.kpr = float(kpr)
        self.tn = float(tn)

    def _rechnen(self, e, dt):
        tn = max(self.tn, 1e-6)
        self.p_anteil = self.kpr * e
        self.i_anteil = self.kpr * self._integral / tn
        y = self.p_anteil + self.i_anteil
        self._integrieren(e, dt, y)
        return y


class PDRegler(_Stetig):
    """
    PD-Regler: y = K_PR * (e + T_V * de/dt), D-Anteil mit Verzoegerung T_V/10

    Unterstuetzte Hardware:
    - beliebige Sensoren und Aktoren (Regler rechnet nur)

    Schnittstelle: keine (reine Berechnung)
    """

    ART = "PD-Regler"
    PARAMETER = ("kpr", "tv", "ymin", "ymax")

    def __init__(self, kpr=1.0, tv=0.2, ymin=None, ymax=None, ts=None):
        """
        :param kpr: Proportionalbeiwert K_PR
        :param tv: Vorhaltezeit T_V in s (0: kein D-Anteil)
        :param ymin: untere Grenze der Stellgroesse (None: keine Begrenzung)
        :param ymax: obere Grenze der Stellgroesse (None: keine Begrenzung)
        :param ts: feste Abtastzeit in s (None: wird gemessen)
        """
        _Stetig.__init__(self, ymin, ymax, False, ts)
        self.kpr = float(kpr)
        self.tv = float(tv)

    def _rechnen(self, e, dt):
        d = self._d_teil(e, dt, self.tv)
        self.p_anteil = self.kpr * e
        self.d_anteil = self.kpr * d
        return self.p_anteil + self.d_anteil


class PIDRegler(_Stetig):
    """
    PID-Regler: y = K_PR * (e + 1/T_N * Integral(e dt) + T_V * de/dt)

    Unterstuetzte Hardware:
    - beliebige Sensoren und Aktoren (Regler rechnet nur)

    Schnittstelle: keine (reine Berechnung)
    """

    ART = "PID-Regler"
    PARAMETER = ("kpr", "tn", "tv", "ymin", "ymax", "anti_windup")

    def __init__(self, kpr=1.0, tn=1.0, tv=0.2, ymin=None, ymax=None,
                 anti_windup=True, ts=None):
        """
        :param kpr: Proportionalbeiwert K_PR
        :param tn: Nachstellzeit T_N in s (muss groesser als 0 sein)
        :param tv: Vorhaltezeit T_V in s (0: kein D-Anteil, also PI-Regler)
        :param ymin: untere Grenze der Stellgroesse (None: keine Begrenzung)
        :param ymax: obere Grenze der Stellgroesse (None: keine Begrenzung)
        :param anti_windup: I-Anteil anhalten, solange die Grenze erreicht ist
        :param ts: feste Abtastzeit in s (None: wird gemessen)
        """
        _Stetig.__init__(self, ymin, ymax, anti_windup, ts)
        if tn <= 0:
            raise ValueError("tn muss groesser als 0 sein")
        self.kpr = float(kpr)
        self.tn = float(tn)
        self.tv = float(tv)

    def _rechnen(self, e, dt):
        tn = max(self.tn, 1e-6)
        d = self._d_teil(e, dt, self.tv)
        self.p_anteil = self.kpr * e
        self.i_anteil = self.kpr * self._integral / tn
        self.d_anteil = self.kpr * d
        y = self.p_anteil + self.i_anteil + self.d_anteil
        self._integrieren(e, dt, y)
        return y


class Zweipunktregler(Regler):
    """
    Zweipunktregler mit Hysterese: schaltet zwischen y_max und y_min.

    Er schaltet auf y_max, wenn e > X_sd/2 ist, und auf y_min, wenn
    e < -X_sd/2 ist. Dazwischen bleibt der Zustand erhalten.
    Mit X_sd = 0 arbeitet er ohne Hysterese.

    Unterstuetzte Hardware:
    - beliebige Schalter (Relais, MOSFET, LED) als Aktor

    Schnittstelle: keine (reine Berechnung)
    """

    ART = "Zweipunktregler"
    PARAMETER = ("ymax", "ymin", "xsd")

    def __init__(self, ymax=1.0, ymin=0.0, xsd=0.2):
        """
        :param ymax: oberer Stellwert (eingeschaltet)
        :param ymin: unterer Stellwert (ausgeschaltet)
        :param xsd: Schaltdifferenz X_sd (Hysterese), 0: ohne Hysterese
        """
        Regler.__init__(self, None)
        self.ymax = float(ymax)
        self.ymin = float(ymin)
        self.xsd = float(xsd)

    def _zeitschritt(self):
        return 0.0    # der Zweipunktregler braucht keine Zeit

    def _rechnen(self, e, dt):
        h = max(0.0, self.xsd) / 2
        if e > h:
            self.an = True       # Istwert deutlich zu klein: einschalten
        elif e < -h:
            self.an = False      # Istwert deutlich zu gross: ausschalten
        return self.ymax if self.an else self.ymin


class Takt:
    """
    Haelt eine feste Abtastzeit ein (wie die Hauptschleife in ReglerLab).

    Unterstuetzte Hardware:
    - ESP32 (Zeitmessung ueber ticks_us)

    Schnittstelle: keine (Zeitsteuerung)
    """

    def __init__(self, ts):
        """
        :param ts: Abtastzeit in s, z. B. 0.05 fuer 50 ms
        """
        if ts <= 0:
            raise ValueError("ts muss groesser als 0 sein")
        self.ts = ts
        self._us = int(ts * 1000000)
        self.zu_langsam = False
        self.start()

    def start(self):
        """Beginnt die Zeitmessung (t = 0) und den ersten Takt."""
        self._start = ticks_us()
        self._naechster = self._start
        self.zu_langsam = False

    def zeit(self):
        """Zeit seit start() in Sekunden."""
        return ticks_diff(ticks_us(), self._start) / 1000000

    def warten(self):
        """
        Wartet bis zum naechsten Takt.

        Dauert die Berechnung laenger als die Abtastzeit, beginnt der Takt neu
        und zu_langsam ist True.
        """
        self._naechster = ticks_add(self._naechster, self._us)
        pause = ticks_diff(self._naechster, ticks_us())
        if pause > 0:
            sleep_ms(pause // 1000)
            sleep_us(pause % 1000)
            self.zu_langsam = False
        else:
            self._naechster = ticks_us()
            self.zu_langsam = True


# --- Parameter aus ReglerLab uebernehmen ---

_RLAB_TYPEN = {
    "pR": PRegler, "iR": IRegler, "dR": DRegler,
    "piR": PIRegler, "pdR": PDRegler, "pidR": PIDRegler,
    "twoPoint": Zweipunktregler,
}


def aus_block(block, ts=None):
    """
    Erzeugt einen Regler aus einem Reglerblock einer .rlab-Datei.

    :param block: Dictionary mit "type" und "params" (wie in der .rlab-Datei)
    :param ts: feste Abtastzeit in s (None: wird gemessen)
    :return: Regler-Objekt mit den Parametern des Blocks
    """
    typ = block.get("type")
    if typ not in _RLAB_TYPEN:
        raise ValueError("Kein Reglerblock: " + str(typ))
    p = block.get("params", {})
    if typ == "twoPoint":
        return Zweipunktregler(p.get("ymax", 1), p.get("ymin", 0), p.get("xsd", 0.2))
    if p.get("limit"):
        ymin, ymax = p.get("ymin", 0), p.get("ymax", 10)
    else:
        ymin, ymax = None, None
    aw = p.get("antiWindup", True)
    if typ == "pR":
        return PRegler(p.get("Kpr", 1), ymin, ymax, ts)
    if typ == "iR":
        return IRegler(p.get("Kir", 1), ymin, ymax, aw, ts)
    if typ == "dR":
        return DRegler(p.get("Kdr", 0.5), ymin, ymax, ts)
    if typ == "piR":
        return PIRegler(p.get("Kpr", 1), p.get("Tn", 1), ymin, ymax, aw, ts)
    if typ == "pdR":
        return PDRegler(p.get("Kpr", 1), p.get("Tv", 0.2), ymin, ymax, ts)
    return PIDRegler(p.get("Kpr", 1), p.get("Tn", 1), p.get("Tv", 0.2), ymin, ymax, aw, ts)


def aus_rlab(pfad, name=None, ts=None):
    """
    Liest die Parameter eines Reglers aus einer .rlab-Datei (JSON).

    :param pfad: Dateiname auf dem ESP32, z. B. "heizung.rlab"
    :param name: Bezeichnung (label) oder Kennung (id) des Reglerblocks;
                 kann entfallen, wenn die Datei genau einen Regler enthaelt
    :param ts: feste Abtastzeit in s (None: wird gemessen)
    :return: Regler-Objekt
    """
    with open(pfad) as f:
        daten = json.load(f)
    treffer = []
    for b in daten.get("blocks", []):
        if b.get("type") in _RLAB_TYPEN:
            if name is None or b.get("label") == name or b.get("id") == name:
                treffer.append(b)
    if len(treffer) == 0:
        raise ValueError("Kein passender Regler in " + str(pfad))
    if len(treffer) > 1:
        namen = [str(b.get("label") or b.get("id")) for b in treffer]
        raise ValueError("Mehrere Regler, bitte name angeben: " + ", ".join(namen))
    return aus_block(treffer[0], ts)
