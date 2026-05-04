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
START_SUBSCRIBE = "10C/#"
USE_CONNECT_ID = True


# --- Initialisierung ---
esp = ESPNow()
mqtt = ESPNowMQTT(esp, BROKER_MAC)

print("=== ESPNOW Broker-Client (subscribe) ===")
print("Eigene MAC:", esp.get_mac())
print("Broker:", mqtt.broker_mac)
print("Subscribe auf:", START_SUBSCRIBE)

if USE_CONNECT_ID:
    ok, reason, bestaetigte_id = mqtt.connect_id(CLIENT_ID, timeout_ms=800)
    if ok:
        print("Connect-ID erfolgreich:", bestaetigte_id)
    else:
        print("Connect-ID fehlgeschlagen:", reason)

mqtt.subscribe(START_SUBSCRIBE)
print("Subscribe gesendet:", START_SUBSCRIBE)
print()


# --- Hauptprogramm ---
zaehler = 0
while True:
    # Optionaler Heartbeat-Publish wie im Minimalcode.
    mqtt.publish("10C/zaehler", str(zaehler))
    zaehler += 1

    # Mehrere Nachrichten pro Runde abholen.
    for eintrag in mqtt.zeige_json(max_nachrichten=5, timeout_ms=120):
        print("Empfangen [{}]: {}".format(eintrag.get("topic"), eintrag.get("payload")))

    time.sleep(1)
