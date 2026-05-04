"""
Beispiel fuer NIT Bibliothek: Stepper (StepperULN)
Zeigt: 28BYJ-48 mit ULN2003 - Schritte, Winkel und Umdrehungen
Hardware: 28BYJ-48 + ULN2003-Platine am ESP32
"""

from nitbw_stepper import StepperULN, VOR, ZURUECK
import time


# --- Initialisierung ---
# ULN2003-Platine: IN1..IN4 an GPIO 14, 27, 26, 25 anschliessen
motor = StepperULN(in1=14, in2=27, in3=26, in4=25,
                   schritte_pro_umdrehung=2048,
                   geschwindigkeit=200)

# --- Hauptprogramm ---
print("=== StepperULN Grundbeispiel (28BYJ-48) ===")

# 512 Schritte vorwaerts (entspricht 90° bei 2048 spr)
print("512 Schritte vorwaerts")
motor.schritte(512, VOR)
time.sleep(0.5)

# 512 Schritte zurueck
print("512 Schritte zurueck")
motor.schritte(512, ZURUECK)
time.sleep(0.5)

# Auf einen Winkel drehen
print("Winkel 90 Grad vorwaerts")
motor.winkel(90, VOR)
time.sleep(0.5)

print("Winkel 180 Grad zurueck")
motor.winkel(180, ZURUECK)
time.sleep(0.5)

print("Winkel 90 Grad vorwaerts (zurueck zur Ausgangsposition)")
motor.winkel(90, VOR)
time.sleep(0.5)

# Eine volle Umdrehung vorwaerts
print("1 volle Umdrehung vorwaerts")
motor.umdrehungen(1, VOR)
time.sleep(0.5)

# Eine volle Umdrehung zurueck
print("1 volle Umdrehung zurueck")
motor.umdrehungen(1, ZURUECK)
time.sleep(0.5)

# Halbe Umdrehung (0.5)
print("0.5 Umdrehungen vorwaerts")
motor.umdrehungen(0.5, VOR)
time.sleep(0.5)

print("0.5 Umdrehungen zurueck")
motor.umdrehungen(0.5, ZURUECK)
time.sleep(0.5)

# Aktuelle Position abfragen
print("Aktuelle Position: " + str(motor.lese_position()) + " Schritte")

# Geschwindigkeit aendern
print("Geschwindigkeit auf 100 sps setzen, dann 1 Umdrehung")
motor.geschwindigkeit(100)
motor.umdrehungen(1, VOR)
time.sleep(0.5)

print("Geschwindigkeit auf 400 sps setzen, dann 1 Umdrehung")
motor.geschwindigkeit(400)
motor.umdrehungen(1, ZURUECK)
time.sleep(0.5)

# Spulen stromlos schalten
motor.aus()
print("Motor abgeschaltet.")
