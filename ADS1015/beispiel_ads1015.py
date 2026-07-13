"""
Beispiel fuer NIT Bibliothek: ADS1015
Zeigt: Single-Ended-Messung auf allen vier Kanaelen
Hardware: ADS1015 am I2C-Bus, Potentiometer/Sensoren an A0-A3
"""

from machine import I2C, Pin
from time import sleep
from nitbw_ads1015 import ADS1015


# --- Initialisierung ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
adc = ADS1015(i2c, addr=0x48, pga=ADS1015.PGA_4_096V, data_rate=ADS1015.DR_1600)


# --- Hauptprogramm ---
while True:
    ch0, ch1, ch2, ch3 = adc.read_all()
    print("--- ADS1015 ---")
    print(f"A0: {ch0:.3f} V")
    print(f"A1: {ch1:.3f} V")
    print(f"A2: {ch2:.3f} V")
    print(f"A3: {ch3:.3f} V")
    sleep(0.5)
