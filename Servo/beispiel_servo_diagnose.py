"""
Diagnose fuer SG90/Standard-Servos am ESP32.

Ziel:
- Zeigt, welche PWM-Methoden die aktuelle MicroPython-Firmware anbietet.
- Sendet direkte Pulsbreiten (us), um Firmware-/Bibliotheksprobleme auszuschliessen.

Anschluss:
- Servo Signal an GPIO 13 (anpassbar unten)
- Servo 5V/GND extern versorgen
- GND von Netzteil und ESP32 verbinden
"""

from machine import Pin, PWM
import time

PIN = 13
FREQ = 50


def set_pulse(pwm, pulse_us):
    if hasattr(pwm, "duty_ns"):
        pwm.duty_ns(int(pulse_us * 1000))
        return "duty_ns"
    if hasattr(pwm, "duty_u16"):
        pwm.duty_u16(int(pulse_us / 20000 * 65535))
        return "duty_u16"
    pwm.duty(int(pulse_us / 20000 * 1023))
    return "duty"


pwm = PWM(Pin(PIN))
pwm.freq(FREQ)

print("=== Servo Diagnose ===")
print("Pin:", PIN, "Frequenz:", FREQ, "Hz")
print("Methoden:")
print("  duty_ns :", hasattr(pwm, "duty_ns"))
print("  duty_u16:", hasattr(pwm, "duty_u16"))
print("  duty    :", hasattr(pwm, "duty"))

for pulse in [1500, 1000, 2000, 1200, 1800, 1500]:
    methode = set_pulse(pwm, pulse)
    print("Puls", pulse, "us via", methode)
    time.sleep(1.5)

print("PWM aus")
if hasattr(pwm, "duty_ns"):
    pwm.duty_ns(0)
elif hasattr(pwm, "duty_u16"):
    pwm.duty_u16(0)
else:
    pwm.duty(0)
