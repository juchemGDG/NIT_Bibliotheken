# NIT Bibliothek: Stepper

## Beschreibung

Diese Bibliothek steuert Schrittmotoren am ESP32 unter MicroPython.
Sie unterstuetzt zwei gaengige Motortypen mit je einer eigenen Klasse:

- **StepperULN**: 28BYJ-48 (unipolar, 4-Draht) am ULN2003-Treiberboard
- **StepperDir**: Bipolare Motoren wie NEMA 17 ueber STEP/DIR-Treiber (A4988, DRV8825)

Beide Klassen bieten blockierende Bewegungsbefehle (blockieren bis die Bewegung
abgeschlossen ist) sowie einen nicht-blockierenden Poll-Modus, der es erlaubt,
mehrere Motoren oder andere Aufgaben gleichzeitig im Hauptloop zu betreiben.

Die Implementierung ist eigenstaendig (keine externen Abhaengigkeiten ausser `machine`)
und bietet eine deutschsprachige API.

**Beachte:** Bei Verwendung des A4988 muss ein ELKO 100 uF parallel zu Vmot und Gnd geschaltet werden!

## Features

- Zwei getrennte Klassen fuer die gaengigsten Motortypen
- Schrittsteuerung: Schritte absolut (`schritte`), Winkel in Grad (`winkel`),
  volle Umdrehungen (`umdrehungen`)
- Einstellbare Geschwindigkeit in Schritten/Sekunde (`geschwindigkeit`)
- Richtungskonstanten: `VOR` und `ZURUECK`
- Nicht-blockierender Modus: `starte`, `ausfuehren`, `ist_fertig`, `stopp`
- Positionsverfolgung: `lese_position` (relative Schrittposition ab Start)
- `StepperULN`: Halbschritt-Betrieb fuer ruhigen Lauf und maximale Aufloesung
- `StepperDir`: Optionaler ENABLE-Pin mit `aktivieren` / `deaktivieren`

## Hardware

### StepperULN – 28BYJ-48 + ULN2003

| Modell | Typ | Spannung | Schritte/Umdr. (Halbschritt) | Haltemoment |
|---|---|---|---|---|
| 28BYJ-48 (5 V) | Unipolar, 4-Phasen | 5 V | typ. 4096 (praxisnah oft ~4076) | ~34 mNm |
| 28BYJ-48 (12 V) | Unipolar, 4-Phasen | 12 V | typ. 4096 (praxisnah oft ~4076) | ~100 mNm |

Empfohlene Geschwindigkeit: 50 – 500 Schritte/s (haengt von Last und Spannung ab).

### StepperDir – NEMA 17 + A4988 / DRV8825

| Modell | Schritte/Umdr. | Max. Strom | Hinweis |
|---|---|---|---|
| 17HS4401 | 200 | 1.7 A | Gaengigster Typ fuer 3D-Drucker / CNC |
| 17HS2408 | 200 | 0.6 A | Kleines, leichtes Modell |
| Beliebiger NEMA 17 | 200 | variabel | Vollschrittbetrieb, Microstepping per Hardware |

Microstepping wird ueber Hardware-Jumper am Treiber eingestellt.
Die Bibliothek erwartet die **effektive** Schrittzahl pro Umdrehung im Konstruktor.
Beispiel: A4988 auf 1/8-Microstepping -> `schritte_pro_umdrehung=1600`.

## Anschluss

### StepperULN (28BYJ-48 + ULN2003)

```text
ULN2003-Platine     ESP32
IN1         ------> GPIO 14
IN2         ------> GPIO 27
IN3         ------> GPIO 26
IN4         ------> GPIO 25
VCC         ------> 5 V (extern empfohlen!)
GND         ------> GND (gemeinsam mit ESP32)
```

**Wichtig**: Den ESP32 nicht direkt ueber USB mit dem Motorstrom belasten.
Bei langen Laufzeiten oder hoher Last ein externes 5-V-Netzteil verwenden
und GND verbinden.

### StepperDir (NEMA 17 + A4988)

