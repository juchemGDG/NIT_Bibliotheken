"""
Beispiel fuer NIT Bibliothek: ESPNOW Broker-Client (ohne Subscribe-Eingabe)
Zeigt: Allereinfachster Client fuer den Mini-Broker

Ablauf:
- Ein festes Topic-Filter wird beim Start abonniert
- Danach nur noch Publish-Eingaben im Format: topic: message

Hardware: 1x ESP32 als Broker + 1x ESP32 als Client
"""

from nitbw_espnow import ESPNow
import time


# --- Konfiguration ---
BROKER_MAC = "AA:BB:CC:DD:EE:FF"
SUBSCRIBE_FILTER = "schule/chat/#"


# --- Initialisierung ---
esp = ESPNow()

print("=== ESPNOW Broker-Client (ohne Subscribe-Eingabe) ===")
print("Eigene MAC:", esp.get_mac())
print("Broker:", BROKER_MAC)
print("Abo-Filter:", SUBSCRIBE_FILTER)
print("")
print("Nur dieses Eingabeformat nutzen:")
print("topic: message")
print("")


def send_subscribe(topic_filter):
    esp.send_json(BROKER_MAC, {
        "_proto": "nitbw-mqtt-lite-broker",
        "type": "subscribe",
        "topic": topic_filter,
    })


def send_publish(topic, message):
    esp.send_json(BROKER_MAC, {
        "_proto": "nitbw-mqtt-lite-broker",
        "type": "publish",
        "topic": topic,
        "payload": message,
    })


def zeige_empfangene_nachrichten(max_nachrichten=8):
    anzahl = 0
    while anzahl < max_nachrichten:
        data, sender = esp.receive_json(timeout_ms=80)
        if data is None:
            break

        if data.get("_proto") != "nitbw-mqtt-lite-broker":
            anzahl += 1
            continue

        msg_type = data.get("type")

        if msg_type == "deliver":
            topic = data.get("topic")
            payload = data.get("payload")
            original_sender = data.get("sender")
            print("Empfangen [{}] von {}: {}".format(topic, original_sender, payload))

        elif msg_type == "ack":
            print("Broker-ACK:", data.get("message"))

        anzahl += 1


# Festes Subscribe beim Start
send_subscribe(SUBSCRIBE_FILTER)
print("Start-Subscribe gesendet:", SUBSCRIBE_FILTER)
time.sleep(0.05)


# --- Hauptprogramm ---
while True:
    zeige_empfangene_nachrichten()

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

    send_publish(topic, message)
    print("Publish gesendet [{}]: {}".format(topic, message))
