"""
Beispiel fuer NIT Bibliothek: ESPNOW Mini-Broker
Zeigt: Ein ESP32 uebernimmt Broker-Rolle und verteilt Publish-Nachrichten
Hardware: 1x ESP32 als Broker, 2+ ESP32 als Clients
"""

from nitbw_espnow import ESPNow
from nitbw_espnow_mqtt import ESPNowMQTT
import time


# --- Initialisierung ---
esp = ESPNow()
REQUIRE_CONNECT = False
mqtt = ESPNowMQTT(esp, require_connect=REQUIRE_CONNECT)

print("=== ESPNOW Mini-Broker ===")
print("Broker-MAC:", esp.get_mac())
print("Connect erforderlich:", REQUIRE_CONNECT)
print("Warte auf subscribe/publish von Clients...")
print()


# --- Hauptprogramm ---
while True:
    verarbeitet = mqtt.handle_broker_message(timeout_ms=400)
    if not verarbeitet:
        time.sleep(0.02)
