"""
NIT Bibliothek: SVG -> 1-Bit-Bitmap Konverter (laeuft auf dem PC, NICHT auf dem ESP32)

Wandelt eine SVG-Datei in ein MONO_VLSB-Bytearray (gleiches Format wie LOGO_PBM
in nitbw_oled.py) und erzeugt eine fertige .py-Datei, die auf den ESP32 kopiert
und mit oled.show_image(...) angezeigt werden kann.

Benoetigt EINMALIG auf dem PC (kein venv noetig):
    pip3 install --user cairosvg pillow
    (macOS zusaetzlich: brew install cairo)

------------------------------------------------------------------------------
VIER WEGE, DEN KONVERTER ZU NUTZEN
------------------------------------------------------------------------------
1) GUI (einfach per Doppelklick, kein Terminal, keine Einstellungen):
   Datei 'svg_zu_bitmap.py' doppelklicken (macOS/Windows) oder in Python-Editor
   mit "Run" starten. Datei-Dialog oeffnet sich -> SVG auswaehlen -> fertig.
   ASCII-Vorschau zeigt das Ergebnis sofort im Fenster.

2) Editor / "Run"-Button (kein Terminal, aber manuelle Einstellungen):
   Unten im Abschnitt "EINSTELLUNGEN" die SVG-Datei eintragen und die Datei
   einfach ausfuehren (gruener Pfeil in VS Code / Thonny / IDLE / Mu).

3) Als Funktion in einem eigenen Skript oder in der Python-Konsole:
       from svg_zu_bitmap import konvertiere
       konvertiere("bild1.svg")                       # -> bild1_bitmap.py
       konvertiere("bild1.svg", invert=True, vorschau=True)

4) Klassische Kommandozeile:
       python3 svg_zu_bitmap.py bild1.svg
       python3 svg_zu_bitmap.py bild1.svg -W 64 -H 64 --invert

Auf dem ESP32:
    oled.show_image('bild1_bitmap')   # Modulname genuegt (v1.4.0+)
    oled.show()
"""

import io
import os


# ==============================================================================
# EINSTELLUNGEN  ->  hier anpassen und die Datei einfach ausfuehren ("Run")
# ==============================================================================
EINGABE  = "bild1.svg"   # Pfad zur SVG-Datei
BREITE   = 128           # Zielbreite in Pixeln (Display: 128)
HOEHE    = 64            # Zielhoehe in Pixeln (Display: 64 oder 32)
INVERT   = False         # True = hell/dunkel tauschen
VORSCHAU = True          # True = ASCII-Vorschau im Editor anzeigen
AUSGABE  = None          # None = <name>_bitmap.py, sonst eigener Dateiname
NAME     = "BITMAP"      # Variablenname in der erzeugten .py-Datei
# ==============================================================================


def svg_zu_mono(svg_pfad, breite=128, hoehe=64, schwelle=128, invert=False):
    """
    Rendert eine SVG und gibt das Bild als MONO_VLSB-bytearray zurueck.

    Reine Funktion ohne Datei-Ausgabe - praktisch, um das Ergebnis direkt
    weiterzuverarbeiten.

    Args:
        svg_pfad: Pfad zur SVG-Datei
        breite, hoehe: Zielgroesse in Pixeln
        schwelle: Helligkeits-Schwellwert 0-255 (dunkler -> "an")
        invert: True tauscht hell/dunkel

    Returns:
        bytearray im MONO_VLSB-Format (breite*hoehe/8 Bytes)
    """
    gray = _render_svg(svg_pfad, breite, hoehe)
    return _image_to_mono_vlsb(gray, schwelle, invert)


