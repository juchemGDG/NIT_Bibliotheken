"""
Beispiel fuer NIT Bibliothek: MQTT
Zeigt: BME280-Messwerte als JSON fuer Node-RED per MQTT senden
Hardware: ESP32 mit WLAN, BME280 am I2C-Bus und MQTT-Broker (z. B. Mosquitto)
"""

import time
import network
from machine import I2C, Pin
from nitbw_bme280 import BME280
from nitbw_mqtt import MQTTClient


# --- Initialisierung ---
SSID = "DEIN_WLAN"
PASSWORT = "DEIN_PASSWORT"
BROKER_IP = "192.168.178.20"
CLIENT_ID = b"deinname"
NAME = "deinname"
TOPIC_MESSWERTE = b"nit/db/messwerte"

MESSINTERVALL_SEKUNDEN = 10


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
def messwerte_aufbereiten(temperatur, feuchte):
    """Baut den JSON-Datensatz fuer die gesendeten Messwerte."""
    return {
        "name": NAME,
        "wert1": round(temperatur, 1),
        "wert2": round(feuchte, 1),
    }


wlan_verbinden()

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = BME280(i2c)

client = MQTTClient(
    client_id=CLIENT_ID,
    server=BROKER_IP,
    keepalive=30,
)
client.connect()

print("MQTT verbunden...")

# --- Hauptprogramm ---
while True:
    temperatur, _druck, feuchte = sensor.read_all()
    payload = messwerte_aufbereiten(temperatur, feuchte)
    client.publish(TOPIC_MESSWERTE, payload, retain=False, qos=0)
    print("Messwerte gesendet:", payload)

    client.keepalive_step()
    time.sleep(max(0, MESSINTERVALL_SEKUNDEN - 1))