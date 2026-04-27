"""
Beispiel fuer NIT Bibliothek: MQTT
Zeigt: Reconnect-Strategie bei Broker- oder WLAN-Unterbrechung
Hardware: ESP32 mit WLAN und MQTT-Broker (z. B. Mosquitto)
"""

import time
import network
from nitbw_mqtt import MQTTClient, MQTTException


# --- Initialisierung ---
SSID = "DEIN_WLAN"
PASSWORT = "DEIN_PASSWORT"
BROKER_IP = "192.168.178.20"

TOPIC_STATUS = b"nit/raum2/status"
TOPIC_CMD = b"nit/raum2/cmd"


def stelle_wlan_sicher():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("WLAN wird verbunden...")
        wlan.connect(SSID, PASSWORT)
        while not wlan.isconnected():
            time.sleep_ms(300)

    return wlan


def verbinde_mqtt(client):
    while True:
        try:
            client.connect(clean_session=False)
            client.subscribe(TOPIC_CMD)
            client.publish(TOPIC_STATUS, "online", retain=True)
            print("MQTT verbunden")
            return
        except Exception as exc:
            print("MQTT Verbindungsfehler:", exc)
            time.sleep(2)


def bei_nachricht(topic, msg):
    print("Cmd:", topic, msg)


wlan = stelle_wlan_sicher()

client = MQTTClient(
    client_id=b"esp32_raum2",
    server=BROKER_IP,
    keepalive=30,
    socket_timeout=5,
)
client.set_callback(bei_nachricht)
client.set_last_will(TOPIC_STATUS, b"offline", retain=True, qos=0)

verbinde_mqtt(client)


# --- Hauptprogramm ---
while True:
    try:
        if not wlan.isconnected():
            print("WLAN getrennt, reconnect...")
            stelle_wlan_sicher()

        client.publish(TOPIC_STATUS, "tick", retain=False, qos=0)

        # Eine Nachricht blockierend abwarten (alternativ check_msg)
        client.wait_msg()
        client.keepalive_step()

    except (OSError, MQTTException) as exc:
        print("Verbindung verloren:", exc)
        try:
            client.disconnect()
        except Exception:
            pass
        time.sleep(2)
        stelle_wlan_sicher()
        verbinde_mqtt(client)
