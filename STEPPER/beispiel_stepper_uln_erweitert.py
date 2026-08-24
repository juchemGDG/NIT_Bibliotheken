"""
Beispiel fuer NIT Bibliothek: Stepper (StepperULN) - Erweitertes Beispiel
Zeigt: Nicht-blockierender Modus, zwei Motoren gleichzeitig, Geschwindigkeitswechsel
Hardware: Zwei 28BYJ-48 + ULN2003-Platinen am ESP32
"""

from nitbw_stepper import StepperULN, VOR, ZURUECK
import time


# --- Initialisierung ---
# Hinweis:
# 28BYJ-48 laeuft hier im Halbschrittbetrieb.
# Fuer 360 Grad sind typischerweise 4096 Schritte noetig (praxisnah oft ~4076).
# Motor A: IN1..IN4 an GPIO 14, 27, 26, 25
motorA = StepperULN(in1=14, in2=27, in3=26, in4=25,
                    schritte_pro_umdrehung=4096,
                    geschwindigkeit=150)

# Motor B: IN1..IN4 an GPIO 13, 12, 4, 2
motorB = StepperULN(in1=13, in2=12, in3=4, in4=2,
                    schritte_pro_umdrehung=4096,
                    geschwindigkeit=300)

print("=== StepperULN Erweitertes Beispiel ===")
print("Hinweis: Halbschrittbetrieb aktiv -> 4096 Schritte pro Umdrehung")

# --- Beispiel 1: Zwei Motoren gleichzeitig (nicht-blockierend) ---
print("\n1) Zwei Motoren gleichzeitig drehen")
print("   Motor A: 2048 Schritte vorwaerts (150 sps)")
print("   Motor B: 4096 Schritte vorwaerts (300 sps)")

motorA.starte(2048, VOR)
motorB.starte(4096, VOR)

while not (motorA.ist_fertig() and motorB.ist_fertig()):
    motorA.ausfuehren()
    motorB.ausfuehren()

print("   Beide Motoren fertig.")
print("   Position A: " + str(motorA.lese_position()) + " | Position B: " + str(motorB.lese_position()))
time.sleep(1)


# --- Beispiel 2: Gegenlaeurige Bewegung ---
print("\n2) Gegenlaeurige Bewegung (A vor, B zurueck)")

motorA.starte(2048, VOR)
motorB.starte(2048, ZURUECK)

while not (motorA.ist_fertig() and motorB.ist_fertig()):
    motorA.ausfuehren()
    motorB.ausfuehren()

print("   Fertig.")
time.sleep(1)


# --- Beispiel 3: stopp() mitten in der Bewegung ---
print("\n3) Bewegung nach 1024 Schritten abbrechen")

motorA.starte(4096, VOR)
schritte_gezaehlt = 0
start_pos = motorA.lese_position()

while not motorA.ist_fertig():
    if motorA.ausfuehren():
        schritte_gezaehlt += 1
    if schritte_gezaehlt >= 1024:
        motorA.stopp()
        break

print("   Motor A abgebrochen. Ausgefuehrte Schritte: " + str(schritte_gezaehlt))
print("   Position A: " + str(motorA.lese_position()))
time.sleep(1)


# --- Beispiel 4: Geschwindigkeitswechsel waehrend Lauf ---
print("\n4) Geschwindigkeit waehrend Lauf erhoehen")
print("   Start: 50 sps, nach Haelfte: 400 sps")

motorB.geschwindigkeit(50)
motorB.starte(1024, VOR)
haelfte = False

while not motorB.ist_fertig():
    motorB.ausfuehren()
    # Nach 512 Schritten Geschwindigkeit erhoehen
    # (Position als Proxy - Startpunkt merken)
    schritte_bisher = abs(motorB.lese_position() - 0)
    if not haelfte and motorB._ziel <= 512:
        motorB.geschwindigkeit(400)
        haelfte = True
        print("   Geschwindigkeit auf 400 sps erhoeht.")

print("   Fertig. Position B: " + str(motorB.lese_position()))
time.sleep(1)


# --- Beispiel 5: Sequenzielle nicht-blockierende Bewegungen ---
print("\n5) Drei Sequenzen hintereinander (nicht-blockierend gesteuert)")

bewegungen = [
    (1024, VOR,     200, "1024 Schritte vor"),
    (512, ZURUECK,  300, "512 Schritte zurueck"),
    (1024, VOR,     150, "1024 Schritte vor"),
]

for schritte, richtung, sps, bezeichnung in bewegungen:
    print("   " + bezeichnung + " (" + str(sps) + " sps)")
    motorA.geschwindigkeit(sps)
    motorA.starte(schritte, richtung)
    while not motorA.ist_fertig():
        motorA.ausfuehren()
    time.sleep(0.3)

print("   Sequenz abgeschlossen.")
print("   Endposition A: " + str(motorA.lese_position()))


# --- Aufraumen ---
motorA.aus()
motorB.aus()
print("\nBeide Motoren abgeschaltet.")
