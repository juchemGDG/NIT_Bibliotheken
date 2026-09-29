"""
Beispiel fuer NIT Bibliothek: PID (Verbindung mit ReglerLab)
Zeigt: Reglerparameter aus einer .rlab-Datei lesen, Messwerte an ReglerLab senden
       und Parameter waehrend des Betriebs aus ReglerLab aendern ("@set KPR=2.5")
Hardware: nur ESP32, Verbindung per USB (in ReglerLab: Mikrocontroller -> Messung starten)
"""

import sys
import select
from math import exp
from nitbw_pid import PIDRegler, Takt, aus_rlab


# --- Initialisierung ---
TS = 0.05                  # Abtastzeit in s
W = 2.0                    # Sollwert w

# Parameter aus ReglerLab uebernehmen: .rlab-Datei auf den ESP32 kopieren und
# den Dateinamen eintragen (sie muss genau einen Regler enthalten).
# DATEI = None: Standardwerte verwenden.
DATEI = None

if DATEI:
    regler = aus_rlab(DATEI, ts=TS)
else:
    regler = PIDRegler(kpr=2.0, tn=1.5, tv=0.3, ts=TS)
print("@bereit")
print(regler)

# Simulierte Strecke (PT1): hier waere spaeter der echte Sensor
KP_STRECKE = 1.5
T_STRECKE = 1.0
x = 0.0

# Lesen der Befehle, die ReglerLab an den ESP32 schickt
_poll = select.poll()
_poll.register(sys.stdin, select.POLLIN)


def befehle_lesen():
    """Wertet Zeilen der Form "@set KPR=2.5" aus und aendert den Parameter."""
    while _poll.poll(0):                       # nur lesen, wenn etwas angekommen ist
        zeile = sys.stdin.readline().strip()
        if not zeile:
            break
        if zeile.startswith("@set "):
            name, _, wert = zeile[5:].partition("=")
            name = name.strip()
            try:
                regler.setzen(name, float(wert))
                print("@ok", name, "=", wert)
            except ValueError:
                print("@fehler", name, "=", wert, "nicht uebernommen")


takt = Takt(TS)

# --- Hauptprogramm ---
try:
    while True:
        befehle_lesen()
        y = regler.berechnen(W, x)

        # Messwerte im Format, das ReglerLab aufzeichnet
        print("@t={:.3f} w={:.4f} x={:.4f} y={:.4f}".format(takt.zeit(), W, x, y))

        x = x + (KP_STRECKE * y - x) * (1 - exp(-TS / T_STRECKE))
        takt.warten()
except KeyboardInterrupt:
    print("Regler angehalten.")
