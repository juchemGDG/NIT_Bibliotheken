# NIT Bibliothek: TOENE

## Beschreibung

Diese Bibliothek spielt Melodien anhand von Notenlisten mit englischer Notennotation.
Jeder Eintrag hat das Format `(notenname, daueranteil)` und kann direkt abgespielt werden.
TOENE eignet sich fuer bekannte Songs, da Noten wie `C4` oder `F#4` leicht lesbar sind.
Die Geschwindigkeit wird in BPM eingestellt und kann jederzeit angepasst werden.

## Features

- Notenwiedergabe mit String-Notation (`C4`, `G#4`, `P`)
- Vollstaendige Frequenz-Tabelle von C1 bis B7
- Pausen mit `P` als Notenname
- Liedwiedergabe aus Listen (`spiele_lied`)
- Tempo-Steuerung per BPM (`set_geschwindigkeit`)
- Stop-Funktion zum sofortigen Stummschalten (`stop`)
- Kompatibilitaetsmethoden (`tone`, `noTone`)
- Kompatibilitaetsklasse `Music` fuer bestehende Altprojekte
- Funktioniert mit passivem Lautsprecher am PWM-Pin

## Hardware

Unterstuetzte Hardware:
- ESP32 mit MicroPython
- Passiver Piezo-Lautsprecher oder kleiner Summer
- PWM-faehiger GPIO-Pin

Technische Hinweise:
- Note `P` steht fuer Pause.
- Dauerwerte sind Notenanteile, z. B. `1/4` fuer Viertelnote.
- Eine kurze Trennpause zwischen zwei Toenen ist bereits eingebaut.

## Anschluss

```text
Lautsprecher +  -----> GPIO 15 (PWM)
Lautsprecher -  -----> GND
```

Die Pinwahl ist frei, solange der GPIO PWM unterstuetzt.

## Installation

Datei `nitbw_toene.py` auf den ESP32 kopieren (z. B. nach `/lib`).

Import:

```python
from nitbw_toene import TOENE
```

## Schnellstart

```python
from machine import Pin
from nitbw_toene import TOENE

speaker = TOENE(Pin(15), geschwindigkeit=60)

lied = [
    ("C4", 1 / 4), ("D4", 1 / 4), ("E4", 1 / 4),
    ("P", 1 / 4),
    ("G4", 1 / 2),
]

speaker.spiele_lied(lied)
speaker.stop()
```

## API-Referenz

### Konstruktor

```python
TOENE(pin, geschwindigkeit=60)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `pin` | Pin | - | PWM-Pinobjekt, z. B. `Pin(15)` |
| `geschwindigkeit` | int | 60 | Tempo in BPM |

### Methodenuebersicht

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `ton(note)` | - | Spielt ein Tupel `(notenname, daueranteil)` |
| `spiele_lied(lied)` | - | Spielt eine komplette Notenliste |
| `set_geschwindigkeit(bpm)` | - | Setzt das Tempo in BPM |
| `get_geschwindigkeit()` | int | Gibt das aktuelle BPM zurueck |
| `stop()` | - | Schaltet den Lautsprecher stumm |
| `tone(note)` | - | Alias zu `ton` (Kompatibilitaet) |
| `noTone()` | - | Alias zu `stop` (Kompatibilitaet) |

## Beispiele

- `beispiel_toene.py`: Einzelnoten und kurzes Lied
- `beispiel_toene_lied.py`: Komplettes Lied (Alle meine Entchen)

Beispiel 1 - Einzelton:

```python
from machine import Pin
from nitbw_toene import TOENE

speaker = TOENE(Pin(15), geschwindigkeit=80)
speaker.ton(("A4", 1 / 4))
```

Beispiel 2 - Pause in der Melodie:

```python
lied = [("C4", 1 / 4), ("P", 1 / 4), ("C4", 1 / 4)]
speaker.spiele_lied(lied)
```

Beispiel 3 - Altcode mit Music-Klasse:

```python
from machine import Pin
from nitbw_toene import Music

alt = Music(Pin(15), 60)
alt.tone(("C4", 1 / 4))
alt.noTone()
```

## Lizenz

MIT-Lizenz, siehe zentrale Datei LICENSE im Repository-Root.
