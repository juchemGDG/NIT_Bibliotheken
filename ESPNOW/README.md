# NIT Bibliothek: ESPNOW

## Beschreibung

Diese Bibliothek vereinfacht die ESP-NOW-Kommunikation zwischen ESP32-Boards
unter MicroPython. Die native API arbeitet mit Bytes-MAC-Adressen und relativ
viel Boilerplate. `nitbw_espnow.py` glattet diese Kanten: MACs als String,
automatische Peer-Verwaltung, komfortables Senden/Empfangen von Text und JSON.

Fuer den Einsatz als Mini-Broker (Broker + Broker-Clients) gibt es zusaetzlich
die Datei `nitbw_espnow_mqtt.py`. Diese kapselt die Broker-spezifischen
Nachrichtentypen (`connect`, `connack`, `subscribe`, `publish`, `ack`, `deliver`) und vereinfacht
dadurch den Beispielcode deutlich.

## Features

- Einfache Initialisierung mit `ESPNow()` und `init()`
- Eigene MAC-Adresse direkt als String ueber `get_mac()`
- Peer als String-MAC hinzufuegen: `add_peer("AA:BB:CC:DD:EE:FF")`
- Automatisches Peer-Management beim Senden
- `send(mac, data)` fuer `str`, `bytes`, `dict`, `list`, Zahlen und Bool
- `receive()` mit optionalem Timeout
- JSON-Komfortfunktionen: `send_json()` und `receive_json()`
- Broadcast ueber `broadcast(data)`
- MQTT-aehnliches, brokerloses Pub/Sub: `publish()`, `subscribe()`, `submit()`
- Topics und Untertopics per `topic/subtopic`
- Optionaler Callback-Empfang mit `on_receive(callback)` (firmware-abhaengig)
- Hilfsfunktion `scan_peers()` fuer bereits bekannte/verwendete Peers
- Sprechende Fehlermeldungen bei MAC- oder Sendeproblemen

## Hardware

### Unterstuetzte Plattform

- ESP32 mit MicroPython und ESP-NOW-Unterstuetzung

### Hinweise

- ESP-NOW benoetigt aktives WLAN-Interface im STA-Modus, aber keine WLAN-Verbindung.
- Die Bibliothek setzt diesen Zustand automatisch.
- Beide ESP32 muessen sich auf dem gleichen WLAN-Kanal befinden.

## Anschluss

ESP-NOW ist Funkkommunikation, es ist keine direkte Kabelverbindung zwischen
zwei ESP32 erforderlich.

```text
ESP32 #1                  ESP32 #2
USB / 5V Versorgung       USB / 5V Versorgung
GND (optional gemeinsam)  GND (optional gemeinsam)

Kommunikation: drahtlos per 2.4 GHz (ESP-NOW)
```

## Installation

Datei `nitbw_espnow.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

Wenn du die Broker-Beispiele nutzt, muss zusaetzlich
`nitbw_espnow_mqtt.py` auf den ESP32 kopiert werden.

Import:

```python
from nitbw_espnow import ESPNow
```

Import fuer Broker-Beispiele:

```python
from nitbw_espnow_mqtt import ESPNowMQTT
```

## Schnellstart

```python
from nitbw_espnow import ESPNow
import time

esp = ESPNow()
print("Eigene MAC:", esp.get_mac())

partner = "AA:BB:CC:DD:EE:FF"

while True:
    esp.send(partner, "Hallo")

    msg, sender = esp.receive(timeout_ms=200)
    if msg is not None:
        print("Empfangen von {}: {}".format(sender, msg))

    time.sleep(1)
```

## API-Referenz

### Konstruktor

```python
ESPNow()
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| - | - | - | Erstellt Instanz und initialisiert WLAN+ESP-NOW |

### Methoden

#### Grundfunktionen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `init()` | bool | Initialisiert WLAN (STA) und ESP-NOW erneut |
| `add_peer(mac)` | bool | Fuegt Peer hinzu (`True` neu, `False` bereits bekannt) |
| `send(mac, data)` | bool | Sendet Daten, Peer wird bei Bedarf automatisch angelegt |
| `receive(timeout_ms=None, decode=True)` | tuple | `(msg, sender_mac)` oder `(None, None)` |
| `get_mac()` | str | Eigene MAC-Adresse als String |

