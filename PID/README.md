# NIT Bibliothek: PID

## Beschreibung
Die Bibliothek `nitbw_pid.py` stellt die Regler aus ReglerLab fuer den ESP32 mit MicroPython bereit: P-, I-, D-, PI-, PD-, PID- und Zweipunktregler mit denselben Bezeichnungen und Parametern wie im Simulator. Ein Regler bekommt Sollwert und Istwert und liefert die Stellgroesse; er greift selbst nicht auf Hardware zu. Damit laeuft derselbe Regler mit jedem Sensor und jedem Aktor. Die Rechenvorschrift entspricht dem Code, den der Codegenerator von ReglerLab erzeugt.

## Features
- Sieben Regler wie in ReglerLab: `PRegler`, `IRegler`, `DRegler`, `PIRegler`, `PDRegler`, `PIDRegler`, `Zweipunktregler`
- Gleiche Parameter und Vorgabewerte wie die Reglerbloecke in ReglerLab (K_PR, T_N, T_V, K_IR, K_DR, X_sd, y_min, y_max)
- Stellgroessenbegrenzung (`ymin`, `ymax`) mit Anti-Windup fuer alle Regler mit I-Anteil
- D-Anteil als verzoegertes Glied (T_V/10), damit Messrauschen und Spruenge keine Nadeln erzeugen
- Feste Abtastzeit (`ts`) oder automatisch gemessene Zeit zwischen den Aufrufen
- Klasse `Takt` haelt die Abtastzeit der Hauptschleife genau ein
- Parameter waehrend des Betriebs aendern: als Attribut (`regler.kpr = 3`) oder per Name (`regler.setzen("KPR", 3)`)
- P-, I- und D-Anteil der letzten Berechnung einzeln abrufbar (`p_anteil`, `i_anteil`, `d_anteil`)
- Parameter aus einer ReglerLab-Datei (`.rlab`) uebernehmen: `aus_rlab()`
- Passt zur Live-Verbindung von ReglerLab (Messwertzeilen `@t=... w=... x=... y=...`, Befehl `@set KPR=2.5`)
- Reine Berechnung, keine Hardware noetig: Regler lassen sich auch an simulierten Strecken ausprobieren

## Hardware
- MCU: ESP32 mit MicroPython. Die Bibliothek nutzt nur `time` und `json`; ReglerLab unterstuetzt ausserdem ESP32-C3, ESP32-S3 und Raspberry Pi Pico 2 W (auf diesen Boards nicht getestet).
- Die Bibliothek selbst braucht keine Hardware. Sensor und Aktor waehlt man selbst.
- Fuer die Temperaturbeispiele: DS18B20 (Bibliothek `nitbw_ds18b20`), MOSFET-Modul (PWM) oder Relais-Modul (Zweipunkt) mit Heizelement
- Speicher: Der Import aus der `.py`-Datei belegt etwa 20 kB RAM (Messung mit MicroPython 1.29, auf dem ESP32 kann der Wert abweichen)

## Anschluss
Die Bibliothek hat keinen Anschluss. Verkabelung der Temperaturbeispiele (ESP32):

```text
DS18B20              ESP32
VDD             ->   3V3
GND             ->   GND
DQ (Daten)      ->   GPIO4   (mit 4,7 kOhm Pull-up nach 3V3)

MOSFET-Modul         ESP32          (beispiel_pid_temperatur.py)
SIG             ->   GPIO25
GND             ->   GND

Relais-Modul         ESP32          (beispiel_pid_zweipunkt.py)
IN              ->   GPIO26
GND             ->   GND
```

## Installation
- Datei `nitbw_pid.py` auf den ESP32 kopieren (Root oder `lib/`).
- Import im Skript:

```python
from nitbw_pid import PIDRegler, Takt
```

## Schnellstart
PI-Regler an einer simulierten PT1-Strecke (ohne weitere Hardware):

```python
from nitbw_pid import PIRegler, Takt
from math import exp

TS = 0.05                          # Abtastzeit in s
W = 2.0                            # Sollwert
regler = PIRegler(kpr=2.0, tn=1.5, ts=TS)
takt = Takt(TS)

x = 0.0                            # Istwert der simulierten Strecke
while takt.zeit() < 10:
    y = regler.berechnen(W, x)     # Stellgroesse
    print("w:", W, "x:", round(x, 3), "y:", round(y, 3))
    x = x + (1.5 * y - x) * (1 - exp(-TS / 1.0))   # PT1: K_P = 1.5, T = 1 s
    takt.warten()
```

## API-Referenz

### Zuordnung zu ReglerLab

| ReglerLab-Block | Klasse | Parameter (Vorgabewert wie in ReglerLab) |
|---|---|---|
| P-Regler | `PRegler` | `kpr=1.0` |
| I-Regler | `IRegler` | `kir=1.0` |
| D-Regler | `DRegler` | `kdr=0.5` |
| PI-Regler | `PIRegler` | `kpr=1.0`, `tn=1.0` |
| PD-Regler | `PDRegler` | `kpr=1.0`, `tv=0.2` |
| PID-Regler | `PIDRegler` | `kpr=1.0`, `tn=1.0`, `tv=0.2` |
| Zweipunktregler | `Zweipunktregler` | `ymax=1.0`, `ymin=0.0`, `xsd=0.2` |