```text
A4988 / DRV8825     ESP32
STEP        ------> GPIO 14
DIR         ------> GPIO 27
ENABLE      ------> GPIO 26 (optional, LOW = aktiv)

A4988 / DRV8825     Externe Versorgung
VMOT        ------> 12 V Netzteil (+)
GND (Power) ------> 12 V Netzteil (-)
GND (Logic) ------> GND des ESP32 (gemeinsame Masse!)
```

**Wichtig**: VMOT und GND niemals vertauschen – Treiber-IC wird sofort
zerstoert. Vor dem Einschalten den Motor anschliessen; Hotplug kann
Treiber beschaedigen. Strombegrenzungs-Trimmer am A4988 vor dem Betrieb einstellen.

## Installation

Datei `nitbw_stepper.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

Import:

```python
from nitbw_stepper import StepperULN, StepperDir, VOR, ZURUECK
```

## Schnellstart

### StepperULN (28BYJ-48)

```python
from nitbw_stepper import StepperULN, VOR, ZURUECK

motor = StepperULN(in1=14, in2=27, in3=26, in4=25)
motor.umdrehungen(1, VOR)   # Eine Umdrehung vorwaerts
motor.winkel(90, ZURUECK)   # 90 Grad zurueck
motor.aus()                 # Spulen stromlos
```

### StepperDir (NEMA 17 + A4988)

```python
from nitbw_stepper import StepperDir, VOR, ZURUECK

motor = StepperDir(step_pin=14, dir_pin=27, enable_pin=26)
motor.umdrehungen(2, VOR)   # Zwei Umdrehungen vorwaerts
motor.winkel(180, ZURUECK)  # 180 Grad zurueck
motor.deaktivieren()        # Strom sparen
```

### Nicht-blockierender Modus

```python
from nitbw_stepper import StepperULN, VOR

motor = StepperULN(in1=14, in2=27, in3=26, in4=25)
motor.starte(1024, VOR)     # Bewegung starten

while not motor.ist_fertig():
    motor.ausfuehren()      # Regelmaessig aufrufen
    # ... hier andere Aufgaben erledigen

motor.aus()
```

## API-Referenz

### Klasse `StepperULN` (28BYJ-48 + ULN2003)

#### Konstruktor

```python
StepperULN(in1, in2, in3, in4, schritte_pro_umdrehung=4096, geschwindigkeit=10)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `in1..in4` | int | - | GPIO-Pin-Nummern fuer IN1 bis IN4 des ULN2003 |
| `schritte_pro_umdrehung` | int | 4096 | Schritte pro Umdrehung (28BYJ-48 Halbschritt, praxisnah oft ~4076) |
| `geschwindigkeit` | int/float | 10 | Startgeschwindigkeit in Schritten/Sekunde |

#### Methoden

| Methode | Beschreibung |
|---|---|
| `schritte(n, richtung=VOR)` | n Schritte blockierend fahren |
| `winkel(grad, richtung=VOR)` | Winkel in Grad blockierend fahren |
| `umdrehungen(n, richtung=VOR)` | n Umdrehungen blockierend fahren |
| `starte(n, richtung=VOR)` | Nicht-blockierende Bewegung starten |
| `ausfuehren()` | Naechsten faelligen Schritt ausfuehren (im Loop aufrufen) |
| `ist_fertig()` | True wenn keine laufende Bewegung vorhanden |
| `stopp()` | Laufende Bewegung sofort abbrechen |
| `geschwindigkeit(sps)` | Geschwindigkeit in Schritten/Sekunde setzen |
| `lese_position()` | Aktuelle absolute Schrittposition abfragen |
| `aus()` | Alle Motorspulen stromlos schalten |
| `deinit()` | Wie `aus()` |

---

### Klasse `StepperDir` (NEMA 17 + A4988 / DRV8825)

#### Konstruktor

