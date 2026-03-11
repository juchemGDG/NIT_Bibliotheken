"""
Beispiel fuer NIT Bibliothek: Servo (Continuous Rotation)
Zeigt: Continuous-Servo mit Geschwindigkeit und Richtung steuern
Hardware: FS90R oder kompatibler 360°-Servo am ESP32
"""

from nitbw_servo import ContinuousServo
import time


# --- Initialisierung ---
# Continuous-Servo an GPIO 14 anschliessen (Signal-Leitung)
motor = ContinuousServo(pin=14)

# --- Hauptprogramm ---
print("=== Continuous Servo Beispiel ===")

# Langsam nach rechts drehen (30 %)
print("Langsam nach rechts (30 %)")
motor.drehen(geschwindigkeit=30, richtung=ContinuousServo.RECHTS)
time.sleep(3)

# Schnell nach rechts drehen (80 %)
print("Schnell nach rechts (80 %)")
motor.drehen(geschwindigkeit=80, richtung=ContinuousServo.RECHTS)
time.sleep(3)

# Stopp
print("Stopp")
motor.stopp()
time.sleep(1)

# Mittel nach links (50 %)
print("Mittel nach links (50 %)")
motor.drehen(geschwindigkeit=50, richtung=ContinuousServo.LINKS)
time.sleep(3)

# Volle Drehzahl nach links
print("Volle Drehzahl nach links (100 %)")
motor.drehen(geschwindigkeit=100, richtung=ContinuousServo.LINKS)
time.sleep(3)

# Alternativ: Richtung direkt als Zahl uebergeben (1 = rechts, -1 = links)
print("Direkt mit 1 nach rechts (40 %)")
motor.drehen(geschwindigkeit=40, richtung=1)
time.sleep(2)

print("Direkt mit -1 nach links (70 %)")
motor.drehen(geschwindigkeit=70, richtung=-1)
time.sleep(2)

motor.stopp()
time.sleep(1)

# Kurzform: Nur Geschwindigkeit uebergeben.
# Positiver Wert = rechts (Standard), negativer Wert = links.
print("Kurzform: 50 = 50 % nach rechts")
motor.drehen(50)
time.sleep(2)

print("Kurzform: -50 = 50 % nach links")
motor.drehen(-50)
time.sleep(2)

print("Kurzform: 80 mit expliziter Richtung LINKS")
motor.drehen(80, ContinuousServo.LINKS)
time.sleep(2)

motor.stopp()
time.sleep(1)

# Geschwindigkeit stufenweise erhoehen (Rampe)
print("Rampe: 0 % -> 100 % nach rechts")
for prozent in range(0, 101, 10):
    print("  " + str(prozent) + " %")
    motor.drehen(geschwindigkeit=prozent, richtung=ContinuousServo.RECHTS)
    time.sleep(0.5)

# Stopp und abschalten
motor.stopp()
time.sleep(1)
motor.aus()
print("Servo abgeschaltet.")