def konvertiere(eingabe, breite=128, hoehe=64, ausgabe=None, name="BITMAP",
                schwelle=128, invert=False, vorschau=False):
    """
    Konvertiert eine SVG in eine fertige .py-Datei fuer oled.show_image().

    Args:
        eingabe: Pfad zur SVG-Datei
        breite, hoehe: Zielgroesse in Pixeln
        ausgabe: Ausgabedatei; None = <name>_bitmap.py neben der SVG
        name: Variablenname in der erzeugten Datei (Standard: BITMAP)
        schwelle: Helligkeits-Schwellwert 0-255
        invert: True tauscht hell/dunkel
        vorschau: True gibt eine ASCII-Vorschau aus

    Returns:
        Pfad der erzeugten .py-Datei
    """
    buf = svg_zu_mono(eingabe, breite, hoehe, schwelle, invert)

    out = ausgabe or (os.path.splitext(os.path.basename(eingabe))[0] + "_bitmap.py")
    literal = _format_bytearray(buf)

    with open(out, "w") as f:
        f.write('"""Erzeugt aus %s mit svg_zu_bitmap.py (MONO_VLSB)."""\n\n'
                % os.path.basename(eingabe))
        f.write("WIDTH = %d\n" % breite)
        f.write("HEIGHT = %d\n\n" % hoehe)
        f.write("%s = (\n%s\n)\n" % (name, literal))

    if vorschau:
        print(ascii_vorschau(buf, breite, hoehe))

    modul = os.path.splitext(os.path.basename(out))[0]
    print("OK: %s  (%dx%d, %d Bytes)" % (out, breite, hoehe, len(buf)))
    print("Auf dem ESP32:")
    print("    from %s import %s, WIDTH, HEIGHT" % (modul, name))
    print("    oled.show_image(%s, 0, 0, WIDTH, HEIGHT); oled.show()" % name)
    return out


