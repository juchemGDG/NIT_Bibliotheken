# NIT Bibliothek: Motor

## Beschreibung

Diese Bibliothek steuert Gleichstrommotoren (DC-Motoren) ueber eine H-Bruecke am
ESP32. Hauptziel ist das L298N-Modul, wie es in vielen Roboter-Bausaetzen steckt.
Die Klasse `Motor` stellt Drehrichtung und Geschwindigkeit in Prozent ein (per PWM),
die Klasse `Fahrwerk` verbindet zwei Motoren zu einem Roboterauto mit
Differentialantrieb. Die Bedienung entspricht `ContinuousServo.drehen()` aus
`nitbw_servo`, die Richtungskonstanten `VOR` und `ZURUECK` denen aus `nitbw_stepper`.

## Features

- Geschwindigkeit in Prozent: `drehen(-100 ... 100)`, das Vorzeichen bestimmt die Richtung
- Gleiche Aufrufarten wie beim Continuous-Servo: `drehen(50)`, `drehen(-50)`, `drehen(50, ZURUECK)`
- Richtungskonstanten `VOR` und `ZURUECK` (gleiche Werte wie in `nitbw_stepper`)
- Zwei Betriebsarten: PWM am EN-Pin (L298N ohne Jumper) oder PWM direkt an IN1/IN2
  (L298N mit Jumper, L9110S, DRV8833, TB6612FNG)
- Anlaufschwelle `min_prozent`: auch kleine Werte bringen traege Getriebemotoren zum Drehen
- Einstellbare PWM-Frequenz, sanfter Start ohne Anlaufruck

Bewegungen:

- **vor / zurueck**: einfache Fahrbefehle mit Geschwindigkeit
- **stopp**: Motor anhalten (mit EN-Pin: freies Auslaufen)
- **bremsen**: aktive Kurzschlussbremse, Motor steht sofort
- **rampe**: sanftes Beschleunigen, Abbremsen und Umkehren

Status:

- **lese_geschwindigkeit**: zuletzt eingestellter Wert (-100 bis 100)
- **lese_richtung**: `VOR`, `ZURUECK` oder 0

Fahrwerk (zwei Motoren):

- **fahren(links, rechts)**: beide Raeder getrennt einstellen (Kurven)
- **vor, zurueck, links, rechts**: geradeaus fahren und auf der Stelle drehen
- **stopp, bremsen, aus**: beide Motoren gemeinsam

## Hardware

### L298N-Modul (Standard im Unterricht)

| Eigenschaft | Wert |
|---|---|
| Kanaele | 2 (Motor A an OUT1/OUT2, Motor B an OUT3/OUT4) |
| Motorspannung | 5-35 V an der Klemme 12V (VS); fuer TT-Getriebemotoren sind 7-9 V sinnvoll |
| Strom | bis 2 A je Kanal, der Kuehlkoerper wird dabei heiss |
| Logikpegel | 3.3 V reichen (HIGH ab ca. 2.3 V), direkt am ESP32 nutzbar |
| Spannungsverlust | ca. 2 V, bei hohem Strom auch mehr |

Wichtig beim L298N:

- **ENA-/ENB-Jumper**: Gesteckt liegt EN dauerhaft auf HIGH. Die Geschwindigkeit
  wird dann per PWM direkt an IN1/IN2 gesteuert: `Motor(in1, in2)` ohne `en`.
  Abgezogen wird der ENA-Pin mit dem ESP32 verbunden und die PWM dort ausgegeben:
  `Motor(in1, in2, en=...)`. Die Beispiele verwenden diese Variante.
- **Nie einen GPIO an ENA anschliessen, solange der Jumper steckt**: ENA liegt dann
  an 5 V, der GPIO-Pin kann beschaedigt werden.
- **Spannungsverlust**: Der L298N arbeitet mit bipolaren Transistoren und verliert
  etwa 2 V. Aus 6 V Akkuspannung werden am Motor nur ca. 4 V. Fuer 6-V-Getriebemotoren
  deshalb 7-9 V verwenden (z. B. 2 Li-Ion-Zellen oder 6 AA-Batterien).
- **Getrennte Versorgung**: Die Motoren nie aus dem 3.3-V- oder 5-V-Pin des ESP32
  versorgen. Der Motor-Akku kommt an die Klemmen 12V und GND des L298N.
- **Gemeinsame Masse**: GND des L298N muss mit GND des ESP32 verbunden sein, sonst
  haben die Steuersignale keinen Bezug.
- **Freilaufdioden**: Die meisten L298N-Module haben die Schutzdioden gegen
  Spannungsspitzen des Motors bereits auf der Platine.
