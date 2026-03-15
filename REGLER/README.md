# NIT Bibliothek: REGLER

## Beschreibung
Die Bibliothek `nitbw_regler.py` stellt einfache Regler fuer den Unterricht mit ESP32 und MicroPython bereit. Enthalten sind Zweipunktregler (mit einstellbarer Breite und Hysterese), P-, I-, D- sowie PI-, PD- und PID-Regler. Sensorwerte koennen direkt eingelesen und intern in der Bibliothek verarbeitet werden. Die erzeugte Stellgroesse kann als 8-10-Bit-PWM-Wert an Aktoren ausgegeben werden.

## Features
- Zweipunktregler mit einstellbarer `breite` und `hysterese`
- Optional invertierter Zweipunktregler (z. B. fuer Kuehlung)
- P-Regler mit `kp`
- I-Regler mit `ki` und Integratorgrenzen (`i_min`, `i_max`)
- D-Regler mit `kd` und optionaler D-Filterung (`alpha`)
- PI-Regler als Kombination aus P + I
- PD-Regler als Kombination aus P + D
- PID-Regler mit P-, I-, D-Anteil und separater Parametrierung
- Einheitliche Methoden (`set_sollwert`, `update`, `status`, `reset`)
- Begrenzung der Eingangs-/Messgroessen (`eingang_min`, `eingang_max`)
- Sensoradapter fuer echte Messwerte (`SensorAdapter`)
- PWM-Aktoradapter fuer ESP32 (`PWMAktor`, 8-10 Bit typisch)
- Vollstaendiger Regelkanal in der Bibliothek (`Regelkanal.step`)
- Didaktischer `ReglerMonitor` fuer Verlauf von Sollwert, Istwert, Fehler und Ausgang
- Textdarstellung als Tabelle (`als_tabelle`) und Trendlinie (`trend`) ohne Zusatzbibliothek

## Hardware
- Zielplattform: ESP32 mit MicroPython
- Sensoren: z. B. BME280 (Temperatur), ADC-Eingang (Spannung/Potentiometer)
- Aktoren: PWM-faehige Lasten ueber Treiber (Luefter, Heizer, LEDs, Motorcontroller)
- Typische Kombinationen im Unterricht:
  - Temperaturregelung (z. B. mit BME280 + Heizer/Luefter)
  - Distanzregelung (z. B. mit Ultraschall + Motor)
  - Lagedynamik (z. B. mit COMPASS/ADXL345 + Servo)
- Hinweise:
  - Stellgroessen-Grenzen immer sinnvoll setzen (`ausgang_min`, `ausgang_max`).
  - Beim Einsatz von I- oder PID-Reglern Integratorgrenzen setzen, um Aufschaukeln zu vermeiden.

## Anschluss
Kein fester Anschluss, da die Bibliothek allgemein ist.

Beispielhafte Kette fuer eine Temperaturregelung am ESP32:
- `BME280` liefert Istwert Temperatur ueber I2C (SCL 22, SDA 21)
- `REGLER` berechnet intern die Stellgroesse
- PWM-Ausgang z. B. GPIO 25 steuert Heizpatrone/Luefter ueber Leistungstreiber

## Installation
- Datei `nitbw_regler.py` auf den ESP32 kopieren (Root oder `lib/`).
- In Skripten importieren, z. B. `from nitbw_regler import PIDRegler`.

## Schnellstart
```python
from machine import ADC, Pin
from time import sleep_ms
from nitbw_regler import PIDRegler, SensorAdapter, PWMAktor, Regelkanal

adc = ADC(Pin(34))
sensor = SensorAdapter(read_func=lambda: adc.read(), minimum=0, maximum=4095)
aktor = PWMAktor(pin=25, freq=2000, bits=10)

regler = PIDRegler(
  kp=0.18, ki=0.05, kd=0.02,
  sollwert=2200,
  ausgang_min=0.0, ausgang_max=100.0,
  eingang_min=0, eingang_max=4095,
)

kanal = Regelkanal(regler=regler, sensor=sensor, aktor=aktor, output_mode="percent", output_min=0, output_max=1023)

while True:
  status = kanal.step(dt=0.1)
  print("Ist={} Soll={} PWM={:.0f}".format(status["istwert"], status["sollwert"], status["output"]))
  sleep_ms(100)
```

## API-Referenz
Kernklassen:
- `Zweipunktregler(..., invertiert=False, eingang_min=None, eingang_max=None)`
- `PRegler(..., bias=0.0, eingang_min=None, eingang_max=None)`
- `IRegler(..., i_min=-1000.0, i_max=1000.0, eingang_min=None, eingang_max=None)`
- `DRegler(..., alpha=0.0, eingang_min=None, eingang_max=None)`
- `PIRegler(...)`, `PDRegler(...)`, `PIDRegler(...)`

