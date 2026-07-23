"""
Beispiel fuer NIT Bibliothek: ACS758
Zeigt: Kalibrierung von Nullpunkt und Empfindlichkeit mit Referenzstrom
Hardware: ACS758 am ESP32 (GPIO34), Multimeter als Stromreferenz
"""

from nitbw_acs758 import ACS758
from time import sleep


# --- Initialisierung ---
sensor = ACS758(pin=34, variante="50B", vcc=5.0, teiler=2.0, messungen=16)


# --- Hauptprogramm ---
print("=== ACS758 Kalibrierung ===")
print("Werkseinstellung: {:.2f} mV/A, Nullpunkt {:.4f} V".format(
    sensor.get_empfindlichkeit_mv_a(), sensor.get_nullpunkt_v()))
print()

print("Schritt 1: Stromkreis ausschalten (0 A durch den Sensor)")
sleep(5)
nullpunkt = sensor.nullpunkt_kalibrieren(n=400)
print("Neuer Nullpunkt: {:.4f} V".format(nullpunkt))
print("Kontrolle: {:+.1f} mA (sollte nahe 0 sein)".format(sensor.messen_ma()))
print()

print("Schritt 2: Bekannten Strom einschalten und mit Multimeter messen")
print("Beispiel: 5.00 A")
sleep(10)

referenz_strom = 5.0
empfindlichkeit = sensor.kalibrieren(referenz_strom, n=400)
print("Neue Empfindlichkeit: {:.2f} mV/A".format(empfindlichkeit))
print()

print("Schritt 3: Laufende Messung mit neuer Kalibrierung")
print("Aufloesung: {:.1f} mA pro ADC-Schritt".format(sensor.aufloesung_ma()))
print()

while True:
    print("Strom: {:+7.3f} A   {:+8.1f} mA".format(
        sensor.messen_a(), sensor.messen_ma()))
    sleep(0.5)
