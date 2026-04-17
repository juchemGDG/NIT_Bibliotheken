# NIT Bibliothek: ESPNOW

## Beschreibung

Diese Bibliothek vereinfacht die ESP-NOW-Kommunikation zwischen ESP32-Boards
unter MicroPython. Die native API arbeitet mit Bytes-MAC-Adressen und relativ
viel Boilerplate. `nitbw_espnow.py` glattet diese Kanten: MACs als String,
automatische Peer-Verwaltung, komfortables Senden/Empfangen von Text und JSON.

## Features

- Einfache Initialisierung mit `ESPNow()` und `init()`
- Eigene MAC-Adresse direkt als String ueber `get_mac()`
- Peer als String-MAC hinzufuegen: `add_peer("AA:BB:CC:DD:EE:FF")`
- Automatisches Peer-Management beim Senden
- `send(mac, data)` fuer `str`, `bytes`, `dict`, `list`, Zahlen und Bool
- `receive()` mit optionalem Timeout
- JSON-Komfortfunktionen: `send_json()` und `receive_json()`
- Broadcast ueber `broadcast(data)`
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

Import:

```python
from nitbw_espnow import ESPNow
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

#### Hilfsfunktionen

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `scan_peers()` | list | Liste bereits bekannter/verwendeter Peer-MACs |

## Beispiele

- `beispiel_espnow.py`: Textnachrichten zwischen zwei ESP32 senden/empfangen
- `beispiel_espnow_json.py`: Dictionaries per JSON austauschen

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

## Lizenz

MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root
sowie `ESPNOW/LICENSE`.
