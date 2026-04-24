"""
Beispiel fuer NIT Bibliothek: ESPNOW Mini-Broker
Zeigt: Ein ESP32 uebernimmt Broker-Rolle und verteilt Publish-Nachrichten
Hardware: 1x ESP32 als Broker, 2+ ESP32 als Clients
"""

from nitbw_espnow import ESPNow
import time


# --- Initialisierung ---
esp = ESPNow()

print("=== ESPNOW Mini-Broker ===")
print("Broker-MAC:", esp.get_mac())
print("Warte auf subscribe/publish von Clients...")
print()


# Mapping: topic_filter -> set(sender_mac)
subscriptions = {}


def topic_matches(topic_filter, topic):
    filter_levels = topic_filter.split("/")
    topic_levels = topic.split("/")

    i = 0
    while i < len(filter_levels):
        f_level = filter_levels[i]

        if f_level == "#":
            return i == len(filter_levels) - 1

        if i >= len(topic_levels):
            return False

        t_level = topic_levels[i]
        if f_level != "+" and f_level != t_level:
            return False

        i += 1

    return i == len(topic_levels)


def add_subscription(sender_mac, topic_filter):
    if topic_filter not in subscriptions:
        subscriptions[topic_filter] = set()
    subscriptions[topic_filter].add(sender_mac)


def remove_subscription(sender_mac, topic_filter):
    if topic_filter not in subscriptions:
        return

    clients = subscriptions[topic_filter]
    if sender_mac in clients:
        clients.remove(sender_mac)

    if not clients:
        del subscriptions[topic_filter]


def send_ack(sender_mac, text):
    esp.send_json(sender_mac, {
        "_proto": "nitbw-mqtt-lite-broker",
        "type": "ack",
        "message": text,
    })


def forward_publish(sender_mac, topic, payload):
    empfaenger = set()

    for topic_filter, clients in subscriptions.items():
        if topic_matches(topic_filter, topic):
            for client_mac in clients:
                empfaenger.add(client_mac)

    # Optional: Sender nicht an sich selbst zuruecksenden.
    if sender_mac in empfaenger:
        empfaenger.remove(sender_mac)

    if not empfaenger:
        print("Keine Empfaenger fuer Topic:", topic)
        return

    for client_mac in empfaenger:
        esp.send_json(client_mac, {
            "_proto": "nitbw-mqtt-lite-broker",
            "type": "deliver",
            "topic": topic,
            "payload": payload,
            "sender": sender_mac,
        })

    print("Weitergeleitet an {} Client(s) fuer Topic {}".format(len(empfaenger), topic))


# --- Hauptprogramm ---
while True:
    data, sender = esp.receive_json(timeout_ms=400)
    if data is None:
        time.sleep(0.02)
        continue

    if data.get("_proto") != "nitbw-mqtt-lite-broker":
        print("Ignoriere Fremdprotokoll von {}: {}".format(sender, data))
        continue

    msg_type = data.get("type")

    if msg_type == "subscribe":
        topic_filter = data.get("topic")
        if isinstance(topic_filter, str) and topic_filter:
            add_subscription(sender, topic_filter)
            print("Subscribe von {} auf {}".format(sender, topic_filter))
            send_ack(sender, "subscribed: {}".format(topic_filter))
        else:
            send_ack(sender, "ungueltiges subscribe")

    elif msg_type == "unsubscribe":
        topic_filter = data.get("topic")
        if isinstance(topic_filter, str) and topic_filter:
            remove_subscription(sender, topic_filter)
            print("Unsubscribe von {} auf {}".format(sender, topic_filter))
            send_ack(sender, "unsubscribed: {}".format(topic_filter))
        else:
            send_ack(sender, "ungueltiges unsubscribe")

    elif msg_type == "publish":
        topic = data.get("topic")
        payload = data.get("payload")
        if isinstance(topic, str) and topic:
            print("Publish von {} auf {}: {}".format(sender, topic, payload))
            forward_publish(sender, topic, payload)
        else:
            send_ack(sender, "ungueltiges publish")

    else:
        print("Unbekannter Nachrichtentyp von {}: {}".format(sender, msg_type))
        send_ack(sender, "unbekannter type")
