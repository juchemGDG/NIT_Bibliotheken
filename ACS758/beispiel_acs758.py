"""
Beispiel fuer NIT Bibliothek: ACS758
Zeigt: Grundmessung der Stromstaerke in mA und A
Hardware: ACS758 (z. B. 050B) am ESP32, VIOUT ueber Spannungsteiler an GPIO34
"""

from nitbw_acs758 import ACS758
import time


# --- Initialisierung ---
# VIOUT -> Spannungsteiler 10k/10k -> GPIO34 (teiler = 2.0)
sensor = ACS758(pin=34, variante="50B", vcc=5.0, teiler=2.0, messungen=16)

# Nullpunkt bei stromlosem Leiter bestimmen (Leiter muss stromlos sein!)
print("Nullpunkt wird bestimmt - bitte keinen Strom fliessen lassen ...")
time.sleep(2)
nullpunkt = sensor.nullpunkt_kalibrieren(n=200)
print("Nullpunkt: {:.4f} V".format(nullpunkt))
print()


# --- Hauptprogramm ---
print("=== ACS758 Grundbeispiel ===")
print("Variante: {}   Empfindlichkeit: {:.1f} mV/A".format(
    sensor.get_variante(), sensor.get_empfindlichkeit_mv_a()))
print("Messbereich: {:.0f} A bis {:.0f} A".format(*sensor.messbereich_a()))
print()

while True:
    strom_a = sensor.messen_a()
    strom_ma = sensor.messen_ma()
    spannung = sensor.lesen_spannung()

    print("Strom: {:+8.3f} A   {:+9.1f} mA   VIOUT: {:.4f} V".format(
        strom_a, strom_ma, spannung))

    time.sleep(0.5)
