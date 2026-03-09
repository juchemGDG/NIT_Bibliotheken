# BME280 Sensor Bibliothek für MicroPython

Diese Bibliothek ermöglicht die Verwendung des Bosch BME280 Temperatur-, Luftdruck- und Feuchtigkeitssensors mit MicroPython auf dem ESP32. Die Implementierung basiert direkt auf dem Datenblatt und verwendet keine externen Bibliotheken (außer `machine` für I2C).

## Features

- ✅ Temperaturmessung (-40°C bis +85°C)
- ✅ Luftdruckmessung (300 hPa bis 1100 hPa)
- ✅ Feuchtigkeitsmessung (0% bis 100% RH)
- ✅ Höhenberechnung aus Luftdruck
- ✅ Taupunktberechnung
- ✅ Hitzeindex (gefühlte Temperatur)
- ✅ Kalibrierungsmöglichkeiten
- ✅ Verschiedene Betriebsmodi (Normal, Forced, Sleep)
- ✅ Konfigurierbares Oversampling
- ✅ IIR-Filter
- ✅ Energiesparfunktionen

## Hardware

Der BME280 kann über I2C verbunden werden. Die I2C-Adresse ist üblicherweise:
- `0x76` (Standard, SDO auf GND)
- `0x77` (SDO auf VCC)

### Anschluss ESP32

```
BME280 VCC  ->  ESP32 3.3V
BME280 GND  ->  ESP32 GND
BME280 SCL  ->  ESP32 GPIO 22 (Standard I2C SCL)
BME280 SDA  ->  ESP32 GPIO 21 (Standard I2C SDA)
```

## Installation

Kopieren Sie die Datei `bme280.py` auf Ihren ESP32 (z.B. in das Root-Verzeichnis oder einen `lib` Ordner).

## Schnellstart

```python
from machine import I2C, Pin
from bme280 import BME280

# I2C initialisieren
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# BME280 initialisieren
sensor = BME280(i2c)

# Alle Werte auslesen
temperatur, druck, feuchtigkeit = sensor.read_all()
print(f"Temperatur: {temperatur:.2f}°C")
print(f"Luftdruck: {druck:.2f} hPa")
print(f"Feuchtigkeit: {feuchtigkeit:.2f}%")

# Höhe berechnen
hoehe = sensor.calculate_altitude()
print(f"Höhe: {hoehe:.2f} m")
```

## Wichtige Funktionen

### Initialisierung

```python
sensor = BME280(i2c, addr=0x76)
```
- `i2c`: I2C Bus Objekt
- `addr`: I2C-Adresse (Standard: 0x76)

### Messwerte auslesen

#### Einzelne Messung

```python
# Nur Temperatur
temperatur = sensor.read_temperature()  # in °C

# Nur Luftdruck
druck = sensor.read_pressure()  # in hPa

# Nur Feuchtigkeit
feuchtigkeit = sensor.read_humidity()  # in %
```

#### Alle Messungen gleichzeitig

```python
temp, druck, feuchte = sensor.read_all()
```
**Empfohlen:** Effizienter als separate Aufrufe, da nur eine Messung durchgeführt wird.

### Höhenmessung

Die Höhenberechnung basiert auf der barometrischen Höhenformel und benötigt einen **Referenzdruck auf Meereshöhe** (QNH-Wert). Der Standardwert ist 1013.25 hPa, aber für präzise Messungen sollte dieser an das aktuelle Wetter angepasst werden.

#### Aktuelle Höhe berechnen

```python
hoehe = sensor.calculate_altitude()  # in Metern
```

Die Höhe wird aus dem aktuellen Luftdruck und dem gespeicherten Referenzdruck berechnet.

#### ⚙️ Methode 1: QNH-Wert setzen (Empfohlen für präzise Messungen)

Wenn Sie den aktuellen Luftdruck auf Meereshöhe kennen (QNH-Wert von Wetterstation):

```python
# Aktuellen QNH-Wert von einer Wetterstation eingeben
sensor.set_sea_level_pressure(1005.3)  # in hPa

# Jetzt wird die korrekte Höhe angezeigt
hoehe = sensor.calculate_altitude()
print(f"Höhe: {hoehe:.1f} m")
```

**Wo bekomme ich den QNH-Wert?**
- Lokale Wetterstationen oder Wetterdienste (DWD, wetter.de, etc.)
- Flughäfen (METAR-Daten)
- Wetter-APIs
- Aktuelle Wetterberichte