- **5-V-Regler**: Der Bordregler (Jumper neben den Schraubklemmen) ist nur bis 12 V
  Eingangsspannung zulaessig. Bei mehr als 12 V den Jumper ziehen und die Klemme 5V
  mit 5 V versorgen. Bei gestecktem Jumper ist die Klemme 5V ein (schwach
  belastbarer) 5-V-Ausgang.

### Kompatible Treiber (Zwei-Pin-PWM-Betrieb, `en=None`)

| Treiber | Motorspannung | Strom je Kanal | Anschluss |
|---|---|---|---|
| L9110S | 2.5-12 V | ca. 0.8 A | IA/IB an `in1`/`in2` |
| DRV8833 | 2.7-10.8 V | ca. 1.5 A | AIN1/AIN2 an `in1`/`in2`, nSLEEP auf HIGH |
| TB6612FNG | 2.5-13.5 V | ca. 1.2 A | AIN1/AIN2 an `in1`/`in2`, PWMA und STBY auf HIGH (oder PWMA als `en`) |

Diese Treiber arbeiten mit MOSFETs und verlieren kaum Spannung.

### Anhalten: stopp() oder bremsen()?

| Aufruf | IN1 | IN2 | EN | Wirkung |
|---|---|---|---|---|
| `stopp()` mit EN-Pin | LOW | LOW | 0 % | Motor laeuft frei aus |
| `stopp()` ohne EN-Pin (Jumper) | LOW | LOW | HIGH (Jumper) | L298N bremst bereits ("Fast Motor Stop") |
| `bremsen()` | HIGH | HIGH | 100 % | Kurzschlussbremse, Motor steht sofort |

`bremsen()` schliesst die Motorwicklung ueber die H-Bruecke kurz. Kurzzeitig fliesst
ein hoher Strom. Die Bremse deshalb nur kurz halten (z. B. 200-500 ms) und danach
`stopp()` aufrufen.

## Anschluss

### Ein Motor am L298N (beispiel_motor.py, beispiel_motor_taster.py)

```text
L298N              ESP32
ENA        -----> GPIO 23   (ENA-Jumper abziehen!)
IN1        -----> GPIO 16
IN2        -----> GPIO 17
GND        -----> GND       (gemeinsame Masse!)

L298N              Motor / Versorgung
OUT1, OUT2 -----> Motor
12V        -----> Akku + (z. B. 7-9 V fuer TT-Getriebemotoren)
GND        -----> Akku - (und GND des ESP32)
```

### Roboterauto mit zwei Motoren (beispiel_motor_fahrwerk.py)

```text
L298N              ESP32
ENA        -----> GPIO 23   (Motor links, Jumper abziehen)
IN1        -----> GPIO 16
IN2        -----> GPIO 17
ENB        -----> GPIO 25   (Motor rechts, Jumper abziehen)
IN3        -----> GPIO 26
IN4        -----> GPIO 27
GND        -----> GND

OUT1, OUT2 -----> linker Motor
OUT3, OUT4 -----> rechter Motor
```

### Taster (beispiel_motor_taster.py)

```text
Taster A:  GPIO 4  ----[Taster]---- 3.3V
Taster B:  GPIO 13 ----[Taster]---- 3.3V
```

Die internen Pull-Down-Widerstaende werden im Beispiel aktiviert, ein externer
Widerstand ist nicht noetig.

Geeignete GPIO-Pins: alle Ausgangspins des ESP32 koennen PWM. Nicht verwenden:
GPIO 34-39 (nur Eingang) und GPIO 6-11 (Flash). Bei ESP32-Modulen mit PSRAM
(WROVER) sind GPIO 16 und 17 belegt, dann andere Pins waehlen.

## Installation

Datei `nitbw_motor.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

Anschliessend kann die Bibliothek importiert werden:

```python
from nitbw_motor import Motor, Fahrwerk, VOR, ZURUECK
```

## Schnellstart

```python
from nitbw_motor import Motor
import time

# L298N Kanal A, ENA-Jumper abgezogen
motor = Motor(in1=16, in2=17, en=23)

motor.vor(60)        # 60 % vorwaerts
time.sleep(2)
motor.zurueck(60)    # 60 % rueckwaerts
time.sleep(2)
motor.drehen(-30)    # 30 % rueckwaerts (Vorzeichen = Richtung)
time.sleep(2)
motor.stopp()        # anhalten
```

## API-Referenz

### Klasse `Motor`

#### Konstruktor

```python
Motor(in1, in2, en=None, freq=1000, min_prozent=0)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `in1` | int | - | GPIO-Pin fuer IN1 (am zweiten L298N-Kanal: IN3) |
| `in2` | int | - | GPIO-Pin fuer IN2 (am zweiten L298N-Kanal: IN4) |
| `en` | int/None | None | GPIO-Pin fuer ENA/ENB. `None` = PWM direkt an IN1/IN2 (Jumper gesteckt) |
| `freq` | int | 1000 | PWM-Frequenz in Hz |
| `min_prozent` | int/float | 0 | Anlaufschwelle: 1-100 % werden auf `min_prozent`-100 % abgebildet, 0 bleibt 0 |

