"""
Beispiel fuer NIT Bibliothek: Servo
Zeigt: Standard-Servo auf verschiedene Winkel fahren
Hardware: SG90 oder kompatibler Servo am ESP32
"""

from nitbw_servo import Servo
import time


# --- Initialisierung ---
# Servo an GPIO 13 anschliessen (Signal-Leitung)
servo = Servo(pin=13)

# --- Hauptprogramm ---
print("=== Servo Grundbeispiel ===")

# Auf Mittelposition fahren
print("Mitte (90°)")
servo.mitte()
time.sleep(1)

# Auf 0° fahren
print("Minimum (0°)")
servo.minimum()
time.sleep(1)

# Auf 180° fahren
print("Maximum (180°)")
servo.maximum()
time.sleep(1)

# Bestimmte Winkel anfahren
for grad in [0, 45, 90, 135, 180, 90]:
    print("Fahre auf " + str(grad) + "°")
    servo.winkel(grad)
    time.sleep(1)

# Aktuellen Winkel abfragen
print("Aktueller Winkel: " + str(servo.lese_winkel()) + "°")

# Servo abschalten
servo.aus()
print("Servo abgeschaltet.")