**Wichtig:** Der QNH-Wert ändert sich täglich mit dem Wetter (typisch 980-1030 hPa). Eine Differenz von ~6 hPa verursacht ca. 50m Höhenunterschied!

#### 🎯 Methode 2: Höhenmessung kalibrieren (Einfachste Methode)

Wenn Sie Ihre aktuelle Höhe kennen (z.B. von GPS oder Karte):

```python
# Bei bekannter Höhe einmalig kalibrieren
sensor.calibrate_altitude(234)  # z.B. 234 Meter über NN

# Ab jetzt stimmt die Höhenmessung
hoehe = sensor.calculate_altitude()
print(f"Höhe: {hoehe:.1f} m")
print(f"Berechneter QNH: {sensor.sea_level_pressure:.2f} hPa")
```

Dies berechnet automatisch den korrekten Meereshöhendruck für Ihre Position und das aktuelle Wetter.

**Tipp:** Führen Sie die Kalibrierung täglich durch, wenn sich das Wetter stark ändert (z.B. bei Hoch-/Tiefdruckgebieten).

#### Meereshöhendruck berechnen

Berechnet den QNH-Wert aus einer bekannten Höhe:

```python
sea_level = sensor.calculate_sea_level_pressure(234)  # Höhe in Metern
print(f"Berechneter QNH: {sea_level:.2f} hPa")
```

### Taupunkt berechnen

Der Taupunkt ist die Temperatur, bei der Kondensation einsetzt:

```python
taupunkt = sensor.calculate_dew_point()
print(f"Taupunkt: {taupunkt:.2f}°C")
```

Nützlich für:
- Vorhersage von Kondensation
- Klimakontrolle
- Wetterbeobachtung

### Hitzeindex berechnen

Der Hitzeindex zeigt die gefühlte Temperatur bei Wärme und hoher Luftfeuchtigkeit:

```python
hitzeindex = sensor.calculate_heat_index()
print(f"Gefühlte Temperatur: {hitzeindex:.2f}°C")
```

### Sensor konfigurieren

```python
sensor.configure(
    mode=BME280.MODE_NORMAL,        # Betriebsmodus
    osrs_t=BME280.OVERSAMPLE_X2,    # Temperatur Oversampling
    osrs_p=BME280.OVERSAMPLE_X16,   # Druck Oversampling
    osrs_h=BME280.OVERSAMPLE_X1,    # Feuchte Oversampling
    filter_coef=BME280.FILTER_OFF,  # IIR-Filter
    standby=BME280.STANDBY_500      # Standby-Zeit (Normal Mode)
)
```

#### Betriebsmodi

- `MODE_SLEEP`: Sensor ist aus (niedrigster Stromverbrauch)
- `MODE_FORCED`: Eine Messung durchführen, dann zurück in Sleep
- `MODE_NORMAL`: Kontinuierliche Messungen mit Standby-Pausen

#### Oversampling-Optionen

Je höher das Oversampling, desto präziser und rauschärmer die Messung:
- `OVERSAMPLE_X1`: 1x (schnell, weniger genau)
- `OVERSAMPLE_X2`: 2x
- `OVERSAMPLE_X4`: 4x
- `OVERSAMPLE_X8`: 8x
- `OVERSAMPLE_X16`: 16x (langsam, sehr genau)

**Empfehlung:** Hohe Werte für Druck (`X16`), niedrigere Werte für Temperatur und Feuchte.

#### IIR-Filter

Der IIR-Filter glättet schnelle Schwankungen:
- `FILTER_OFF`: Kein Filter
- `FILTER_2` bis `FILTER_16`: Zunehmende Glättung

### Energiesparmodus

#### Forced Mode (einzelne Messung)

```python
# Sensor aufwecken, messen und wieder schlafen
temp, druck, feuchte = sensor.forced_measurement()
```

Ideal für batteriebetriebene Anwendungen mit seltenen Messungen.

#### Sleep Mode

```python
# Sensor in Sleep Mode versetzen
sensor.sleep()
```

## Erweiterte Beispiele

### Beispiel 1: Wetterstation

