"""
Beispiel fuer NIT Bibliothek: RTC
Zeigt: Datum und Uhrzeit im Seriellen Monitor ausgeben
Hardware: DS3231 oder DS1307 RTC-Modul am ESP32
"""

from nitbw_rtc import RTC
from machine import I2C, Pin
import time


# --- Initialisierung ---
# DS3231 ist der Standard-Chip. Fuer DS1307: RTC(chip='DS1307')
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
rtc = RTC(chip='DS3231', i2c=i2c)

# --- Hauptprogramm ---
print("=== RTC Einfaches Beispiel ===")
print("Datum und Uhrzeit werden jede Sekunde ausgegeben.")
print()

while True:
    print(rtc.toString("DD.MM.YYYY hh:mm:ss"))
    time.sleep(1)
