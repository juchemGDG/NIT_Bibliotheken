"""
Testprogramm für die Logo-Anzeige auf dem LCD-Display.

Testet verschiedene Ansätze, um das NIT-Logo (9×4 Zeichen)
korrekt auf dem HD44780 anzuzeigen.

Problem: Der HD44780 hat nur 8 CGRAM-Plätze für eigene Zeichen.
Das Logo braucht aber bis zu 8 verschiedene Zeichen PRO Zeile × 4 Zeilen.
Lösung: Das Logo wird in 4 Phasen angezeigt – jede Zeile einzeln,
da sich CGRAM-Änderungen sofort auf alle angezeigten Zeichen auswirken.

Volker Rust
03.2026
"""

from lcd import LCD
import time

# Logo beim Start deaktivieren, damit wir es manuell testen können
lcd = LCD(scl=22, sda=21, addr=0x27, logo=False, begruessung=False)

# ── Logo-Daten direkt aus der LCD-Klasse verwenden ──────────────
LOGO = LCD._LOGO

# HD44780 Befehle
_BEFEHL_CGRAM_ADRESSE = 0x40


def zeige_logo_zeilenweise():
    """
    Zeigt das Logo Zeile für Zeile – jede Zeile einzeln korrekt,
    vorherige Zeilen werden dabei gelöscht.
    So kann man prüfen, ob jede Zeile richtig aussieht.
    """
    lcd.clear()
    start_spalte = (lcd.spalten - 9) // 2

    for zeile in range(4):
        lcd.clear()
        # CGRAM mit den Zeichen dieser Zeile laden
        cgram_idx = 0
        zuordnung = {}
        for spalte in range(9):
            zeichendaten = LOGO[zeile][spalte]
            if any(b != 0 for b in zeichendaten):
                lcd.eigenes_zeichen(cgram_idx, zeichendaten)
                zuordnung[spalte] = cgram_idx
                cgram_idx += 1

        # Zeile anzeigen
        lcd.treiber.cursor_setzen(start_spalte, zeile)
        for spalte in range(9):
            if spalte in zuordnung:
                lcd.treiber.zeichen_senden(zuordnung[spalte])
            else:
                lcd.treiber.zeichen_senden(ord(' '))

        lcd.print(f"Zeile {zeile} ({cgram_idx} Zeichen)", 0, 3)
        time.sleep(2)


def zeige_logo_halbiert():
    """
    Zeigt das Logo in 2 Hälften:
    Phase 1: Zeilen 0+1 (obere Hälfte)
    Phase 2: Zeilen 2+3 (untere Hälfte)
    Jeweils max. 8 CGRAM-Zeichen für 2 Zeilen zusammen.
    """
    lcd.clear()
    start_spalte = (lcd.spalten - 9) // 2

    for phase in range(2):
        # Alle 8 CGRAM-Plätze für 2 Zeilen gemeinsam laden
        cgram_idx = 0
        zuordnung = {}  # (zeile, spalte) -> cgram_idx

        for zeile_offset in range(2):
            zeile = phase * 2 + zeile_offset
            for spalte in range(9):
                zeichendaten = LOGO[zeile][spalte]
                if any(b != 0 for b in zeichendaten):
                    if cgram_idx < 8:
                        lcd.eigenes_zeichen(cgram_idx, zeichendaten)
                        zuordnung[(zeile, spalte)] = cgram_idx
                        cgram_idx += 1

        # Beide Zeilen dieser Phase anzeigen
        for zeile_offset in range(2):
            zeile = phase * 2 + zeile_offset
            lcd.treiber.cursor_setzen(start_spalte, zeile)
            for spalte in range(9):
                if (zeile, spalte) in zuordnung:
                    lcd.treiber.zeichen_senden(zuordnung[(zeile, spalte)])
                else:
                    lcd.treiber.zeichen_senden(ord(' '))

        print(f"Phase {phase}: {cgram_idx} CGRAM-Zeichen benutzt")

    time.sleep(3)


def zaehle_zeichen():
    """Zählt nicht-leere Zeichen pro Zeile und gesamt."""
    print("=== Logo-Analyse ===")
    gesamt = 0
    for zeile in range(4):
        anzahl = sum(1 for s in range(9) if any(b != 0 for b in LOGO[zeile][s]))
        gesamt += anzahl
        print(f"Zeile {zeile}: {anzahl} nicht-leere Zeichen")
    print(f"Gesamt: {gesamt} Zeichen (max 8 pro Phase)")
    print()

    # Prüfe ob 2 Zeilen zusammen in 8 CGRAM passen
    for phase in range(2):
        z0 = phase * 2
        z1 = phase * 2 + 1
        n0 = sum(1 for s in range(9) if any(b != 0 for b in LOGO[z0][s]))
        n1 = sum(1 for s in range(9) if any(b != 0 for b in LOGO[z1][s]))
        print(f"Phase {phase} (Zeile {z0}+{z1}): {n0}+{n1} = {n0+n1} Zeichen", end="")
        print(" ✓" if n0 + n1 <= 8 else " ✗ ZU VIELE!")


# ── Hauptprogramm ──────────────────────────────────────────────
print("=== Logo-Test ===")
print()

# 1) Analyse: Wieviele Zeichen brauchen wir?
zaehle_zeichen()
print()

# 2) Jede Zeile einzeln testen
print("--- Test 1: Zeile für Zeile ---")
zeige_logo_zeilenweise()

# 3) Logo in 2 Hälften
print("--- Test 2: Obere + untere Hälfte ---")
zeige_logo_halbiert()

lcd.clear()
lcd.print_center("Logo-Test Ende", 1)
