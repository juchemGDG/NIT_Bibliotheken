"""
Beispiel fuer NIT Bibliothek: REGLER
Zeigt: Zweipunktregelung mit echtem Temperatursensor und PWM-Aktor
Hardware: BME280 (I2C) + PWM-Luefter/Heizer am ESP32
"""

from machine import I2C, Pin
from time import sleep

from nitbw_bme280 import BME280
from nitbw_regler import Zweipunktregler, SensorAdapter, PWMAktor, Regelkanal


# --- Initialisierung ---
# BME280 an ESP32 Standard-I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor_bme = BME280(i2c)

# Sensordaten fuer den Regelkanal: Temperatur in Grad C
sensor = SensorAdapter(
    read_func=lambda: sensor_bme.read_temperature(),
    minimum=0.0,
    maximum=60.0,
)

# PWM-Aktor an GPIO 25, 10 Bit (0..1023)
aktor = PWMAktor(pin=25, freq=5000, bits=10)

# Zweipunktregler: Temperatur im Bereich um Soll halten
regler = Zweipunktregler(
    sollwert=28.0,
    breite=1.0,
    hysterese=1.5,
    ausgang_min=0.0,
    ausgang_max=100.0,   # Prozent
    invertiert=True,     # invertiert=True passt typischerweise fuer Kuehlung
    eingang_min=0.0,
    eingang_max=60.0,
)

# output_mode='percent': 0..100% wird intern auf 0..1023 skaliert
kanal = Regelkanal(
    regler=regler,
    sensor=sensor,
    aktor=aktor,
    output_mode="percent",
    output_min=0,
    output_max=1023,
)

# --- Hauptprogramm ---
print("=== Zweipunktregelung mit BME280 + PWM ===")
print("Ctrl+C zum Beenden")

try:
    while True:
        status = kanal.step(dt=1.0)
        print(
            "T={:5.2f} C | Soll={:5.2f} C | Fehler={:6.2f} | Regler={:6.1f}% | PWM={:4.0f}".format(
                status["istwert"],
                status["sollwert"],
                status["fehler"],
                status["reglerwert"],
                status["output"],
            )
        )
        sleep(1)
except KeyboardInterrupt:
    aktor.aus()
    print("Regelung gestoppt, PWM aus")
