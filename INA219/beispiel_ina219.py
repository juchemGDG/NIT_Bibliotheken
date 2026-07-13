"""
Beispiel fuer NIT Bibliothek: INA219
Zeigt: Grundlegendes Auslesen von Strom, Spannung und Leistung
Hardware: INA219 am I2C-Bus mit Shunt (typisch 0.1 Ohm)
"""

from machine import I2C, Pin
from time import sleep
from nitbw_ina219 import INA219


# --- Initialisierung ---
# I2C initialisieren
# ESP32 Standard: SCL=22, SDA=21
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# INA219 initialisieren
sensor = INA219(i2c, addr=0x40, shunt_ohms=0.1, max_expected_current=2.0)


# --- Hauptprogramm ---
while True:
    bus_v, shunt_mv, current_ma, power_mw, load_v = sensor.read_all()

    print("--- INA219 Messung ---")
    print(f"Busspannung:  {bus_v:.3f} V")
    print(f"Shunt:       {shunt_mv:.3f} mV")
    print(f"Strom:       {current_ma:.2f} mA")
    print(f"Leistung:    {power_mw:.2f} mW")
    print(f"Lastspannung:{load_v:.3f} V")

    if sensor.overflow():
        print("Hinweis: Messbereichsueberlauf erkannt")

    sleep(1)
