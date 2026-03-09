# GY-261 Kompass Sensor Bibliothek

Eine leistungsstarke MicroPython-Bibliothek zur Ansteuerung des **GY-261** Kompass-Sensors (HMC5883L) auf dem **ESP32**.

Die Bibliothek misst das Erdmagnetfeld in drei Dimensionen (X, Y, Z) und berechnet daraus die Kompassrichtung (Heading). Sie kommt **vollständig ohne externe Abhängigkeiten** aus (außer `machine` für I2C).

## ✨ Features

- **3-Achsen Magnetfeld-Messung** - X, Y, Z Komponenten des Magnetfeldes
- **Kompassrichtung (Heading)** - Berechnung der genauen Nordrichtung in Grad (0°-360°)
- **Himmelsrichtungen** - Automatische Umwandlung in Kompassrose (N, NE, E, SE, S, SW, W, NW)
- **Automatische Kalibrierung** - Offset-Kalibrierung durch Sensor-Rotation
- **Lokale Deklination** - Berücksichtigung des lokalen Deklinationswinkels
- **Einstellbare Empfindlichkeit** - 8 verschiedene Messbereiche (Gains)
- **Digitale Filter** - Einstellbare Sample Rate (0,75 Hz bis 75 Hz)
- **Feldstärke-Messung** - Berechnung der Gesamtfeldstärke
- **Keine externen Abhängigkeiten** - Reine MicroPython Implementierung
- **I2C Interface** - Standard I2C Kommunikation

## 🔧 Hardware-Anforderungen

### Unterstützte Sensoren
- **GY-261** (basierend auf HMC5883L)
- 3-Achsen Magnetometer
- I2C Schnittstelle

### Anschluss ESP32

```
GY-261 VCC  ->  ESP32 3.3V
GY-261 GND  ->  ESP32 GND
GY-261 SCL  ->  ESP32 GPIO 22 (Standard I2C SCL)
GY-261 SDA  ->  ESP32 GPIO 21 (Standard I2C SDA)
```

**Alternative GPIO Pins möglich** - einfach beim Initialisieren übergeben.

## 📦 Installation

Kopieren Sie die Datei `compass.py` auf Ihren ESP32 (z.B. in das Root-Verzeichnis).

## 🚀 Quick Start

```python
from machine import I2C, Pin
from compass import Compass

# I2C initialisieren (Standard Pins: SCL=22, SDA=21)
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Kompass initialisieren
compass = Compass(i2c)

# Kompassrichtung auslesen (Grad, 0° = Nord)
heading = compass.read_heading()
print(f"Kompassrichtung: {heading:.1f}°")

# Himmelsrichtung auslesen
direction = compass.read_heading_direction()
print(f"Richtung: {direction}")

# Magnetfeldstärke auslesen (in Milligauss)
x, y, z = compass.read_field()
print(f"Magnetfeld: X={x:.1f} mG, Y={y:.1f} mG, Z={z:.1f} mG")
```

## 📚 Detaillierte Verwendungsbeispiele

### Beispiel 1: Einfacher Kompass

```python
from machine import I2C, Pin
from compass import Compass
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
compass = Compass(i2c)

# Lokale Deklination setzen (z.B. 3° 45' für Mitteleuropa)
compass.set_declination(degrees=3, minutes=45)

while True:
    heading = compass.read_heading()
    direction = compass.read_heading_direction()
    
    print(f"Heading: {heading:6.1f}°  |  Richtung: {direction}")
    time.sleep(0.5)
```

### Beispiel 2: Kalibrierung

Der Kompass muss kalibriert werden, um genaue Messwerte zu liefern. Magnetfeldstörungen (z.B. von Elektronik) verfälschen die Messung.

