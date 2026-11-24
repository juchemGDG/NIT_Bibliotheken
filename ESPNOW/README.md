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
- `send()` meldet, ob der Empfaenger den Empfang bestaetigt hat (`True`/`False`)
- Mini-Broker robust gegen fremde Funknachrichten; Clients erneuern ihre Abos
  nach einem Broker-Neustart automatisch (siehe „Robustheit im Klassenraum“)

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
| `send(mac, data)` | bool | Sendet Daten, Peer wird bei Bedarf automatisch angelegt. `True` = Empfaenger hat den Empfang auf Funkebene bestaetigt, `False` = keine Bestaetigung (bei Broadcast nicht aussagekraeftig) |
| `receive(timeout_ms=None, decode=True)` | tuple | `(msg, sender_mac)` oder `(None, None)` |
| `get_mac()` | str | Eigene MAC-Adresse als String |

#### Komfortfunktionen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `send_json(mac, data_dict)` | bool | Serialisiert Dictionary als JSON und sendet; Rueckgabe wie `send()` |
| `receive_json(timeout_ms=None, ignore_invalid=False)` | tuple | `(dict_msg, sender_mac)` oder `(None, None)`. Bei ungueltigem JSON oder JSON ohne Dictionary: `ValueError`, mit `ignore_invalid=True` stattdessen `(None, None)` |
| `on_receive(callback)` | bool | Registriert IRQ-Callback (nur falls Firmware dies unterstuetzt) |
| `broadcast(data)` | bool | Sendet an `FF:FF:FF:FF:FF:FF` (Rueckgabe nicht aussagekraeftig, Broadcasts werden nicht bestaetigt) |
| `publish(mac, topic, payload=None, subtopic=None)` | bool | Sendet MQTT-aehnliche Publish-Nachricht; Rueckgabe wie `send()` |
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
ESPNowMQTT(esp, broker_mac=None, require_connect=False, abo_erneuern_ms=None)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `esp` | ESPNow | - | Initialisiertes ESPNow-Objekt |
| `broker_mac` | str/None | `None` | MAC des Brokers fuer Client-Betrieb. Ohne `broker_mac` arbeitet das Objekt als Broker und sendet beim Erstellen einmal `broker_start` per Broadcast |
| `require_connect` | bool | `False` | Wenn `True`, akzeptiert der Broker `subscribe`/`publish`/`unsubscribe` erst nach erfolgreichem `connect` |
| `abo_erneuern_ms` | int/None | `None` | Nur Client: Wenn gesetzt (z. B. `60000`), erneuert `receive()` die gemerkten Abos automatisch nach dieser Zeit. `None` = keine automatische Erneuerung |

#### Client-Methoden

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `connect_id(client_id, timeout_ms=800, max_nachrichten=4)` | tuple | Sendet `connect` an den Broker und wartet auf `connack`; Rueckgabe `(ok, reason, client_id)`. Die ID wird fuer `erneuere_abos()` gemerkt |
| `subscribe(topic_filter)` | bool | Sendet Subscribe an den Broker und merkt sich das Abo; `True` = Broker hat Empfang bestaetigt |
| `unsubscribe(topic_filter)` | bool | Sendet Unsubscribe an den Broker und vergisst das Abo |
| `publish(topic, payload)` | bool | Sendet Publish an den Broker; `True` = Broker hat Empfang bestaetigt, `False` = keine Bestaetigung |
| `erneuere_abos()` | int | Sendet alle gemerkten Abos erneut (vorher `connect`, falls `connect_id()` benutzt wurde); Rueckgabe: Anzahl Abos |
| `resubscribe()` | int | Englischer Alias fuer `erneuere_abos()` |
| `list_abos()` | list | Gemerkte Abos dieses Clients |
| `receive(timeout_ms=80, nur_nicht_none=False, wartezeit_ms=None)` | tuple | `(msg_type, data, sender)` oder `(None, None, None)`; `msg_type` z. B. `"deliver"`, `"ack"`, `"connack"`, `"broker_start"` (eigener Broker neu gestartet, Abos bereits erneuert) oder `"other"` (fremdes Protokoll oder kein JSON, `data` ist dann Dictionary bzw. Rohtext); bei `nur_nicht_none=True` wartet die Methode intern bis eine Nachricht vorhanden ist, optional begrenzt durch `wartezeit_ms` |
| `zeige_nachrichten(max_nachrichten=8, timeout_ms=80, zeige_fremdprotokoll=False, nur_nicht_none=True, wartezeit_ms=None)` | None | Zeigt `deliver`/`ack` direkt auf der Konsole; standardmaessig wird auf die erste Nachricht gewartet, optional begrenzt durch `wartezeit_ms` |
| `zeige_json(max_nachrichten=1, timeout_ms=80, include_sender=False, include_broker_mac=False, zeige_fremdprotokoll=False, nur_nicht_none=True, wartezeit_ms=None)` | dict/list/None | Liefert standardmaessig genau eine reduzierte `deliver`-JSON mit `topic` und `payload` (optional `sender`, `broker_mac`); bei `max_nachrichten>1` eine Liste; mit `wartezeit_ms` kann das Warten auf die erste Nachricht begrenzt werden |

