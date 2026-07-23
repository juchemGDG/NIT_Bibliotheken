# NIT Bibliothek: ACS758

## Beschreibung
Die Bibliothek `nitbw_acs758.py` bindet den Hall-Stromsensor ACS758 am ESP32 unter MicroPython ein. Sie liest die analoge Ausgangsspannung `VIOUT` ueber einen ADC ein und rechnet sie in Stromstaerke um - wahlweise in Ampere oder Milliampere. Alle Umrechnungsfaktoren werden vorab berechnet, sodass pro Messwert nur eine Multiplikation und eine Subtraktion noetig sind. Damit sind sehr schnelle Messreihen moeglich, waehrend Mittelwert-, Median- und Effektivwertfunktionen fuer genaue und ruhige Messwerte sorgen.

Wichtig: Der ACS758 misst potentialfrei ueber ein Magnetfeld. Genauigkeit entsteht deshalb erst durch Kalibrierung. Der Nullpunkt schwankt mit Versorgungsspannung, Sensorexemplar und Spannungsteiler - deshalb sollte vor der ersten Messung immer `nullpunkt_kalibrieren()` bei stromlosem Leiter aufgerufen werden.

## Features
Messung:
- Stromstaerke in Ampere (`messen_a()`) und Milliampere (`messen_ma()`)
- Einzelmessung mit maximaler Geschwindigkeit (`messen_schnell_a()`)
- Mittelwertmessung ueber frei waehlbare Anzahl Einzelmessungen
- Medianmessung fuer robuste Werte trotz Stoerimpulsen
- Schnelle Messreihen als Liste (`messen_serie_ma()`)
- Effektivwert (RMS) fuer Wechselstrom ueber ein Zeitfenster
- Spitzenwerte und Spitze-Spitze-Wert (`messen_spitze_a()`)
- Sammelauswertung mit Min/Max/Mittel/RMS/Messrate (`messen_statistik()`)
- Ausgangsspannung an `VIOUT` in Volt sowie ADC-Rohwerte
- Stromrichtung und Stromfluss-Erkennung

Kalibrierung und Einstellungen:
- Nullpunktkalibrierung bei stromlosem Leiter
- Kalibrierung der Empfindlichkeit mit bekanntem Referenzstrom (A oder mA)
- Manuelles Setzen von Nullpunkt und Empfindlichkeit
- Varianten-Presets fuer 50/100/150/200 A, bidirektional und unidirektional
- Ratiometrische Anpassung an die Versorgungsspannung (`set_vcc()`)
- Teilerfaktor fuer den Spannungsteiler (`set_teiler()`)
- Einstellbare Glaettung (EMA), Totzone und Standard-Messanzahl
- Vorzeichenumkehr bei vertauschter Stromrichtung (`set_invertiert()`)
- Einstellbare ADC-Daempfung und ADC-Aufloesung
- Nutzt automatisch den werkskalibrierten ADC (`read_uv()`), falls vorhanden

## Hardware
- Sensor: ACS758 Hall-Stromsensor (Allegro)
- Versorgung: 5 V (`VCC`), Ausgang `VIOUT` ist analog
- Der Sensor ist ratiometrisch: Nullpunkt und Empfindlichkeit skalieren mit `VCC`

Varianten und Presets:

| Preset | Typ | Messbereich | Empfindlichkeit (bei 5 V) | Nullpunkt |
|---|---|---|---|---|
| `"50B"` | ACS758LCB-050B | -50 A bis +50 A | 40.0 mV/A | 0.50 x Vcc = 2.50 V |
| `"50U"` | ACS758LCB-050U | 0 A bis 50 A | 60.0 mV/A | 0.12 x Vcc = 0.60 V |
| `"100B"` | ACS758LCB-100B | -100 A bis +100 A | 20.0 mV/A | 0.50 x Vcc = 2.50 V |
| `"100U"` | ACS758LCB-100U | 0 A bis 100 A | 40.0 mV/A | 0.12 x Vcc = 0.60 V |
| `"150B"` | ACS758KCB-150B | -150 A bis +150 A | 13.3 mV/A | 0.50 x Vcc = 2.50 V |
| `"150U"` | ACS758KCB-150U | 0 A bis 150 A | 26.7 mV/A | 0.12 x Vcc = 0.60 V |
| `"200B"` | ACS758ECB-200B | -200 A bis +200 A | 10.0 mV/A | 0.50 x Vcc = 2.50 V |
| `"200U"` | ACS758ECB-200U | 0 A bis 200 A | 20.0 mV/A | 0.12 x Vcc = 0.60 V |

