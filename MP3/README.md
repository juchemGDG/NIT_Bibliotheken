# NIT Bibliothek: MP3

## Beschreibung

Diese Bibliothek steuert den Mini MP3 Player MP3-TF-16P V3.0 am ESP32.
Die Kommunikation erfolgt ueber UART mit dem ueblichen DFPlayer-kompatiblen
10-Byte-Protokoll. Neben Start/Stop/Pause unterstuetzt die Bibliothek
Lautstaerke, Equalizer, Ordnerwiedergabe und Zufallsmodus.

## Features

- DFPlayer-kompatible UART-Kommunikation (9600 Baud typisch)
- Wiedergabe einzelner Tracks per globalem Titelindex
- Wiedergabe aus dem MP3-Ordner (`play_mp3`)
- Wiedergabe aus numerischen Ordnern (`play_folder`)
- Wiedergabesteuerung: `pause`, `resume`, `stop`, `next`, `previous`
- Lautstaerkeregelung 0 bis 30
- Equalizer-Modi (normal, pop, rock, jazz, classic, bass)
- Wiederholung des aktuellen Titels
- Endlosschleife ueber alle Titel
- Zufallswiedergabe
- Prioritaets-Einspieler (Advert-Funktion)
- Soft-Reset und Sleep-Befehl

## Hardware

Unterstuetztes Modul:

- MP3-TF-16P V3.0 (DFPlayer-kompatibel)

Technische Hinweise:

- Betriebsspannung Modul: typischerweise 3.2 V bis 5 V
- UART-Pegel: 3.3 V kompatibel mit ESP32
- MicroSD: FAT16/FAT32, sinnvoll mit 2 GB bis 32 GB
- Dateibenennung fuer stabile Reihenfolge: `0001.mp3`, `0002.mp3`, ...
- Lautsprecher direkt am Modul oder Audio-Ausgang auf Verstaerker

## Anschluss

Beispielverkabelung (ESP32):

```text
MP3-TF-16P         ESP32
VCC        ----->  5V (oder 3V3, je nach Modul)
GND        ----->  GND
TX         ----->  GPIO16 (RX2)
RX         ----->  GPIO17 (TX2)
SPK_1/SPK_2 -----> Lautsprecher
```

Hinweis: Manche Boards sind weniger stoeranfaellig, wenn zwischen ESP32-TX und
MP3-RX ein kleiner Serienwiderstand (z. B. 1 kOhm) eingesetzt wird.

## Installation

Datei `nitbw_mp3.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

Import in deinem Skript:

```python
from nitbw_mp3 import MP3TF16P
```

## Schnellstart

```python
from machine import Pin, UART
from time import sleep
from nitbw_mp3 import MP3TF16P

uart = UART(2, baudrate=9600, tx=Pin(17), rx=Pin(16))
player = MP3TF16P(uart)

player.set_source(MP3TF16P.DEVICE_TF)
player.set_volume(20)
player.play_mp3(1)
sleep(5)
player.stop()
```

## API-Referenz

### Konstruktor

```python
MP3TF16P(uart, ack=False)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `uart` | UART | - | Vorgefertigtes `machine.UART` Objekt |
| `ack` | bool | False | Fordert ACK-Rueckmeldungen vom Modul an |

### Methodenuebersicht

| Methode | Beschreibung |
|---|---|
| `play(track)` | Globalen Titelindex abspielen |
| `play_mp3(track)` | Titel aus MP3-Ordner abspielen |
| `play_folder(folder, track)` | Titel aus numerischem Ordner abspielen |
| `next()` / `previous()` | Vor/zurueck zum naechsten Titel |
| `pause()` / `resume()` / `stop()` | Wiedergabe steuern |
| `set_volume(value)` | Lautstaerke 0..30 setzen |
| `volume_up()` / `volume_down()` | Lautstaerke schrittweise aendern |
| `get_volume()` | Letzten lokal gesetzten Lautstaerkewert lesen |
| `set_eq(mode)` | Equalizer-Modus setzen |
| `set_source(device)` | Quelle waehlen (z. B. TF-Karte) |
| `loop_all(enable=True)` | Endlosschleife ueber alle Titel |
| `repeat_current(enable=True)` | Aktuellen Titel wiederholen |
| `loop_folder(folder)` | Endlosschleife innerhalb Ordner |
| `random_all()` | Zufallswiedergabe starten |
| `advert_play(track)` / `advert_stop()` | Prioritaets-Einspieler starten/stoppen |
| `sleep()` / `reset()` | Modul schlafen legen bzw. neu starten |

## Beispiele

Dateien im Ordner:

- `beispiel_mp3.py`
- `beispiel_mp3_ordner.py`

1. Einfacher Start eines Titels:

```python
from machine import Pin, UART
from nitbw_mp3 import MP3TF16P

uart = UART(2, baudrate=9600, tx=Pin(17), rx=Pin(16))
player = MP3TF16P(uart)
player.set_source(MP3TF16P.DEVICE_TF)
player.play_mp3(1)
```

2. Lautstaerke und EQ einstellen:

```python
player.set_volume(22)
player.set_eq(MP3TF16P.EQ_ROCK)
```

3. Ordner 01, Datei 003 spielen:

```python
player.play_folder(folder=1, track=3)
```

4. Durchsage ueber laufende Musik (Advert):

```python
player.advert_play(1)
# ... danach
player.advert_stop()
```

Fehlersuche / Hinweise:

- Keine Wiedergabe: SD-Karte auf FAT32 formatieren und Dateinamen pruefen.
- Modul reagiert nicht: RX/TX ggf. kreuzen und GND-Verbindung kontrollieren.
- Falsche Titelreihenfolge: Dateien sauber mit fuehrenden Nullen nummerieren.
- Stoerungen im Ton: stabile Spannungsversorgung und kurze Leitungen verwenden.

## Lizenz

MIT-Lizenz, siehe zentrale Datei LICENSE im Repository-Root.