#### Broker-Methoden

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `handle_broker_message(timeout_ms=400)` | bool | Verarbeitet genau eine Broker-Nachricht; fremde oder kaputte Nachrichten werden ignoriert (`False`), der Broker stuerzt nicht ab |
| `broker_start()` | bool | Meldet den (Neu-)Start per Broadcast; wird im Konstruktor ohne `broker_mac` automatisch aufgerufen |
| `send_connack(sender_mac, ok, reason="ok", client_id=None)` | bool | Sendet Verbindungsantwort auf `connect` |
| `add_subscription(sender_mac, topic_filter)` | bool | Merkt Topic-Filter fuer einen Client; `True` = neues Abo, `False` = bestand schon |
| `remove_subscription(sender_mac, topic_filter)` | None | Entfernt Topic-Filter fuer einen Client |
| `forward_publish(sender_mac, topic, payload, exclude_sender=True)` | int | Leitet Publish an passende Subscriber weiter |
| `send_ack(sender_mac, text)` | bool | Sendet ACK-Text an Client |
| `list_clients()` | list | Liefert aktuelle Zuordnung von `client_id` zu Client-MACs |
| `topic_matches(topic_filter, topic)` | bool | Prueft Topic-Wildcards (`+`, `#`) |

## Beispiele

- `beispiel_espnow.py`: Textnachrichten zwischen zwei ESP32 senden/empfangen
- `beispiel_espnow_json.py`: Dictionaries per JSON austauschen
- `beispiel_espnow_mqtt_lite.py`: Brokerloses publish/subscribe mit Topics
- `beispiel_espnow_mqtt_broker.py`: ESP32 als Mini-Broker mit Topic-Verteilung
- `beispiel_espnow_mqtt_client_subscribe.py`: Minimaler Subscribe-Client fuer den Mini-Broker mit `connect_id`, Subscribe auf `10C/#` und einfacher Empfangsschleife
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
  - `#` nur am Ende, z. B. `sensoren/#`


### ESP32 als Broker (optional)

Wenn ein ESP32 als Verteiler arbeiten soll, kannst du das mit den neuen Beispielen nutzen:

- Vorher beide Dateien auf alle beteiligten Geraete kopieren:
- `nitbw_espnow.py`
- `nitbw_espnow_mqtt.py`
- `beispiel_espnow_mqtt_broker.py` auf dem Broker-ESP32 starten
- `beispiel_espnow_mqtt_client_subscribe.py` auf dem Empfaenger-ESP32 starten
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

### Robustheit im Klassenraum

Viele ESP32 in einem Raum, haeufige Neustarts: Darauf sind Broker und Clients
ab `nitbw_espnow_mqtt.py` 2.1.0 vorbereitet.

**Fremde Nachrichten werden ignoriert.**
Schickt ein anderer ESP32 einfachen Text (`esp.send(mac, "Hallo")`),
`esp.broadcast(...)`, JSON ohne Dictionary (`[1, 2]`) oder Nachrichten eines
anderen Protokolls, laeuft der Broker weiter. `handle_broker_message()` gibt
dann `False` zurueck, `receive()` auf Client-Seite liefert `("other", data, sender)`.
Ein `try`/`except` im eigenen Programm ist nicht noetig.

`ESPNow.receive_json()` wirft bei ungueltigem JSON weiterhin einen `ValueError`
(bestehende Programme verhalten sich unveraendert). Mit
`receive_json(ignore_invalid=True)` kommt stattdessen `(None, None)` zurueck.

**Abos werden nach einem Broker-Neustart erneuert.**
Der Broker speichert Abos nur im Arbeitsspeicher. Nach Reset, Stromausfall oder
neuem Hochladen sind sie weg. Deshalb:

- Clients merken sich ihre Abos (`subscribe()`/`unsubscribe()`).
- Der Broker sendet beim Start einmal `broker_start` per Broadcast.
  Clients mit dieser Broker-MAC erneuern ihre Abos dann sofort und automatisch
  (beim naechsten Aufruf von `receive()`, `zeige_json()` oder `zeige_nachrichten()`).
  `receive()` liefert dabei `("broker_start", data, sender)`; darauf reagieren
  kann das Programm, muss es aber nicht.
- Als Rueckfallebene (z. B. Client war beim Broker-Start gerade aus) erneuert
  `ESPNowMQTT(esp, BROKER_MAC, abo_erneuern_ms=60000)` die Abos jede Minute.
  Von Hand geht es mit `mqtt.erneuere_abos()`.
- Doppelte Abos erzeugen keine doppelten Nachrichten. Automatische Erneuerungen
  werden vom Broker nicht mit `ack` beantwortet und stoeren daher nicht.

Hinweis: Ein reiner Publish-Client ruft nie `receive()` auf und bemerkt den
Neustart daher nicht. Das ist nur bei `require_connect=True` im Broker relevant:
Dann muss der Publisher nach einem Broker-Neustart `connect_id()` erneut aufrufen
(oder regelmaessig `mqtt.erneuere_abos()`).

**Wurde die Nachricht empfangen?**
`send()`, `send_json()`, `publish()` usw. geben `True` zurueck, wenn der
Empfaenger den Empfang auf Funkebene bestaetigt hat, sonst `False`. So kann z. B.
eine Messstation zaehlen, wie viele Werte nicht angekommen sind. Bei Broadcast
ist der Wert nicht aussagekraeftig.

```python
fehlversuche = 0
if not mqtt.publish("10C/temperatur", 21.5):
    fehlversuche += 1
```

## Lizenz

MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root
sowie `ESPNOW/LICENSE`.