#### Komfortfunktionen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `send_json(mac, data_dict)` | bool | Serialisiert Dictionary als JSON und sendet |
| `receive_json(timeout_ms=None)` | tuple | `(dict_msg, sender_mac)` oder `(None, None)` |
| `on_receive(callback)` | bool | Registriert IRQ-Callback (nur falls Firmware dies unterstuetzt) |
| `broadcast(data)` | bool | Sendet an `FF:FF:FF:FF:FF:FF` |
| `publish(mac, topic, payload=None, subtopic=None)` | bool | Sendet MQTT-aehnliche Publish-Nachricht |
| `broadcast_publish(topic, payload=None, subtopic=None)` | bool | Sendet Publish als Broadcast |
| `subscribe(topic, callback=None, subtopic=None)` | str | Abonniert Topic/Filter, optional mit Callback |
| `submit(topic, callback=None, subtopic=None)` | str | Alias fuer `subscribe()` |
| `unsubscribe(topic, callback=None, subtopic=None)` | bool | Entfernt Abo/Callback |
| `receive_publish(timeout_ms=None)` | tuple | `(topic, payload, sender_mac)` oder `(None, None, None)` |
| `poll_subscriptions(timeout_ms=0)` | tuple | Empfaengt und verteilt an passende Subscriptions |
| `list_subscriptions()` | list | Liste aller Topic-Filter |

#### Hilfsfunktionen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `scan_peers()` | list | Liste bereits bekannter/verwendeter Peer-MACs |

### API fuer Mini-Broker-Helfer (`ESPNowMQTT`)

```python
ESPNowMQTT(esp, broker_mac=None, require_connect=False)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `esp` | ESPNow | - | Initialisiertes ESPNow-Objekt |
| `broker_mac` | str/None | `None` | MAC des Brokers fuer Client-Betrieb |
| `require_connect` | bool | `False` | Wenn `True`, akzeptiert der Broker `subscribe`/`publish`/`unsubscribe` erst nach erfolgreichem `connect` |

#### Client-Methoden

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `connect_id(client_id, timeout_ms=800, max_nachrichten=4)` | tuple | Sendet `connect` an den Broker und wartet auf `connack`; Rueckgabe `(ok, reason, client_id)` |
| `subscribe(topic_filter)` | bool | Sendet Subscribe an den Broker |
| `unsubscribe(topic_filter)` | bool | Sendet Unsubscribe an den Broker |
| `publish(topic, payload)` | bool | Sendet Publish an den Broker |
| `receive(timeout_ms=80, nur_nicht_none=False, wartezeit_ms=None)` | tuple | `(msg_type, data, sender)` oder `(None, None, None)`; bei `nur_nicht_none=True` wartet die Methode intern bis eine Nachricht vorhanden ist, optional begrenzt durch `wartezeit_ms` |
| `zeige_nachrichten(max_nachrichten=8, timeout_ms=80, zeige_fremdprotokoll=False, nur_nicht_none=True, wartezeit_ms=None)` | None | Zeigt `deliver`/`ack` direkt auf der Konsole; standardmaessig wird auf die erste Nachricht gewartet, optional begrenzt durch `wartezeit_ms` |
| `zeige_json(max_nachrichten=1, timeout_ms=80, include_sender=False, include_broker_mac=False, zeige_fremdprotokoll=False, nur_nicht_none=True, wartezeit_ms=None)` | dict/list/None | Liefert standardmaessig genau eine reduzierte `deliver`-JSON mit `topic` und `payload` (optional `sender`, `broker_mac`); bei `max_nachrichten>1` eine Liste; mit `wartezeit_ms` kann das Warten auf die erste Nachricht begrenzt werden |

#### Broker-Methoden

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `handle_broker_message(timeout_ms=400)` | bool | Verarbeitet genau eine Broker-Nachricht |
| `send_connack(sender_mac, ok, reason="ok", client_id=None)` | None | Sendet Verbindungsantwort auf `connect` |
| `add_subscription(sender_mac, topic_filter)` | None | Merkt Topic-Filter fuer einen Client |
| `remove_subscription(sender_mac, topic_filter)` | None | Entfernt Topic-Filter fuer einen Client |
| `forward_publish(sender_mac, topic, payload, exclude_sender=True)` | int | Leitet Publish an passende Subscriber weiter |
| `send_ack(sender_mac, text)` | None | Sendet ACK-Text an Client |
| `list_clients()` | list | Liefert aktuelle Zuordnung von `client_id` zu Client-MACs |
| `topic_matches(topic_filter, topic)` | bool | Prueft Topic-Wildcards (`+`, `#`) |