Formelzeichen: `kpr` = K_PR, `kir` = K_IR, `kdr` = K_DR, `tn` = T_N, `tv` = T_V, `xsd` = X_sd.

### Konstruktoren

| Klasse | Aufruf |
|---|---|
| `PRegler` | `PRegler(kpr=1.0, ymin=None, ymax=None, ts=None)` |
| `IRegler` | `IRegler(kir=1.0, ymin=None, ymax=None, anti_windup=True, ts=None)` |
| `DRegler` | `DRegler(kdr=0.5, ymin=None, ymax=None, ts=None)` |
| `PIRegler` | `PIRegler(kpr=1.0, tn=1.0, ymin=None, ymax=None, anti_windup=True, ts=None)` |
| `PDRegler` | `PDRegler(kpr=1.0, tv=0.2, ymin=None, ymax=None, ts=None)` |
| `PIDRegler` | `PIDRegler(kpr=1.0, tn=1.0, tv=0.2, ymin=None, ymax=None, anti_windup=True, ts=None)` |
| `Zweipunktregler` | `Zweipunktregler(ymax=1.0, ymin=0.0, xsd=0.2)` |

| Parameter | Bedeutung |
|---|---|
| `ymin`, `ymax` | Grenzen der Stellgroesse (`None`: keine Begrenzung; entspricht "Stellgroesse begrenzen" in ReglerLab) |
| `anti_windup` | I-Anteil anhalten, solange die Grenze erreicht ist und e weiter hinausdrueckt |
| `ts` | feste Abtastzeit in s (empfohlen, zusammen mit `Takt`); `None`: Zeit zwischen den Aufrufen wird gemessen |
| `tn` | Nachstellzeit in s, muss groesser als 0 sein |
| `tv` | Vorhaltezeit in s, `0` schaltet den D-Anteil ab |

### Rechenvorschrift

| Regler | Stellgroesse |
|---|---|
| P | y = K_PR * e |
| I | y = K_IR * Integral(e dt) |
| D | y = K_DR * de/dt |
| PI | y = K_PR * (e + 1/T_N * Integral(e dt)) |
| PD | y = K_PR * (e + T_V * de/dt) |
| PID | y = K_PR * (e + 1/T_N * Integral(e dt) + T_V * de/dt) |
| Zweipunkt | y_max bei e > X_sd/2, y_min bei e < -X_sd/2, dazwischen bleibt der Zustand |

Dabei ist e = w - x. Das Integral wird nach der Rechteckregel aufsummiert. Die Ableitung wird als DT1-Glied mit der Verzoegerung T_V/10 (mindestens eine Abtastzeit) gerechnet, beim D-Regler mit 0,05 s. Beim ersten Aufruf startet der D-Anteil ohne Sprung.

### Methoden aller Regler

| Methode | Beschreibung |
|---|---|
| `berechnen(soll, ist)` | Stellgroesse aus Sollwert und Istwert (e = soll - ist) |
| `berechnen_e(e)` | Stellgroesse direkt aus der Regeldifferenz |
| `reset()` | Integral, D-Filter, Schaltzustand und Zeitmessung zuruecksetzen |
| `setzen(name, wert)` | Parameter per Name aendern: `KPR`, `TN`, `TV`, `KIR`, `KDR`, `XSD`, `YMIN`, `YMAX`, `AW` (Gross-/Kleinschreibung egal). `TD` wird angenommen und ignoriert. |
| `parameter()` | aktuelle Parameter als Dictionary |
| `print(regler)` | Regler mit Parametern als Text |

### Attribute

| Attribut | Bedeutung |
|---|---|
| `e` | letzte Regeldifferenz |
| `y` | letzte Stellgroesse (nach der Begrenzung) |
| `y_roh` | letzte Stellgroesse vor der Begrenzung |
| `p_anteil`, `i_anteil`, `d_anteil` | Anteile der letzten Berechnung (vor der Begrenzung) |
| `an` | Schaltzustand des Zweipunktreglers (`True` = y_max) |
| `kpr`, `tn`, `tv`, ... | Reglerparameter, koennen direkt geaendert werden |

### Takt

| Aufruf | Beschreibung |
|---|---|
| `Takt(ts)` | Abtastzeit `ts` in s |
| `zeit()` | Zeit seit dem Start in s |
| `warten()` | wartet bis zum naechsten Takt |
| `start()` | Zeitmessung neu beginnen |
| `zu_langsam` | `True`, wenn die Berechnung laenger als `ts` gedauert hat |

### Parameter aus ReglerLab

| Funktion | Beschreibung |
|---|---|
| `aus_rlab(pfad, name=None, ts=None)` | Regler aus einer `.rlab`-Datei auf dem ESP32. `name` = Bezeichnung oder Kennung des Blocks; entfaellt, wenn die Datei genau einen Regler enthaelt. |
| `aus_block(block, ts=None)` | Regler aus einem Block-Dictionary (`{"type": "pidR", "params": {...}}`) |

