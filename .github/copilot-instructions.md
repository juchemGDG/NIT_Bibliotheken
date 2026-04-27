# NIT Bibliotheken – Copilot-Anweisungen

Diese Datei definiert die verbindlichen Konventionen fuer alle NIT-Bibliotheken.
Halte dich bei der Erstellung oder Aenderung von Bibliotheken exakt an diese Regeln.

---

## 1. Namensregeln

### 1.1 Bibliotheksdatei

Verwende das Muster `nitbw_<name>.py`.

```
nitbw_ultraschall.py
nitbw_bme280.py
```

### 1.2 Beispieldateien

Verwende das Muster `beispiel_<thema>.py`. Weitere Beispiele mit Suffix:

```
beispiel_ultraschall.py
beispiel_ultraschall_einparkhilfe.py
beispiel_ultraschall_median.py
```

### 1.3 Ordnername

Grossbuchstaben, identisch mit dem Thema:

```
ULTRASCHALL/
BME280/
TOF/
```

### 1.4 Variablennamen

Variablennamen duerfen Englisch bleiben (Python-Konvention).

---

## 2. Modul-Header

Beginne jede Bibliotheksdatei mit exakt diesem Block:

```python
"""
NIT Bibliothek: <Name> - <Kurzbeschreibung>
Fuer ESP32 mit MicroPython

Version:    1.0.0
Autor:      <Vorname Nachname> / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   <YYYY-MM>

<1-2 Saetze: technische Kernidee, z. B. Registeransteuerung,
 verwendete Schnittstelle, Besonderheiten>
"""
```

Regeln:

- Setze die Version beim Erstellen immer auf `1.0.0`.
- Verwende keine `__version__`-Variable im Code.
- Schreibe das Datum als Jahr und Monat (z. B. `2026-03`).
- Halte die Lizenzzeile woertlich: `MIT (siehe LICENSE)`.
- Bei mehreren Autoren trenne die Namen mit Komma:
  `Autor:      Stephan Juchem, Volker Rust / nitbw`

### Versionierung

Zaehle die Version nach Aenderungen hoch:

| Aenderungsart | Beispiel | Version |
|---|---|---|
| Neue Funktionalitaet (rueckwaertskompatibel) | Neue Methode hinzugefuegt | Minor: 1.0.0 → 1.1.0 |
| Bugfix oder kleine Korrektur | Randbedingung korrigiert | Patch: 1.1.0 → 1.1.1 |
| API-Aenderung (bricht Kompatibilitaet) | Konstruktor-Signatur geaendert | Major: 1.1.1 → 2.0.0 |

---

## 3. Klassen-Docstring

Verwende dieses Format fuer den Klassen-Docstring:

```python
class <Klasse>:
    """
    <1 Satz: Was macht die Klasse?>

    Unterstuetzte Hardware:
    - <Komponente 1>
    - <Komponente 2>

    Schnittstelle: <I2C/SPI/PWM/GPIO/...>
    """
```

Referenz: `BME280/nitbw_bme280.py`, `ULTRASCHALL/nitbw_ultraschall.py`.

---

## 4. Schnittstellenkonvention (I2C / SPI)

Erstelle die Hardware-Schnittstelle **immer ausserhalb** der Bibliothek.
Die Bibliothek akzeptiert ein fertiges Schnittstellenobjekt im Konstruktor.

### Bibliotheks-Konstruktor (richtig)

```python
class MeinSensor:
    def __init__(self, i2c, addr=0x76):
        self.i2c = i2c
        self.addr = addr
```

### Beispiel-Initialisierung (richtig)

```python
from machine import I2C, Pin
from nitbw_meinsensor import MeinSensor

# --- Initialisierung ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
sensor = MeinSensor(i2c)
```

### Verboten

Erstelle **keine** I2C-Schnittstelle intern per `sda`/`scl`-Pins:

```python
# FALSCH – nicht so machen:
class MeinSensor:
    def __init__(self, sda=21, scl=22):
        self.i2c = I2C(0, scl=Pin(scl), sda=Pin(sda))
```

### Warum?

- Bei Pin-Aenderungen muss nur **eine** Stelle angepasst werden.
- Mehrere Sensoren am selben Bus teilen sich ein `i2c`-Objekt.
- Einheitliches Muster fuer alle I2C-Bibliotheken.

Vorbilder: `BME280/nitbw_bme280.py`, `TOF/nitbw_tof.py`.
Gleiches Prinzip gilt fuer SPI, falls zukuenftig relevant.

Fuer GPIO-basierte Sensoren (Ultraschall, TCS3200) oder PWM (Servo)
werden die Pins weiterhin direkt im Konstruktor angegeben.

---

## 5. Sprache und Stil

- Docstrings: **Deutsch**
- Kommentare: **Deutsch**
- Beispieltexte / print-Ausgaben: **Deutsch**
- Technische Bezeichner (Variablen, Funktionen): duerfen **Englisch** bleiben
- Umlaute als ae/oe/ue schreiben (MicroPython-Kompatibilitaet)

