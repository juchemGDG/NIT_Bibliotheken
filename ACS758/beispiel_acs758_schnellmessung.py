"""
Beispiel fuer NIT Bibliothek: ACS758
Zeigt: Schnelle Messreihen, Spitzenwerte, Effektivwert und Messrate
Hardware: ACS758 am ESP32 (GPIO34), Last mit veraenderlichem Strom
"""

from nitbw_acs758 import ACS758
from time import sleep


# --- Initialisierung ---
sensor = ACS758(pin=34, variante="50B", vcc=5.0, teiler=2.0)

print("Nullpunkt wird bestimmt - Stromkreis bitte ausschalten ...")
sleep(2)
sensor.nullpunkt_kalibrieren(n=200)
print("Nullpunkt: {:.4f} V".format(sensor.get_nullpunkt_v()))
print()


# --- Hauptprogramm ---
print("=== ACS758 Schnellmessung ===")
print("Moegliche Messrate: {:.0f} Messungen/s".format(sensor.messrate(200)))
print()

# Eine schnelle Messreihe aufnehmen und danach auswerten
print("Messreihe mit 100 Werten (ohne Pause):")
serie = sensor.messen_serie_ma(anzahl=100)
print("  erster Wert: {:+.1f} mA".format(serie[0]))
print("  letzter Wert: {:+.1f} mA".format(serie[-1]))
print("  kleinster:   {:+.1f} mA".format(min(serie)))
print("  groesster:   {:+.1f} mA".format(max(serie)))
print()

while True:
    # Zeitfenster von 200 ms auswerten (bei 50 Hz genau 10 Perioden)
    stat = sensor.messen_statistik(dauer_ms=200)

    print("Mittelwert:   {:+7.3f} A".format(stat["mittel_a"]))
    print("Effektivwert: {:7.3f} A".format(stat["effektiv_a"]))
    print("Minimum:      {:+7.3f} A".format(stat["min_a"]))
    print("Maximum:      {:+7.3f} A".format(stat["max_a"]))
    print("Spitze-Spitze:{:7.3f} A".format(stat["spitze_spitze_a"]))
    print("Messwerte:    {} in 200 ms ({:.0f} Hz)".format(
        stat["anzahl"], stat["rate_hz"]))
    print("-" * 46)

    sleep(1)