```python
from compass import Compass
from machine import I2C, Pin

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
compass = Compass(i2c)

# Automatische Kalibrierung durchführen
# Sensor während des Vorgangs LANGSAM in alle Richtungen drehen
compass.auto_calibrate(samples=200)

# Jetzt ist der Kompass kalibriert
heading = compass.read_heading()
print(f"Genaue Heading: {heading:.1f}°")
```

**Wichtig:** Die Auto-Kalibrierung sollte durchgeführt werden:
- Nach dem ersten Einschalten
- Bei Änderungen der Umgebung/des Aufbaus
- Wenn die Genauigkeit abnimmt

### Beispiel 3: Magnetfeld-Visualisierung

```python
from compass import Compass
from machine import I2C, Pin
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
compass = Compass(i2c)
compass.set_declination(degrees=3, minutes=45)

print("=" * 50)
print("Magnetfeld-Monitor")
print("=" * 50)

while True:
    x, y, z = compass.read_field()
    heading = compass.read_heading()
    strength = compass.read_strength()
    
    print(f"\nHeading: {heading:6.1f}°")
    print(f"X-Feld: {x:7.1f} mG")
    print(f"Y-Feld: {y:7.1f} mG")
    print(f"Z-Feld: {z:7.1f} mG")
    print(f"Feldstärke (gesamt): {strength:6.1f} mG")
    
    time.sleep(1)
```

### Beispiel 4: Gaineinstellung (Empfindlichkeit)

```python
from compass import Compass
from machine import I2C, Pin

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
compass = Compass(i2c)

# Standardgain: 1370 (beste Balance)
# compass.set_gain(compass.GAIN_1370)  # 0.73 mG/LSB

# Für stärkere Felder: höherer Gain
# compass.set_gain(compass.GAIN_165)   # 5.80 mG/LSB

# Für schwache Felder: niedrigerer Gain
compass.set_gain(compass.GAIN_1090)     # 0.92 mG/LSB

heading = compass.read_heading()
print(f"Heading mit angepasstem Gain: {heading:.1f}°")
```

### Beispiel 5: Sample Rate (Messhäufigkeit)

```python
from compass import Compass
from machine import I2C, Pin
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
compass = Compass(i2c)

# Schnelle Aktualisierung für dynamische Anwendungen
compass.set_sample_rate(compass.RATE_75HZ)  # 75 Messungen pro Sekunde

print("Schnelle Sample Rate (75 Hz)")

for i in range(10):
    heading = compass.read_heading()
    print(f"  {heading:.1f}°")
    time.sleep(0.05)

# Für stromspartenden Betrieb
compass.set_sample_rate(compass.RATE_1_5HZ)  # 1.5 Messungen pro Sekunde

print("\nLangsame Sample Rate (1.5 Hz)")

for i in range(5):
    heading = compass.read_heading()
    print(f"  {heading:.1f}°")
    time.sleep(1)
```

### Beispiel 6: Vollständiges Navigationssystem

