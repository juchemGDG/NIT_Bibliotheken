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
| RTC | `RTC/nitbw_rtc.py` | `RTC/beispiel_rtc.py`, `RTC/beispiel_rtc_komplett.py` | 1.1.0 |
| Servo | `Servo/nitbw_servo.py` | `Servo/beispiel_servo.py`, `Servo/beispiel_servo_continuous.py` | 1.1.0 |
| Ultraschall | `ULTRASCHALL/nitbw_ultraschall.py` | `ULTRASCHALL/beispiel_ultraschall.py`, `ULTRASCHALL/beispiel_ultraschall_einparkhilfe.py` | 1.0.0 |

## Schnellstart-Muster

```python
# Beispiel LCD
from nitbw_lcd import LCD
lcd = LCD(scl=22, sda=21, addr=0x27)
lcd.print('Hallo NIT', 0, 0)
```

```python
# Beispiel OLED
from nitbw_oled import OLED
oled = OLED(scl=22, sda=21, chip='ssd1306')
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

## Dokumentation je Bibliothek

- `LCD/README.md`
- `OLED/README.md`
- `BME280/README.md`
- `COMPASS/README.md`
- `MLEARN/README.md`
- `RTC/README.md`
- `Servo/README.md`
- `ULTRASCHALL/README.md`

## Lizenz

MIT-Lizenz, siehe zentrale Datei `LICENSE`.
