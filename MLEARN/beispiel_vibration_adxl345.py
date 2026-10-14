"""
Beispiel fuer NIT Bibliothek: MLEARN-Vibration
Lernt ein gesundes Motorprofil ein oder prueft es auf Schwingungsabweichungen.
Hardware: ESP32 + GY-261 mit ADXL345 am I2C-Bus
"""

import time
from machine import I2C, Pin
from nitbw_compass import Accelerometer
from nitbw_vibration import (
    VibrationsReferenz,
    berechne_merkmale,
    sammle_fenster,
)


# --- Initialisierung ---
MOTOR_ID = "motor_1"
EINLERNEN = True
DATEI = "referenz_{}.json".format(MOTOR_ID)
ABTASTRATE = 200
SAMPLES_PRO_FENSTER = 128
REFERENZFENSTER = 30

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = Accelerometer(i2c)


# --- Hauptprogramm ---
if not sensor.is_available():
    raise RuntimeError("ADXL345 nicht gefunden; I2C-Adresse und Anschluss pruefen.")

if EINLERNEN:
    print("Motor {} muss gesund und im spaeteren Betriebspunkt laufen.".format(MOTOR_ID))
    feature_fenster = []
    for nummer in range(REFERENZFENSTER):
        samples = sammle_fenster(sensor, SAMPLES_PRO_FENSTER, ABTASTRATE)
        merkmale = berechne_merkmale(samples, ABTASTRATE)
        feature_fenster.append(merkmale)
        print("Referenz {}/{} aufgenommen".format(nummer + 1, REFERENZFENSTER))

    referenz = VibrationsReferenz(MOTOR_ID, schwelle=3.0)
    referenz.einlernen(feature_fenster)
    referenz.speichern(DATEI)
    print("Referenz gespeichert: {}".format(DATEI))
    print("Zum Ueberwachen EINLERNEN auf False setzen und erneut starten.")
else:
    referenz = VibrationsReferenz.laden(DATEI)
    if referenz.motor_id != MOTOR_ID:
        raise RuntimeError("Das geladene Referenzprofil gehoert zu einem anderen Motor.")

    abweichungen_in_folge = 0
    while True:
        samples = sammle_fenster(sensor, SAMPLES_PRO_FENSTER, ABTASTRATE)
        merkmale = berechne_merkmale(samples, ABTASTRATE)
        score = referenz.abweichung(merkmale)
        if score > referenz.schwelle:
            abweichungen_in_folge += 1
        else:
            abweichungen_in_folge = 0

        status = "MOEGLICHE ABWEICHUNG" if abweichungen_in_folge >= 3 else "normal"
        print("{} | Abweichung {:.2f} | {}".format(MOTOR_ID, score, status))
        time.sleep_ms(100)