## Beispiele

- `beispiel_espnow.py`: Textnachrichten zwischen zwei ESP32 senden/empfangen
- `beispiel_espnow_json.py`: Dictionaries per JSON austauschen
- `beispiel_espnow_mqtt_lite.py`: Brokerloses publish/subscribe mit Topics
- `beispiel_espnow_broker.py`: ESP32 als Mini-Broker mit Topic-Verteilung
- `beispiel_espnow_mqtt_client_subscirbe.py`: Minimaler Subscribe-Client fuer den Mini-Broker mit `connect_id`, Subscribe auf `10C/#` und einfacher Empfangsschleife
- `beispiel_espnow_mqtt_client_publish.py`: Minimaler Publish-Client fuer den Mini-Broker mit `connect_id` und periodischem Senden auf `10C/zaehler`


### Zusatzbeispiele

1. Broadcast an alle:

```python
from nitbw_espnow import ESPNow

esp = ESPNow()
esp.broadcast("Hallo an alle ESP32 in Reichweite")
```

2. MAC-Adressen im Unterricht verteilen:

```python
from nitbw_espnow import ESPNow

esp = ESPNow()
print("Bitte diese MAC weitergeben:", esp.get_mac())
```

3. Callback-Empfang (falls Firmware `irq` unterstuetzt):

```python
from nitbw_espnow import ESPNow

esp = ESPNow()

def bei_nachricht(msg, sender):
    print("Von {}: {}".format(sender, msg))

esp.on_receive(bei_nachricht)
```

4. Bekannte Peers anzeigen:

```python
from nitbw_espnow import ESPNow

esp = ESPNow()
esp.send("AA:BB:CC:DD:EE:FF", "Test")
print("Bekannte Peers:", esp.scan_peers())
```

5. MQTT-light: publish + subscribe (ohne Broker):

```python
from nitbw_espnow import ESPNow

esp = ESPNow()
partner = "AA:BB:CC:DD:EE:FF"

# Topic-Filter abonnieren
esp.subscribe("sensoren/+/temperatur")

# Nachricht senden
esp.publish(
    partner,
    topic="sensoren",
    subtopic="raum1/temperatur",
    payload={"wert": 22.4, "einheit": "C"}
)

# Nachricht empfangen (aktiv pollen)
topic, payload, sender = esp.poll_subscriptions(timeout_ms=300)
if topic is not None:
    print("Von {} auf {}: {}".format(sender, topic, payload))
```

### MQTT-light Hinweise

- Es gibt keinen Broker: Nachrichten werden direkt an einen Peer oder Broadcast gesendet.
- Keine Benutzerverwaltung oder Authentifizierung eingebaut.
- Topic-Wildcards in `subscribe()`:
- `+` fuer genau eine Ebene, z. B. `sensoren/+/temperatur`


### ESP32 als Broker (optional)

Wenn ein ESP32 als Verteiler arbeiten soll, kannst du das mit den neuen Beispielen nutzen:

- Vorher beide Dateien auf alle beteiligten Geraete kopieren:
- `nitbw_espnow.py`
- `nitbw_espnow_mqtt.py`
- `beispiel_espnow_broker.py` auf dem Broker-ESP32 starten
- `beispiel_espnow_mqtt_client_subscirbe.py` auf dem Empfaenger-ESP32 starten
- `beispiel_espnow_mqtt_client_publish.py` auf dem Sender-ESP32 starten

Hinweis: Beide Minimalbeispiele nutzen optional `connect_id`.
Wenn im Broker `require_connect = True` gesetzt ist, muessen die Clients sich zuerst erfolgreich verbinden.

Fuer den schnellen Unterrichtseinsatz ist das bewusst einfach gehalten:
Der Publisher sendet periodisch auf `10C/zaehler`, der Subscriber abonniert `10C/#` und zeigt eingehende Nutzdaten an.

### Mini-Broker Connect-ID (optional)

- Mit `connect_id(client_id)` kann ein Client sich zunaechst beim Broker anmelden.
- Der Broker beantwortet dies mit `connack` (`ok`/`reason`).
- Mit `require_connect=True` im Broker werden `subscribe`/`publish`/`unsubscribe` erst nach erfolgreichem `connect` angenommen.
- Ohne `require_connect` bleibt das bisherige Verhalten unveraendert.
- `#` nur am Ende, z. B. `sensoren/#`

## Lizenz

MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root
sowie `ESPNOW/LICENSE`.
