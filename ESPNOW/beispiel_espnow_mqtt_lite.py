"""
Beispiel fuer NIT Bibliothek: ESPNOW MQTT-light
Zeigt: Brokerloses publish/subscribe mit topic/subtopic
Hardware: 2x ESP32 mit WLAN
"""

from nitbw_espnow import ESPNow
import time


esp = ESPNow()

print("=== ESPNOW MQTT-light Beispiel ===")
print("Eigene MAC:", esp.get_mac())
print("Partner-MAC in PARTNER_MAC eintragen.")
print()

PARTNER_MAC = "AA:BB:CC:DD:EE:FF"


# Optional: Callback fuer passende Topics

def bei_topic(topic, payload, sender):
    print("Callback von {} auf {}: {}".format(sender, topic, payload))


# Einfache Subscriptions
esp.subscribe("klasse7/#", callback=bei_topic)
esp.submit("klasse7/+/status")  # submit ist ein Alias fuer subscribe


zaehler = 0
while True:
    payload = {
        "zaehler": zaehler,
        "ok": True,
    }

    # Publish an Partner
    esp.publish(
        PARTNER_MAC,
        topic="klasse7",
        subtopic="gruppe1/status",
        payload=payload,
    )

    print("Publish gesendet:", payload)

    # Eingehende Publish-Nachrichten empfangen und an Callbacks verteilen
    topic, rx_payload, sender = esp.poll_subscriptions(timeout_ms=300)
    if topic is not None:
        print("Direkt empfangen von {} auf {}: {}".format(sender, topic, rx_payload))

    zaehler += 1
    time.sleep(1)
