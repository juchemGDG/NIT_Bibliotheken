"""
Beispiel fuer NIT Bibliothek: RTC
Zeigt: Alle Funktionen der RTC-Bibliothek im Ueberblick
Hardware: DS3231 RTC-Modul am ESP32 (DS1307 unterstuetzt weniger Funktionen)
"""

from nitbw_rtc import RTC, DS3231
import time


# --- Initialisierung ---
rtc = RTC(chip='DS3231', scl=22, sda=21)

# --- Hauptprogramm ---

# ============================================================
# 1. Verschiedene Formatierungen mit toString()
# ============================================================
print("=== Formatierung ===")
print("Deutsch:   " + rtc.toString("DD.MM.YYYY hh:mm:ss"))
print("US-Format: " + rtc.toString("MM/DD/YYYY hh:mm:ss"))
print("ISO 8601:  " + rtc.toString("YYYY-MM-DD hh:mm:ss"))
print("Nur Zeit:  " + rtc.toString("hh:mm:ss"))
print("Nur Datum: " + rtc.toString("DD.MM.YYYY"))
print("Mit Tag:   " + rtc.toString("DDD, DD. MMM YYYY"))
print("Kurz:      " + rtc.toString("DD.MM.YY hh:mm"))
print()

# ============================================================
# 2. Einzelne Werte abfragen
# ============================================================
print("=== Einzelwerte ===")
daten = rtc.aktuelleDaten()
print("Alle Daten:", daten)
print("Stunde:    ", rtc.stunden())
print("Minute:    ", rtc.minuten())
print("Sekunde:   ", rtc.sekunden())
print("Tag:       ", rtc.tag())
print("Monat:     ", rtc.monat())
print("Jahr:      ", rtc.jahr())
print("Wochentag: ", rtc.wochentag(), rtc.wochentagName())
print("Monatsname:", rtc.monatsName())
print()

# ============================================================
# 3. Hilfsfunktionen
# ============================================================
print("=== Hilfsfunktionen ===")
print("Schaltjahr " + str(rtc.jahr()) + ":", rtc.istSchaltjahr())
print("Schaltjahr 2024:", rtc.istSchaltjahr(2024))
print("Schaltjahr 2025:", rtc.istSchaltjahr(2025))
print("Tage im aktuellen Monat:", rtc.tageImMonat())
print("Tage im Februar 2024:", rtc.tageImMonat(2, 2024))
print("Tage im Februar 2025:", rtc.tageImMonat(2, 2025))
print("Zeit als Tuple:", rtc.zeitTuple())
print("Sekunden seit 2000:", rtc.unixZeit())
print()

# ============================================================
# 4. Oszillator-Status
# ============================================================
print("=== Oszillator ===")
print("Oszillator laeuft:", rtc.laueft())
print()

# ============================================================
# 5. DS3231-spezifisch: Temperatur
# ============================================================
if isinstance(rtc, DS3231):
    print("=== Temperatur (DS3231) ===")
    print("Temperatur: {:.2f} C".format(rtc.temperatur()))
    print()

# ============================================================
# 6. DS3231-spezifisch: Alarm setzen
# ============================================================
if isinstance(rtc, DS3231):
    print("=== Alarm (DS3231) ===")

    # Alarm 1: In 1 Minute ausloesen
    d = rtc.aktuelleDaten()
    alarm_min = (d['minuten'] + 1) % 60
    alarm_std = d['stunden']
    if d['minuten'] == 59:
        alarm_std = (alarm_std + 1) % 24

    rtc.alarm1(stunden=alarm_std, minuten=alarm_min, sekunden=0)
    print("Alarm 1 gesetzt auf {:02d}:{:02d}:00".format(alarm_std, alarm_min))

    # Alarm-Status pruefen
    a1, a2 = rtc.alarmStatus()
    print("Alarm 1 aktiv:", a1)
    print("Alarm 2 aktiv:", a2)

    # Alarm loeschen
    rtc.alarmLoeschen()
    print("Alarm-Status geloescht.")
    print()

# ============================================================
# 7. Uhr ueber String stellen (Beispiel)
# ============================================================
print("=== Uhr stellen per String ===")
print("Vor dem Stellen: " + rtc.toString("DD.MM.YYYY hh:mm:ss"))

# Auskommentiert - nur bei Bedarf aktivieren:
# rtc.setVonString("2026-03-10 14:30:00")
# print("Nach dem Stellen: " + rtc.toString("DD.MM.YYYY hh:mm:ss"))
print("(Auskommentiert - zum Testen Kommentarzeichen entfernen)")
print()

# ============================================================
# 8. Stell-Pin pruefen beim Boot (Beispiel)
# ============================================================
print("=== Stell-Pin (GPIO 4) ===")
print("Falls GPIO 4 beim Boot HIGH ist, wird seriell gestellt.")
# Auskommentiert - nur bei Bedarf aktivieren:
# rtc.pruefeStellPin(pin_nr=4)
print("(Auskommentiert - zum Testen Kommentarzeichen entfernen)")
print()

# ============================================================
# 9. Endlosschleife: Uhrzeit anzeigen
# ============================================================
print("=== Laufende Uhr ===")
while True:
    zeile = rtc.toString("DDD DD.MM.YYYY hh:mm:ss")
    if isinstance(rtc, DS3231):
        zeile += "  {:.1f}C".format(rtc.temperatur())
    print(zeile)
    time.sleep(1)
