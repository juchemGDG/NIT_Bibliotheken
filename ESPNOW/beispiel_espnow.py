"""
Beispiel fuer NIT Bibliothek: ESPNOW
Zeigt: Textnachrichten senden und empfangen
Hardware: 2x ESP32 mit WLAN
"""

from nitbw_espnow import ESPNow
import time


# --- Initialisierung ---
esp = ESPNow()

print("=== ESPNOW Grundbeispiel ===")
print("Eigene MAC:", esp.get_mac())
print("Trage unten die MAC des Partner-ESP32 ein.")
print()

PARTNER_MAC = "AA:BB:CC:DD:EE:FF"

# Peer optional vorab anlegen (send() wuerde ihn auch automatisch anlegen)
esp.add_peer(PARTNER_MAC)


# --- Hauptprogramm ---
zaehler = 0
while True:
    nachricht = "Hallo vom ESP32 #{}".format(zaehler)
    esp.send(PARTNER_MAC, nachricht)
    print("Gesendet an {}: {}".format(PARTNER_MAC, nachricht))

    msg, sender = esp.receive(timeout_ms=250)
    if msg is not None:
        print("Empfangen von {}: {}".format(sender, msg))

    zaehler += 1
    time.sleep(1)
