from machine import I2C, Pin
from bme280 import BME280

# I2C initialisieren
# ESP32 Standard: SCL=22, SDA=21
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Sensor initialisieren
sensor = BME280(i2c)

# Messwerte lesen
temperatur, druck, feuchtigkeit = sensor.read_all()
print(f"Temperatur: {temperatur:.2f} C")
print(f"Luftdruck: {druck:.2f} hPa")
print(f"Feuchtigkeit: {feuchtigkeit:.2f}%")

# Hoehe berechnen
hoehe = sensor.calculate_altitude()
print(f"Hoehe: {hoehe:.2f} m")
