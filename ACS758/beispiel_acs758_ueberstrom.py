"""
Beispiel fuer NIT Bibliothek: ACS758
Zeigt: Ueberstromueberwachung mit Glaettung, Totzone und Richtungserkennung
Hardware: ACS758 am ESP32 (GPIO34), LED an GPIO2 als Warnanzeige
"""

from machine import Pin
from nitbw_acs758 import ACS758
from time import sleep


# --- Initialisierung ---
sensor = ACS758(pin=34, variante="50B", vcc=5.0, teiler=2.0)
led = Pin(2, Pin.OUT)

# Wichtige Einstellungen
sensor.set_messungen(32)        # mehr Einzelmessungen -> genauer
sensor.set_glaettung(0.8)       # ruhige Anzeige
sensor.set_totzone_ma(300)      # Rauschen unter 300 mA als 0 mA melden
sensor.set_invertiert(False)    # bei vertauschter Stromrichtung auf True

print("Nullpunkt wird bestimmt - Stromkreis bitte ausschalten ...")
sleep(2)
sensor.nullpunkt_kalibrieren(n=200)


# --- Hauptprogramm ---
GRENZE_A = 10.0

print("=== ACS758 Ueberstromueberwachung ===")
print("Grenzwert: {:.1f} A".format(GRENZE_A))
print("Einstellungen:", sensor.info())
print()

while True:
    strom_a = sensor.messen_a()
    richtung = sensor.richtung(schwelle_ma=300)

    if richtung > 0:
        text = "vorwaerts"
    elif richtung < 0:
        text = "rueckwaerts"
    else:
        text = "kein Strom"

    if abs(strom_a) > GRENZE_A:
        led.value(1)
        zustand = "UEBERSTROM!"
    else:
        led.value(0)
        zustand = "ok"

    print("{:+7.3f} A  ({:+8.1f} mA)  {:11s}  {}".format(
        strom_a, strom_a * 1000.0, text, zustand))

    sleep(0.2)