#### Methoden

| Methode | Rueckgabe | Beschreibung |
|---|---|---|
| `drehen(geschwindigkeit, richtung=None)` | - | -100 bis 100 (Vorzeichen = Richtung) oder 0-100 mit `VOR`/`ZURUECK`; 0 = `stopp()` |
| `vor(geschwindigkeit=100)` | - | Vorwaerts mit 0-100 % |
| `zurueck(geschwindigkeit=100)` | - | Rueckwaerts mit 0-100 % |
| `stopp()` | - | Beide IN auf LOW, PWM 0 (mit EN-Pin: freies Auslaufen) |
| `bremsen()` | - | Beide IN auf HIGH, EN voll an: Kurzschlussbremse, nur kurz halten |
| `rampe(ziel, dauer_ms=1000, schritte=20)` | - | Sanfter Uebergang vom aktuellen Wert zum Ziel (-100 bis 100), blockierend |
| `lese_geschwindigkeit()` | int/float | Zuletzt eingestellter Wert -100 bis 100 (ohne Anlaufschwelle) |
| `lese_richtung()` | int | `VOR` (1), `ZURUECK` (-1) oder 0 bei Stillstand |
| `aus()` | - | Wie `stopp()` |
| `deinit()` | - | Anhalten, PWM freigeben, Pins fest auf LOW |

Ungueltige Werte (z. B. `drehen(120)` oder `drehen(-50, VOR)`) loesen einen
`ValueError` mit deutscher Meldung aus.

### Klasse `Fahrwerk`

#### Konstruktor

```python
Fahrwerk(links, rechts)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `links` | Motor | - | Motor-Objekt fuer das linke Rad |
| `rechts` | Motor | - | Motor-Objekt fuer das rechte Rad |

Die Motoren sind danach auch als `fahrwerk.motor_links` und `fahrwerk.motor_rechts`
erreichbar.

#### Methoden

| Methode | Beschreibung |
|---|---|
| `fahren(links, rechts)` | Beide Raeder getrennt, je -100 bis 100 |
| `vor(geschwindigkeit=100)` | Geradeaus vorwaerts |
| `zurueck(geschwindigkeit=100)` | Geradeaus rueckwaerts |
| `links(geschwindigkeit=100)` | Auf der Stelle links drehen (links rueckwaerts, rechts vorwaerts) |
| `rechts(geschwindigkeit=100)` | Auf der Stelle rechts drehen (links vorwaerts, rechts rueckwaerts) |
| `stopp()` | Beide Motoren anhalten |
| `bremsen()` | Beide Motoren aktiv bremsen (nur kurz halten) |
| `aus()` | Wie `stopp()` |

### Richtungskonstanten

| Konstante | Wert | Bedeutung |
|---|---|---|
| `VOR` | 1 | Vorwaerts |
| `ZURUECK` | -1 | Rueckwaerts |

Welche Richtung "vorwaerts" ist, haengt von der Verkabelung ab. Dreht ein Motor
falsch herum, die Motorkabel an OUT1/OUT2 tauschen oder `in1` und `in2` im
Konstruktor tauschen.

## Beispiele

- `beispiel_motor.py`: Ein Motor am L298N: vorwaerts 50 % und 100 %, Stopp, rueckwaerts, Rampe, Bremse
- `beispiel_motor_fahrwerk.py`: Roboterauto faehrt ein Quadrat, Kurve, rueckwaerts, Drehung
- `beispiel_motor_taster.py`: Taster A schaltet die Geschwindigkeit in Stufen, Taster B kehrt die Richtung um (ohne blockierende Pausen)

### Zusatzbeispiele

1. L298N mit gestecktem ENA-Jumper (PWM direkt an IN1/IN2):
```python
from nitbw_motor import Motor
import time

# ENA-Jumper bleibt gesteckt, ENA wird NICHT mit dem ESP32 verbunden
motor = Motor(in1=16, in2=17)
motor.vor(50)
time.sleep(2)
motor.stopp()
```

2. Anlaufschwelle fuer traege Getriebemotoren:
```python
from nitbw_motor import Motor

# Viele TT-Motoren laufen erst ab ca. 35 % an.
# Mit min_prozent=35 dreht der Motor schon bei drehen(5).
motor = Motor(in1=16, in2=17, en=23, min_prozent=35)
motor.vor(5)
print(motor.lese_geschwindigkeit())   # 5 (angefordert, nicht der PWM-Wert)
```

3. Sanfter Richtungswechsel mit Rampe:
```python
from nitbw_motor import Motor