Wichtiger Hinweis zum Spannungsteiler:
- Der ACS758 liefert an 5 V bis zu 5 V Ausgangsspannung. Der ESP32-ADC vertraegt maximal 3.3 V.
- `VIOUT` darf deshalb **niemals direkt** an einen ESP32-Pin. Immer einen Spannungsteiler verwenden.
- Teiler 10k/10k halbiert die Spannung: `teiler=2.0`. Damit liegt der Bereich 0-5 V bei 0-2.5 V am ADC.
- Toleranzen des Teilers werden durch `nullpunkt_kalibrieren()` und `kalibrieren()` mit ausgeglichen.
- Ein Kondensator von 100 nF vom ADC-Pin gegen GND beruhigt das Signal deutlich.

## Anschluss
Beispielverkabelung fuer ESP32:

- `ACS758 VCC -> 5V`
- `ACS758 GND -> GND` (gemeinsame Masse mit dem ESP32)
- `ACS758 VIOUT -> R1 (10k) -> Messpunkt -> R2 (10k) -> GND`
- `Messpunkt -> GPIO 34` (ADC1, eingangsseitig hochohmig)
- Optional `100 nF` vom Messpunkt gegen GND

Lastpfad ueber die Stromschienen des Sensors:
- Versorgung `+` -> `IP+`
- `IP-` -> Last `+`
- Last `-` -> Versorgung `-`

Sicherheitshinweise:
- Nur mit Kleinspannung (z. B. 12 V DC) arbeiten, niemals mit Netzspannung.
- Der Leistungspfad (`IP+`/`IP-`) ist vom Messteil galvanisch getrennt, die Verdrahtung muss trotzdem fuer den Laststrom ausgelegt sein.

## Installation
- Datei `nitbw_acs758.py` auf den ESP32 kopieren (Root oder `lib/`).
- Import im Programm:

```python
from nitbw_acs758 import ACS758
```

## Schnellstart
```python
from nitbw_acs758 import ACS758
from time import sleep

# VIOUT ueber Spannungsteiler 10k/10k an GPIO34
sensor = ACS758(pin=34, variante="50B", vcc=5.0, teiler=2.0, messungen=16)

# Nullpunkt bei stromlosem Leiter bestimmen
sensor.nullpunkt_kalibrieren(n=200)

while True:
    print("Strom: {:+.3f} A   {:+.1f} mA".format(sensor.messen_a(), sensor.messen_ma()))
    sleep(0.5)
```

