"""
NIT Bibliothek: LCD - HD44780 LCD-Display ueber PCF8574 I2C-Adapter
Fuer ESP32 mit MicroPython

Version:    1.1.0
Autor:      Volker Rust / nitbw
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Unterstuetzt 16x2 und 20x4 LCD-Displays im 4-Bit-Modus.
Die Implementierung ist eigenstaendig und benoetigt keine externen Bibliotheken.
"""

from machine import I2C, Pin
import time


# ============================================================================
# HD44780 Befehle (aus dem offiziellen Datenblatt des HD44780 Controllers)
# ============================================================================

# Grundbefehle
_BEFEHL_LOESCHEN = 0x01          # Display löschen
_BEFEHL_ANFANG = 0x02            # Cursor auf Position (0,0) setzen
_BEFEHL_EINGABEMODUS = 0x04      # Eingabemodus konfigurieren
_BEFEHL_ANZEIGE = 0x08           # Display, Cursor und Blinken steuern
_BEFEHL_VERSCHIEBEN = 0x10       # Display oder Cursor verschieben
_BEFEHL_FUNKTION = 0x20          # Datenlänge, Zeilenanzahl, Zeichensatz
_BEFEHL_CGRAM_ADRESSE = 0x40     # Adresse im Zeichengenerator-RAM setzen
_BEFEHL_DDRAM_ADRESSE = 0x80     # Adresse im Display-Daten-RAM setzen

# Eingabemodus-Flags
_EINGABE_RECHTS = 0x00           # Cursor nach links bewegen
_EINGABE_LINKS = 0x02            # Cursor nach rechts bewegen (Standard)
_EINGABE_VERSCHIEBEN = 0x01      # Display mitverschieben

# Anzeige-Steuerung
_ANZEIGE_AN = 0x04               # Display einschalten
_ANZEIGE_AUS = 0x00              # Display ausschalten
_CURSOR_AN = 0x02                # Unterstrich-Cursor anzeigen
_CURSOR_AUS = 0x00               # Cursor verbergen
_BLINKEN_AN = 0x01               # Blinkenden Cursor anzeigen
_BLINKEN_AUS = 0x00              # Blinken deaktivieren

# Verschiebe-Flags
_DISPLAY_VERSCHIEBEN = 0x08      # Display verschieben
_CURSOR_VERSCHIEBEN = 0x00       # Cursor verschieben
_NACH_RECHTS = 0x04              # Richtung: rechts
_NACH_LINKS = 0x00               # Richtung: links

# Funktions-Flags
_MODUS_4BIT = 0x00               # 4-Bit Datenmodus
_ZWEI_ZEILEN = 0x08              # 2-Zeilen-Modus
_EINE_ZEILE = 0x00               # 1-Zeilen-Modus
_ZEICHEN_5X10 = 0x04             # 5x10 Pixel Zeichensatz
_ZEICHEN_5X8 = 0x00              # 5x8 Pixel Zeichensatz (Standard)

# PCF8574 Bit-Zuordnung für den I2C-Adapter
_BIT_RS = 0x01                   # Register Select (0=Befehl, 1=Daten)
_BIT_RW = 0x02                   # Lesen/Schreiben (immer 0=Schreiben)
_BIT_EN = 0x04                   # Enable-Signal (Taktung)
_BIT_LICHT = 0x08                # Hintergrundbeleuchtung