---

## 6. Beispieldateien

Beginne jede Beispieldatei mit diesem Header:

```python
"""
Beispiel fuer NIT Bibliothek: <Name>
Zeigt: <Anwendungsziel>
Hardware: <benoetigte Hardware>
"""
```

Strukturiere den Code so:

1. Imports
2. Abschnitt `# --- Initialisierung ---`
3. Abschnitt `# --- Hauptprogramm ---`

Erstelle mindestens ein Grundbeispiel. Weitere Beispiele fuer erweiterte
Funktionen sind willkommen.

Referenz: `ULTRASCHALL/beispiel_ultraschall.py`, `BME280/beispiel_bme280.py`.

---

## 7. README-Struktur

Erstelle fuer jede Bibliothek eine `README.md` mit exakt diesen Abschnitten
in dieser Reihenfolge:

1. **Beschreibung** – 2-4 Saetze
2. **Features** – 8+ Punkte, gerne gruppiert
3. **Hardware** – Varianten, Adressen, Pins, Besonderheiten
4. **Anschluss** – Verkabelungsbeispiel fuer ESP32
5. **Installation** – Datei kopieren, Import-Zeile
6. **Schnellstart** – Vollstaendiger, lauffaehiger Codeblock
7. **API-Referenz** – Konstruktor-Tabelle + Methodenuebersicht
8. **Beispiele** – Dateiverweise + 3-6 Code-Snippets
9. **Lizenz** – Kurzhinweis auf MIT + LICENSE-Datei

Mindesttiefe:

- API: Konstruktor mit allen Parametern + alle oeffentlichen Methoden
- Beispiele: mindestens 3 verschiedene Anwendungsfaelle
- Fehlersuche / Hinweise: typische Stolperfallen auflisten

Referenz: `ULTRASCHALL/README.md`.

---

## 8. Lizenz

- Im Modul-Header steht nur: `Lizenz: MIT (siehe LICENSE)`.
- Jedes Bibliotheksverzeichnis enthaelt eine eigene `LICENSE`-Datei
  (identisch mit der Root-LICENSE). So ist der Lizenztext auch bei
  Einzeldownload vorhanden.
- In der README genuegt: „MIT-Lizenz, siehe zentrale Datei LICENSE
  im Repository-Root."

---

## 9. Root-README aktualisieren

Ergaenze nach dem Anlegen einer neuen Bibliothek die Tabelle in der
Root-`README.md`. Verwende exakt dieses Spaltenformat:

```markdown
| <Name> | `<ORDNER>/nitbw_<name>.py` | `<ORDNER>/beispiel_<name>.py`, `<ORDNER>/beispiel_<name>_<variante>.py` | 1.0.0 |
```

---

## 10. Checkliste fuer eine neue Bibliothek

- [ ] Ordner angelegt (Grossbuchstaben)
- [ ] `nitbw_<name>.py` mit Modul-Header und Klassen-Docstring
- [ ] I2C/SPI-Schnittstelle wird als Objekt im Konstruktor akzeptiert (nicht intern erstellt)
- [ ] Mindestens eine `beispiel_<thema>.py`
- [ ] `README.md` nach Abschnitt 7 angelegt
- [ ] `LICENSE`-Datei in den Ordner kopiert
- [ ] Root-`README.md`: neue Zeile in der Bibliothekstabelle ergaenzt

---

## 11. Bestehende Autoren (Referenz)

| Bibliothek | Autor |
|---|---|
| LCD | Volker Rust / nitbw |
| Servo | Volker Rust / nitbw |
| RTC | Volker Rust / nitbw |
| ULTRASCHALL | Volker Rust / nitbw |
| TOF | Volker Rust / nitbw |
| BME280 | Stephan Juchem / nitbw |
| COMPASS | Stephan Juchem / nitbw |
| MLEARN | Stephan Juchem / nitbw |
| OLED | Stephan Juchem, Volker Rust / nitbw |
| AS7262 | Stephan Juchem / nitbw |
| TCS3200 | Stephan Juchem / nitbw |
| DS18B20 | Stephan Juchem / nitbw |
| KY023 | Stephan Juchem / nitbw |
| NITON | Stephan Juchem / nitbw |
| TOENE | Stephan Juchem / nitbw |

Neue Bibliotheken: Autor ist die Person, die die Bibliothek erstellt.

---

## 12. Referenz-Implementierungen

Orientiere dich an diesen bestehenden Bibliotheken als Vorbilder:

- **I2C-Sensor:** `BME280/` – sauberes I2C-Objekt-Pattern, Konstruktor, Beispiel
- **I2C-Sensor (Mehrfach):** `TOF/` – mehrere Sensoren am selben Bus, XSHUT-Pins
- **GPIO-Sensor:** `ULTRASCHALL/` – vollstaendige Referenz fuer GPIO-basierte Sensoren
- **Allgemein:** `ULTRASCHALL/` – folgt allen Konventionen am saubersten
