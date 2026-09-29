"""
Beispiel fuer NIT Bibliothek: PID (Zweipunktregler)
Zeigt: Temperaturregelung mit Hysterese, Heizung wird ueber ein Relais geschaltet
Hardware: ESP32, DS18B20 (Temperatursensor), Relais- oder MOSFET-Modul mit Heizelement
"""

from machine import Pin
from nitbw_ds18b20 import DS18B20
from nitbw_pid import Zweipunktregler, Takt


# --- Initialisierung ---
SOLL = 40.0                # Solltemperatur in Grad C
TS = 1.0                   # Abtastzeit in s (der DS18B20 braucht ca. 0,75 s pro Messung)

sensor = DS18B20(Pin(4))                 # Datenleitung an GPIO 4
relais = Pin(26, Pin.OUT, value=0)       # Relais an GPIO 26 (aus)

# y_max = 1: Heizung ein, y_min = 0: Heizung aus, Schaltdifferenz X_sd = 1 Grad C
regler = Zweipunktregler(ymax=1, ymin=0, xsd=1.0)
takt = Takt(TS)

# --- Hauptprogramm ---
print("=== Zweipunktregler: Temperatur auf {} Grad C regeln ===".format(SOLL))

try:
    while True:
        temperatur = sensor.messen()
        y = regler.berechnen(SOLL, temperatur)
        relais.value(1 if y > 0.5 else 0)

        print("t = {:6.1f} s | T = {:5.2f} Grad C | Heizung {}".format(
            takt.zeit(), temperatur, "EIN" if regler.an else "AUS"))
        takt.warten()
except KeyboardInterrupt:
    relais.value(0)        # beim Beenden (Strg + C) Heizung sicher ausschalten
    print("Regler angehalten, Heizung aus.")
