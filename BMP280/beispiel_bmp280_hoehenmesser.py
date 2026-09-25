"""
Beispiel fuer NIT Bibliothek: BMP280
Zeigt: Relativer Hoehenmesser (z. B. Stockwerke im Treppenhaus) mit Filter und Mittelwert
Hardware: BMP280 am I2C-Bus (Adresse 0x76 oder 0x77)
"""

from machine import I2C, Pin
from time import sleep
from nitbw_bmp280 import BMP280


# --- Initialisierung ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = BMP280(i2c)

# Hohe Aufloesung fuer kleine Hoehenaenderungen
sensor.configure(
    mode=BMP280.MODE_NORMAL,
    osrs_t=BMP280.OVERSAMPLE_X2,
    osrs_p=BMP280.OVERSAMPLE_X16,
    filter_coef=BMP280.FILTER_16,
    standby=BMP280.STANDBY_0_5
)

STOCKWERK_M = 3.0  # typische Stockwerkshoehe

# Startpunkt als Referenz (Hoehe 0 m) festlegen
print("Referenzmessung, Sensor ruhig halten ...")
_, p_start = sensor.read_averaged(n=20, delay_ms=20)
sensor.set_sea_level_pressure(sensor.calculate_sea_level_pressure(0, p_start))


# --- Hauptprogramm ---
while True:
    temperatur, druck = sensor.read_averaged(n=10, delay_ms=10)
    hoehe = sensor.calculate_altitude(druck)
    stockwerk = round(hoehe / STOCKWERK_M)

    print(f"{druck:8.2f} hPa | {hoehe:+6.2f} m | Stockwerk {stockwerk:+d} | {temperatur:.1f} C")
    sleep(1)
