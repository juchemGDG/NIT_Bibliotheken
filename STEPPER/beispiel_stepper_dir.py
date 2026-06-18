"""
Beispiel fuer NIT Bibliothek: Stepper (StepperDir)
Zeigt: NEMA 17 mit A4988/DRV8825 - Schritte, Winkel, Umdrehungen
Hardware: NEMA 17 + A4988 (oder DRV8825) am ESP32
"""

from nitbw_stepper import StepperDir, VOR, ZURUECK
import time


# --- Initialisierung ---
# A4988/DRV8825 Anschluss:
#   STEP  -> GPIO 14
#   DIR   -> GPIO 27
#   ENABLE -> GPIO 26 (optional, LOW = aktiv)
#   VMOT  -> 12 V (externes Netzteil!)
#   GND   -> GND (gemeinsam mit ESP32)
# Hinweis: 800 sps liegt oberhalb des Vollschritt-Resonanzbereichs
# (~200-600 sps). Bei niedrigeren Werten kann der NEMA 17 rau laufen
# oder stottern - das ist Motorphysik, kein Fehler der Bibliothek.
motor = StepperDir(step_pin=14, dir_pin=27, enable_pin=26,
                   schritte_pro_umdrehung=200,
                   geschwindigkeit=800)

# --- Hauptprogramm ---
print("=== StepperDir Grundbeispiel (NEMA 17 + A4988) ===")

# 100 Schritte vorwaerts (entspricht 180° bei 200 spr)
print("100 Schritte vorwaerts")
motor.schritte(100, VOR)
time.sleep(0.5)

# 100 Schritte zurueck
print("100 Schritte zurueck")
motor.schritte(100, ZURUECK)
time.sleep(0.5)

# Auf einen Winkel drehen
print("Winkel 90 Grad vorwaerts")
motor.winkel(90, VOR)
time.sleep(0.5)

print("Winkel 90 Grad zurueck")
motor.winkel(90, ZURUECK)
time.sleep(0.5)

# Volle Umdrehungen
print("2 Umdrehungen vorwaerts")
motor.umdrehungen(2, VOR)
time.sleep(0.5)

print("2 Umdrehungen zurueck")
motor.umdrehungen(2, ZURUECK)
time.sleep(0.5)

# Aktuelle Position abfragen
print("Aktuelle Position: " + str(motor.lese_position()) + " Schritte")

# Geschwindigkeit aendern
# 300 sps liegt im Resonanzbereich -> im Vollschritt merklich rauer.
# Fuer wirklich ruhigen Langsamlauf am Treiber Mikroschritt aktivieren.
print("Langsamer: 300 sps, 1 Umdrehung")
motor.geschwindigkeit(300)
motor.umdrehungen(1, VOR)
time.sleep(0.5)

print("Schnell: 1000 sps, 1 Umdrehung zurueck")
motor.geschwindigkeit(1000)
motor.umdrehungen(1, ZURUECK)
time.sleep(0.5)

# Treiber deaktivieren (spart Strom, kein Haltemoment mehr)
motor.deaktivieren()
print("Treiber deaktiviert (Motor stromlos).")
time.sleep(2)

# Treiber wieder aktivieren
motor.aktivieren()
print("Treiber aktiviert.")
motor.schritte(50, VOR)
time.sleep(0.5)

# Abschalten
motor.aus()
print("Motor abgeschaltet.")
