"""
Beispiel fuer NIT Bibliothek: ADS1015
Zeigt: Differenzialmessung zwischen A0 und A1
Hardware: ADS1015 am I2C-Bus, zwei Messpunkte an A0/A1
"""

from machine import I2C, Pin
from time import sleep
from nitbw_ads1015 import ADS1015


# --- Initialisierung ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
adc = ADS1015(i2c, pga=ADS1015.PGA_2_048V)


# --- Hauptprogramm ---
while True:
    spannung_diff = adc.read_diff_voltage(ADS1015.MUX_DIFF_0_1)
    raw_diff = adc.read_diff_raw(ADS1015.MUX_DIFF_0_1)
    print(f"Differenzial A0-A1: {spannung_diff:.5f} V (raw={raw_diff})")
    sleep(0.5)
