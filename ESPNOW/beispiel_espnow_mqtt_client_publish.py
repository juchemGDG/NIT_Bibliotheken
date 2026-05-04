"""
Beispiel fuer NIT Bibliothek: ESPNOW Broker-Client (publish)
Zeigt: Minimaler Publish-Client mit optionalem connect_id
Hardware: 1x ESP32 als Broker, 1x ESP32 als Client
"""

from nitbw_espnow import ESPNow
from nitbw_espnow_mqtt import ESPNowMQTT
import time


# --- Konfiguration ---
BROKER_MAC = "0C:8B:95:B9:6B:40"
CLIENT_ID = "10c_publisher"
PUBLISH_TOPIC = "10C/zaehler"
USE_CONNECT_ID = True


# --- Initialisierung ---
esp = ESPNow()
mqtt = ESPNowMQTT(esp, BROKER_MAC)

print("=== ESPNOW Broker-Client (publish) ===")
print("Eigene MAC:", esp.get_mac())
print("Broker:", mqtt.broker_mac)
print("Publish auf:", PUBLISH_TOPIC)

verbunden = True
if USE_CONNECT_ID:
    ok, reason, bestaetigte_id = mqtt.connect_id(CLIENT_ID, timeout_ms=800)
    verbunden = ok
    if ok:
        print("Connect-ID erfolgreich:", bestaetigte_id)
    else:
        print("Connect-ID fehlgeschlagen:", reason)

print()


# --- Hauptprogramm ---
zaehler = 0
while True:
    if not verbunden:
        print("Kein Publish: connect_id war nicht erfolgreich.")
        time.sleep(2)
        continue

    payload = str(zaehler)
    mqtt.publish(PUBLISH_TOPIC, payload)
    #print("Publish gesendet [{}]: {}".format(PUBLISH_TOPIC, payload))

    zaehler += 1
    time.sleep(1)