## API-Referenz
Konstruktor: `ACS758(pin, variante='50B', vcc=5.0, teiler=1.0, adc_bits=12, vref=3.3, attenuation='11db', messungen=8, glaettung=0.0, totzone_ma=0.0, invertiert=False)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `pin` | int | - | ADC-faehiger GPIO fuer `VIOUT` (z. B. 34, 35, 32, 33) |
| `variante` | str | `'50B'` | Sensortyp aus `ACS758.VARIANTEN` |
| `vcc` | float | `5.0` | Versorgungsspannung des Sensors in Volt |
| `teiler` | float | `1.0` | Teilerfaktor Vsensor/Vadc (10k/10k -> `2.0`) |
| `adc_bits` | int | `12` | ADC-Aufloesung (9-12) |
| `vref` | float | `3.3` | Referenzspannung des ADC in Volt |
| `attenuation` | str | `'11db'` | ADC-Daempfung (`'0db'`, `'2.5db'`, `'6db'`, `'11db'`) |
| `messungen` | int | `8` | Standard-Anzahl Einzelmessungen pro Messwert |
| `glaettung` | float | `0.0` | EMA-Glaettung, 0.0 = aus bis 0.99 = sehr traege |
| `totzone_ma` | float | `0.0` | Betraege darunter werden als 0 mA gemeldet |
| `invertiert` | bool | `False` | Dreht das Vorzeichen der Messung |

Messmethoden:
- `messen_a(n=None)` -> `float` (Strom in A)
- `messen_ma(n=None)` -> `float` (Strom in mA)
- `messen_schnell_a()` / `messen_schnell_ma()` -> `float` (eine ADC-Wandlung)
- `messen_median_a(n=9)` / `messen_median_ma(n=9)` -> `float`
- `messen_serie_a(anzahl=100, intervall_us=0)` / `messen_serie_ma(...)` -> `list`
- `messen_effektivwert_a(dauer_ms=200)` / `messen_effektivwert_ma(...)` -> `float`
- `messen_spitze_a(dauer_ms=200)` -> `(min_a, max_a)`
- `messen_statistik(dauer_ms=200)` -> `dict`
- `messrate(anzahl=200)` -> `float` (moegliche Messungen pro Sekunde)
- `lesen_spannung(n=None)` -> `float` (Spannung an `VIOUT` in V)
- `lesen_roh(n=1)` -> `float` (ADC-Rohwert bzw. Mikrovolt)
- `ist_stromfluss(schwelle_ma=200.0)` -> `bool`
- `richtung(schwelle_ma=200.0)` -> `1`, `-1` oder `0`
- `daten(n=None)` -> `dict` mit `roh`, `spannung_v`, `strom_a`, `strom_ma`

Kalibrierung:
- `nullpunkt_kalibrieren(n=200)` -> `float` (neuer Nullpunkt in V)
- `kalibrieren(referenz_strom_a, n=200)` -> `float` (neue Empfindlichkeit in mV/A)
- `kalibrieren_referenz_ma(referenz_strom_ma, n=200)` -> `float`
- `set_nullpunkt_v(spannung)` / `get_nullpunkt_v()`
- `set_empfindlichkeit_mv_a(mv_pro_a)` / `get_empfindlichkeit_mv_a()`

Einstellungen:
- `set_variante(variante)` / `get_variante()`
- `set_vcc(vcc)` / `get_vcc()`
- `set_teiler(teiler)` / `get_teiler()`
- `set_messungen(n)` / `get_messungen()`
- `set_glaettung(faktor)` / `get_glaettung()`
- `set_totzone_ma(totzone_ma)` / `get_totzone_ma()`
- `set_invertiert(invertiert=True)` / `ist_invertiert()`
- `set_daempfung(attenuation)`
- `zuruecksetzen()` (Filterspeicher leeren)
- `messbereich_a()` -> `(min_a, max_a)`
- `aufloesung_ma()` -> `float` (mA pro ADC-Schritt)
- `info()` -> `dict` mit allen Einstellungen

## Beispiele
Dateien im Ordner:
- `ACS758/beispiel_acs758.py`
- `ACS758/beispiel_acs758_kalibrierung.py`
- `ACS758/beispiel_acs758_schnellmessung.py`
- `ACS758/beispiel_acs758_ueberstrom.py`

Snippet 1: Strom in A und mA lesen
```python
print("{:.3f} A".format(sensor.messen_a()))
print("{:.1f} mA".format(sensor.messen_ma()))
```

Snippet 2: Nullpunkt kalibrieren (Leiter stromlos)
```python
nullpunkt = sensor.nullpunkt_kalibrieren(n=400)
print("Nullpunkt: {:.4f} V".format(nullpunkt))
```

Snippet 3: Empfindlichkeit mit Referenzstrom kalibrieren
```python
sensor.nullpunkt_kalibrieren(n=400)   # ohne Strom
# jetzt bekannten Strom einschalten, z. B. 5.00 A laut Multimeter
print("{:.2f} mV/A".format(sensor.kalibrieren(5.0, n=400)))
```

Snippet 4: Schnelle Messreihe aufnehmen
```python
werte = sensor.messen_serie_ma(anzahl=200)
print("min {:.1f} mA / max {:.1f} mA".format(min(werte), max(werte)))
```

Snippet 5: Wechselstrom als Effektivwert messen
```python
print("Effektivwert: {:.3f} A".format(sensor.messen_effektivwert_a(dauer_ms=200)))
```

Snippet 6: Genauigkeit und Ruhe einstellen
```python
sensor.set_messungen(32)     # mehr Einzelmessungen -> weniger Rauschen
sensor.set_glaettung(0.85)   # ruhige Anzeige
sensor.set_totzone_ma(300)   # Rauschen um 0 A unterdruecken
```

Snippet 7: Andere Variante und Versorgungsspannung
```python
sensor.set_variante("100U")  # unidirektional, 0 bis 100 A
sensor.set_vcc(4.95)         # gemessene Versorgungsspannung
```

Praktische Hinweise/Fehlersuche:
- Messwert liegt konstant bei ca. der halben Versorgungsspannung: es fliesst kein Strom oder der Leiter ist nicht durch `IP+`/`IP-` gefuehrt.
- Werte immer positiv trotz `50B`: Nullpunkt nicht kalibriert. Erst `nullpunkt_kalibrieren()` ohne Strom aufrufen.
- Vorzeichen falsch herum: `set_invertiert(True)` oder Lastanschluesse tauschen.
- Werte springen stark: `set_messungen(32)`, `messen_median_a()` oder `set_glaettung(0.85)` nutzen, 100 nF am ADC-Pin ergaenzen.
- Anzeige bleibt bei kleinen Stroemen ungenau: Der ACS758 ist ein Sensor fuer grosse Stroeme. Ein ADC-Schritt entspricht je nach Variante mehreren zehn mA (siehe `aufloesung_ma()`). Fuer Stroeme unter 1 A ist der INA219 die bessere Wahl.
- Messwert haengt an 3.3 V fest: Spannungsteiler fehlt oder ist falsch dimensioniert, `teiler` passend setzen.
- Gemessener Strom weicht konstant um einen Faktor ab: `kalibrieren()` mit einem per Multimeter gemessenen Referenzstrom durchfuehren.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
