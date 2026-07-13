"""
Beispiel fuer NIT Bibliothek: INA219
Zeigt: Lastprofil mit gleitendem Mittelwert fuer den Strom
Hardware: INA219 am I2C-Bus mit Last (z. B. LED-Streifen oder Motor)
"""

from machine import I2C, Pin
from time import sleep
from nitbw_ina219 import INA219


# --- Initialisierung ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = INA219(i2c, shunt_ohms=0.1, max_expected_current=2.0)

fenster = []
fenster_groesse = 10


# --- Hauptprogramm ---
while True:
    strom_ma = sensor.read_current_ma()
    fenster.append(strom_ma)
    if len(fenster) > fenster_groesse:
        fenster.pop(0)

    mittelwert = sum(fenster) / len(fenster)
    print(f"Strom aktuell: {strom_ma:8.2f} mA | Mittelwert({len(fenster)}): {mittelwert:8.2f} mA")
    sleep(0.2)