def ascii_vorschau(buf, breite, hoehe):
    """Gibt eine grobe Textvorschau des MONO_VLSB-Bitmaps zurueck."""
    def pixel(x, y):
        return (buf[(y // 8) * breite + x] >> (y % 8)) & 1
    zeilen = []
    for y in range(0, hoehe, 2):          # je 2 Zeilen/Spalten zusammenfassen
        zeilen.append("".join("#" if pixel(x, y) else " "
                              for x in range(0, breite, 2)))
    return "\n".join(zeilen)


# ---------------------------------------------------------------------------
# interne Helfer
# ---------------------------------------------------------------------------

def _render_svg(svg_pfad, breite, hoehe):
    """Rendert die SVG auf weissem Hintergrund und gibt ein L-Mode-PIL-Image."""
    try:
        import cairosvg
    except ImportError:
        raise SystemExit(
            "Fehler: 'cairosvg' fehlt.\n"
            "  Installieren: pip3 install --user cairosvg pillow\n"
            "  macOS zusaetzlich: brew install cairo")
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit(
            "Fehler: 'Pillow' fehlt.\n"
            "  Installieren: pip3 install --user pillow")

    if not os.path.exists(svg_pfad):
        raise SystemExit("Fehler: SVG-Datei nicht gefunden: %s" % svg_pfad)

    png_bytes = cairosvg.svg2png(url=svg_pfad, output_width=breite, output_height=hoehe)
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    # Transparenz auf weissem Hintergrund zusammenfuehren
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    bg.alpha_composite(img)
    return bg.convert("L")


def _image_to_mono_vlsb(gray, schwelle, invert):
    """Konvertiert ein L-Mode-PIL-Image in ein MONO_VLSB-Bytearray."""
    w, h = gray.size
    px = gray.load()
    pages = (h + 7) // 8
    buf = bytearray(pages * w)
    for page in range(pages):
        for x in range(w):
            b = 0
            for bit in range(8):
                yy = page * 8 + bit
                if yy < h:
                    on = px[x, yy] < schwelle  # dunkel = an
                    if invert:
                        on = not on
                    if on:
                        b |= (1 << bit)
            buf[page * w + x] = b
    return buf


def _format_bytearray(buf, per_line=16):
    """Formatiert das Bytearray als b'...'-Literal-Bloecke (wie LOGO_PBM)."""
    lines = []
    for i in range(0, len(buf), per_line):
        chunk = buf[i:i + per_line]
        body = "".join("\\x%02x" % byte for byte in chunk)
        lines.append("    b'%s'" % body)
    return "\n".join(lines)


def _cli():
    """Klassische Kommandozeilen-Schnittstelle (optional)."""
    import argparse
    ap = argparse.ArgumentParser(description="SVG -> MONO_VLSB Bitmap fuer nitbw_oled")
    ap.add_argument("svg", help="Pfad zur SVG-Datei")
    ap.add_argument("-W", "--width", type=int, default=128, help="Breite (Standard: 128)")
    ap.add_argument("-H", "--height", type=int, default=64, help="Hoehe (Standard: 64)")
    ap.add_argument("-t", "--threshold", type=int, default=128, help="Schwellwert 0-255")
    ap.add_argument("--invert", action="store_true", help="Hell/Dunkel tauschen")
    ap.add_argument("--vorschau", action="store_true", help="ASCII-Vorschau zeigen")
    ap.add_argument("-o", "--output", help="Ausgabedatei (Standard: <name>_bitmap.py)")
    ap.add_argument("-n", "--name", default="BITMAP", help="Variablenname (Standard: BITMAP)")
    args = ap.parse_args()
    konvertiere(args.svg, args.width, args.height, ausgabe=args.output,
                name=args.name, schwelle=args.threshold, invert=args.invert,
                vorschau=args.vorschau)


def _gui():
    """Einfache GUI (Datei-Dialog) fuer Schueler ohne Terminal-Erfahrung."""
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except ImportError:
        print("tkinter fehlt (sollte in Standard-Python enthalten sein).")
        return

    root = tk.Tk()
    root.title("SVG -> OLED Bitmap Konverter")
    root.geometry("500x400")

    # Status-Label
    status = tk.StringVar(value="SVG-Datei auswaehlen...")
    tk.Label(root, textvariable=status, wraplength=450, justify="left", height=3).pack(pady=10)

    # Vorschau-Textfeld
    vorschau_text = tk.Text(root, height=12, width=64, font=("Courier", 8))
    vorschau_text.pack(pady=10)

    # Einstellungen
    frame_opts = tk.Frame(root)
    frame_opts.pack(pady=5)
    var_invert = tk.BooleanVar(value=False)
    tk.Checkbutton(frame_opts, text="Hell/Dunkel tauschen", variable=var_invert).pack(side="left", padx=5)
    var_breite = tk.IntVar(value=128)
    var_hoehe = tk.IntVar(value=64)
    tk.Label(frame_opts, text="Breite:").pack(side="left")
    tk.Entry(frame_opts, textvariable=var_breite, width=5).pack(side="left", padx=2)
    tk.Label(frame_opts, text="Hoehe:").pack(side="left")
    tk.Entry(frame_opts, textvariable=var_hoehe, width=5).pack(side="left", padx=2)

    def datei_waehlen():
        pfad = filedialog.askopenfilename(
            title="SVG-Datei auswaehlen",
            filetypes=[("SVG-Dateien", "*.svg"), ("Alle Dateien", "*.*")])
        if not pfad:
            return
        status.set("Konvertiere " + os.path.basename(pfad) + " ...")
        root.update()
        try:
            buf = svg_zu_mono(pfad, var_breite.get(), var_hoehe.get(), invert=var_invert.get())
            ausgabe = os.path.splitext(os.path.basename(pfad))[0] + "_bitmap.py"
            ausgabe = os.path.join(os.path.dirname(pfad), ausgabe)
            literal = _format_bytearray(buf)
            with open(ausgabe, "w") as f:
                f.write('"""Erzeugt aus %s mit svg_zu_bitmap.py (MONO_VLSB)."""\n\n'
                        % os.path.basename(pfad))
                f.write("WIDTH = %d\n" % var_breite.get())
                f.write("HEIGHT = %d\n\n" % var_hoehe.get())
                f.write("BITMAP = (\n%s\n)\n" % literal)
            # ASCII-Vorschau
            vorschau_text.delete("1.0", "end")
            vorschau_text.insert("1.0", ascii_vorschau(buf, var_breite.get(), var_hoehe.get()))
            status.set("Fertig: " + ausgabe + "\nAuf den ESP32 kopieren und mit oled.show_image('" +
                       os.path.splitext(os.path.basename(ausgabe))[0] + "') anzeigen.")
            messagebox.showinfo("Fertig", "Datei erzeugt:\n" + ausgabe)
        except Exception as e:
            status.set("Fehler: " + str(e))
            messagebox.showerror("Fehler", str(e))

    tk.Button(root, text="SVG-Datei waehlen und konvertieren", command=datei_waehlen, height=2).pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Mit Argumenten -> Kommandozeilen-Modus
        _cli()
    else:
        # Ohne Argumente (z.B. Doppelklick/Run) -> GUI starten
        try:
            _gui()
        except Exception:
            # Falls tkinter fehlt/nicht anzeigbar -> Fallback auf EINSTELLUNGEN
            konvertiere(EINGABE, BREITE, HOEHE, ausgabe=AUSGABE, name=NAME,
                        invert=INVERT, vorschau=VORSCHAU)
