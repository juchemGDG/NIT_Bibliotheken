"""
Beispiel fuer NIT Bibliothek: Stepper (StepperDir) - Erweitertes Beispiel
Zeigt: Nicht-blockierender Modus, Richtungswechsel, Sequenzen, stopp()
Hardware: NEMA 17 + A4988 (oder DRV8825) am ESP32
"""

from nitbw_stepper import StepperDir, VOR, ZURUECK
import time


# --- Initialisierung ---
# STEP -> GPIO 14, DIR -> GPIO 27, ENABLE -> GPIO 26
# 800 sps liegt oberhalb der Vollschritt-Resonanz (~200-600 sps) -> ruhiger Lauf.
motor = StepperDir(step_pin=14, dir_pin=27, enable_pin=26,
                   schritte_pro_umdrehung=200,
                   geschwindigkeit=800)

print("=== StepperDir Erweitertes Beispiel ===")


# --- Beispiel 1: Nicht-blockierende Bewegung mit Status-Ausgabe ---
print("\n1) 400 Schritte nicht-blockierend (800 sps)")

motor.starte(400, VOR)

schritt_log = 0
while not motor.ist_fertig():
    if motor.ausfuehren():
        schritt_log += 1
        # Alle 100 Schritte eine Meldung ausgeben
        if schritt_log % 100 == 0:
            print("   ... " + str(schritt_log) + " Schritte ausgefuehrt")

print("   Fertig. Position: " + str(motor.lese_position()))
time.sleep(0.5)


# --- Beispiel 2: Hin- und Herfahren (Pendelbewegung) ---
print("\n2) Pendelbewegung: 3x hin und her (je 200 Schritte)")

for i in range(3):
    motor.starte(200, VOR)
    while not motor.ist_fertig():
        motor.ausfuehren()
    time.sleep(0.1)

    motor.starte(200, ZURUECK)
    while not motor.ist_fertig():
        motor.ausfuehren()
    time.sleep(0.1)
    print("   Durchlauf " + str(i + 1) + " fertig")

print("   Endposition: " + str(motor.lese_position()))
time.sleep(0.5)


# --- Beispiel 3: Bewegung per stopp() abbrechen ---
print("\n3) Bewegung nach ca. 100 ms abbrechen")

motor.geschwindigkeit(200)
motor.starte(2000, VOR)

start_ms = time.ticks_ms()
while not motor.ist_fertig():
    motor.ausfuehren()
    if time.ticks_diff(time.ticks_ms(), start_ms) >= 100:
        motor.stopp()
        break

print("   Abgebrochen. Position: " + str(motor.lese_position()))
time.sleep(0.5)


# --- Beispiel 4: Geschwindigkeitsrampe ---
print("\n4) Geschwindigkeitsrampe: 100 -> 2000 sps in 10 Stufen")

for sps in range(100, 2001, 190):
    motor.geschwindigkeit(sps)
    motor.starte(50, VOR)
    while not motor.ist_fertig():
        motor.ausfuehren()
    print("   " + str(sps) + " sps: 50 Schritte abgeschlossen")

time.sleep(0.5)

# Wieder zurueck zur Ausgangsposition
schritte_zurueck = abs(motor.lese_position())
print("   Zurueck: " + str(schritte_zurueck) + " Schritte")
motor.geschwindigkeit(800)
motor.starte(schritte_zurueck, ZURUECK)
while not motor.ist_fertig():
    motor.ausfuehren()
print("   Nullposition: " + str(motor.lese_position()))
time.sleep(0.5)


# --- Beispiel 5: Treiber deaktivieren und wieder aktivieren ---
print("\n5) Treiber deaktivieren und reaktivieren")

motor.deaktivieren()
print("   Treiber AUS (Motor kann frei gedreht werden)")
time.sleep(3)

motor.aktivieren()
print("   Treiber EIN")
motor.geschwindigkeit(400)
motor.schritte(100, VOR)
print("   100 Schritte ausgefuehrt. Position: " + str(motor.lese_position()))
time.sleep(0.5)


# --- Aufraumen ---
motor.aus()
print("\nMotor abgeschaltet.")
