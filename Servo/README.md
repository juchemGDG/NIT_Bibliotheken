# NIT Bibliothek: Servo

## Beschreibung

Diese Bibliothek steuert Standard-Servos und Continuous-Rotation-Servos am ESP32
ueber PWM-Signale. Standard-Servos werden ueber Winkelangaben (0-180°) angesteuert,
Continuous-Servos ueber Geschwindigkeit in Prozent (0-100 %) und Drehrichtung.

Die Implementierung ist eigenstaendig (ohne externe Abhaengigkeiten ausser `machine`)
und bietet fuer beide Servo-Typen eine intuitive, deutschsprachige API.

## Features

- Zwei getrennte Klassen fuer Standard- und Continuous-Servos
- Standard-Servo: Winkelsteuerung von 0° bis 180°
- Continuous-Servo: Geschwindigkeit in Prozent (0-100 %) mit Drehrichtung (CW/CCW)
- Konfigurierbare Pulsbreiten (Anpassung an verschiedene Servo-Modelle)
- Konfigurierbare Winkelbereiche (z. B. 0-270° fuer spezielle Servos)

Unterstuetzte Funktionsgruppen:

- **Standard-Servo**: `winkel`, `mitte`, `minimum`, `maximum`, `lese_winkel`
- **Continuous-Servo**: `drehen`, `stopp`
- **Gemeinsam**: `puls` (Direktzugriff), `aus` (PWM abschalten), `deinit` (Pin freigeben)

## Hardware

### Standard-Servos

- **SG90**: Kleiner Micro-Servo, 180°, ~1.2 kg/cm, 4.8-6 V
- **SG92R**: Verbesserte Version des SG90, metallgetriebe
- **MG90S**: Micro-Servo mit Metallgetriebe
- **MG996R**: Grosser Servo, ~10 kg/cm, fuer hoehere Lasten

### Continuous-Rotation-Servos

- **FS90R**: Micro-360°-Servo (basierend auf SG90)
- **SM-S4303R**: Standard-360°-Servo mit hohem Drehmoment

### Typische Pulsbreiten

| Wert | Standard-Servo | Continuous-Servo |
|---|---|---|
| 500 us | 0° | Volle Drehzahl (CCW) |
| 1500 us | 90° (Mitte) | Stillstand |
| 2500 us | 180° | Volle Drehzahl (CW) |

Hinweis: Die Pulsbreiten koennen je nach Modell leicht abweichen. Die
Bibliothek erlaubt die Anpassung ueber Konstruktor-Parameter.

## Anschluss

```text
Servo               ESP32
GND (braun)  -----> GND
VCC (rot)    -----> 5V (externes Netzteil empfohlen!)
Signal (orange) --> GPIO (z. B. 13)
```

**Wichtig**: Servos koennen hohe Stroeme ziehen (bis zu 1 A unter Last).
Den ESP32 nicht direkt ueber USB mit Servo-Strom belasten! Bei mehr als
einem Servo oder bei Servos unter Last ein **externes 5-V-Netzteil** verwenden
und GND mit dem ESP32 verbinden.

Empfohlene GPIO-Pins am ESP32: 13, 14, 15, 27, 32, 33 (PWM-faehig).

## Installation

Datei `nitbw_servo.py` auf den ESP32 kopieren (z. B. nach `/lib` oder `/`).

Anschliessend kann die Bibliothek importiert werden:

```python
from nitbw_servo import Servo, ContinuousServo
```

## Schnellstart

### Standard-Servo

```python
from nitbw_servo import Servo

servo = Servo(pin=13)
servo.winkel(90)   # Auf 90° fahren
servo.mitte()      # Mittelposition
servo.winkel(0)    # Auf 0° fahren
servo.winkel(180)  # Auf 180° fahren
servo.aus()        # PWM abschalten
```

### Continuous-Servo

```python
from nitbw_servo import ContinuousServo

motor = ContinuousServo(pin=14)
motor.drehen(50, ContinuousServo.RECHTS)   # 50 % nach rechts
motor.drehen(80, ContinuousServo.LINKS)    # 80 % nach links
motor.stopp()                            # Anhalten
motor.aus()                              # PWM abschalten
```

## API-Referenz

### Klasse `Servo` (Standard-Servo)

#### Konstruktor

```python
Servo(pin, puls_min_us=500, puls_max_us=2500, winkel_min=0, winkel_max=180)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `pin` | int | - | GPIO-Pin-Nummer (z. B. 13) |
| `puls_min_us` | int | 500 | Pulsbreite fuer Minimalwinkel in Mikrosekunden |
| `puls_max_us` | int | 2500 | Pulsbreite fuer Maximalwinkel in Mikrosekunden |
| `winkel_min` | int | 0 | Minimaler Winkel in Grad |
| `winkel_max` | int | 180 | Maximaler Winkel in Grad |

#### Methoden

| Methode | Zweck |
|---|---|
| `winkel(grad)` | Servo auf bestimmten Winkel fahren (0-180°) |
| `mitte()` | Servo auf Mittelposition fahren |
| `minimum()` | Servo auf Minimalwinkel fahren |
| `maximum()` | Servo auf Maximalwinkel fahren |
| `puls(puls_us)` | Pulsbreite direkt setzen (Mikrosekunden) |
| `lese_winkel()` | Zuletzt gesetzten Winkel abfragen |
| `aus()` | PWM-Signal abschalten (Servo stromlos) |
| `deinit()` | PWM-Pin freigeben |

### Klasse `ContinuousServo` (360°-Servo)

#### Konstruktor

```python
ContinuousServo(pin, puls_mitte_us=1500, puls_min_us=500, puls_max_us=2500)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `pin` | int | - | GPIO-Pin-Nummer (z. B. 14) |
| `puls_mitte_us` | int | 1500 | Pulsbreite fuer Stillstand in Mikrosekunden |
| `puls_min_us` | int | 500 | Pulsbreite fuer volle Drehzahl rueckwaerts |
| `puls_max_us` | int | 2500 | Pulsbreite fuer volle Drehzahl vorwaerts |

