"""
Beispiel fuer NIT Bibliothek: MQTT
Zeigt: Einfaches Publish/Subscribe mit Broker auf dem Raspberry Pi
Hardware: ESP32 mit WLAN und MQTT-Broker (z. B. Mosquitto)
"""

import time
import network
from nitbw_mqtt import MQTTClient


# --- Initialisierung ---
SSID = "DEIN_WLAN"
PASSWORT = "DEIN_PASSWORT"
BROKER_IP = "192.168.178.20"
CLIENT_ID = b"esp32_raum1"
TOPIC_SUB = b"nit/raum1/cmd"
TOPIC_PUB = b"nit/raum1/status"


def wlan_verbinden():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Verbinde WLAN...")
        wlan.connect(SSID, PASSWORT)
        while not wlan.isconnected():
            time.sleep_ms(300)

    print("WLAN OK:", wlan.ifconfig())
    return wlan


def bei_nachricht(topic, msg):
    try:
        topic = topic.decode("utf-8")
    except Exception:
        pass

    try:
        msg = msg.decode("utf-8")
    except Exception:
        pass

    print("Empfangen [{}]: {}".format(topic, msg))


wlan_verbinden()

client = MQTTClient(
    client_id=CLIENT_ID,
    server=BROKER_IP,
    keepalive=30,
)
client.set_callback(bei_nachricht)
client.connect()
client.subscribe(TOPIC_SUB)

print("MQTT verbunden. Warte auf Nachrichten...")


# --- Hauptprogramm ---
zaehler = 0
while True:
    # Eigene Mess-/Statusdaten senden
    text = "alive {}".format(zaehler)
    client.publish(TOPIC_PUB, text, retain=False, qos=0)

    # Eingehende Nachrichten verarbeiten
    for _ in range(10):
        client.check_msg()
        time.sleep_ms(100)

    # Keepalive bei langen Schleifen bedienen
    client.keepalive_step()
    zaehler += 1
