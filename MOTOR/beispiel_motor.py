"""
Beispiel fuer NIT Bibliothek: Motor
Zeigt: Einen Gleichstrommotor vorwaerts, rueckwaerts, mit Rampe und Bremse steuern
Hardware: L298N-Modul (Kanal A), DC-Getriebemotor, eigene Motorversorgung (z. B. 7-12 V)
"""

from nitbw_motor import Motor, VOR, ZURUECK
import time


# --- Initialisierung ---
# L298N Kanal A:
#   ENA -> GPIO 23  (Jumper an ENA abziehen, sonst wirkt die PWM nicht!)
#   IN1 -> GPIO 16
#   IN2 -> GPIO 17
#   GND -> GND des ESP32 (gemeinsame Masse mit der Motorversorgung!)
#   OUT1/OUT2 -> Motor
motor = Motor(in1=16, in2=17, en=23)


def zeige_status():
    """Gibt Geschwindigkeit und Richtung des Motors aus."""
    richtung = motor.lese_richtung()
    if richtung == VOR:
        text = "VOR"
    elif richtung == ZURUECK:
        text = "ZURUECK"
    else:
        text = "Stillstand"
    print("  -> Geschwindigkeit: {} %, Richtung: {}".format(
        motor.lese_geschwindigkeit(), text))


# --- Hauptprogramm ---
print("=== Motor Grundbeispiel (L298N) ===")

try:
    print("Vorwaerts mit 50 %")
    motor.vor(50)
    zeige_status()
    time.sleep(2)

    print("Vorwaerts mit 100 %")
    motor.vor(100)
    zeige_status()
    time.sleep(2)

    print("Stopp (Motor laeuft frei aus)")
    motor.stopp()
    zeige_status()
    time.sleep(1)

    print("Rueckwaerts mit 60 %")
    motor.zurueck(60)
    zeige_status()
    time.sleep(2)

    # Kurzform: Vorzeichen bestimmt die Richtung
    print("Kurzform: drehen(-30) = 30 % rueckwaerts")
    motor.drehen(-30)
    zeige_status()
    time.sleep(2)

    # Sanfter Richtungswechsel: von -30 % auf +80 % in 3 Sekunden
    print("Rampe: sanft von -30 % auf +80 % (3 Sekunden)")
    motor.rampe(80, dauer_ms=3000)
    zeige_status()
    time.sleep(1)

    # Aktiv bremsen: Wicklung kurzschliessen, nur kurz halten
    print("Bremsen (Kurzschlussbremse, nur kurz halten)")
    motor.bremsen()
    time.sleep_ms(300)
    motor.stopp()
    zeige_status()

finally:
    # Auch bei Abbruch mit Ctrl+C den Motor sicher anhalten
    motor.aus()
    print("Motor aus.")
