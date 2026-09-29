"""
Beispiel fuer NIT Bibliothek: PID
Zeigt: P-, PI-, PD- und PID-Regler an derselben simulierten PT2-Strecke vergleichen
Hardware: nur ESP32 (keine weitere Hardware noetig)
"""

from nitbw_pid import PRegler, PIRegler, PDRegler, PIDRegler


# --- Initialisierung ---
TS = 0.02                  # Abtastzeit in s
DAUER = 12.0               # Simulationsdauer in s
W = 2.0                    # Sollwert w

# Simulierte Strecke (PT2-Glied): K_P = 1.5, T1 = 1.0 s, T2 = 0.5 s
KP_S, T1, T2 = 1.5, 1.0, 0.5

# Die vier Regler mit ihren ReglerLab-Parametern
regler_liste = [
    ("P",   PRegler(kpr=2.0, ts=TS)),
    ("PI",  PIRegler(kpr=2.0, tn=1.5, ts=TS)),
    ("PD",  PDRegler(kpr=2.0, tv=0.3, ts=TS)),
    ("PID", PIDRegler(kpr=2.0, tn=1.5, tv=0.3, ts=TS)),
]


def simulieren(regler):
    """Regelkreis simulieren; Rueckgabe: x_max, x_ende, Zeit bis 90 % von w."""
    x1 = 0.0               # Zustand 1 der PT2-Strecke
    x = 0.0                # Zustand 2 = Istwert
    x_max = 0.0
    t90 = None
    n = int(DAUER / TS)
    for i in range(n):
        t = i * TS
        y = regler.berechnen(W, x)
        # PT2 = zwei PT1-Glieder hintereinander (Euler-Schritt)
        x1 += (KP_S * y - x1) * TS / T1
        x += (x1 - x) * TS / T2
        x_max = max(x_max, x)
        if t90 is None and x >= 0.9 * W:
            t90 = t
    return x_max, x, t90


# --- Hauptprogramm ---
print("Sollwert w = {} | Strecke: PT2 mit K_P = {}, T1 = {} s, T2 = {} s".format(W, KP_S, T1, T2))
print()
print("Regler | bleibende Abw. | Ueberschwingen | Zeit bis 90 %")
print("-------+----------------+----------------+--------------")

for name, regler in regler_liste:
    x_max, x_ende, t90 = simulieren(regler)
    abw = W - x_ende
    if abs(abw) < 0.0005:
        abw = 0.0          # -0.000 vermeiden
    ueber = max(0.0, x_max - W) / W * 100
    if t90 is None:
        zeit = "nicht erreicht"
    else:
        zeit = "{:.2f} s".format(t90)
    print("{:6s} | {:11.3f}    | {:11.1f} %   | {}".format(name, abw, ueber, zeit))
