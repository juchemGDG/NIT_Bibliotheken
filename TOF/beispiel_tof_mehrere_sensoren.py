"""
Beispiel fuer NIT Bibliothek: TOF
Zeigt: Zwei VL53L0X-Sensoren am selben I2C-Bus mit XSHUT-Pins
Hardware: 2x VL53L0X (GY-530) am ESP32

VERKABELUNG:
===========
Beide Sensoren teilen sich den I2C-Bus (SDA + SCL).
Jeder Sensor braucht einen eigenen XSHUT-Pin zur Adress-Konfiguration.

Sensor LINKS        ESP32           Sensor RECHTS
VCC  ------------>  3.3V  <---------  VCC
SDA  ------------>  GPIO 21  <------  SDA    (gleicher Bus!)
SCL  ------------>  GPIO 22  <------  SCL    (gleicher Bus!)
GND  ------------>  GND   <---------  GND
XSHUT ----------->  GPIO 25          (eigener Pin)
                    GPIO 26  <------  XSHUT  (eigener Pin)

WICHTIG - Warum XSHUT noetig ist:
=================================
Alle VL53L0X starten mit derselben I2C-Adresse (0x29).
Wenn beide gleichzeitig aktiv waeren, wuerden sie sich gegenseitig stoeren.
Loesung: Ueber den XSHUT-Pin (Shutdown) schalten wir die Sensoren
         einzeln ein und geben jedem eine eigene Adresse.

Ablauf:
1. Beide XSHUT-Pins auf LOW  -> beide Sensoren sind AUS
2. Sensor LINKS einschalten   -> wacht bei 0x29 auf
3. Adresse aendern auf 0x30  -> Sensor LINKS hoert jetzt auf 0x30
4. Sensor RECHTS einschalten  -> wacht bei 0x29 auf (kein Konflikt!)
5. Beide Sensoren sind bereit mit verschiedenen Adressen
"""

from machine import I2C, Pin
from nitbw_tof import TOF
import time


# --- Initialisierung ---

# Schritt 1: Beide Sensoren ausschalten (XSHUT = LOW)
# Damit nur ein Sensor zur Zeit am Bus aktiv ist.
print("Sensoren werden konfiguriert...")
Pin(25, Pin.OUT, value=0)   # Sensor LINKS aus
Pin(26, Pin.OUT, value=0)   # Sensor RECHTS aus
time.sleep_ms(50)

# I2C-Bus erstellen (wird von beiden Sensoren geteilt)
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Schritt 2+3: Sensor LINKS aufwecken und Adresse auf 0x30 aendern
# Der Konstruktor setzt XSHUT=HIGH, wartet auf den Boot,
# und aendert die Adresse automatisch von 0x29 auf 0x30.
sensor_links = TOF(i2c, addr=0x30, xshut=25)
print("  Sensor LINKS:  Adresse 0x{:02X}".format(sensor_links.lese_adresse()))

# Schritt 4: Sensor RECHTS aufwecken (bleibt bei Standard-Adresse 0x29)
# Da Sensor LINKS jetzt auf 0x30 hoert, gibt es keinen Adresskonflikt.
sensor_rechts = TOF(i2c, addr=0x29, xshut=26)
print("  Sensor RECHTS: Adresse 0x{:02X}".format(sensor_rechts.lese_adresse()))

print()
print("Beide Sensoren bereit!")
print()

# --- Hauptprogramm ---
print("=== Zwei-Sensor-Messung ===")
print()

while True:
    links = sensor_links.messen_mm()
    rechts = sensor_rechts.messen_mm()

    # Ergebnisse formatieren
    text_l = "{:4d} mm".format(links) if links > 0 else "  -- mm"
    text_r = "{:4d} mm".format(rechts) if rechts > 0 else "  -- mm"

    print("LINKS: {}  |  RECHTS: {}".format(text_l, text_r))
    time.sleep(0.3)