```python
from machine import I2C, Pin
from bme280 import BME280
from time import sleep

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = BME280(i2c)

# Höhe kalibrieren (z.B. 320m über NN)
sensor.calibrate_altitude(320)

while True:
    temp, druck, feuchte = sensor.read_all()
    hoehe = sensor.calculate_altitude(druck)
    taupunkt = sensor.calculate_dew_point(temp, feuchte)
    
    print("=" * 40)
    print(f"Temperatur:     {temp:.1f}°C")
    print(f"Luftdruck:      {druck:.1f} hPa")
    print(f"Feuchtigkeit:   {feuchte:.1f}%")
    print(f"Höhe:           {hoehe:.1f} m")
    print(f"Taupunkt:       {taupunkt:.1f}°C")
    
    # Kondensationswarnung
    if temp - taupunkt < 2:
        print("⚠️  WARNUNG: Kondensationsgefahr!")
    
    sleep(10)
```

### Beispiel 2: Höhenmesser mit Kalibrierung

```python
from machine import I2C, Pin
from bme280 import BME280
from time import sleep

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = BME280(i2c)

# Kalibrierung auf bekannter Höhe (z.B. Erdgeschoss = 0m)
print("Drücken Sie Enter auf bekannter Referenzhöhe...")
input()
sensor.calibrate_altitude(0)
print(f"Kalibriert! Meereshöhendruck: {sensor.sea_level_pressure:.2f} hPa")

# Höhenmessung
start_hoehe = 0
while True:
    hoehe = sensor.calculate_altitude()
    delta = hoehe - start_hoehe
    
    print(f"Höhe: {hoehe:.2f}m (Δ {delta:+.2f}m)")
    sleep(1)
```

### Beispiel 3: Präzise Höhenmessung mit QNH-Wert

```python
from machine import I2C, Pin
from bme280 import BME280
from time import sleep

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = BME280(i2c)

# QNH-Wert von lokaler Wetterstation eingeben
# (z.B. von wetter.de, Flughafen METAR, oder Wetterstation)
aktueller_qnh = 1005.3  # Beispielwert in hPa
sensor.set_sea_level_pressure(aktueller_qnh)

print(f"QNH gesetzt auf: {aktueller_qnh:.2f} hPa")
print("=" * 40)

while True:
    temp, druck, feuchte = sensor.read_all()
    hoehe = sensor.calculate_altitude()
    
    # Berechne, wie sich der Luftdruck verhält
    pressure_trend = "stabil"
    
    print(f"Temperatur:     {temp:.1f}°C")
    print(f"Luftdruck:      {druck:.2f} hPa")
    print(f"Feuchtigkeit:   {feuchte:.1f}%")
    print(f"Höhe (präzise): {hoehe:.1f} m")
    print(f"QNH (Referenz): {sensor.sea_level_pressure:.2f} hPa")
    print("=" * 40)
    
    sleep(10)
```

**Tipp:** Aktualisieren Sie den QNH-Wert täglich für beste Genauigkeit!

### Beispiel 4: Energiesparende Datenerfassung

```python
from machine import I2C, Pin, deepsleep
from bme280 import BME280

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = BME280(i2c)

# Konfiguration für Forced Mode optimiert
sensor.configure(
    mode=BME280.MODE_SLEEP,
    osrs_t=BME280.OVERSAMPLE_X1,
    osrs_p=BME280.OVERSAMPLE_X4,
    osrs_h=BME280.OVERSAMPLE_X1
)

# Eine Messung durchführen
temp, druck, feuchte = sensor.forced_measurement()

# Daten loggen/senden
print(f"{temp:.1f}°C, {druck:.1f}hPa, {feuchte:.1f}%")

# 5 Minuten schlafen (300000 ms)
deepsleep(300000)
```

### Beispiel 5: Überwachung mit Schwellwerten

```python
from machine import I2C, Pin
from bme280 import BME280
from time import sleep

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = BME280(i2c)

# Schwellwerte
TEMP_MIN = 18.0
TEMP_MAX = 26.0
HUMIDITY_MAX = 65.0

while True:
    temp, druck, feuchte = sensor.read_all()
    
    # Überprüfung
    if temp < TEMP_MIN:
        print(f"❄️  Zu kalt: {temp:.1f}°C")
    elif temp > TEMP_MAX:
        print(f"🔥 Zu warm: {temp:.1f}°C")
    
    if feuchte > HUMIDITY_MAX:
        print(f"💧 Zu feucht: {feuchte:.1f}%")
    
    # Hitzeindex bei Wärme
    if temp > 27:
        hitze = sensor.calculate_heat_index(temp, feuchte)
        print(f"🌡️  Gefühlt: {hitze:.1f}°C")
    
    sleep(5)
```

### Beispiel 6: Mehrere Sensoren

