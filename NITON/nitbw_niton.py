"""
NIT Bibliothek: NITON - Noten und Melodien per PWM-Lautsprecher
Fuer ESP32 mit MicroPython

Version:    2.1.1
Autor:      Volker Rust / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Spielt einzelne Toene, Pausen und komplette Lied-Listen mit BPM und Legato.
Bietet deutsche Notenkonstanten, Notenlaengen, punktierte Noten und Triolen.
"""

from machine import Pin, PWM
import time

# Noten (deutsche Bezeichnung)
C = 130
D = 147
E = 165
F = 175
G = 196
A = 220
H = 247

Cis = 138
Dis = 156
Fis = 185
Gis = 207
Ais = 233
B = 233  # B = Ais (Bb)

c = 262
d = 294
e = 330
f = 349
g = 392
a = 440
h = 493

cis = 277
dis = 311
fis = 370
gis = 415
ais = 466
b = 466  # b = ais (Bb)

c2 = 523
d2 = 587
e2 = 659
f2 = 698
g2 = 784
a2 = 880
h2 = 988

cis2 = 554
dis2 = 622
fis2 = 740
gis2 = 831
ais2 = 932
b2 = 932

# Notenlaengen (Vielfache einer 32stel Note)
viertel = 8
achtel = 4
sechzehntel = 2
halbe = 16
ganze = 32

# Kurzformen
vi = viertel
ac = achtel
se = sechzehntel
ha = halbe
ga = ganze

# Punktierte Noten
punkt = 1.5
viertelpunkt = int(viertel * punkt)
achtelpunkt = int(achtel * punkt)
sechzehntelpunkt = int(sechzehntel * punkt)
halbepunkt = int(halbe * punkt)
ganzepunkt = int(ganze * punkt)

# Kurzformen punktiert
vip = viertelpunkt
acp = achtelpunkt
sep = sechzehntelpunkt
hap = halbepunkt
gap = ganzepunkt

triolenfaktor = 2.0 / 3.0


def triole(basis_laenge):
	"""Berechnet die Triolenlaenge zu einer gegebenen Basislaenge."""
	return max(1, int(round(basis_laenge * triolenfaktor)))


# Vorgefertigte Triolen-Konstanten
vierteltriole = triole(viertel)
achteltriole = triole(achtel)
sechzehnteltriole = triole(sechzehntel)
halbetriole = triole(halbe)
ganzetriole = triole(ganze)

# Kurzformen Triolen
vi_t = vierteltriole
ac_t = achteltriole
se_t = sechzehnteltriole
ha_t = halbetriole
ga_t = ganzetriole


class NITon:
	"""
	Spielt Toene und Melodien ueber einen PWM-Lautsprecher.

	Unterstuetzte Hardware:
	- Passiver Piezo-Lautsprecher
	- PWM-faehige GPIO-Pins am ESP32

	Schnittstelle: PWM
	"""

	def __init__(self, lautsprecherpin, geschwindigkeit=80, legato=95):
		self._pin_num = int(lautsprecherpin)
		self._pwm = PWM(Pin(self._pin_num))
		self._safe_duty_off()
		self._pwm.freq(1000)
		self.geschw = 100
		self.legato = 95
		self.setGeschw(geschwindigkeit)
		self.setLegato(legato)

	def _safe_duty_on(self, duty_50=True):
		try:
			self._pwm.duty_u16(32768 if duty_50 else 65535)
		except AttributeError:
			self._pwm.duty(512 if duty_50 else 1023)

	def _safe_duty_off(self):
		try:
			self._pwm.duty_u16(0)
		except AttributeError:
			self._pwm.duty(0)

	def ton(self, hoehe, laenge):
		"""Spielt einen Ton (Hz) fuer eine Notenlaenge in 32stel-Vielfachen."""
		laenge32_ms = (60000.0 / self.geschw) / 8.0

		if hoehe and hoehe > 0:
			self._pwm.freq(int(hoehe))
			ton_ms = int(laenge32_ms * laenge * (self.legato / 100.0))
			gap_ms = int(laenge32_ms * laenge * (1.0 - self.legato / 100.0))

			self._safe_duty_on()
			if ton_ms > 0:
				time.sleep_ms(ton_ms)
			self._safe_duty_off()
			if gap_ms > 0:
				time.sleep_ms(gap_ms)
		else:
			dauer_ms = int(laenge32_ms * laenge)
			if dauer_ms > 0:
				time.sleep_ms(dauer_ms)

	def spiele_lied(self, noten_liste):
		"""Spielt eine Liste aus Tupeln im Format (hoehe, laenge)."""
		for note, dauer in noten_liste:
			self.ton(note, dauer)

	def pause(self, laenge_ms):
		"""Macht eine Pause in Millisekunden."""
		time.sleep_ms(int(laenge_ms))

	def setzteGeschw(self, geschwindigkeit):
		"""Alias fuer setGeschw aus Gruenden der Rueckwaertskompatibilitaet."""
		self.setGeschw(geschwindigkeit)

	def setGeschw(self, geschwindigkeit):
		if 20 < int(geschwindigkeit) < 500:
			self.geschw = int(geschwindigkeit)
		else:
			self.geschw = 100

	def getGeschw(self):
		return self.geschw

	def setLPin(self, lautsprecherpin):
		try:
			self._pwm.deinit()
		except Exception:
			pass
		self._pin_num = int(lautsprecherpin)
		self._pwm = PWM(Pin(self._pin_num))
		self._pwm.freq(1000)
		self._safe_duty_off()

	def getLPin(self):
		return self._pin_num

	def setLegato(self, legato):
		if 0 < int(legato) <= 100:
			self.legato = int(legato)
		else:
			self.legato = 95

	def getLegato(self):
		return self.legato


__all__ = [
	"NITon",
	"triole",
	"C", "D", "E", "F", "G", "A", "H",
	"Cis", "Dis", "Fis", "Gis", "Ais", "B",
	"c", "d", "e", "f", "g", "a", "h",
	"cis", "dis", "fis", "gis", "ais", "b",
	"c2", "d2", "e2", "f2", "g2", "a2", "h2",
	"cis2", "dis2", "fis2", "gis2", "ais2", "b2",
	"viertel", "achtel", "sechzehntel", "halbe", "ganze",
	"vi", "ac", "se", "ha", "ga",
	"viertelpunkt", "achtelpunkt", "sechzehntelpunkt", "halbepunkt", "ganzepunkt",
	"vip", "acp", "sep", "hap", "gap",
	"vierteltriole", "achteltriole", "sechzehnteltriole", "halbetriole", "ganzetriole",
	"vi_t", "ac_t", "se_t", "ha_t", "ga_t",
]
