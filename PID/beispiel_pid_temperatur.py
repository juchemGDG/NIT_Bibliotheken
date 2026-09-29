"""
Beispiel fuer NIT Bibliothek: PID
Zeigt: Temperaturregelung mit PID-Regler, Heizleistung ueber PWM, Parameter live aendern
Hardware: ESP32, DS18B20 (Temperatursensor), MOSFET-Modul mit Heizelement
"""

from machine import Pin, PWM
from nitbw_ds18b20 import DS18B20
from nitbw_pid import PIDRegler, Takt


# --- Initialisierung ---
SOLL = 40.0                # Solltemperatur in Grad C
TS = 1.0                   # Abtastzeit in s (der DS18B20 braucht ca. 0,75 s pro Messung)

sensor = DS18B20(Pin(4))                 # Datenleitung an GPIO 4
heizung = PWM(Pin(25), freq=1000)        # MOSFET an GPIO 25
heizung.duty_u16(0)

# Stellgroesse y = 0 ... 1 (0 % ... 100 % Heizleistung), mit Anti-Windup
regler = PIDRegler(kpr=0.15, tn=60, tv=5, ymin=0, ymax=1, anti_windup=True, ts=TS)
takt = Takt(TS)

# --- Hauptprogramm ---
print("=== PID-Regler: Temperatur auf {} Grad C regeln ===".format(SOLL))
print("Regler:", regler)
print("t;soll;ist;heizleistung;p;i;d")

try:
    while True:
        temperatur = sensor.messen()
        y = regler.berechnen(SOLL, temperatur)
        heizung.duty_u16(int(y * 65535))

        print("{:.0f};{:.1f};{:.2f};{:.2f};{:.2f};{:.2f};{:.2f}".format(
            takt.zeit(), SOLL, temperatur, y,
            regler.p_anteil, regler.i_anteil, regler.d_anteil))
        takt.warten()
except KeyboardInterrupt:
    heizung.duty_u16(0)    # beim Beenden (Strg + C) Heizung sicher ausschalten
    print("Regler angehalten, Heizung aus.")