```python
from compass import Compass
from machine import I2C, Pin
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
compass = Compass(i2c)

# Für Mitteleuropa typisch: 3° 45' östlich
compass.set_declination(degrees=3, minutes=45)

# Initial kalibrieren (einmalig)
print("Initialkalibierung durchführen...")
compass.auto_calibrate(samples=100)

def get_direction_text(heading):
    """Ausführliche Richtungsbeschreibung"""
    if 348.75 <= heading or heading < 11.25:
        return "Nord (N)"
    elif 11.25 <= heading < 33.75:
        return "Nord-Nordost (NNE)"
    elif 33.75 <= heading < 56.25:
        return "Nordost (NE)"
    elif 56.25 <= heading < 78.75:
        return "Ost-Nordost (ENE)"
    elif 78.75 <= heading < 101.25:
        return "Ost (E)"
    elif 101.25 <= heading < 123.75:
        return "Ost-Südost (ESE)"
    elif 123.75 <= heading < 146.25:
        return "Südost (SE)"
    elif 146.25 <= heading < 168.75:
        return "Süd-Südost (SSE)"
    elif 168.75 <= heading < 191.25:
        return "Süd (S)"
    elif 191.25 <= heading < 213.75:
        return "Süd-Südwest (SSW)"
    elif 213.75 <= heading < 236.25:
        return "Südwest (SW)"
    elif 236.25 <= heading < 258.75:
        return "West-Südwest (WSW)"
    elif 258.75 <= heading < 281.25:
        return "West (W)"
    elif 281.25 <= heading < 303.75:
        return "West-Nordwest (WNW)"
    elif 303.75 <= heading < 326.25:
        return "Nordwest (NW)"
    else:  # 326.25 <= heading < 348.75
        return "Nord-Nordwest (NNW)"

# Navigationsschleife
heading_history = []
max_history = 5

while True:
    heading = compass.read_heading()
    heading_history.append(heading)
    
    if len(heading_history) > max_history:
        heading_history.pop(0)
    
    # Durchschnitt der letzten Werte für stabilere Anzeige
    avg_heading = sum(heading_history) / len(heading_history)
    
    print("=" * 40)
    print(f"Heading:     {heading:6.1f}°")
    print(f"Durchschnitt: {avg_heading:6.1f}°")
    print(f"Richtung:    {get_direction_text(avg_heading)}")
    print("=" * 40)
    
    time.sleep(0.5)
```

## 📖 API Referenz

### Initialisierung

```python
Compass(i2c=None, addr=0x1E, scl=22, sda=21)
```

**Parameter:**
- `i2c` (I2C): I2C Bus Objekt oder None (dann wird auto-erstellt)
- `addr` (int): I2C Adresse (Standard: 0x1E)
- `scl` (int): SCL Pin falls i2c=None (Standard: 22)
- `sda` (int): SDA Pin falls i2c=None (Standard: 21)

### Messmethoden

#### Rohdaten auslesen
```python
x, y, z = compass.read_raw()
```
Gibt rohe ADC-Werte ohne Kalibrierung zurück.

#### Magnetfeld auslesen
```python
x, y, z = compass.read_field()
```
Gibt Magnetfeldstärke in mG (Milligauss) für alle drei Achsen zurück.

#### Kompassrichtung auslesen
```python
heading = compass.read_heading()
```
Gibt Kompassrichtung in Grad (0°=Nord, 360°=Nord) zurück.

#### Himmelsrichtung auslesen
```python
direction = compass.read_heading_direction()
```
Gibt Himmelsrichtung als Text zurück (N, NE, E, SE, S, SW, W, NW).

#### Feldstärke auslesen
```python
strength = compass.read_strength()
```
Gibt Größe des Magnetvektors in mG zurück.

#### Bereitschaft prüfen
```python
if compass.is_ready():
    data = compass.read_heading()
```
Gibt True zurück, falls neue Daten verfügbar sind.

### Konfigurationsmethoden

#### Deklinationswinkel setzen
```python
compass.set_declination(degrees=3, minutes=45)
```
Setzt lokale magnetische Deklination (Unterschied zwischen magnetischem und geographischem Nord).

**Deklinationswerte für verschiedene Orte:**
- Deutschland: ca. 3-4° östlich
- Schweiz: ca. 2-3° östlich
- Österreich: ca. 3-4° östlich
- Niederlande: ca. 1-2° östlich
- USA (New York): ca. 13° westlich
- Werte abrufen: https://www.ngdc.noaa.gov/geomag/calculators/magcalc.shtml

#### Empfindlichkeit einstellen
```python
compass.set_gain(compass.GAIN_1370)
```

Verfügbare Gains (niedrig zu hoch):
- `GAIN_1370` - 0.73 mG/LSB (Standard, beste Balance)
- `GAIN_1090` - 0.92 mG/LSB
- `GAIN_820` - 1.22 mG/LSB
- `GAIN_660` - 1.52 mG/LSB
- `GAIN_440` - 2.27 mG/LSB
- `GAIN_330` - 3.03 mG/LSB
- `GAIN_220` - 4.35 mG/LSB
- `GAIN_165` - 5.80 mG/LSB (höchste Auflösung)