class LCDTreiber:
    """
    Basis-Treiber für HD44780-kompatible LCD-Displays über PCF8574 I2C-Adapter.

    Kommuniziert im 4-Bit-Modus mit dem LCD-Controller.
    Die Daten werden über den PCF8574 Portexpander per I2C übertragen.
    """

    def __init__(self, i2c, addr, spalten, zeilen):
        """
        Initialisiert den LCD-Treiber.

        Args:
            i2c: MicroPython I2C-Objekt
            addr: I2C-Adresse des PCF8574 (z.B. 0x27 oder 0x3F)
            spalten: Anzahl der Spalten (z.B. 16 oder 20)
            zeilen: Anzahl der Zeilen (z.B. 2 oder 4)
        """
        self.i2c = i2c
        self.addr = addr
        self.spalten = spalten
        self.zeilen = zeilen
        self._licht = _BIT_LICHT
        self._anzeige = _ANZEIGE_AN | _CURSOR_AUS | _BLINKEN_AUS
        self._eingabemodus = _EINGABE_LINKS
        self._display_initialisieren()

    def _display_initialisieren(self):
        """
        Führt die Initialisierungs-Sequenz gemäß HD44780 Datenblatt durch.
        Setzt das Display in den 4-Bit-Modus und konfiguriert die Grundeinstellungen.
        """
        # Warten bis LCD-Controller bereit ist (mind. 40ms nach Spannungsanstieg)
        time.sleep_ms(50)

        # Portexpander zurücksetzen (Hintergrundbeleuchtung beibehalten)
        self._port_schreiben(self._licht)
        time.sleep_ms(100)

        # Initialisierungs-Sequenz: Dreimal 0x03 senden, dann auf 4-Bit umschalten
        # (siehe HD44780 Datenblatt, Seite 46, Abbildung 24)
        self._halbbyte_senden(0x30)
        time.sleep_us(4500)
        self._halbbyte_senden(0x30)
        time.sleep_us(4500)
        self._halbbyte_senden(0x30)
        time.sleep_us(150)

        # Auf 4-Bit-Modus umschalten
        self._halbbyte_senden(0x20)
        time.sleep_us(150)

        # Funktions-Set: 4-Bit, Zeilenanzahl, Zeichensatz
        funktions_flags = _MODUS_4BIT | _ZEICHEN_5X8
        if self.zeilen > 1:
            funktions_flags |= _ZWEI_ZEILEN
        self.befehl(_BEFEHL_FUNKTION | funktions_flags)

        # Display einschalten, Cursor aus, Blinken aus
        self.befehl(_BEFEHL_ANZEIGE | self._anzeige)

        # Display löschen
        self.loeschen()

        # Eingabemodus: Links nach rechts, kein Verschieben
        self.befehl(_BEFEHL_EINGABEMODUS | self._eingabemodus)

        # Cursor auf Startposition
        self.anfang()

    def _port_schreiben(self, daten):
        """Schreibt ein Byte an den PCF8574 Portexpander."""
        self.i2c.writeto(self.addr, bytes([daten]))

    def _enable_puls(self, daten):
        """
        Erzeugt einen Enable-Puls zum Übernehmen der Daten.
        Der HD44780 liest die Datenleitungen bei der fallenden Flanke von Enable.
        """
        self._port_schreiben(daten | _BIT_EN)
        time.sleep_us(1)          # Enable mind. 450ns halten
        self._port_schreiben(daten & ~_BIT_EN)
        time.sleep_us(50)         # Befehl benötigt mind. 37µs

    def _halbbyte_senden(self, daten):
        """Sendet ein halbes Byte (obere 4 Bit) mit Enable-Puls."""
        byte = (daten & 0xF0) | self._licht
        self._port_schreiben(byte)
        self._enable_puls(byte)

    def _byte_senden(self, daten, modus=0):
        """
        Sendet ein komplettes Byte im 4-Bit-Modus.
        Zuerst die oberen 4 Bit, dann die unteren 4 Bit.

        Args:
            daten: Das zu sendende Byte
            modus: 0 für Befehl, _BIT_RS für Daten (Zeichen)
        """
        oberes = (daten & 0xF0) | modus | self._licht
        unteres = ((daten << 4) & 0xF0) | modus | self._licht
        self._port_schreiben(oberes)
        self._enable_puls(oberes)
        self._port_schreiben(unteres)
        self._enable_puls(unteres)

    def befehl(self, wert):
        """Sendet einen Befehl an den LCD-Controller (RS=0)."""
        self._byte_senden(wert, modus=0)

    def zeichen_senden(self, wert):
        """Sendet ein Daten-Byte (Zeichen) an den LCD-Controller (RS=1)."""
        self._byte_senden(wert, modus=_BIT_RS)

    def loeschen(self):
        """Löscht den gesamten Displayinhalt und setzt den Cursor auf (0,0)."""
        self.befehl(_BEFEHL_LOESCHEN)
        time.sleep_ms(2)           # Löschbefehl benötigt ca. 1,52ms

    def anfang(self):
        """Setzt den Cursor auf die Position (0,0) zurück."""
        self.befehl(_BEFEHL_ANFANG)
        time.sleep_ms(2)           # Home-Befehl benötigt ca. 1,52ms

    def cursor_setzen(self, spalte, zeile):
        """
        Setzt den Cursor auf eine bestimmte Position.

        Args:
            spalte: Spalte (0-basiert, von links)
            zeile: Zeile (0-basiert, von oben)
        """
        # Zeilenanfangs-Adressen im DDRAM des HD44780
        zeilen_offsets = (0x00, 0x40, 0x14, 0x54)
        if zeile >= self.zeilen:
            zeile = self.zeilen - 1
        if spalte >= self.spalten:
            spalte = self.spalten - 1
        self.befehl(_BEFEHL_DDRAM_ADRESSE | (spalte + zeilen_offsets[zeile]))

    # Zuordnung: CGRAM-Zeichen (Umlaute) und HD44780-ROM-Zeichen (°)
    _UMLAUT_MAP = {'ä': 0, 'ö': 1, 'ü': 2, 'Ä': 3, 'Ö': 4, 'Ü': 5, 'ß': 6, '♥': 7}
    _ROM_MAP = {'°': 0xDF}  # Grad-Zeichen ° liegt im HD44780-ROM bei 0xDF

    def text_senden(self, text):
        """
        Sendet einen Text zeichenweise an das Display.
        Deutsche Umlaute (äöüÄÖÜß) und Sonderzeichen (♥, °)
        werden automatisch auf die passenden Zeichen abgebildet.

        Args:
            text: Der anzuzeigende Text (wird automatisch in String umgewandelt)
        """
        for zeichen in str(text):
            if zeichen in self._UMLAUT_MAP:
                self.zeichen_senden(self._UMLAUT_MAP[zeichen])
            elif zeichen in self._ROM_MAP:
                self.zeichen_senden(self._ROM_MAP[zeichen])
            else:
                self.zeichen_senden(ord(zeichen))