```python
StepperDir(step_pin, dir_pin, enable_pin=None, schritte_pro_umdrehung=200, geschwindigkeit=800)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `step_pin` | int | - | GPIO-Pin fuer STEP-Signal |
| `dir_pin` | int | - | GPIO-Pin fuer DIR-Signal |
| `enable_pin` | int/None | None | GPIO-Pin fuer ENABLE (optional, LOW = aktiv) |
| `schritte_pro_umdrehung` | int | 200 | Schritte pro Umdrehung (inkl. Microstepping-Faktor) |
| `geschwindigkeit` | int/float | 800 | Startgeschwindigkeit in Schritten/Sekunde |

#### Methoden

Alle Methoden aus `StepperULN` sind vorhanden, zusaetzlich:

| Methode | Beschreibung |
|---|---|
| `aktivieren()` | ENABLE-Pin auf LOW (Treiber aktiv, Motor bestromt) |
| `deaktivieren()` | ENABLE-Pin auf HIGH (Treiber inaktiv, Motor dreht frei) |
| `aus()` | STEP auf LOW, dann `deaktivieren()` |

> **Motor stottert / laeuft nicht rund?** Im **Vollschritt** hat ein NEMA 17
> eine mechanische Resonanz bei ca. **200 - 600 sps** (~1 - 3 Umdrehungen/s).
> In diesem Bereich kann der Motor rau laufen oder nur stottern. Loesung:
> - Geschwindigkeit **oberhalb** der Resonanz waehlen (z. B. 800 - 1500 sps).
> - Fuer ruhigen Langsamlauf am Treiber **Mikroschritt** aktivieren
>   (MS1/MS2/MS3) und `schritte_pro_umdrehung` entsprechend erhoehen
>   (z. B. 1/16-Schritt -> 3200).

---

### Richtungskonstanten

| Konstante | Wert | Bedeutung |
|---|---|---|
| `VOR` | 1 | Vorwaerts (Uhrzeigersinn von Motorachse betrachtet) |
| `ZURUECK` | -1 | Rueckwaerts (Gegenuhrzeigersinn) |

Die tatsaechliche Drehrichtung haengt von der Verkabelung ab. Falls der Motor
falsch herum dreht, einfach zwei der Motorleitungen (bei ULN: IN1/IN3 tauschen;
bei NEMA 17: ein Spulenpaar umpolen) oder `VOR` und `ZURUECK` in der Verwendung tauschen.

---

### Nicht-blockierender Modus (beide Klassen)

```python
motor.starte(n, richtung)  # Ziel setzen, Startzeit merken
while not motor.ist_fertig():
    motor.ausfuehren()     # Gibt True zurueck wenn Schritt ausgefuehrt
    # Weitere Aufgaben (zweiter Motor, Sensoren, ...)
motor.aus()
```

`ausfuehren()` prueft per `time.ticks_us()`, ob das Intervall seit dem letzten
Schritt abgelaufen ist, und setzt genau dann den naechsten Schritt. Es blockiert
nicht. Der Benutzer ist verantwortlich, `ausfuehren()` oft genug aufzurufen –
Verzoegerungen im Loop (z. B. durch `print` oder `time.sleep`) verspaeten den
naechsten Schritt.

## Beispiele

Hinweis fuer 28BYJ-48 am ULN2003: Im Halbschrittbetrieb sind fuer eine volle
mechanische Umdrehung typischerweise 4096 Schritte noetig (in der Praxis oft
nahe 4076 durch Getriebetoleranzen).

- [beispiel_stepper_uln.py](beispiel_stepper_uln.py): 28BYJ-48 Grundfunktionen
- [beispiel_stepper_dir.py](beispiel_stepper_dir.py): NEMA 17 + A4988 Grundfunktionen
- [beispiel_stepper_uln_erweitert.py](beispiel_stepper_uln_erweitert.py): Zwei Motoren gleichzeitig, Geschwindigkeitswechsel, stopp()
- [beispiel_stepper_dir_erweitert.py](beispiel_stepper_dir_erweitert.py): Pendelbewegung, Geschwindigkeitsrampe, Treiber-Verwaltung

### Weitere Beispiele

1. Schrittmotor als einfacher Zeiger (Messinstrument):
```python
from nitbw_stepper import StepperULN, VOR, ZURUECK

motor = StepperULN(in1=14, in2=27, in3=26, in4=25,
                   schritte_pro_umdrehung=4096)
