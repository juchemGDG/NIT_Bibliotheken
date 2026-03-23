# NIT Bibliotheken - ESP32 MicroPython

Konsolidierte Bibliothekssammlung fuer den NIT-Unterricht mit einheitlichem Namensschema:
- Bibliotheken: `nitbw_<name>.py`
- Beispiele: `beispiel_<thema>.py`

## Verfuegbare Bibliotheken

| Bibliothek | Moduldatei | Beispiele (Auswahl) | Version |
|---|---|---|---|
| LCD | `LCD/nitbw_lcd.py` | `LCD/beispiel_lcd.py`, `LCD/beispiel_lcd_funktionen.py` | 1.1.0 |
| OLED | `OLED/nitbw_oled.py` | `OLED/beispiel_oled_schnellstart.py`, `OLED/beispiel_oled.py` | 1.1.0 |
| BME280 | `BME280/nitbw_bme280.py` | `BME280/beispiel_bme280.py` | 1.1.0 |
| COMPASS | `COMPASS/nitbw_compass.py` | `COMPASS/beispiel_compass.py`, `COMPASS/beispiel_compass_rotation.py` | 1.1.0 |
| MLEARN | `MLEARN/nitbw_mlearn.py` | `MLEARN/beispiel_mlearn.py` | 1.1.0 |
| AS7262 | `AS7262/nitbw_as7262.py` | `AS7262/beispiel_as7262.py`, `AS7262/beispiel_as7262_kalibriert.py` | 1.0.0 |
| RTC | `RTC/nitbw_rtc.py` | `RTC/beispiel_rtc.py`, `RTC/beispiel_rtc_komplett.py` | 1.1.0 |
| Servo | `Servo/nitbw_servo.py` | `Servo/beispiel_servo.py`, `Servo/beispiel_servo_continuous.py` | 1.1.0 |
| Ultraschall | `ULTRASCHALL/nitbw_ultraschall.py` | `ULTRASCHALL/beispiel_ultraschall.py`, `ULTRASCHALL/beispiel_ultraschall_einparkhilfe.py` | 1.0.0 |
| TOF | `TOF/nitbw_tof.py` | `TOF/beispiel_tof.py`, `TOF/beispiel_tof_modi.py` | 1.0.0 |
| TCS3200 | `TCS3200/nitbw_tcs3200.py` | `TCS3200/beispiel_tcs3200.py`, `TCS3200/beispiel_tcs3200_rgb.py` | 1.0.0 |
| NITON | `NITON/nitbw_niton.py` | `NITON/beispiel_niton.py`, `NITON/beispiel_niton_listen.py` | 2.1.1 |
| TOENE | `TOENE/nitbw_toene.py` | `TOENE/beispiel_toene.py`, `TOENE/beispiel_toene_lied.py` | 1.2.0 |

## Schnellstart-Muster

```python
# Beispiel LCD
from machine import I2C, Pin
from nitbw_lcd import LCD
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = LCD(i2c, addr=0x27)
lcd.print('Hallo NIT', 0, 0)
```

```python
# Beispiel OLED
from machine import I2C, Pin
from nitbw_oled import OLED
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
oled = OLED(i2c, chip='ssd1306')
oled.print('Hello', 0, 0)
oled.show()
```

```python
# Beispiel BME280
from machine import I2C, Pin
from nitbw_bme280 import BME280
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = BME280(i2c)
print(sensor.read_all())
```

```python
# Beispiel TCS3200
from nitbw_tcs3200 import TCS3200
sensor = TCS3200(out=27, s2=14, s3=12, s0=26, s1=25)
sensor.set_frequenzskalierung(2)
print(sensor.dominante_farbe())
```

```python
# Beispiel AS7262
from machine import I2C, Pin
from nitbw_as7262 import AS7262
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = AS7262(i2c, led=True)
print(sensor.messen_roh())
```

```python
# Beispiel MLEARN
from nitbw_mlearn import MLearn
model = MLearn(k=3)
model.load_csv('iris.csv', separator=',', target=0)
model.train_knn()
print(model.predict_knn([5.1, 3.5, 1.4, 0.2]))
```

```python
# Beispiel MLEARN2 mit AS7262
from nitbw_mlearn import MLearn
model = MLearn(k=3)
model.load_csv('farben.csv', target=6)
model.train_forest(n_trees=5, max_depth=3)
print(model.predict_forest([52, 70, 151, 214, 210, 140]))
```

## Dokumentation je Bibliothek

- `LCD/README.md`
- `OLED/README.md`
- `BME280/README.md`
- `COMPASS/README.md`
- `MLEARN/README.md`
- `MLEARN2/README.md`
- `RTC/README.md`
- `Servo/README.md`
- `ULTRASCHALL/README.md`
- `TOF/README.md`
- `TCS3200/README.md`
- `AS7262/README.md`
- `NITON/README.md`
- `TOENE/README.md`

## Lizenz

MIT-Lizenz, siehe zentrale Datei `LICENSE`.
