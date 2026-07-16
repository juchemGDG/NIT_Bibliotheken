# NIT Bibliothek: HX711AD

## Beschreibung
Die Bibliothek `nitbw_hx711ad.py` bindet den HX711AD-Waegedrucksensor am ESP32 unter MicroPython ein. Sie liest 24-bit Rohwerte einer Waegezelle aus und bietet darauf aufbauend Tara, Mittelwert-/Medianfilter sowie kalibrierte Gewichtsausgabe. Durch frei waehlbare Einheit und Kalibrierfaktor eignet sich die Bibliothek fuer Gramm-, Kilogramm- oder Kraftmessungen.

Wichtig: Der Kalibrierfaktor ist nicht an die Nennlast der Zelle gekoppelt. Eine 5-kg-Zelle kann je nach Mechanik und Montage zum Beispiel einen Faktor von 400, 800 oder 1500 liefern. Entscheidend ist nur, dass der Faktor mit eurer konkreten Waage kalibriert wird.

## Features
- Rohwertauslesung als signed 24-bit Integer
- Messbereitschaft pruefen mit `ist_bereit()`
- Timeout-gesichertes Warten ueber `warten_bereit()`
- Kanal-/Gain-Umschaltung (A/128, A/64, B/32)
- Mittelwertmessung ueber `messen_mittelwert()`
- Medianmessung fuer robuste Werte ueber `messen_median()`
- Tara-Funktion mit `tara()`
- Manuelle Offset- und Skala-Einstellung
- Kalibrierfunktion mit bekanntem Referenzgewicht
- Gewichtsausgabe in frei definierter Einheit (z. B. g, kg, N)
- Stromsparfunktionen `power_down()` und `power_up()`

## Hardware
- Sensor: HX711 / HX711AD Verstaerker-Modul
- Lastsensor: 4-Draht-Waegezelle (Wheatstone-Bruecke)
- Typischer Einsatz: Waegezellen bis 5 kg
- Versorgung: meist 3.3 V oder 5 V (modulabhaengig)
- Digitale Pins:
  - `DT` (DOUT): Datenausgang vom HX711 zum ESP32
  - `SCK` (PD_SCK): Taktleitung vom ESP32 zum HX711

Hinweise:
- Viele HX711-Module arbeiten stabil mit 3.3 V Logik am ESP32.
- Bei 5 V Versorgung sind Modulvariante und Pegelverhalten zu pruefen.
- Mechanisch stabile Montage der Waegezelle ist entscheidend fuer reproduzierbare Messwerte.

## Anschluss
Beispielverkabelung fuer ESP32:

- `HX711 VCC -> 3V3` (oder 5V je nach Modul)
- `HX711 GND -> GND`
- `HX711 DT  -> GPIO 19`
- `HX711 SCK -> GPIO 18`

Waegezelle typischerweise am HX711:
- `E+` / `E-` Versorgung der Bruecke
- `A+` / `A-` Messsignal Kanal A

## Installation
- Datei `nitbw_hx711ad.py` auf den ESP32 kopieren (Root oder `lib/`).
- Import im Programm:

```python
from nitbw_hx711ad import HX711AD
```

## Schnellstart
```python
from nitbw_hx711ad import HX711AD
from time import sleep

waage = HX711AD(dt_pin=19, sck_pin=18)
waage.set_skala(1000.0)   # Grober Startwert fuer 5-kg-Waegezelle
waage.tara(n=20, median=True)

while True:
    print("Gewicht: {:.2f} g".format(waage.messen_gewicht(n=5, median=True)))
    sleep(0.5)
```

## API-Referenz
Konstruktor: `HX711AD(dt_pin, sck_pin, kanal='A', gain=128, timeout_ms=1000)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `dt_pin` | int | - | GPIO fuer Datenleitung DT (DOUT) |
| `sck_pin` | int | - | GPIO fuer Taktleitung SCK (PD_SCK) |
| `kanal` | str | `'A'` | Startkanal (`'A'` oder `'B'`) |
| `gain` | int | `128` | Gain passend zum Kanal (A:128/64, B:32) |
| `timeout_ms` | int | `1000` | Timeout fuer Messbereitschaft |

Wichtige Methoden:
- `ist_bereit()` -> `bool`
- `warten_bereit(timeout_ms=None, poll_ms=1)` -> `bool`
- `set_timeout(timeout_ms)`
- `set_kanal_gain(kanal='A', gain=128)`
- `get_kanal_gain()` -> `(kanal, gain)`
- `messen_roh()` -> `int`
- `messen_mittelwert(n=10, delay_ms=5)` -> `int`
- `messen_median(n=7, delay_ms=5)` -> `int`
- `tara(n=20, delay_ms=5, median=False)` -> `int`
- `set_offset(offset)` / `get_offset()`
- `set_skala(scale)` / `get_skala()`
- `messen_wert(n=5, delay_ms=5, median=False)` -> `int`
- `messen_gewicht(n=5, delay_ms=5, median=False)` -> `float`
- `kalibrieren(referenz_gewicht, n=20, delay_ms=5, median=True)` -> `float`
- `power_down()` / `power_up()`

## Beispiele
Dateien im Ordner:
- `HX711AD/beispiel_hx711ad.py`
- `HX711AD/beispiel_hx711ad_tara.py`
- `HX711AD/beispiel_hx711ad_kalibrierung.py`

Snippet 1: Rohwert direkt lesen
```python
roh = waage.messen_roh()
print("Rohwert:", roh)
```

Snippet 2: Tara setzen
```python
offset = waage.tara(n=30, median=True)
print("Offset:", offset)
```

Snippet 3: Gewicht mit Medianfilter
```python
gewicht = waage.messen_gewicht(n=7, median=True)
print("Gewicht: {:.2f} g".format(gewicht))
```

Snippet 4: Kalibrierung mit Referenzgewicht
```python
waage.tara(n=30, median=True)
skala = waage.kalibrieren(referenz_gewicht=1000.0, n=30, median=True)
print("Skala:", skala)
```

Snippet 5: Kanal/Gain umschalten
```python
waage.set_kanal_gain("A", 64)
print(waage.get_kanal_gain())
```

Praktische Hinweise/Fehlersuche:
- Messwert springt stark: Median (`median=True`) nutzen und Mechanik stabilisieren.
- Immer gleiche Werte: DT/SCK-Verkabelung und Stromversorgung pruefen.
- Unplausible Gewichtswerte: erst tara(), dann sauber kalibrieren.
- Wenn bei eurer Waage der Wert 400 das richtige Ergebnis liefert, ist das normal. Dann ist 400 euer passender Kalibrierfaktor fuer genau diese Kombination aus Zelle, Mechanik und Verstärkung.
- Negative Vorzeichen sind normal, wenn Waegezelle invertiert angeschlossen ist.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