# Auf 0° fahren (Nullpunkt)
motor.schritte(100, ZURUECK)
motor.aus()

# Zeiger auf Wert 50 % -> 90° -> 1024 Schritte (bei 4096 spr/U)
motor.winkel(90, VOR)
motor.aus()
```

2. Zwei Motoren gleichzeitig (Roboter-Antrieb):
```python
from nitbw_stepper import StepperULN, VOR

links = StepperULN(in1=14, in2=27, in3=26, in4=25,
                   schritte_pro_umdrehung=4096, geschwindigkeit=200)
rechts = StepperULN(in1=13, in2=12, in3=4, in4=2,
                    schritte_pro_umdrehung=4096, geschwindigkeit=200)

links.starte(4096, VOR)
rechts.starte(4096, VOR)

while not (links.ist_fertig() and rechts.ist_fertig()):
    links.ausfuehren()
    rechts.ausfuehren()

links.aus()
rechts.aus()
```

3. NEMA 17 mit Microstepping (1/8-Schritt per Hardware-Jumper):
```python
from nitbw_stepper import StepperDir, VOR

# A4988 auf 1/8-Schritt: MS1=HIGH, MS2=HIGH, MS3=LOW
# -> 200 Vollschritte * 8 = 1600 Mikroschritte pro Umdrehung
motor = StepperDir(step_pin=14, dir_pin=27,
                   schritte_pro_umdrehung=1600,
                   geschwindigkeit=800)
motor.umdrehungen(1, VOR)
```

4. Positionsrueckstellung nach Bewegung:
```python
from nitbw_stepper import StepperDir, VOR, ZURUECK

motor = StepperDir(step_pin=14, dir_pin=27, schritte_pro_umdrehung=200)
motor.umdrehungen(3, VOR)

# Zurueck zur Ausgangsposition
pos = motor.lese_position()
if pos > 0:
    motor.schritte(pos, ZURUECK)
elif pos < 0:
    motor.schritte(-pos, VOR)
print("Position:", motor.lese_position())  # Sollte 0 sein
```

## Fehlersuche

- **Motor dreht sich nicht / brummt nur**:
  Motorstrom pruefen. Beim 28BYJ-48 unbedingt externes 5-V-Netzteil verwenden,
  USB-Strom des ESP32 reicht nicht aus. Beim NEMA 17 den Strom-Trimmer des A4988
  korrekt einstellen (Formel: Iref = Vref / (8 * Rs), typisch Vref ~ 0.4 V fuer 1 A).

- **Motor dreht in falscher Richtung**:
  Entweder `VOR` und `ZURUECK` im Code tauschen oder beim 28BYJ-48 die
  Pinbelegung IN1/IN3 vertauschen. Beim NEMA 17 ein Spulenpaar umpolen (A1/A2 oder B1/B2).

- **Motor ueberspringt Schritte (Schrittverlust)**:
  Geschwindigkeit reduzieren. Die Geschwindigkeit ist zu hoch fuer die
  aktuelle Last oder Spannung. Beim 28BYJ-48: max. 500 sps (5 V), max. ~900 sps (12 V).
  Beim NEMA 17: haengt stark von Motorstrom und Spannung ab.

- **Motor wird sehr heiss**:
  Beim NEMA 17: Motorstrom zu hoch eingestellt. Trimmer am A4988 zurueckdrehen.
  `deaktivieren()` aufrufen, wenn der Motor still steht und kein Haltemoment
  benoetigt wird.

- **Nicht-blockierender Modus ungenaue Geschwindigkeit**:
  Andere Operationen im Loop (z. B. `print`, I2C-Kommunikation) verzoegern
  den Aufruf von `ausfuehren()`. Zeitkritische Anwendungen blockierenden Modus
  bevorzugen oder zeitintensive Operationen aus dem Schritt-Loop heraushalten.

- **`ValueError: n muss positiv sein`**:
  Negative Schrittanzahlen sind nicht erlaubt. Richtung ausschliesslich ueber
  den `richtung`-Parameter (`VOR` / `ZURUECK`) steuern.

## Lizenz

MIT-Lizenz, siehe zentrale Datei LICENSE im Repository-Root.