class LCD:
    """
    Benutzerfreundliche LCD-Klasse fuer HD44780-kompatible Displays.

    Unterstuetzte Hardware:
    - HD44780-kompatible LCD-Module (16x2 und 20x4)
    - PCF8574/PCF8574A I2C-Adapter

    Schnittstelle: I2C
    """

    # Zuordnung deutscher Umlaute und Sonderzeichen zu CGRAM-Positionen (0-7).
    # Die Bitmaps definieren jeweils ein 5×8-Pixel-Zeichen.
    # Platz 7: Hier darf gerne ein anderes Zeichen hin – einfach Bitmap ändern!
    # Wer mehr als 1 eigenes Zeichen braucht, kann dafür Umlaute entfernen.
    _UMLAUTE_CGRAM = {
        'ä': (0, (0x0A,0x00,0x0E,0x01,0x0F,0x11,0x0F,0x00)),  # ä
        'ö': (1, (0x0A,0x00,0x0E,0x11,0x11,0x11,0x0E,0x00)),  # ö
        'ü': (2, (0x0A,0x00,0x11,0x11,0x11,0x13,0x0D,0x00)),  # ü
        'Ä': (3, (0x0A,0x00,0x0E,0x11,0x1F,0x11,0x11,0x00)),  # Ä
        'Ö': (4, (0x0A,0x00,0x0E,0x11,0x11,0x11,0x0E,0x00)),  # Ö
        'Ü': (5, (0x0A,0x00,0x11,0x11,0x11,0x11,0x0E,0x00)),  # Ü
        'ß': (6, (0x00,0x0E,0x11,0x1E,0x11,0x1E,0x10,0x00)),  # ß
        '♥': (7, (0x00,0x0A,0x1F,0x1F,0x1F,0x0E,0x04,0x00)),  # ♥ Herz – änderbar!
    }

    def __init__(self, scl=22, sda=21, addr=0x27, zeilen=4, spalten=20,
                 enabled=True, i2c_id=0, begruessung=True):
        """
        Initialisiert das LCD-Display.

        Args:
            scl: SCL-Pin (Standard: GPIO 22)
            sda: SDA-Pin (Standard: GPIO 21)
            addr: I2C-Adresse des PCF8574 (Standard: 0x27, oft auch 0x3F)
            zeilen: Anzahl der Zeilen (Standard: 4)
            spalten: Anzahl der Spalten (Standard: 20)
            enabled: True = Display aktiv, False = alle Ausgaben unterdrückt
            i2c_id: I2C-Bus-ID (Standard: 0)
            begruessung: True zeigt beim Start eine Begrüßung (Standard: True)
        """
        self.spalten = spalten
        self.zeilen = zeilen
        self.enabled = enabled

        if not self.enabled:
            self.treiber = None
            return

        # I2C-Bus initialisieren
        self.i2c = I2C(i2c_id, scl=Pin(scl), sda=Pin(sda), freq=400000)

        # LCD-Treiber initialisieren
        self.treiber = LCDTreiber(self.i2c, addr, spalten, zeilen)

        # Deutsche Umlaute als eigene Zeichen in CGRAM laden
        self._umlaute_laden()

        # Begrüßung anzeigen
        if begruessung:
            self._begruessung_anzeigen()

    def _umlaute_laden(self):
        """Lädt die deutschen Umlaute (äöüÄÖÜß) als eigene Zeichen ins CGRAM."""
        for zeichen, (pos, bitmap) in self._UMLAUTE_CGRAM.items():
            self.treiber.befehl(_BEFEHL_CGRAM_ADRESSE | (pos << 3))
            for byte in bitmap:
                self.treiber.zeichen_senden(byte)

    def _begruessung_anzeigen(self):
        """Zeigt eine kurze Begrüßung beim Einschalten für 2 Sekunden."""
        if not self.enabled:
            return

        self.treiber.loeschen()

        # "NIT" zentriert anzeigen
        text = "NIT"
        start_spalte = (self.spalten - len(text)) // 2
        start_zeile = self.zeilen // 2 - 1 if self.zeilen > 1 else 0
        self.treiber.cursor_setzen(start_spalte, start_zeile)
        self.treiber.text_senden(text)

        # Zweite Zeile mit "MicroPython"
        if self.zeilen > 1:
            text2 = "MicroPython"
            start_spalte2 = (self.spalten - len(text2)) // 2
            self.treiber.cursor_setzen(start_spalte2, start_zeile + 1)
            self.treiber.text_senden(text2)

        time.sleep(2)
        self.clear()

    # ========================================================================
    # Textausgabe
    # ========================================================================

    def print(self, text, spalte=0, zeile=0):
        """
        Gibt Text an einer bestimmten Position auf dem Display aus.

        Args:
            text: Der anzuzeigende Text
            spalte: Spalte (0-basiert, Standard: 0)
            zeile: Zeile (0-basiert, Standard: 0)

        Beispiel:
            lcd.print("Hallo Welt!", 0, 0)     # Zeile 0, ab Spalte 0
            lcd.print("Temperatur:", 0, 1)      # Zeile 1, ab Spalte 0
        """
        if not self.enabled:
            return

        self.treiber.cursor_setzen(spalte, zeile)
        self.treiber.text_senden(str(text))

    def print_center(self, text, zeile=0):
        """
        Gibt Text zentriert in einer bestimmten Zeile aus.

        Args:
            text: Der anzuzeigende Text
            zeile: Zeile (0-basiert, Standard: 0)

        Beispiel:
            lcd.print_center("Willkommen!", 0)
        """
        if not self.enabled:
            return

        text = str(text)
        # Text auf Spaltenbreite begrenzen
        if len(text) > self.spalten:
            text = text[:self.spalten]
        start = (self.spalten - len(text)) // 2
        self.treiber.cursor_setzen(start, zeile)
        self.treiber.text_senden(text)

    def print_right(self, text, zeile=0):
        """
        Gibt Text rechtsbündig in einer bestimmten Zeile aus.

        Args:
            text: Der anzuzeigende Text
            zeile: Zeile (0-basiert, Standard: 0)

        Beispiel:
            lcd.print_right("12:30", 0)
        """
        if not self.enabled:
            return

        text = str(text)
        if len(text) > self.spalten:
            text = text[:self.spalten]
        start = self.spalten - len(text)
        self.treiber.cursor_setzen(start, zeile)
        self.treiber.text_senden(text)

    def clear(self):
        """Löscht den gesamten Displayinhalt."""
        if not self.enabled:
            return
        self.treiber.loeschen()

    def clear_line(self, zeile):
        """
        Löscht eine einzelne Zeile, indem sie mit Leerzeichen überschrieben wird.

        Args:
            zeile: Die zu löschende Zeile (0-basiert)
        """
        if not self.enabled:
            return
        self.treiber.cursor_setzen(0, zeile)
        self.treiber.text_senden(" " * self.spalten)

    def home(self):
        """Setzt den Cursor auf Position (0,0) zurück."""
        if not self.enabled:
            return
        self.treiber.anfang()

    # ========================================================================
    # Display-Steuerung
    # ========================================================================

    def backlight(self, an=True):
        """
        Schaltet die Hintergrundbeleuchtung ein oder aus.

        Args:
            an: True = Licht an (Standard), False = Licht aus

        Beispiel:
            lcd.backlight(True)    # Licht an
            lcd.backlight(False)   # Licht aus
        """
        if not self.enabled:
            return

        if an:
            self.treiber._licht = _BIT_LICHT
        else:
            self.treiber._licht = 0x00
        # Aktuellen Zustand an den Portexpander senden
        self.treiber._port_schreiben(self.treiber._licht)

    def display(self, an=True):
        """
        Schaltet die Anzeige ein oder aus (Inhalt bleibt erhalten).

        Args:
            an: True = Display an (Standard), False = Display aus
        """
        if not self.enabled:
            return

        if an:
            self.treiber._anzeige |= _ANZEIGE_AN
        else:
            self.treiber._anzeige &= ~_ANZEIGE_AN
        self.treiber.befehl(_BEFEHL_ANZEIGE | self.treiber._anzeige)

    def cursor(self, an=True):
        """
        Zeigt oder verbirgt den Unterstrich-Cursor.

        Args:
            an: True = Cursor sichtbar, False = Cursor verborgen (Standard)
        """
        if not self.enabled:
            return

        if an:
            self.treiber._anzeige |= _CURSOR_AN
        else:
            self.treiber._anzeige &= ~_CURSOR_AN
        self.treiber.befehl(_BEFEHL_ANZEIGE | self.treiber._anzeige)

    def blink(self, an=True):
        """
        Aktiviert oder deaktiviert den blinkenden Block-Cursor.

        Args:
            an: True = Blinken an, False = Blinken aus (Standard)
        """
        if not self.enabled:
            return

        if an:
            self.treiber._anzeige |= _BLINKEN_AN
        else:
            self.treiber._anzeige &= ~_BLINKEN_AN
        self.treiber.befehl(_BEFEHL_ANZEIGE | self.treiber._anzeige)

    # ========================================================================
    # Scrollen
    # ========================================================================

    def scroll_links(self):
        """Verschiebt den gesamten Displayinhalt um eine Position nach links."""
        if not self.enabled:
            return
        self.treiber.befehl(_BEFEHL_VERSCHIEBEN | _DISPLAY_VERSCHIEBEN | _NACH_LINKS)

    def scroll_rechts(self):
        """Verschiebt den gesamten Displayinhalt um eine Position nach rechts."""
        if not self.enabled:
            return
        self.treiber.befehl(_BEFEHL_VERSCHIEBEN | _DISPLAY_VERSCHIEBEN | _NACH_RECHTS)

    # ========================================================================
    # Eigene Zeichen
    # ========================================================================

    def eigenes_zeichen(self, position, bitmap):
        """
        Speichert ein selbst definiertes Zeichen im CGRAM des LCD-Controllers.
        Es stehen 8 Speicherplätze (0-7) zur Verfügung.
        Jedes Zeichen besteht aus 8 Zeilen mit je 5 Pixeln.

        Args:
            position: Speicherplatz (0-7)
            bitmap: Liste/Tuple mit 8 Byte-Werten (je eine Zeile, 5 Bit breit)

        Beispiel:
            # Herz-Symbol definieren
            herz = [0b00000,
                     0b01010,
                     0b11111,
                     0b11111,
                     0b11111,
                     0b01110,
                     0b00100,
                     0b00000]
            lcd.eigenes_zeichen(0, herz)
            lcd.zeichen_schreiben(0, 5, 1)   # Herz an Position (5,1) anzeigen
        """
        if not self.enabled:
            return

        position &= 0x07   # Nur 8 Plätze (0-7) verfügbar
        self.treiber.befehl(_BEFEHL_CGRAM_ADRESSE | (position << 3))
        for zeile in bitmap:
            self.treiber.zeichen_senden(zeile)

    def zeichen_schreiben(self, position, spalte=0, zeile=0):
        """
        Zeigt ein zuvor gespeichertes eigenes Zeichen an.

        Args:
            position: Speicherplatz des Zeichens (0-7)
            spalte: Spalte (0-basiert)
            zeile: Zeile (0-basiert)
        """
        if not self.enabled:
            return

        self.treiber.cursor_setzen(spalte, zeile)
        self.treiber.zeichen_senden(position)

    # ========================================================================
    # Hilfsfunktionen (analog zur OLED-Bibliothek)
    # ========================================================================

    def map(self, wert, ein_min, ein_max, aus_min, aus_max):
        """
        Bildet einen Wert aus einem Eingabebereich auf einen Ausgabebereich ab.
        Nützlich für Sensordaten (z.B. ADC-Wert auf LCD-Spalten abbilden).

        Args:
            wert: Der abzubildende Wert
            ein_min: Minimaler Eingabewert
            ein_max: Maximaler Eingabewert
            aus_min: Minimaler Ausgabewert
            aus_max: Maximaler Ausgabewert

        Returns:
            Der abgebildete Ganzzahlwert

        Beispiel:
            # 12-Bit ADC (0-4095) auf Spalten (0-19) abbilden
            spalte = lcd.map(adc_wert, 0, 4095, 0, 19)
        """
        if wert < ein_min:
            wert = ein_min
        if wert > ein_max:
            wert = ein_max
        return int((wert - ein_min) * (aus_max - aus_min) / (ein_max - ein_min) + aus_min)

    def progress_bar(self, zeile, prozent):
        """
        Zeichnet einen textbasierten Fortschrittsbalken über die gesamte Zeilenbreite.
        Nutzt eigene Zeichen, um eine feingranulare Darstellung zu erreichen.

        Args:
            zeile: Zeile für den Balken (0-basiert)
            prozent: Fortschritt in Prozent (0-100)

        Beispiel:
            lcd.progress_bar(2, 75)   # 75% Fortschritt in Zeile 2
        """
        if not self.enabled:
            return

        if prozent < 0:
            prozent = 0
        if prozent > 100:
            prozent = 100

        # Eigene Balken-Zeichen für feinere Auflösung (5 Pixel pro Zeichen)
        # Zeichen 0: leer, 1: 1 Spalte, 2: 2 Spalten, ... 5: voll
        balken_bitmaps = [
            [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000],
            [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000],
            [0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000],
            [0b11100, 0b11100, 0b11100, 0b11100, 0b11100, 0b11100, 0b11100, 0b11100],
            [0b11110, 0b11110, 0b11110, 0b11110, 0b11110, 0b11110, 0b11110, 0b11110],
            [0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111],
        ]

        # Eigene Zeichen 0-5 für Balkensegmente laden
        for i in range(6):
            self.eigenes_zeichen(i, balken_bitmaps[i])

        # Gesamte Pixel berechnen (jede Spalte hat 5 Unter-Pixel)
        gesamt_pixel = self.spalten * 5
        gefuellt = int(prozent / 100.0 * gesamt_pixel)

        self.treiber.cursor_setzen(0, zeile)

        for s in range(self.spalten):
            pixel_fuer_spalte = gefuellt - s * 5
            if pixel_fuer_spalte >= 5:
                self.treiber.zeichen_senden(5)          # Volles Segment
            elif pixel_fuer_spalte > 0:
                self.treiber.zeichen_senden(pixel_fuer_spalte)  # Teilsegment
            else:
                self.treiber.zeichen_senden(0)          # Leeres Segment

    def draw_bar(self, zeile, spalte_start, breite, prozent):
        """
        Zeichnet einen einzelnen Balken ab einer bestimmten Spalte.
        Nützlich für nebeneinander liegende Balkenanzeigen.

        Args:
            zeile: Zeile (0-basiert)
            spalte_start: Startspalte (0-basiert)
            breite: Breite des Balkens in Spalten
            prozent: Füllgrad in Prozent (0-100)

        Beispiel:
            # Zwei Balken nebeneinander für Temperatur und Feuchte
            lcd.draw_bar(2, 0, 9, temp_prozent)
            lcd.draw_bar(2, 11, 9, feuchte_prozent)
        """
        if not self.enabled:
            return

        if prozent < 0:
            prozent = 0
        if prozent > 100:
            prozent = 100

        # Einfache Block-Darstellung mit Standard-Zeichen
        gefuellt = int(prozent / 100.0 * breite + 0.5)

        self.treiber.cursor_setzen(spalte_start, zeile)
        for s in range(breite):
            if s < gefuellt:
                self.treiber.zeichen_senden(0xFF)       # Voller Block
            else:
                self.treiber.zeichen_senden(0x5F)       # Unterstrich als "leer"


# ============================================================================
# Beispiel-Verwendung:
#
# lcd = LCD(scl=22, sda=21, addr=0x27)
#
# lcd.print("Hallo Welt!", 0, 0)
# lcd.print("Temperatur:", 0, 1)
# lcd.print("23.5 C", 0, 2)
# lcd.progress_bar(3, 75)
#
# # Eigenes Herz-Symbol:
# herz = [0b00000, 0b01010, 0b11111, 0b11111,
#          0b11111, 0b01110, 0b00100, 0b00000]
# lcd.eigenes_zeichen(0, herz)
# lcd.zeichen_schreiben(0, 10, 2)
# ============================================================================
