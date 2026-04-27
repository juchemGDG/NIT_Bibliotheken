# NIT Bibliothek: MQTT

## Beschreibung

Diese Bibliothek stellt einen robusten MQTT-Client fuer ESP32 mit MicroPython bereit.
Sie orientiert sich an der bekannten `umqtt.simple`-API, erweitert diese aber um
stabilere Fehlerbehandlung, klarere Typpruefungen und praktische Reconnect-Helfer.
Damit laesst sich ein MQTT-Broker auf dem Raspberry Pi im Unterricht sehr zuverlaessig nutzen.

## Features

- MQTT v3.1.1 CONNECT, PUBLISH, SUBSCRIBE, PING, DISCONNECT
- QoS 0 und QoS 1 (inklusive PUBACK-Behandlung)
- Last-Will-Unterstuetzung (`set_last_will`)
- Klare Exceptions mit verstaendlichen Meldungen (`MQTTException`)
- Typkonvertierung fuer Payloads (`str`, `bytes`, Zahlen, `dict`, `list`, `bool`)
- Nicht-blockierendes Pruefen auf Nachrichten (`check_msg`)
- Blockierendes Warten auf Nachrichten (`wait_msg`)
- Keepalive-Hilfsmethode fuer Hauptschleifen (`keepalive_step`)
- Reconnect-Methode fuer Verbindungsabbrueche (`reconnect`)
- Optional TLS/SSL ueber `ssl_context`

## Hardware

### Unterstuetzte Plattform

- ESP32 mit MicroPython
- MQTT-Broker, z. B. Mosquitto auf Raspberry Pi

### Hinweise

- WLAN muss im STA-Modus aktiv und verbunden sein.
- Standard-Port ist `1883`, mit TLS standardmaessig `8883`.
- Fuer Unterricht ist QoS 0 oft ausreichend, QoS 1 ist bei kritischen Nachrichten robuster.

## Anschluss

MQTT benoetigt keine zusaetzliche Sensor-Verkabelung. Nur WLAN und Broker:

```text
ESP32 (WLAN)  <---->  Router / Access Point  <---->  Raspberry Pi (MQTT Broker)
```

## Installation

Datei `nitbw_mqtt.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

Import:

```python
from nitbw_mqtt import MQTTClient, MQTTException
```

## Schnellstart

```python
import network
import time
from nitbw_mqtt import MQTTClient

# WLAN verbinden
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    wlan.connect("DEIN_WLAN", "DEIN_PASSWORT")
    while not wlan.isconnected():
        time.sleep_ms(300)

# MQTT
def on_msg(topic, msg):
    print("Empfangen:", topic, msg)

client = MQTTClient(client_id=b"esp32_demo", server="192.168.178.20", keepalive=30)
client.set_callback(on_msg)
client.connect()
client.subscribe(b"nit/demo/cmd")

while True:
    client.publish(b"nit/demo/status", b"alive")
    client.check_msg()
    client.keepalive_step()
    time.sleep(1)
```

## API-Referenz

### Konstruktor

```python
MQTTClient(
    client_id,
    server,
    port=0,
    user=None,
    password=None,
    keepalive=60,
    ssl=None,
    ssl_context=None,
    socket_timeout=5,
)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `client_id` | str/bytes | - | Eindeutige Client-ID |
| `server` | str | - | Broker-Adresse (IP oder DNS) |
| `port` | int | 0 | 1883 (oder 8883 bei TLS) |
| `user` | str/bytes | `None` | MQTT-Benutzername |
| `password` | str/bytes | `None` | MQTT-Passwort |
| `keepalive` | int | 60 | Keepalive in Sekunden |
| `ssl` | bool/Objekt/None | `None` | Kompatibilitaetsparameter (alt), intern Alias auf `ssl_context` |
| `ssl_context` | Objekt/None | `None` | Optionaler TLS-Kontext |
| `socket_timeout` | int/None | 5 | Timeout fuer Socket-Operationen |

### Methoden

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `set_callback(callback)` | - | Setzt Callback fuer Subscribe-Nachrichten |
| `set_last_will(topic, msg, retain=False, qos=0)` | - | Setzt Last-Will-Nachricht |
| `connect(clean_session=True)` | bool | Verbindet zum Broker, gibt Session-Flag zurueck |
| `disconnect()` | - | Trennt sauber vom Broker |
| `reconnect(clean_session=True)` | bool | Baut Verbindung neu auf |
| `is_connected()` | bool | Prueft, ob Socket gesetzt ist |
| `ping()` | - | Sendet PINGREQ |
| `publish(topic, msg, retain=False, qos=0)` | - | Veroeffentlicht Nachricht |
| `subscribe(topic, qos=0)` | - | Abonniert Topic |
| `wait_msg()` | int/None | Wartet blockierend auf ein Paket |
| `check_msg()` | int/None | Prueft nicht-blockierend auf Paket |
| `keepalive_step()` | - | Keepalive-Wartung fuer Schleifen |

## Beispiele

- `beispiel_mqtt.py`: Basis-Publish/Subscribe mit Keepalive
- `beispiel_mqtt_reconnect.py`: Wiederverbinden bei WLAN/Broker-Abbruch

1. Last-Will setzen:

```python
client.set_last_will(b"nit/raum1/status", b"offline", retain=True, qos=0)
```

2. JSON-Payload senden:

```python
client.publish(b"nit/raum1/sensor", {"temp": 22.4, "hum": 48}, qos=0)
```

3. Nicht-blockierend pollen:

```python
while True:
    client.check_msg()
    client.keepalive_step()
```

4. QoS 1 fuer wichtiges Topic:

```python
client.publish(b"nit/raum1/alarm", b"1", qos=1)
```

5. Reconnect bei Fehler:

```python
try:
    client.wait_msg()
except Exception:
    client.reconnect(clean_session=False)
```

## Lizenz

MIT-Lizenz, siehe zentrale Datei LICENSE im Repository-Root
sowie `MQTT/LICENSE`.
