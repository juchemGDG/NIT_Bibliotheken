"""
NIT Bibliothek: Puls - Herzfrequenzmessung mit analogem Pulssensor
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      NIT / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-05

Liest die analogen Pulssignale per ADC aus und stellt Rohwerte bereit.
Bestimmt die Herzfrequenz (BPM) ueber dynamische Schwellwerterkennung.
"""

from machine import ADC, Pin
import time


class Pulssensor:
    """
    Liest einen analogen Pulssensor aus und berechnet die Herzfrequenz.

    Unterstuetzte Hardware:
    - Funduino Pulssensor (analog)
    - Kompatible analoge Pulse Sensor Module

    Schnittstelle: ADC (analog)
    """

    def __init__(self, adc_pin, adc_bits=12, attenuation=None):
        """
        Initialisiert den Pulssensor.

        Args:
            adc_pin: GPIO-Pin fuer den analogen Ausgang (z. B. 34)
            adc_bits: ADC-Aufloesung (9-12, ESP32 typisch 12)
            attenuation: ADC-Attenuation, None -> ATTN_11DB falls verfuegbar
        """
        self.adc = ADC(Pin(adc_pin))

        self.adc_bits = max(9, min(12, int(adc_bits)))
        self.max_raw = (1 << self.adc_bits) - 1

        try:
            self.adc.width(getattr(ADC, "WIDTH_{}BIT".format(self.adc_bits)))
        except Exception:
            pass

        if attenuation is None:
            attenuation = getattr(ADC, "ATTN_11DB", None)
        if attenuation is not None:
            try:
                self.adc.atten(attenuation)
            except Exception:
                pass

    def lesen_roh(self):
        """
        Liest einen einzelnen ADC-Rohwert.

        Returns:
            int: ADC-Rohwert (typisch 0..4095 bei 12 Bit)
        """
        return self.adc.read()

    def lesen_roh_mittelwert(self, samples=8, pause_ms=2):
        """
        Liest mehrere ADC-Werte und gibt den Mittelwert zurueck.

        Args:
            samples: Anzahl Messpunkte
            pause_ms: Pause zwischen den Samples

        Returns:
            int: Gemittelter Rohwert
        """
        samples = max(1, int(samples))
        pause_ms = max(0, int(pause_ms))

        summiert = 0
        for _ in range(samples):
            summiert += self.lesen_roh()
            if pause_ms:
                time.sleep_ms(pause_ms)

        return summiert // samples

    def messen_puls(self, dauer_s=10, sample_ms=10, sperrzeit_ms=300, mindest_schwelle=18):
        """
        Misst die Herzfrequenz in BPM ueber ein Zeitfenster.

        Das Verfahren entfernt zuerst den DC-Anteil per gleitendem Mittelwert
        und nutzt dann einen dynamischen Schwellwert fuer die Schlagerkennung.

        Args:
            dauer_s: Messdauer in Sekunden
            sample_ms: Abtastintervall in Millisekunden
            sperrzeit_ms: Mindestabstand zwischen zwei Schlaegen
            mindest_schwelle: Untergrenze fuer die Schwellwertbildung

        Returns:
            float: Herzfrequenz in BPM oder -1 wenn keine stabile Messung
        """
        dauer_s = max(2, int(dauer_s))
        sample_ms = max(5, int(sample_ms))
        sperrzeit_ms = max(120, int(sperrzeit_ms))
        mindest_schwelle = max(1, int(mindest_schwelle))

        start = time.ticks_ms()
        ende = time.ticks_add(start, dauer_s * 1000)

        basis = self.lesen_roh()
        signal_alt = 0.0
        huelle = 0.0

        letzter_schlag = None
        intervalle = []

        while time.ticks_diff(ende, time.ticks_ms()) > 0:
            roh = self.lesen_roh()

            # DC-Anteil langsam nachfuehren, Pulsanteil als AC-Signal auswerten.
            basis = 0.95 * basis + 0.05 * roh
            signal = roh - basis

            # Dynamische Schwellwertbildung ueber Signalhuelle.
            huelle = 0.9 * huelle + 0.1 * abs(signal)
            schwelle = max(float(mindest_schwelle), huelle * 0.55)

            jetzt = time.ticks_ms()
            anstieg = signal > schwelle and signal_alt <= schwelle

            if anstieg:
                if letzter_schlag is None:
                    letzter_schlag = jetzt
                else:
                    delta = time.ticks_diff(jetzt, letzter_schlag)
                    if delta >= sperrzeit_ms:
                        intervalle.append(delta)
                        letzter_schlag = jetzt

            signal_alt = signal
            time.sleep_ms(sample_ms)

        # Nur plausible Herzschlagintervalle beruecksichtigen.
        plausible = []
        for delta in intervalle:
            if 300 <= delta <= 1500:
                plausible.append(delta)

        if len(plausible) < 2:
            return -1

        mittel_intervall = sum(plausible) / len(plausible)
        bpm = 60000.0 / mittel_intervall
        return round(bpm, 1)
