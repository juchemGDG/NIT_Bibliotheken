"""
NIT Bibliothek: SVG -> 1-Bit-Bitmap Konverter (laeuft auf dem PC, NICHT auf dem ESP32)

Wandelt eine SVG-Datei in ein MONO_VLSB-Bytearray (gleiches Format wie LOGO_PBM
in nitbw_oled.py) und erzeugt eine fertige .py-Datei, die auf den ESP32 kopiert
und mit oled.show_image(...) angezeigt werden kann.

Benoetigt (nur auf dem PC):
    pip install cairosvg pillow

Verwendung:
    python svg_zu_bitmap.py icon.svg                 # -> icon_bitmap.py (128x64)
    python svg_zu_bitmap.py icon.svg -W 64 -H 64     # andere Groesse
    python svg_zu_bitmap.py icon.svg --invert        # hell/dunkel tauschen
    python svg_zu_bitmap.py icon.svg -o logo.py -n LOGO

Auf dem ESP32:
    from icon_bitmap import BITMAP, WIDTH, HEIGHT
    oled.show_image(BITMAP, 0, 0, WIDTH, HEIGHT)
    oled.show()
"""

import argparse
import io
import os
import sys


def render_svg_to_image(svg_path, width, height):
    """Rendert die SVG auf weissem Hintergrund und gibt ein 1-Bit-PIL-Image zurueck."""
    try:
        import cairosvg
    except ImportError:
        sys.exit("Fehler: 'cairosvg' fehlt. Installieren mit: pip install cairosvg pillow")
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Fehler: 'Pillow' fehlt. Installieren mit: pip install pillow")

    png_bytes = cairosvg.svg2png(url=svg_path, output_width=width, output_height=height)
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")

    # Auf weissem Hintergrund zusammenfuehren (Transparenz -> weiss)
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    bg.alpha_composite(img)
    gray = bg.convert("L")
    # Schwellwert: dunkle Pixel werden zu "an" (1)
    return gray


def image_to_mono_vlsb(gray, threshold, invert):
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
                    on = px[x, yy] < threshold  # dunkel = an
                    if invert:
                        on = not on
                    if on:
                        b |= (1 << bit)
            buf[page * w + x] = b
    return buf


def format_bytearray(buf, per_line=16):
    """Formatiert das Bytearray als b'...'-Literal-Bloecke (wie LOGO_PBM)."""
    lines = []
    for i in range(0, len(buf), per_line):
        chunk = buf[i:i + per_line]
        body = "".join("\\x%02x" % byte for byte in chunk)
        lines.append("    b'%s'" % body)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="SVG -> MONO_VLSB Bitmap fuer nitbw_oled")
    ap.add_argument("svg", help="Pfad zur SVG-Datei")
    ap.add_argument("-W", "--width", type=int, default=128, help="Breite in Pixeln (Standard: 128)")
    ap.add_argument("-H", "--height", type=int, default=64, help="Hoehe in Pixeln (Standard: 64)")
    ap.add_argument("-t", "--threshold", type=int, default=128, help="Schwellwert 0-255 (Standard: 128)")
    ap.add_argument("--invert", action="store_true", help="Hell/Dunkel tauschen")
    ap.add_argument("-o", "--output", help="Ausgabedatei (Standard: <name>_bitmap.py)")
    ap.add_argument("-n", "--name", default="BITMAP", help="Variablenname (Standard: BITMAP)")
    args = ap.parse_args()

    gray = render_svg_to_image(args.svg, args.width, args.height)
    buf = image_to_mono_vlsb(gray, args.threshold, args.invert)

    out = args.output or (os.path.splitext(os.path.basename(args.svg))[0] + "_bitmap.py")
    literal = format_bytearray(buf)

    with open(out, "w") as f:
        f.write('"""Erzeugt aus %s mit svg_zu_bitmap.py (MONO_VLSB)."""\n\n' % os.path.basename(args.svg))
        f.write("WIDTH = %d\n" % args.width)
        f.write("HEIGHT = %d\n\n" % args.height)
        f.write("%s = (\n%s\n)\n" % (args.name, literal))

    print("OK: %s  (%dx%d, %d Bytes)" % (out, args.width, args.height, len(buf)))
    print("Auf dem ESP32:")
    print("    from %s import %s, WIDTH, HEIGHT" % (os.path.splitext(os.path.basename(out))[0], args.name))
    print("    oled.show_image(%s, 0, 0, WIDTH, HEIGHT); oled.show()" % args.name)


if __name__ == "__main__":
    main()
