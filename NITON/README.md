# NIT Bibliothek: NITON

## Beschreibung

Diese Bibliothek spielt Toene und Melodien ueber einen passiven Lautsprecher am ESP32.
Die Steuerung erfolgt ueber PWM mit einstellbarer Geschwindigkeit (BPM) und Legato-Anteil.
NITON nutzt deutsche Notenkonstanten und Notenlaengen, inklusive punktierter Noten und Triolen.
Dadurch eignet sie sich gut fuer Musik, Physik und algorithmisches Denken im Unterricht.

## Features

- Tonwiedergabe ueber PWM (`ton(hoehe, laenge)`)
- Pausen ueber Tonhoehe `0` oder `pause(ms)`
- Liedwiedergabe mit Listen (`spiele_lied`)
- Einstellbares Tempo in BPM (`setGeschw`)
- Einstellbares Legato/Stakkato (`setLegato`)
- Deutsche Notennamen als Konstanten (`c`, `d`, `e`, ...)
- Notenlaengen als Konstanten (`viertel`, `achtel`, ...)
- Punktierte Noten (`vip`, `acp`, ...)
- Triolen-Hilfsfunktion (`triole`) und Triolenkonstanten (`ac_t`, `vi_t`, ...)
- Rueckwaertskompatible API (`setzteGeschw` Alias)

## Hardware

Unterstuetzte Hardware:
- ESP32 mit MicroPython
- Passiver Piezo-Lautsprecher oder kleiner Summer
- PWM-faehiger GPIO-Pin

Typische Parameter:
- Lautsprecherpin: frei waehlbar (z. B. GPIO 15)
- Tempo: sinnvoll im Bereich 60 bis 180 BPM
- Legato: 0 bis 100 Prozent

Hinweise:
- Sehr hohe Lautstaerken bitte vermeiden, sonst verzerrt der Ton.
- Bei anderen Boards als ESP32 kann der PWM-Duty-Bereich abweichen.

## Anschluss

```text
Lautsprecher +  -----> GPIO 15 (PWM)
Lautsprecher -  -----> GND
```

Alternativ kann jeder andere PWM-faehige GPIO genutzt werden.

## Installation

Datei `nitbw_niton.py` auf den ESP32 kopieren (z. B. nach `/lib`).

Import:

```python
from nitbw_niton import NITon
```

## Schnellstart

```python
from nitbw_niton import NITon, c, d, e, f, g, viertel, halbe

ton = NITon(15, geschwindigkeit=80, legato=95)

ton.ton(c, viertel)
ton.ton(d, viertel)
ton.ton(e, viertel)
ton.ton(f, viertel)
ton.ton(g, halbe)
```

## API-Referenz

### Konstruktor

```python
NITon(lautsprecherpin, geschwindigkeit=80, legato=95)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `lautsprecherpin` | int | - | PWM-Pin fuer den Lautsprecher |
| `geschwindigkeit` | int | 80 | Tempo in BPM |
| `legato` | int | 95 | Anteil der klingenden Zeit in Prozent |

### Methodenuebersicht

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `ton(hoehe, laenge)` | - | Spielt einen Ton in Hz fuer eine Notenlaenge |
| `spiele_lied(noten_liste)` | - | Spielt eine Liste aus `(hoehe, laenge)` |
| `pause(laenge_ms)` | - | Wartet die gegebene Zeit in ms |
| `setGeschw(geschwindigkeit)` | - | Setzt das Tempo in BPM |
| `getGeschw()` | int | Gibt das aktuelle Tempo zurueck |
| `setLegato(legato)` | - | Setzt den Legato-Anteil |
| `getLegato()` | int | Gibt den Legato-Anteil zurueck |
| `setLPin(lautsprecherpin)` | - | Wechselt den Lautsprecherpin |
| `getLPin()` | int | Gibt den aktiven Lautsprecherpin zurueck |

## Beispiele

- `beispiel_niton.py`: Grundfunktionen, Tempo, Legato und Triolen
- `beispiel_niton_listen.py`: Lied-Listen mit mehreren Einstellungen

Beispiel 1 - Lied als Liste abspielen:

```python
from nitbw_niton import NITon, c, d, e, f, viertel

lied = [(c, viertel), (d, viertel), (e, viertel), (f, viertel)]
ton = NITon(15)
ton.spiele_lied(lied)
```

Beispiel 2 - Stakkato statt Legato:

```python
from nitbw_niton import NITon, c, viertel

ton = NITon(15)
ton.setLegato(40)
ton.ton(c, viertel)
```

Beispiel 3 - Triolen berechnen:

```python
from nitbw_niton import triole, viertel

print(triole(viertel))
```

## Lizenz

MIT-Lizenz, siehe zentrale Datei LICENSE im Repository-Root.
