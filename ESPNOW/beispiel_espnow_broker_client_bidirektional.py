"""
Beispiel fuer NIT Bibliothek: ESPNOW Broker-Client (bidirektional)
Zeigt: Jeder Client ist Sender und Empfaenger, Broker uebernimmt Verteilung
Hardware: 1x ESP32 als Broker + mehrere ESP32 als Clients

Nutzung in der Klasse (z. B. bis 10 Gruppen/Clients):
- Beide Clients nutzen diese Datei
- Jeder Client setzt einen eindeutigen CLIENT_NAME (z. B. "gruppe01")
- Gleiche BROKER_MAC eintragen
- Topic/Subscription wird automatisch erzeugt
"""

from nitbw_espnow import ESPNow
import time


# --- Konfiguration ---
BROKER_MAC = "AA:BB:CC:DD:EE:FF"
CLIENT_NAME = "gruppe01"

# Verfuegbare Modi:
# - "all": empfange alle Gruppen (ausser eigene Nachrichten)
# - "selected": empfange nur in TARGET_CLIENTS genannte Gruppen
SUBSCRIBE_MODE = "all"
TARGET_CLIENTS = ["gruppe02", "gruppe03"]

# Jeder Client sendet auf sein eigenes Topic.
OUTGOING_TOPIC = "schule/chat/{}/out".format(CLIENT_NAME)

# Jeder Client abonniert je nach Modus alle oder nur ausgewaehlte Topics.
if SUBSCRIBE_MODE == "all":
    SUBSCRIPTIONS = ["schule/chat/+/out"]
elif SUBSCRIBE_MODE == "selected":
    SUBSCRIPTIONS = []
    for name in TARGET_CLIENTS:
        if name != CLIENT_NAME:
            SUBSCRIPTIONS.append("schule/chat/{}/out".format(name))
else:
    raise ValueError("SUBSCRIBE_MODE muss 'all' oder 'selected' sein")

PUBLISH_INTERVAL_S = 2.0


# --- Initialisierung ---
esp = ESPNow()

print("=== ESPNOW Broker-Client (bidirektional) ===")
print("Eigene MAC:", esp.get_mac())
print("Client:", CLIENT_NAME)
print("Broker:", BROKER_MAC)
print("Sende-Topic:", OUTGOING_TOPIC)
print("Subscriptions:", SUBSCRIPTIONS)
print()


def send_subscribe(topic_filter):
    esp.send_json(BROKER_MAC, {
        "_proto": "nitbw-mqtt-lite-broker",
        "type": "subscribe",
        "topic": topic_filter,
    })


def send_publish(topic, payload):
    esp.send_json(BROKER_MAC, {
        "_proto": "nitbw-mqtt-lite-broker",
        "type": "publish",
        "topic": topic,
        "payload": payload,
    })


# Subscriptions beim Start anmelden.
for topic_filter in SUBSCRIPTIONS:
    send_subscribe(topic_filter)
    print("Subscribe gesendet:", topic_filter)
    time.sleep(0.05)


# --- Hauptprogramm ---
zaehler = 0
naechstes_publish = time.ticks_ms()

while True:
    jetzt = time.ticks_ms()

    # Regelmaessig eigene Nachricht veroeffentlichen.
    if time.ticks_diff(jetzt, naechstes_publish) >= 0:
        payload = {
            "client": CLIENT_NAME,
            "zaehler": zaehler,
            "text": "Hallo von {}".format(CLIENT_NAME),
        }

        send_publish(OUTGOING_TOPIC, payload)
        print("Publish gesendet auf {}: {}".format(OUTGOING_TOPIC, payload))

        zaehler += 1
        naechstes_publish = time.ticks_add(jetzt, int(PUBLISH_INTERVAL_S * 1000))

    # Nachrichten vom Broker empfangen.
    data, sender = esp.receive_json(timeout_ms=120)
    if data is None:
        continue

    if data.get("_proto") != "nitbw-mqtt-lite-broker":
        print("Ignoriere Fremdprotokoll von {}: {}".format(sender, data))
        continue

    msg_type = data.get("type")

    if msg_type == "deliver":
        topic = data.get("topic")
        payload = data.get("payload")
        original_sender = data.get("sender")

        print("Empfangen von {} auf {}: {}".format(original_sender, topic, payload))

    elif msg_type == "ack":
        print("Broker-ACK:", data.get("message"))

    else:
        print("Unbekannter Typ vom Broker:", msg_type)