motor = Motor(in1=16, in2=17, en=23)
motor.rampe(80, dauer_ms=1500)    # sanft auf 80 % vorwaerts
motor.rampe(-80, dauer_ms=3000)   # sanft ueber 0 auf 80 % rueckwaerts
motor.rampe(0, dauer_ms=1000)     # sanft anhalten
```

4. Geschwindigkeit mit einem Potentiometer einstellen:
```python
from machine import ADC, Pin
from nitbw_motor import Motor
import time

motor = Motor(in1=16, in2=17, en=23)
poti = ADC(Pin(34))
poti.atten(ADC.ATTN_11DB)

while True:
    # 0-65535 -> -100 bis 100 (Mitte = Stillstand)
    wert = poti.read_u16() * 200 // 65535 - 100
    if -10 < wert < 10:
        wert = 0          # kleiner Totbereich in der Mitte
    motor.drehen(wert)
    time.sleep_ms(50)
```

5. Hindernissen ausweichen mit Ultraschall (`nitbw_ultraschall`):
```python
from nitbw_motor import Motor, Fahrwerk
from nitbw_ultraschall import Ultraschall
import time

auto = Fahrwerk(Motor(in1=16, in2=17, en=23), Motor(in1=26, in2=27, en=25))
sensor = Ultraschall(trigger=5, echo=18)

try:
    while True:
        if sensor.ist_naeher_als(20):
            auto.bremsen()
            time.sleep_ms(200)
            auto.zurueck(50)
            time.sleep_ms(400)
            auto.rechts(50)
            time.sleep_ms(500)
        else:
            auto.vor(60)
        time.sleep_ms(50)
finally:
    auto.stopp()
```

6. Fahrzeug faehrt nicht geradeaus: Raeder einzeln abgleichen:
```python
from nitbw_motor import Motor, Fahrwerk

auto = Fahrwerk(Motor(in1=16, in2=17, en=23), Motor(in1=26, in2=27, en=25))
# Zieht das Auto nach rechts, ist der linke Motor staerker:
auto.fahren(57, 60)
```

### Fehlersuche

- **Motor dreht nicht, nur Brummen oder Pfeifen**: Die Geschwindigkeit ist zu klein,
  um die Haftreibung zu ueberwinden. `min_prozent` setzen (z. B. 30-40) oder eine
  hoehere Akkuspannung verwenden (Spannungsverlust des L298N beachten).
- **Motor dreht gar nicht**: Gemeinsame Masse (GND L298N - GND ESP32) pruefen.
  Bei `Motor(..., en=23)` muss der ENA-Jumper abgezogen sein. Ist der Akku geladen?
- **Motor laeuft immer mit voller Geschwindigkeit**: Der ENA-Jumper steckt noch,
  die PWM am EN-Pin hat dann keine Wirkung. Jumper ziehen oder `Motor(in1, in2)`
  ohne `en` verwenden (dann ENA nicht mit dem ESP32 verbinden).
- **Motor dreht falsch herum**: Motorkabel an OUT1/OUT2 tauschen oder `in1`/`in2`
  im Konstruktor tauschen.
- **Motor laeuft nach Programmabbruch (Ctrl+C) weiter**: Die PWM laeuft ohne Programm
  weiter. Wie in den Beispielen `try: ... finally: motor.aus()` verwenden oder in der
  Shell `motor.stopp()` eingeben.
- **ESP32 startet neu, sobald der Motor anlaeuft**: Die Versorgung bricht ein.
  Motoren nie ueber USB bzw. den ESP32 versorgen, eigenen Akku verwenden und GND
  verbinden. Ein Elko (100-470 uF) an der Motorversorgung hilft zusaetzlich.
- **L298N wird sehr heiss**: Der Motorstrom ist hoch (Blockieren, zu grosse Motoren).
  `bremsen()` nur kurz halten, fuer kleine Roboter einen MOSFET-Treiber (TB6612FNG,
  DRV8833) erwaegen.
- **Pfeifgeraeusch bei kleiner Geschwindigkeit**: Die PWM-Frequenz von 1000 Hz ist
  hoerbar. Mit `freq=20000` wird es leiser; der L298N schaltet dann aber weniger
  sauber und wird waermer.
- **`ValueError: Geschwindigkeit ungueltig`**: Werte nur von -100 bis 100. Wird
  `richtung` angegeben, ist nur 0-100 erlaubt (`drehen(50, ZURUECK)`, nicht `drehen(-50, ZURUECK)`).

## Lizenz

MIT-Lizenz, siehe zentrale Datei LICENSE im Repository-Root.