#### Sample Rate einstellen
```python
compass.set_sample_rate(compass.RATE_15HZ)
```

Verfügbare Raten:
- `RATE_0_75HZ` - 0,75 Messungen/Sekunde
- `RATE_1_5HZ` - 1,5 Messungen/Sekunde
- `RATE_3HZ` - 3 Messungen/Sekunde
- `RATE_7_5HZ` - 7,5 Messungen/Sekunde
- `RATE_15HZ` - 15 Messungen/Sekunde (Standard)
- `RATE_30HZ` - 30 Messungen/Sekunde
- `RATE_75HZ` - 75 Messungen/Sekunde

#### Betriebsmodus einstellen
```python
compass.set_mode(compass.MODE_CONTINUOUS)
```

Verfügbare Modi:
- `MODE_CONTINUOUS` - Kontinuierliche Messungen
- `MODE_SINGLE` - Einzelne Messung
- `MODE_IDLE` - Standbymodus

### Kalibrierungsmethoden

#### Automatische Kalibrierung
```python
compass.auto_calibrate(samples=200)
```
Sensor muss dabei LANGSAM in alle Richtungen gedreht werden.

**Empfehlung:** 200-300 Samples durchführen (dauert 10-20 Sekunden).

#### Manuelle Kalibrierung
```python
compass.calibrate_with_bias(x_bias=10, y_bias=-5, z_bias=0)
```
Falls bereits bekannte Offset-Werte vorliegen.

## ⚠️ Wichtige Hinweise

### 1. Kalibrierung ist essentiell
- Der Sensor misst das Erdmagnetfeld + alle lokalen Störfelder
- Ohne Kalibrierung sind die Messwerte ungenau
- Nach jeder Änderung des Aufbaus neu kalibrieren

### 2. Magnetfeldstörungen vermeiden
- Elektronische Komponenten (Motoren, Leiterbahnen) können das Feld stören
- Sensor möglichst weit weg von Spulen/Transformatoren platzieren
- Nicht neben anderen I2C Devices montieren

### 3. Deklination beachten
- Der Kompass zeigt auf den **magnetischen** Nordpol, nicht den geografischen
- Die Deklination ist vom Aufenthaltsort abhängig
- Für genaue Navigation MUSS die Deklination gesetzt werden

### 4. Ausrichtung des Sensors
- Der Sensor muss **horizontal** (parallel zum Boden) ausgerichtet sein
- Z-Achse sollte vertikal zeigen
- Nicht vertikal oder im Winkel einbauen

## 🛠️ Fehlerbehebung

### Problem: Kompass zeigt keine sinnvollen Werte
- **Lösung**: Sensor kalibrieren (`auto_calibrate()`)
- Überprüfer Deklinationswinkel

### Problem: Heading springt wild hin und her
- **Lösung**: Magnetfeldstörungen prüfen
- Sensor entfernt von Elektronik platzieren
- Sample Rate erhöhen (`set_sample_rate(RATE_75HZ)`)
- Mehrere Messungen durchschnittlich darstellen

### Problem: I2C Kommunikation schlägt fehl
- **Lösung**: Kabel und Pin-Nummern prüfen
- `i2c.scan()` testen ob Sensor auf 0x1E antwortet
- Pullup-Widerstände auf SCL/SDA prüfen (sonst 4,7 kΩ hinzufügen)

### Problem: Nach Kalibrierung immer noch ungenau
- **Lösung**: Mit mehr Samples kalibrieren
- Längere Zeit beim Drehen (langsame Bewegungen)
- Mehrfach nachkalibrieren

## 📝 Lizenz

MIT License - Siehe `../LICENSE` Datei für Details.

---

**Viel Spaß mit der GY-261 Kompass Bibliothek! 🧭**
