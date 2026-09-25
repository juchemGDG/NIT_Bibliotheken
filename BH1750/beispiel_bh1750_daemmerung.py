"""
Beispiel fuer NIT Bibliothek: BH1750
Zeigt: Daemmerungsschalter mit Mittelwert und einstellbarer Empfindlichkeit
Hardware: BH1750 (GY-302) am I2C-Bus, LED an GPIO 2 (interne LED des ESP32)
"""

from machine import I2C, Pin
from time import sleep
from nitbw_bh1750 import BH1750


# --- Initialisierung ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = BH1750(i2c, mode=BH1750.CONT_HIRES)

# Hoehere Empfindlichkeit fuer den dunklen Bereich (laengere Messzeit)
sensor.set_sensitivity(2.0)

led = Pin(2, Pin.OUT)
SCHWELLE_LX = 20.0


# --- Hauptprogramm ---
while True:
    # Mittelwert ueber mehrere Messungen gegen Flackern (z. B. Leuchtstoffroehren)
    lux = sensor.read_averaged(n=5)

    if lux < SCHWELLE_LX:
        led.value(1)
        zustand = "AN "
    else:
        led.value(0)
        zustand = "AUS"

    print(f"{lux:8.1f} lx | Licht: {zustand} (Schwelle {SCHWELLE_LX:.0f} lx)")
    sleep(1)
