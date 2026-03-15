"""
Beispiel fuer NIT Bibliothek: REGLER
Zeigt: PID-Regelung mit echtem ADC-Wert und PWM-Ausgang (8/10 Bit)
Hardware: Potentiometer an ADC + PWM-Ausgang am ESP32
"""

from machine import ADC, Pin
from time import sleep_ms, ticks_ms, ticks_diff

from nitbw_regler import PIDRegler, SensorAdapter, PWMAktor, Regelkanal, ReglerMonitor


# --- Initialisierung ---
# ADC-Eingang, z. B. Potentiometer an GPIO34 (0..4095)
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

# PWM-Ausgang mit 10 Bit an GPIO25
aktor = PWMAktor(pin=25, freq=2000, bits=10)

regler = PIDRegler(
    kp=0.18,
    ki=0.05,
    kd=0.02,
    sollwert=2200,
    ausgang_min=0.0,
    ausgang_max=100.0,   # Prozent fuer output_mode='percent'
    i_min=-40.0,
    i_max=40.0,
    alpha=0.2,
    eingang_min=0,
    eingang_max=4095,
)

kanal = Regelkanal(
    regler=regler,
    sensor=sensor,
    aktor=aktor,
    output_mode="percent",
    output_min=0,
    output_max=1023,   # 10 Bit PWM
)

monitor = ReglerMonitor(max_punkte=120)

# --- Hauptprogramm ---
print("=== PID mit ADC-Eingang und PWM-Ausgang ===")
print("Sollwert aktuell:", regler.sollwert)
print("Ctrl+C zum Beenden")

letzte_zeit = ticks_ms()
sekunden = 0

try:
    while True:
        jetzt = ticks_ms()
        dt_ms = ticks_diff(jetzt, letzte_zeit)
        letzte_zeit = jetzt
        dt = dt_ms / 1000.0
        if dt <= 0:
            dt = 0.05

        status = kanal.step(dt=dt)
        monitor.add(sekunden, status["sollwert"], status["istwert"], status["output"], status["fehler"])

        print(
            "Ist={:4.0f} | Soll={:4.0f} | e={:7.1f} | P={:6.1f} I={:6.1f} D={:6.1f} | PWM={:4.0f}".format(
                status["istwert"],
                status["sollwert"],
                status["fehler"],
                status.get("p", 0.0),
                status.get("i", 0.0),
                status.get("d", 0.0),
                status["output"],
            )
        )

        sekunden += dt
        sleep_ms(100)
except KeyboardInterrupt:
    aktor.aus()
    print("Regelung gestoppt, PWM aus")
    print(monitor.trend("ist", breite=50))
    print(monitor.trend("ausgang", breite=50))
