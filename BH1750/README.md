# NIT Bibliothek: BH1750

## Beschreibung
Die Bibliothek `nitbw_bh1750.py` stellt eine kompakte Anbindung des digitalen Lichtsensors BH1750 (ROHM) fuer ESP32 mit MicroPython bereit. Der Sensor liefert die Beleuchtungsstaerke direkt in Lux ueber I2C, ohne dass eine externe Umrechnung noetig ist. Kontinuierliche und einmalige Messungen stehen in hoher und niedriger Aufloesung zur Verfuegung. Ueber die einstellbare Messzeit (MTreg) laesst sich die Empfindlichkeit an sehr helle oder sehr dunkle Umgebungen anpassen. Mit einer Referenzmessung kann der BH1750 ausserdem als einfaches Fotometer Transmission und Extinktion einer Probe bestimmen.

## Features
- Beleuchtungsstaerke direkt in Lux
- Kontinuierliche Modi (H-Res, H-Res2, L-Res)
- Einmal-Modi mit automatischem Power-Down
- Hohe Aufloesung bis 0.5 lx (H-Res2)
- Einstellbare Messzeit/Empfindlichkeit ueber MTreg (31..254)
- Bequeme Empfindlichkeitsanpassung ueber `set_sensitivity(faktor)`
- Gemittelte Messung gegen Flackern mit `read_averaged()`
- Rohwertausgabe ueber `read_raw()`
- Hell-/Dunkel-Abfrage mit `is_dark()`
- Referenzkalibrierung fuer Fotometer-Messungen mit `kalibrieren()`
- Transmission einer Probe relativ zur Referenz mit `transmission()`
- Extinktion (Absorbanz) einer Probe mit `extinktion()`
- Gemeinsame Lux-, Transmissions- und Extinktionsmessung mit `messung()`
- Power-On, Power-Down und Reset steuerbar
- Zwei waehlbare I2C-Adressen (0x23 / 0x5C)
- Direkte Befehlsansteuerung ohne Fremdbibliotheken

## Hardware
- Sensor: BH1750 / BH1750FVI (z. B. GY-302 Breakout)
- I2C-Adresse: `0x23` (ADDR=GND/offen) oder `0x5C` (ADDR=VCC)
- Aufloesung: 1 lx (H-Res), 0.5 lx (H-Res2), 4 lx (L-Res)
- Messbereich: ca. 1 bis 65535 lx (je nach MTreg)
- Versorgung: 3.3 V (viele Breakouts haben einen Spannungsregler fuer 3.3–5 V)
- Hinweise:
  - Die meisten Module besitzen Pull-ups fuer SDA/SCL bereits on-board.
  - Der ADDR-Pin waehlt die Adresse: offen/GND -> `0x23`, VCC -> `0x5C`.

## Anschluss
Beispielverkabelung fuer ESP32:

- `VCC -> 3V3`
- `GND -> GND`
- `SCL -> GPIO 22`
- `SDA -> GPIO 21`
- `ADDR -> offen/GND` (Adresse `0x23`) oder `VCC` (Adresse `0x5C`)

## Installation
- Datei `nitbw_bh1750.py` auf den ESP32 kopieren (Root oder `lib/`).
- Import in deinem Programm: `from nitbw_bh1750 import BH1750`

## Schnellstart
```python
from machine import I2C, Pin
from nitbw_bh1750 import BH1750

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = BH1750(i2c, addr=BH1750.ADDR_LOW)

lux = sensor.read_lux()
print(f"Helligkeit: {lux:.1f} lx")
```

## Transmission und Extinktion
Fuer Fotometer-Messungen wird zuerst ohne die zu untersuchende Probe ein Referenzwert aufgenommen, zum Beispiel mit Wasser in der Messzelle oder mit freiem Strahlengang. Dieser Leerwert beschreibt, wie viel Licht unter den aktuellen Bedingungen am Sensor ankommt.

Die **Transmission** beschreibt, welcher Anteil dieses Referenzlichts die Probe durchlaesst. Eine klare Probe hat daher eine hohe Transmission; eine dunkle oder truebe Probe eine niedrige Transmission.

Die **Extinktion**, auch Absorbanz genannt, beschreibt umgekehrt, wie stark eine Probe das Licht abschwaecht. Sie ist fuer Vergleiche von Proben, Kalibrierreihen und als Eingabewert fuer Machine-Learning-Modelle oft geeigneter als der rohe Lux-Wert. Da alle Werte auf die Referenz bezogen werden, stoeren sich aendernde LED-Helligkeit, Abstand oder schwaches Umgebungslicht weniger stark aus.

