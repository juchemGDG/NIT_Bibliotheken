"""
Beispiel fuer NIT Bibliothek: REGLER
Zeigt: Laufende Umschaltung zwischen P, PI und PID mit echtem Sensor/Aktor
Hardware: ADC-Eingang + PWM-Ausgang am ESP32
"""

from machine import ADC, Pin
from time import sleep_ms, ticks_ms, ticks_diff

from nitbw_regler import PRegler, PIRegler, PIDRegler, SensorAdapter, PWMAktor, Regelkanal


# --- Initialisierung ---
adc = ADC(Pin(34))
if hasattr(adc, "atten"):
    adc.atten(ADC.ATTN_11DB)
if hasattr(adc, "width"):
    adc.width(ADC.WIDTH_12BIT)

sensor = SensorAdapter(
    read_func=lambda: adc.read(),
    minimum=0,
    maximum=4095,
)

aktor = PWMAktor(pin=25, freq=1500, bits=10)

regler_p = PRegler(kp=0.22, sollwert=2200, ausgang_min=0, ausgang_max=100, eingang_min=0, eingang_max=4095)
regler_pi = PIRegler(kp=0.18, ki=0.03, sollwert=2200, ausgang_min=0, ausgang_max=100, i_min=-30, i_max=30, eingang_min=0, eingang_max=4095)
regler_pid = PIDRegler(kp=0.16, ki=0.025, kd=0.01, sollwert=2200, ausgang_min=0, ausgang_max=100, i_min=-30, i_max=30, alpha=0.2, eingang_min=0, eingang_max=4095)

kanal = Regelkanal(regler=regler_p, sensor=sensor, aktor=aktor, output_mode="percent", output_min=0, output_max=1023)

# --- Hauptprogramm ---
print("=== Reglerumschaltung P -> PI -> PID ===")
print("t<20s: P, 20-40s: PI, ab 40s: PID")
print("Ctrl+C zum Beenden")

start = ticks_ms()
letzte_zeit = start

try:
    while True:
        jetzt = ticks_ms()
        dt = ticks_diff(jetzt, letzte_zeit) / 1000.0
        letzte_zeit = jetzt
        if dt <= 0:
            dt = 0.05

        t = ticks_diff(jetzt, start) / 1000.0

        if t < 20:
            kanal.regler = regler_p
            name = "P"
        elif t < 40:
            kanal.regler = regler_pi
            name = "PI"
        else:
            kanal.regler = regler_pid
            name = "PID"

        status = kanal.step(dt=dt)

        print(
            "{:>3} | Ist={:4.0f} Soll={:4.0f} e={:7.1f} u={:6.1f}% PWM={:4.0f}".format(
                name,
                status["istwert"],
                status["sollwert"],
                status["fehler"],
                status["reglerwert"],
                status["output"],
            )
        )
        sleep_ms(120)
except KeyboardInterrupt:
    aktor.aus()
    print("Regelung gestoppt, PWM aus")
