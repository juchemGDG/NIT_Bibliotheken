"""
Beispiel fuer NIT Bibliothek: RTC
Zeigt: Uhr stellen ueber die serielle Schnittstelle
Hardware: DS3231 oder DS1307 RTC-Modul am ESP32
"""

from nitbw_rtc import RTC
from machine import I2C, Pin
import time


# --- Initialisierung ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
rtc = RTC(chip='DS3231', i2c=i2c)

# --- Hauptprogramm ---
print("=== RTC Uhr stellen (Seriell) ===")
print()

# Aktuelle Zeit anzeigen
print("Aktuelle Zeit: " + rtc.toString("DDD DD.MM.YYYY hh:mm:ss"))
print()

# Uhr ueber serielle Eingabe stellen
print("Die Uhr wird jetzt ueber die serielle Schnittstelle gestellt.")
print("Öffne die Shell in Thonny (unten meist schon geöffnet).")
print("Gib dort Datum und Uhrzeit im folgenden Format ein:")
print("  YYYY-MM-DD hh:mm:ss")
print("  Beispiel: 2026-03-10 14:30:00")
print()
rtc.stellenSeriell()

# Neue Zeit anzeigen
print()
print("Neue Zeit: " + rtc.toString("DDD DD.MM.YYYY hh:mm:ss"))
print()

# Danach laeuft die Uhr weiter und zeigt die aktuelle Zeit
print("Zeit laeuft weiter:")
while True:
    print(rtc.toString("hh:mm:ss"))
    time.sleep(1)