#### Methoden

| Methode | Zweck |
|---|---|
| `drehen(geschwindigkeit, richtung)` | Drehung mit Geschwindigkeit (0-100 %) und Richtung (CW/CCW) |
| `stopp()` | Servo anhalten (Stillstandspunkt) |
| `puls(puls_us)` | Pulsbreite direkt setzen (fuer Kalibrierung) |
| `aus()` | PWM-Signal abschalten (Servo stromlos) |
| `deinit()` | PWM-Pin freigeben |

#### Richtungskonstanten

| Konstante | Wert | Bedeutung |
|---|---|---|
| `ContinuousServo.RECHTS` | 1 | Uhrzeigersinn (von vorne betrachtet) |
| `ContinuousServo.LINKS` | -1 | Gegen Uhrzeigersinn (von vorne betrachtet) |

Alternativ kann auch direkt `1` oder `-1` uebergeben werden.

## Beispiele

- `beispiel_servo.py`: Standard-Servo auf verschiedene Winkel fahren
- `beispiel_servo_continuous.py`: Continuous-Servo mit Geschwindigkeitsrampe und Richtungswechsel

### Zusatzbeispiele

1. Servo langsam durchschwenken (Sweep):
```python
from nitbw_servo import Servo
import time

servo = Servo(pin=13)
while True:
    for grad in range(0, 181, 1):
        servo.winkel(grad)
        time.sleep_ms(15)
    for grad in range(180, -1, -1):
        servo.winkel(grad)
        time.sleep_ms(15)
```

2. Continuous-Servo: Richtungswechsel alle 3 Sekunden:
```python
from nitbw_servo import ContinuousServo
import time

motor = ContinuousServo(pin=14)
while True:
    motor.drehen(60, ContinuousServo.RECHTS)
    time.sleep(3)
    motor.drehen(60, ContinuousServo.LINKS)
    time.sleep(3)
```

3. Servo mit angepassten Pulsbreiten (z. B. MG996R):
```python
from nitbw_servo import Servo

# MG996R hat oft einen engeren nutzbaren Bereich
servo = Servo(pin=13, puls_min_us=600, puls_max_us=2400)
servo.winkel(90)
```

4. Erweiterter Winkelbereich (0-270°):
```python
from nitbw_servo import Servo

# Spezialservo mit 270° Bereich
servo = Servo(pin=13, winkel_min=0, winkel_max=270,
              puls_min_us=500, puls_max_us=2500)
servo.winkel(135)  # Mittelposition bei 270°-Servo
```

5. Pulsbreite direkt setzen (Feinabstimmung):
```python
from nitbw_servo import Servo

servo = Servo(pin=13)
# Feinabstimmung: Pulsbreite manuell in Mikrosekunden
servo.puls(1500)  # Entspricht ca. 90°
servo.puls(750)   # Feiner Zwischenwert
```

6. Continuous-Servo Stillstandspunkt kalibrieren:
```python
from nitbw_servo import ContinuousServo

# Falls stopp() nicht ganz still steht: Mitte anpassen
motor = ContinuousServo(pin=14, puls_mitte_us=1480)
motor.stopp()  # Sollte jetzt exakt stillstehen
```

### Fehlersuche

- **Servo zittert oder brummt**: Stromversorgung pruefen. USB-Strom reicht fuer
  Servos unter Last oft nicht aus. Externes 5-V-Netzteil verwenden.
- **Servo faehrt nicht auf 0° oder 180°**: Pulsbreiten im Konstruktor anpassen
  (`puls_min_us`, `puls_max_us`). Guenstige Servos weichen oft vom Standard ab.
- **Continuous-Servo steht nicht ganz still bei `stopp()`**:
  Den Stillstandspunkt ueber `puls_mitte_us` im Konstruktor feinjustieren.
  Alternativ mit `motor.puls(1480)` etc. experimentieren.
- **Mehrere Servos gleichzeitig**: Jeden Servo an einen eigenen GPIO-Pin
  anschliessen. Der ESP32 unterstuetzt mehrere PWM-Kanaele gleichzeitig.

## Lizenz

MIT Lizenz. Der Modul-Header enthaelt nur die Kurzangabe:
`Lizenz: MIT (siehe LICENSE)`.
Der vollstaendige Lizenztext bleibt zentral in der Datei `LICENSE` im Projektstamm.