Nach jeder Aenderung von Messmodus oder Empfindlichkeit muss die Referenz erneut aufgenommen werden.

## API-Referenz
Konstruktor: `BH1750(i2c, addr=ADDR_LOW, mode=CONT_HIRES, mtreg=MTREG_DEFAULT, n_kalibrierung=10)`

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `i2c` | `machine.I2C` | - | Initialisierter I2C-Bus |
| `addr` | `int` | `0x23` | Sensoradresse (`ADDR_LOW`/`ADDR_HIGH`) |
| `mode` | `int` | `CONT_HIRES` | Startmodus |
| `mtreg` | `int` | `69` | Messzeitregister (31..254) |
| `n_kalibrierung` | `int` | `10` | Standard-Anzahl Einzelmessungen fuer die Referenzkalibrierung |

Wichtige Methoden:
- `read_lux()` -> `float`
- `read_raw()` -> `int`
- `read_averaged(n=5, pause_ms=10)` -> `float`
- `is_dark(schwelle=10.0)` -> `bool`
- `set_mode(mode)`
- `set_mtreg(mtreg)`
- `set_sensitivity(faktor)`
- `power_on()`
- `power_down()`
- `reset()`
- `kalibrieren(n=None)` -> `float`: Nimmt den Referenzwert (Leerwert) auf.
- `ist_kalibriert()` -> `bool`: Prueft, ob ein Referenzwert vorhanden ist.
- `transmission(n=5)` -> `float`: Gibt die Lichtdurchlaessigkeit der Probe in Prozent zurueck.
- `extinktion(n=5)` -> `float`: Gibt die Abschwaechung der Probe als Extinktion zurueck.
- `messung(n=5)` -> `dict`: Gibt `lux`, `transmission` und `extinktion` aus einer Messreihe zurueck.

Modus-Konstanten:
- `CONT_HIRES`, `CONT_HIRES2`, `CONT_LORES` (kontinuierlich)
- `ONCE_HIRES`, `ONCE_HIRES2`, `ONCE_LORES` (einmalig, danach Power-Down)

Adress-Konstanten:
- `ADDR_LOW` = `0x23`, `ADDR_HIGH` = `0x5C`

## Beispiele
Dateien im Ordner:
- `BH1750/beispiel_bh1750.py`
- `BH1750/beispiel_bh1750_daemmerung.py`

Snippet 1: Helligkeit auslesen
```python
lux = sensor.read_lux()
print(f"{lux:.1f} lx")
```

Snippet 2: Gemittelte Messung gegen Flackern
```python
lux = sensor.read_averaged(n=10)
print(f"Mittelwert: {lux:.1f} lx")
```

Snippet 3: Empfindlichkeit fuer dunkle Raeume erhoehen
```python
sensor.set_sensitivity(2.0)   # laengere Messzeit, feinere Aufloesung
print(sensor.read_lux())
```

Snippet 4: Einmal-Messung mit Stromsparmodus
```python
sensor.set_mode(BH1750.ONCE_HIRES)
print(sensor.read_lux())      # Sensor geht danach automatisch in Power-Down
```

Snippet 5: Dunkelheit erkennen (Daemmerungsschalter)
```python
if sensor.is_dark(schwelle=20):
    print("Es ist dunkel - Licht einschalten")
```

Snippet 6: Probe fotometrisch messen
```python
# Zuerst ohne Probe bzw. mit Referenzfluessigkeit kalibrieren.
sensor.kalibrieren(n=10)

# Anschliessend die Probe in den Strahlengang einsetzen.
werte = sensor.messung(n=10)
print(f"Transmission: {werte['transmission']:.1f} %")
print(f"Extinktion: {werte['extinktion']:.3f}")
```

Praktische Hinweise/Fehlersuche:
- Keine Werte / OSError: I2C-Adresse (`0x23` vs. `0x5C`) und Verkabelung pruefen (`i2c.scan()`).
- Wert bleibt bei 65535: Umgebung zu hell -> Empfindlichkeit senken (`set_sensitivity(0.5)`) oder `CONT_LORES` nutzen.
- Sehr verrauschte/flackernde Werte: `read_averaged()` verwenden.
- Zu grobe Aufloesung im Dunkeln: `CONT_HIRES2` und/oder hoehere Empfindlichkeit waehlen.
- `RuntimeError` bei `transmission()`, `extinktion()` oder `messung()`: Zuerst mit `kalibrieren()` einen Referenzwert aufnehmen.
- Fotometer-Werte passen nicht mehr: Nach `set_mode()`, `set_mtreg()` oder `set_sensitivity()` erneut kalibrieren.

## Lizenz
MIT-Lizenz, siehe zentrale Datei `LICENSE` im Repository-Root.
