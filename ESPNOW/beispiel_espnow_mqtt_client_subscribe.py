"""
Beispiel fuer NIT Bibliothek: ESPNOW Broker-Client (subscribe)
Zeigt: Minimaler Subscribe-Client mit optionalem connect_id
Hardware: 1x ESP32 als Broker, 1x ESP32 als Client
"""

from nitbw_espnow import ESPNow
from nitbw_espnow_mqtt import ESPNowMQTT
import time


# --- Konfiguration ---
BROKER_MAC = "0C:8B:95:B9:6B:40"
CLIENT_ID = "10c_client"
USE_CONNECT_ID = True
# Maximale Wartezeit auf die naechste Nachricht in Millisekunden.
# None bedeutet unbegrenzt warten.
WARTEZEIT_MS = None

# --- Initialisierung ---
esp = ESPNow()
mqtt = ESPNowMQTT(esp, BROKER_MAC)

print("=== ESPNOW Broker-Client (subscribe) ===")
print("Eigene MAC:", esp.get_mac())
print("Broker:", mqtt.broker_mac)

if USE_CONNECT_ID:
    ok, reason, bestaetigte_id = mqtt.connect_id(CLIENT_ID, timeout_ms=800)
    if ok:
        print("Connect-ID erfolgreich:", bestaetigte_id)
    else:
        print("Connect-ID fehlgeschlagen:", reason)

mqtt.subscribe("10C/#")

# --- Hauptprogramm ---
while True:
    nachricht = mqtt.zeige_json(wartezeit_ms=WARTEZEIT_MS)
    if nachricht:
        print(nachricht.get("payload"))
    time.sleep(1)
