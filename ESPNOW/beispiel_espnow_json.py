"""
Beispiel fuer NIT Bibliothek: ESPNOW
Zeigt: JSON-Daten (Dictionary) senden und empfangen
Hardware: 2x ESP32 mit WLAN
"""

from nitbw_espnow import ESPNow
import time


# --- Initialisierung ---
esp = ESPNow()

print("=== ESPNOW JSON-Beispiel ===")
print("Eigene MAC:", esp.get_mac())
print("Partner-MAC in PARTNER_MAC eintragen.")
print()

PARTNER_MAC = "AA:BB:CC:DD:EE:FF"


# --- Hauptprogramm ---
counter = 0
while True:
    daten = {
        "sensor": "temperatur",
        "wert": 21.5 + (counter % 5) * 0.1,
        "einheit": "C",
        "zaehler": counter
    }

    esp.send_json(PARTNER_MAC, daten)
    print("JSON gesendet:", daten)

    rx_dict, sender = esp.receive_json(timeout_ms=300)
    if rx_dict is not None:
        print("JSON empfangen von {}: {}".format(sender, rx_dict))

    counter += 1
    time.sleep(1)
