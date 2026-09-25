"""
Beispiel fuer NIT Bibliothek: BH1750
Zeigt: Kontinuierliche Messung der Beleuchtungsstaerke in Lux
Hardware: BH1750 (GY-302) am I2C-Bus
"""

from machine import I2C, Pin
from time import sleep
from nitbw_bh1750 import BH1750


# --- Initialisierung ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = BH1750(i2c, addr=BH1750.ADDR_LOW, mode=BH1750.CONT_HIRES)


# --- Hauptprogramm ---
while True:
    lux = sensor.read_lux()
    print(f"Beleuchtungsstaerke: {lux:8.1f} lx")
    sleep(1)
