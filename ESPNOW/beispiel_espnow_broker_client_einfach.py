"""
Beispiel fuer NIT Bibliothek: ESPNOW Broker-Client (einfach)
Zeigt: Sehr einfacher Client fuer den Mini-Broker

Eingaben:
- Subscribe:   sub: topic/filter
- Publish:     topic: message

Hardware: 1x ESP32 als Broker + 1x ESP32 als Client
"""

from nitbw_espnow import ESPNow
import time


# --- Konfiguration ---
BROKER_MAC = "AA:BB:CC:DD:EE:FF"
START_SUBSCRIBE = "schule/chat/#"


# --- Initialisierung ---
esp = ESPNow()

print("=== ESPNOW Broker-Client (einfach) ===")
print("Eigene MAC:", esp.get_mac())
print("Broker:", BROKER_MAC)
print("")
print("Eingaben:")
print("- sub: topic/filter")
print("- topic: message")
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
    """Holt einige Nachrichten ab und zeigt sie auf der Konsole."""
    anzahl = 0
    while anzahl < max_nachrichten:
        data, sender = esp.receive_json(timeout_ms=80)
        if data is None:
            break

        if data.get("_proto") != "nitbw-mqtt-lite-broker":
            print("Ignoriere Fremdprotokoll von {}: {}".format(sender, data))
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

        else:
            print("Unbekannter Typ vom Broker:", msg_type)

        anzahl += 1


# Start-Subscribe (optional) direkt anmelden
if START_SUBSCRIBE:
    send_subscribe(START_SUBSCRIBE)
    print("Start-Subscribe gesendet:", START_SUBSCRIBE)
    time.sleep(0.05)


# --- Hauptprogramm ---
while True:
    # Vor jeder Eingabe kurz auf neue Nachrichten pruefen.
    zeige_empfangene_nachrichten()

    eingabe = input("Eingabe (sub: topic/filter oder topic: message): ").strip()
    if not eingabe:
        continue

    if eingabe.lower() in ("q", "quit", "exit"):
        print("Beendet.")
        break

    if eingabe.lower().startswith("sub:"):
        topic_filter = eingabe[4:].strip()
        if not topic_filter:
            print("Ungueltig. Beispiel: sub: schule/chat/#")
            continue

        send_subscribe(topic_filter)
        print("Subscribe gesendet:", topic_filter)
        continue

    # Erwartetes Publish-Format: topic: message
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