## Beispiele
Dateien:
- `beispiel_pid.py`: PI-Regler an simulierter PT1-Strecke, Ausgabe fuer den Thonny-Plotter
- `beispiel_pid_vergleich.py`: P, PI, PD und PID an derselben PT2-Strecke, Kennwerte im Vergleich
- `beispiel_pid_zweipunkt.py`: Temperaturregelung mit Hysterese und Relais (DS18B20)
- `beispiel_pid_temperatur.py`: Temperaturregelung mit PID-Regler und PWM (DS18B20, MOSFET)
- `beispiel_pid_reglerlab.py`: Messwerte an ReglerLab senden, Parameter per `@set` aendern, `.rlab` einlesen

Snippets:

```python
# Begrenzung und Anti-Windup: Stellgroesse nur zwischen 0 und 1
from nitbw_pid import PIDRegler
regler = PIDRegler(kpr=0.15, tn=60, tv=5, ymin=0, ymax=1, anti_windup=True, ts=1.0)
y = regler.berechnen(40.0, 23.5)       # Soll 40, Ist 23,5
```

```python
# P-, I- und D-Anteil einzeln ansehen
y = regler.berechnen(40.0, 23.5)
print(regler.p_anteil, regler.i_anteil, regler.d_anteil)
```

```python
# Parameter waehrend des Betriebs aendern
regler.kpr = 0.3                       # direkt als Attribut
regler.setzen("TN", 30)                # oder per Name wie in ReglerLab
print(regler)                          # PID-Regler(kpr=0.3, tn=30.0, ...)
```

```python
# Zweipunktregler mit Hysterese
from nitbw_pid import Zweipunktregler
regler = Zweipunktregler(ymax=1, ymin=0, xsd=1.0)
if regler.berechnen(40.0, temperatur) > 0.5:
    relais.value(1)
else:
    relais.value(0)
```

```python
# Parameter aus einer ReglerLab-Datei uebernehmen (Datei liegt auf dem ESP32)
from nitbw_pid import aus_rlab
regler = aus_rlab("heizung.rlab", name="Regler", ts=1.0)
```

```python
# Regler mit echtem Sensor: Istwert am ADC, Stellgroesse per PWM
from machine import Pin, ADC, PWM
from nitbw_pid import PIRegler, Takt

adc = ADC(Pin(34))
adc.atten(ADC.ATTN_11DB)
pwm = PWM(Pin(25), freq=1000)
regler = PIRegler(kpr=1.0, tn=2.0, ymin=0, ymax=1, ts=0.05)
takt = Takt(0.05)
while True:
    x = adc.read_uv() / 1000000        # Istwert in Volt
    y = regler.berechnen(1.5, x)       # Sollwert 1,5 V
    pwm.duty_u16(int(y * 65535))
    takt.warten()
```

## Fehlersuche / Hinweise
- **Regler schwingt:** K_PR zu gross oder T_N zu klein. Erst nur P-Anteil einstellen, dann T_N, zuletzt T_V.
- **Bleibende Regeldifferenz:** P-, PD- und D-Regler koennen sie nicht beseitigen, ein I-Anteil (PI, PID) schon.
- **Abtastzeit:** `ts` beim Regler und bei `Takt` gleich waehlen. Mit `ts=None` wird die Zeit gemessen, beim ersten Aufruf ist sie 0.
- **`zu_langsam` ist True:** Sensor oder `print` brauchen laenger als `ts`. Abtastzeit vergroessern. Der DS18B20 braucht etwa 0,75 s pro Messung, also `ts` mindestens 1 s.
- **Integral laeuft weg:** Grenzen `ymin`/`ymax` setzen und `anti_windup=True` lassen.
- **D-Anteil rauscht:** `tv` verkleinern oder den Istwert vorher mitteln.
- **Zweipunktregler schaltet zu oft:** Schaltdifferenz `xsd` vergroessern.
- **`ValueError` bei `tn`:** Die Nachstellzeit muss groesser als 0 sein.
- **`aus_rlab()` meldet `MemoryError`:** Grosse `.rlab`-Dateien (mit Programmen im Mikrocontroller-Block) passen nicht in den Speicher. Dann den Block-Ausschnitt in `aus_block()` uebergeben oder die Werte von Hand eintragen.
- **Simulation und Hardware im Vergleich:** Der Simulator startet den D-Filter bei 0, der erzeugte Code und diese Bibliothek beim ersten Wert von e. Nur in den ersten Sekunden mit D-Anteil sehen die Kurven deshalb etwas anders aus.
- **Sicherer Zustand:** Beim Beenden mit Strg + C die Stellgroesse auf einen ungefaehrlichen Wert setzen (siehe `beispiel_pid_temperatur.py`).

## Lizenz
MIT-Lizenz, siehe zentrale Datei LICENSE im Repository-Root (Kopie im Ordner).
