"""
Beispiel fuer NIT Bibliothek: NITON
Zeigt: Lied-Listen mit unterschiedlichem Tempo und Legato
Hardware: ESP32, passiver Piezo-Lautsprecher an PWM-Pin
"""

from nitbw_niton import NITon
from nitbw_niton import c, d, e, f, g, a
from nitbw_niton import viertel, halbe, vi, ha, ga, vip, ac, hap


# --- Initialisierung ---
SPEAKER_PIN = 15
ton = NITon(SPEAKER_PIN)

lied_langsam = [
    (c, viertel), (d, viertel), (e, viertel), (f, viertel),
    (g, halbe), (g, halbe), (0, ga),
]

lied_schnell = [
    (c, vi), (d, vi), (e, vi), (f, vi),
    (g, ha), (g, ha), (0, ga),
]

lied_legato = [
    (d, ha), (d, vi), (a, ac), (a, vip),
    (a, vi), (e, vip), (f, ac), (e, vi), (d, hap),
]


# --- Hauptprogramm ---
ton.setGeschw(80)
ton.setLegato(95)
ton.spiele_lied(lied_langsam)

ton.setGeschw(140)
ton.spiele_lied(lied_schnell)

ton.setGeschw(60)
ton.setLegato(98)
ton.spiele_lied(lied_legato)
