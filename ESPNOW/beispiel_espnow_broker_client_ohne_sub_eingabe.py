"""
Beispiel fuer NIT Bibliothek: ESPNOW Broker-Client (ohne Subscribe-Eingabe)
Zeigt: Allereinfachster Client fuer den Mini-Broker

Ablauf:
- Ein festes Topic-Filter wird beim Start abonniert
- Danach nur noch Publish-Eingaben im Format: topic: message

Hardware: 1x ESP32 als Broker + 1x ESP32 als Client
"""

from nitbw_espnow import ESPNow
from nitbw_espnow_mqtt import ESPNowMQTT
import time


# --- Konfiguration ---
BROKER_MAC = "AA:BB:CC:DD:EE:FF"
SUBSCRIBE_FILTER = "schule/chat/#"


# --- Initialisierung ---
esp = ESPNow()
mqtt = ESPNowMQTT(esp, BROKER_MAC)

print("=== ESPNOW Broker-Client (ohne Subscribe-Eingabe) ===")
print("Eigene MAC:", esp.get_mac())
print("Broker:", mqtt.broker_mac)
print("Abo-Filter:", SUBSCRIBE_FILTER)
print("")
print("Nur dieses Eingabeformat nutzen:")
print("topic: message")
print("")


# Festes Subscribe beim Start
mqtt.subscribe(SUBSCRIBE_FILTER)
print("Start-Subscribe gesendet:", SUBSCRIBE_FILTER)
time.sleep(0.05)


# --- Hauptprogramm ---
while True:
    mqtt.zeige_nachrichten()

    eingabe = input("Eingabe (topic: message): ").strip()
    if not eingabe:
        continue

    if eingabe.lower() in ("q", "quit", "exit"):
        print("Beendet.")
        break

    if ":" not in eingabe:
        print("Ungueltig. Format: topic: message")
        continue

    topic, message = eingabe.split(":", 1)
    topic = topic.strip()
    message = message.strip()

    if not topic:
        print("Ungueltig. Topic fehlt.")
        continue

    mqtt.publish(topic, message)
    print("Publish gesendet [{}]: {}".format(topic, message))
