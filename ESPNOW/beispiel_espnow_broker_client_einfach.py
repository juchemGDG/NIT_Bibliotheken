"""
Beispiel fuer NIT Bibliothek: ESPNOW Broker-Client (einfach)
Zeigt: Sehr einfacher Client fuer den Mini-Broker

Eingaben:
- Subscribe:   sub: topic/filter
- Publish:     topic: message

Hardware: 1x ESP32 als Broker + 1x ESP32 als Client
"""

from nitbw_espnow import ESPNow
from nitbw_espnow_mqtt import ESPNowMQTT
import time


# --- Konfiguration ---
BROKER_MAC = "AA:BB:CC:DD:EE:FF"
START_SUBSCRIBE = "schule/chat/#"


# --- Initialisierung ---
esp = ESPNow()
mqtt = ESPNowMQTT(esp, BROKER_MAC)

print("=== ESPNOW Broker-Client (einfach) ===")
print("Eigene MAC:", esp.get_mac())
print("Broker:", mqtt.broker_mac)
print("")
print("Eingaben:")
print("- sub: topic/filter")
print("- topic: message")
print("")


# Start-Subscribe (optional) direkt anmelden
if START_SUBSCRIBE:
    mqtt.subscribe(START_SUBSCRIBE)
    print("Start-Subscribe gesendet:", START_SUBSCRIBE)
    time.sleep(0.05)


# --- Hauptprogramm ---
while True:
    # Vor jeder Eingabe kurz auf neue Nachrichten pruefen.
    mqtt.zeige_nachrichten(zeige_fremdprotokoll=True)

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

        mqtt.subscribe(topic_filter)
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

    mqtt.publish(topic, message)
    print("Publish gesendet [{}]: {}".format(topic, message))
