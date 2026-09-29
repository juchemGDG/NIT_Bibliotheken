"""
Beispiel fuer NIT Bibliothek: PID
Zeigt: PI-Regler regelt eine simulierte PT1-Strecke (Sprungantwort im Regelkreis)
Hardware: nur ESP32 (keine weitere Hardware noetig)
"""

from nitbw_pid import PIRegler, Takt
from math import exp


# --- Initialisierung ---
TS = 0.05                  # Abtastzeit in s (alle 50 ms wird geregelt)
W = 2.0                    # Sollwert w

# Regler: Parameter wie im Reglerblock von ReglerLab
regler = PIRegler(kpr=2.0, tn=1.5, ts=TS)
takt = Takt(TS)

# Simulierte Strecke (PT1-Glied): K_P = 1.5, Zeitkonstante T = 1 s
KP_STRECKE = 1.5
T_STRECKE = 1.0
x = 0.0                    # Istwert x (Regelgroesse)

# --- Hauptprogramm ---
print("=== PID Grundbeispiel: PI-Regler an simulierter PT1-Strecke ===")
print("Die Ausgabe passt zum Plotter in Thonny (Ansicht -> Plotter)")
print()

while takt.zeit() < 10:
    y = regler.berechnen(W, x)      # Stellgroesse aus Sollwert und Istwert

    print("w:", W, "x:", round(x, 3), "y:", round(y, 3))

    # Strecke einen Schritt weiterrechnen (exakte Loesung des PT1-Glieds)
    x = x + (KP_STRECKE * y - x) * (1 - exp(-TS / T_STRECKE))

    takt.warten()          # bis zum naechsten Takt warten

print("Fertig.")
