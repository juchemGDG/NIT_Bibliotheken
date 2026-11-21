"""
Beispiel fuer NIT Bibliothek: Motor (Fahrwerk)
Zeigt: Roboterauto mit zwei Motoren faehrt ein Quadrat und einfache Manoever
Hardware: L298N mit zwei DC-Getriebemotoren (Roboter-Chassis), Akku fuer die Motoren
"""

from nitbw_motor import Motor, Fahrwerk
import time


# --- Initialisierung ---
# Linker Motor an L298N Kanal A (OUT1/OUT2):  ENA=23, IN1=16, IN2=17
# Rechter Motor an L298N Kanal B (OUT3/OUT4): ENB=25, IN3=26, IN4=27
# Jumper an ENA und ENB abziehen. GND des L298N mit GND des ESP32 verbinden.
motor_links = Motor(in1=16, in2=17, en=23)
motor_rechts = Motor(in1=26, in2=27, en=25)
auto = Fahrwerk(motor_links, motor_rechts)

# Werte an das eigene Fahrzeug anpassen (Akku, Motoren, Untergrund)
GESCHWINDIGKEIT = 60    # Prozent fuer die Geradeausfahrt
DREH_TEMPO = 50         # Prozent fuer die Drehung auf der Stelle
ZEIT_GERADE_MS = 1500   # Dauer einer Quadratseite
ZEIT_90_GRAD_MS = 550   # Dauer fuer ca. 90 Grad Drehung (ausprobieren!)

# --- Hauptprogramm ---
print("=== Fahrwerk: Quadrat fahren ===")
print("Tipp: Dreht ein Rad falsch herum, in1 und in2 dieses Motors tauschen.")
print("Start in 3 Sekunden ...")
time.sleep(3)

try:
    for seite in range(1, 5):
        print("Seite {}: geradeaus mit {} %".format(seite, GESCHWINDIGKEIT))
        auto.vor(GESCHWINDIGKEIT)
        time.sleep_ms(ZEIT_GERADE_MS)

        # Kurz bremsen, damit das Auto nicht nachrollt
        auto.bremsen()
        time.sleep_ms(200)

        print("Seite {}: 90 Grad nach rechts drehen".format(seite))
        auto.rechts(DREH_TEMPO)
        time.sleep_ms(ZEIT_90_GRAD_MS)
        auto.stopp()
        time.sleep_ms(500)

    print("Linkskurve: linkes Rad langsamer als rechtes")
    auto.fahren(30, 70)
    time.sleep(2)

    print("Rueckwaerts mit 50 %")
    auto.zurueck(50)
    time.sleep(1)

    print("Auf der Stelle nach links drehen")
    auto.links(DREH_TEMPO)
    time.sleep(1)

finally:
    # Auch bei Abbruch mit Ctrl+C beide Motoren anhalten
    auto.stopp()
    print("Fahrwerk gestoppt.")