```python
from machine import I2C, Pin
from bme280 import BME280

i2c = I2C(0, scl=Pin(22), sda=Pin(21))

# Zwei Sensoren mit unterschiedlichen Adressen
sensor_innen = BME280(i2c, addr=0x76)
sensor_aussen = BME280(i2c, addr=0x77)

# Messungen
t_in, p_in, h_in = sensor_innen.read_all()
t_out, p_out, h_out = sensor_aussen.read_all()

print(f"Innen:  {t_in:.1f}°C, {h_in:.1f}%")
print(f"Außen:  {t_out:.1f}°C, {h_out:.1f}%")
print(f"Differenz: {t_in - t_out:.1f}°C")
```

## Häufige Anwendungen

### 🌦️ Wetterstation
- Temperatur, Luftdruck und Feuchtigkeit erfassen
- Wettertrends erkennen (steigender/fallender Luftdruck)
- Komfortindex berechnen

### 🏔️ Höhenmesser
- Für Wanderungen und Outdoor-Aktivitäten
- Drohnen-Höhenmessung
- Treppenzähler

### 🏠 Smart Home
- Klimaüberwachung
- Lüftungssteuerung basierend auf Luftfeuchtigkeit
- Schimmelprävention durch Taupunktüberwachung

### 🔋 IoT-Sensoren
- Batteriefreundlicher Forced Mode
- Datenlogging mit Deep Sleep
- Funkübertragung von Umweltdaten

## Technische Details

### Messgenauigkeit (typisch)

- **Temperatur:** ±1.0°C (0°C bis 65°C)
- **Luftdruck:** ±1.0 hPa (absolute Genauigkeit)
- **Feuchtigkeit:** ±3% RH (20% bis 80%)

### Messbereiche

- **Temperatur:** -40°C bis +85°C
- **Luftdruck:** 300 hPa bis 1100 hPa
- **Feuchtigkeit:** 0% bis 100% RH

### Stromverbrauch

- **Sleep Mode:** 0.1 µA
- **Forced Mode:** 1x Messung ~3.6 µA avg
- **Normal Mode:** kontinuierlich ~3.6 µA (1 Hz)

### I2C-Geschwindigkeit

- Standard Mode (100 kHz)
- Fast Mode (400 kHz) ← empfohlen
- High Speed Mode (3.4 MHz)

## Fehlerbehebung

### Sensor nicht gefunden

```
RuntimeError: BME280 nicht gefunden!
```

**Lösungen:**
- I2C-Adresse prüfen (0x76 oder 0x77)
- Verkabelung überprüfen
- I2C-Scan durchführen:
  ```python
  i2c.scan()  # Zeigt alle gefundenen Geräte
  ```

### Ungültige Messwerte

**Symptome:** Werte sind 0, NaN oder unrealistisch

**Lösungen:**
- Sensor zurücksetzen: `sensor.reset()`
- Längere Wartezeit nach Initialisierung
- Oversampling erhöhen
- Stromversorgung prüfen (min. 1.8V, typ. 3.3V)

### Höhenmessung ungenau

**Symptome:** Die angezeigte Höhe weicht um 50-100m von der tatsächlichen Höhe ab

**Ursache:** Der verwendete Referenzdruck (Standard: 1013.25 hPa) passt nicht zum aktuellen Wetter. Der tatsächliche Luftdruck auf Meereshöhe ändert sich täglich mit Hoch- und Tiefdruckgebieten (typisch 980-1030 hPa).

**Lösungen:**

1. **Höhe kalibrieren (einfachste Methode):**
   ```python
   sensor.calibrate_altitude(234)  # Ihre bekannte Höhe in Metern
   ```

2. **Aktuellen QNH-Wert eingeben:**
   ```python
   sensor.set_sea_level_pressure(1005.3)  # Von Wetterstation
   ```

3. **Regelmäßig neu kalibrieren:** Bei starken Wetteränderungen täglich kalibrieren

**Hinweis:** Eine Luftdruckdifferenz von ~6 hPa verursacht etwa 50m Höhenunterschied. Dies ist physikalisch bedingt und keine Fehlfunktion des Sensors!

## Lizenz

Diese Bibliothek steht unter der MIT-Lizenz. Siehe LICENSE-Datei für Details.

## Referenzen

- [BME280 Datenblatt](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf)
- [Bosch Sensortec BME280](https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/)

## Autor

Erstellt für NIT Bibliotheken - MicroPython Sensor Libraries