Adapter/Verkettung:
- `SensorAdapter(read_func, minimum=None, maximum=None)`
- `PWMAktor(pin, freq=1000, bits=10)`
- `Regelkanal(regler, sensor, aktor=None, output_mode='raw'|'percent', output_min=0, output_max=1023)`

Wichtige Methoden (alle Regler):
- `set_sollwert(sollwert)`
- `set_ausgangsgrenzen(minimum, maximum)`
- `set_eingangsgrenzen(minimum=None, maximum=None)`
- `update(istwert, dt=...)` (bei Zweipunkt/P optional ohne `dt`)
- `status()` -> `dict` mit aktuellen Regelgroessen
- `reset()`

Spezielle Methoden:
- Zweipunkt: `set_breite(breite)`, `set_hysterese(hysterese)`
- PID: `set_parameter(kp=None, ki=None, kd=None)`
- Regelkreis komplett: `Regelkanal.step(dt)`
- Monitor: `ReglerMonitor.add(...)`, `als_tabelle(...)`, `trend(...)`
- Utility: `format_status(status)`

## Beispiele
Dateien im Ordner:
- `REGLER/beispiel_regler_zweipunkt.py`
- `REGLER/beispiel_regler_pid.py`
- `REGLER/beispiel_regler_kombinationen.py`

Snippet 1: Zweipunkt mit Breite und Hysterese
```python
from nitbw_regler import Zweipunktregler, SensorAdapter, Regelkanal

sensor = SensorAdapter(read_func=lambda: 21.2, minimum=0.0, maximum=60.0)
regler = Zweipunktregler(sollwert=22.0, breite=0.5, hysterese=1.0, eingang_min=0.0, eingang_max=60.0)
kanal = Regelkanal(regler=regler, sensor=sensor)
print(kanal.step())
```

Snippet 2: PI-Regler
```python
from nitbw_regler import PIRegler, SensorAdapter, Regelkanal

sensor = SensorAdapter(read_func=lambda: 43.0, minimum=0.0, maximum=100.0)
pi = PIRegler(kp=1.8, ki=0.25, sollwert=50.0, ausgang_min=0, ausgang_max=100, eingang_min=0, eingang_max=100)
kanal = Regelkanal(regler=pi, sensor=sensor)
print(kanal.step(dt=0.2))
```

Snippet 3: PD-Regler
```python
from nitbw_regler import PDRegler, SensorAdapter, Regelkanal

sensor = SensorAdapter(read_func=lambda: 46.0, minimum=0.0, maximum=100.0)
pd = PDRegler(kp=2.0, kd=0.6, sollwert=50.0, alpha=0.2, eingang_min=0, eingang_max=100)
kanal = Regelkanal(regler=pd, sensor=sensor)
print(kanal.step(dt=0.1))
```

Snippet 4: PID mit Parameteraenderung zur Laufzeit
```python
from nitbw_regler import PIDRegler

pid = PIDRegler(kp=2.5, ki=0.2, kd=0.4, sollwert=60.0)
pid.set_parameter(kp=3.0, ki=0.3)
```

Snippet 5: PWM mit 8 oder 10 Bit ansteuern
```python
from nitbw_regler import PWMAktor

aktor_8bit = PWMAktor(pin=25, freq=2000, bits=8)   # 0..255
aktor_10bit = PWMAktor(pin=26, freq=2000, bits=10) # 0..1023
aktor_10bit.schreibe_prozent(50)                    # halbe Leistung
```

Snippet 6: Regelgroessen als Tabelle und Trend
```python
from nitbw_regler import ReglerMonitor, PIDRegler, format_status

pid = PIDRegler(kp=2, ki=0.1, kd=0.3, sollwert=10)
pid.update(7.5, dt=0.5)
print(format_status(pid.status()))

m = ReglerMonitor(max_punkte=50)
m.add(0.0, sollwert=10, istwert=7.5, ausgang=pid.status()["ausgang"])
print(m.als_tabelle(start=-5))
```

Praktische Hinweise / Fehlersuche:
- Schwingt das System stark: `kp` senken, `kd` erhoehen oder `dt` verkleinern.
- Bleibt ein Restfehler: `ki` erhoehen (vorsichtig), ggf. Integratorgrenzen anpassen.
- Zweipunkt klappert schnell: `hysterese` vergroessern.
- Ausgang ist dauernd am Limit: Reglerparameter oder Streckenmodell pruefen.
- Messwert ausserhalb Bereich: `eingang_min`/`eingang_max` passend einstellen.
- PWM wirkt invertiert: `invertiert` beim Zweipunktregler bzw. Aktorlogik pruefen.

## Lizenz
MIT-Lizenz, siehe `LICENSE` im Repository-Root.
