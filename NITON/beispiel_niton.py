"""
Beispiel fuer NIT Bibliothek: NITON
Zeigt: Grundlegendes Abspielen von Toenen, Legato und Triolen
Hardware: ESP32, passiver Piezo-Lautsprecher an PWM-Pin
"""

from nitbw_niton import NITon
from nitbw_niton import c, d, e, f, g, a, h, c2
from nitbw_niton import viertel, halbe, vi, ha, ga, ac_t, vi_t


# --- Initialisierung ---
SPEAKER_PIN = 15
ton = NITon(SPEAKER_PIN, geschwindigkeit=80, legato=95)


# --- Hauptprogramm ---
# Einfache Tonfolge
ton.ton(c, viertel)
ton.ton(d, viertel)
ton.ton(e, viertel)
ton.ton(f, viertel)
ton.ton(g, halbe)
ton.ton(g, halbe)
ton.pause(ga)

# Schneller
ton.setGeschw(140)
ton.ton(c, vi)
ton.ton(d, vi)
ton.ton(e, vi)
ton.ton(f, vi)
ton.ton(g, ha)
ton.ton(g, ha)

# Triolenbeispiel
ton.setGeschw(90)
ton.setLegato(90)
ton.ton(c, ac_t)
ton.ton(d, ac_t)
ton.ton(e, ac_t)
ton.ton(f, ac_t)
ton.ton(g, ac_t)
ton.ton(a, ac_t)
ton.ton(g, vi_t)
ton.ton(a, vi_t)
ton.ton(h, vi_t)
ton.ton(c2, viertel)
