"""
NIT Bibliothek: OLED - Grafiktreiber fuer SSD1306 und SH1106 Displays
Fuer ESP32 mit MicroPython

Version:    1.1.0
Autor:      Stephan Juchem
Lizenz:     MIT (siehe LICENSE)
Erstellt:   2026-03

Umfangreiche Grafikfunktionen inkl. Text, Linien, Kreise und Balkenanzeigen.
Treiber und Fontdaten sind direkt im Modul enthalten, ohne externe Abhaengigkeiten.
"""

from machine import I2C, Pin
import time
import framebuf

# Integrierte serifenfreie 5x7 Bitmap-Font
FONT_SANS_WIDTH = 5
FONT_SANS_HEIGHT = 7
FONT_SANS = {
    ' ': ('00000', '00000', '00000', '00000', '00000', '00000', '00000'),
    '.': ('00000', '00000', '00000', '00000', '00000', '01100', '01100'),
    ',': ('00000', '00000', '00000', '00000', '00110', '00110', '01100'),
    ':': ('00000', '01100', '01100', '00000', '01100', '01100', '00000'),
    '-': ('00000', '00000', '00000', '11111', '00000', '00000', '00000'),
    '!': ('00100', '00100', '00100', '00100', '00100', '00000', '00100'),
    '?': ('01110', '10001', '00001', '00010', '00100', '00000', '00100'),
    '/': ('00001', '00010', '00100', '01000', '10000', '00000', '00000'),
    '(': ('00010', '00100', '01000', '01000', '01000', '00100', '00010'),
    ')': ('01000', '00100', '00010', '00010', '00010', '00100', '01000'),
    '+': ('00000', '00100', '00100', '11111', '00100', '00100', '00000'),
    '*': ('00000', '10101', '01110', '11111', '01110', '10101', '00000'),
    '$': ('00100', '01111', '10100', '01110', '00101', '11110', '00100'),
    '&': ('01100', '10010', '10100', '01000', '10101', '10010', '01101'),
    '°': ('00100', '01010', '00100', '00000', '00000', '00000', '00000'),
    '€': ('00111', '01000', '11110', '01000', '11110', '01000', '00111'),
    '0': ('01110', '10001', '10011', '10101', '11001', '10001', '01110'),
    '1': ('00100', '01100', '00100', '00100', '00100', '00100', '01110'),
    '2': ('01110', '10001', '00001', '00010', '00100', '01000', '11111'),
    '3': ('11110', '00001', '00001', '01110', '00001', '00001', '11110'),
    '4': ('00010', '00110', '01010', '10010', '11111', '00010', '00010'),
    '5': ('11111', '10000', '10000', '11110', '00001', '00001', '11110'),
    '6': ('01110', '10000', '10000', '11110', '10001', '10001', '01110'),
    '7': ('11111', '00001', '00010', '00100', '01000', '01000', '01000'),
    '8': ('01110', '10001', '10001', '01110', '10001', '10001', '01110'),
    '9': ('01110', '10001', '10001', '01111', '00001', '00001', '01110'),
    'A': ('01110', '10001', '10001', '11111', '10001', '10001', '10001'),
    'B': ('11110', '10001', '10001', '11110', '10001', '10001', '11110'),
    'C': ('01111', '10000', '10000', '10000', '10000', '10000', '01111'),
    'D': ('11110', '10001', '10001', '10001', '10001', '10001', '11110'),
    'E': ('11111', '10000', '10000', '11110', '10000', '10000', '11111'),
    'F': ('11111', '10000', '10000', '11110', '10000', '10000', '10000'),
    'G': ('01111', '10000', '10000', '10111', '10001', '10001', '01111'),
    'H': ('10001', '10001', '10001', '11111', '10001', '10001', '10001'),
    'I': ('01110', '00100', '00100', '00100', '00100', '00100', '01110'),
    'J': ('00001', '00001', '00001', '00001', '10001', '10001', '01110'),
    'K': ('10001', '10010', '10100', '11000', '10100', '10010', '10001'),
    'L': ('10000', '10000', '10000', '10000', '10000', '10000', '11111'),
    'M': ('10001', '11011', '10101', '10101', '10001', '10001', '10001'),
    'N': ('10001', '10001', '11001', '10101', '10011', '10001', '10001'),
    'O': ('01110', '10001', '10001', '10001', '10001', '10001', '01110'),
    'P': ('11110', '10001', '10001', '11110', '10000', '10000', '10000'),
    'Q': ('01110', '10001', '10001', '10001', '10101', '10010', '01101'),
    'R': ('11110', '10001', '10001', '11110', '10100', '10010', '10001'),
    'S': ('01111', '10000', '10000', '01110', '00001', '00001', '11110'),
    'T': ('11111', '00100', '00100', '00100', '00100', '00100', '00100'),
    'U': ('10001', '10001', '10001', '10001', '10001', '10001', '01110'),
    'V': ('10001', '10001', '10001', '10001', '10001', '01010', '00100'),
    'W': ('10001', '10001', '10001', '10101', '10101', '11011', '10001'),
    'X': ('10001', '10001', '01010', '00100', '01010', '10001', '10001'),
    'Y': ('10001', '10001', '01010', '00100', '00100', '00100', '00100'),
    'Z': ('11111', '00001', '00010', '00100', '01000', '10000', '11111'),
    'Ä': ('01010', '00000', '01110', '10001', '11111', '10001', '10001'),
    'Ö': ('01010', '00000', '01110', '10001', '10001', '10001', '01110'),
    'Ü': ('01010', '00000', '10001', '10001', '10001', '10001', '01110'),
    'a': ('00000', '00000', '01110', '00001', '01111', '10001', '01111'),
    'b': ('10000', '10000', '11110', '10001', '10001', '10001', '11110'),
    'c': ('00000', '00000', '01111', '10000', '10000', '10000', '01111'),
    'd': ('00001', '00001', '01111', '10001', '10001', '10001', '01111'),
    'e': ('00000', '00000', '01110', '10001', '11111', '10000', '01111'),
    'f': ('00110', '01000', '11110', '01000', '01000', '01000', '01000'),
    'g': ('00000', '00000', '01111', '10001', '10001', '01111', '00001'),
    'h': ('10000', '10000', '11110', '10001', '10001', '10001', '10001'),
    'i': ('00100', '00000', '00100', '00100', '00100', '00100', '00110'),
    'j': ('00010', '00000', '00010', '00010', '00010', '10010', '01100'),
    'k': ('10000', '10000', '10010', '10100', '11000', '10100', '10010'),
    'l': ('00100', '00100', '00100', '00100', '00100', '00100', '00110'),
    'm': ('00000', '00000', '11010', '10101', '10101', '10001', '10001'),
    'n': ('00000', '00000', '11110', '10001', '10001', '10001', '10001'),
    'o': ('00000', '00000', '01110', '10001', '10001', '10001', '01110'),
    'p': ('00000', '00000', '11110', '10001', '10001', '11110', '10000'),
    'q': ('00000', '00000', '01111', '10001', '10001', '01111', '00001'),
    'r': ('00000', '00000', '11110', '10001', '10000', '10000', '10000'),
    's': ('00000', '00000', '01111', '10000', '01110', '00001', '11110'),
    't': ('00100', '00100', '01110', '00100', '00100', '00100', '00011'),
    'u': ('00000', '00000', '10001', '10001', '10001', '10001', '01111'),
    'v': ('00000', '00000', '10001', '10001', '10001', '01010', '00100'),
    'w': ('00000', '00000', '10001', '10101', '10101', '10101', '01010'),
    'x': ('00000', '00000', '10001', '01010', '00100', '01010', '10001'),
    'y': ('00000', '00000', '10001', '10001', '10001', '01111', '00001'),
    'z': ('00000', '00000', '11111', '00010', '00100', '01000', '11111'),
    'ä': ('01010', '00000', '01110', '00001', '01111', '10001', '01111'),
    'ö': ('01010', '00000', '01110', '10001', '10001', '10001', '01110'),
    'ü': ('01010', '00000', '10001', '10001', '10001', '10001', '01111'),
    'ß': ('01110', '10001', '10010', '10100', '10010', '10001', '10110'),
}


# SSD1306/SH1106 Register-Befehle
# Fundamental Commands
SET_CONTRAST = 0x81
SET_ENTIRE_ON = 0xA4
SET_NORM_INV = 0xA6
SET_DISP = 0xAE
SET_MEM_ADDR = 0x20
SET_COL_ADDR = 0x21
SET_PAGE_ADDR = 0x22
SET_DISP_START_LINE = 0x40
SET_SEG_REMAP = 0xA0
SET_MUX_RATIO = 0xA8
SET_COM_OUT_DIR = 0xC0
SET_DISP_OFFSET = 0xD3
SET_COM_PIN_CFG = 0xDA
SET_DISP_CLK_DIV = 0xD5
SET_PRECHARGE = 0xD9
SET_VCOM_DESEL = 0xDB
SET_CHARGE_PUMP = 0x8D


class DisplayDriver:
    """Basis-Treiber für SSD1306 und SH1106"""
    
    def __init__(self, width, height, i2c, addr=0x3c):
        self.i2c = i2c
        self.addr = addr
        self.width = width
        self.height = height
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.poweron()
        self.init_display()
    
    def init_display(self):
        """Initialisiert das Display - muss in Unterklasse implementiert werden"""
        pass
    
    def poweroff(self):
        """Schaltet das Display aus"""
        self.write_cmd(SET_DISP | 0x00)
    
    def poweron(self):
        """Schaltet das Display ein"""
        self.write_cmd(SET_DISP | 0x01)
    
    def contrast(self, contrast):
        """Setzt den Kontrast (0-255)"""
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)
    
    def invert(self, invert):
        """Invertiert die Anzeige"""
        self.write_cmd(SET_NORM_INV | (invert & 1))
    
    def write_cmd(self, cmd):
        """Sendet einen Befehl an das Display"""
        self.i2c.writeto(self.addr, bytearray([0x80, cmd]))
    
    def write_data(self, buf):
        """Sendet Daten an das Display"""
        self.i2c.writeto(self.addr, b'\x40' + buf)
    
    def show(self):
        """Aktualisiert das Display - muss in Unterklasse implementiert werden"""
        pass
    
    # FrameBuffer-Methoden delegieren
    def fill(self, col):
        self.framebuf.fill(col)
    
    def pixel(self, x, y, col=None):
        if col is None:
            return self.framebuf.pixel(x, y)
        self.framebuf.pixel(x, y, col)
    
    def hline(self, x, y, w, col):
        self.framebuf.hline(x, y, w, col)
    
    def vline(self, x, y, h, col):
        self.framebuf.vline(x, y, h, col)
    
    def line(self, x1, y1, x2, y2, col):
        self.framebuf.line(x1, y1, x2, y2, col)
    
    def rect(self, x, y, w, h, col):
        self.framebuf.rect(x, y, w, h, col)
    
    def fill_rect(self, x, y, w, h, col):
        self.framebuf.fill_rect(x, y, w, h, col)
    
    def text(self, string, x, y, col=1):
        self.framebuf.text(string, x, y, col)
    
    def blit(self, fbuf, x, y):
        self.framebuf.blit(fbuf, x, y)
    
    def scroll(self, dx, dy):
        self.framebuf.scroll(dx, dy)


class SSD1306(DisplayDriver):
    """SSD1306 OLED Treiber"""
    
    def init_display(self):
        """Initialisiert das SSD1306 Display"""
        for cmd in (
            SET_DISP | 0x00,  # Display aus
            SET_MEM_ADDR, 0x00,  # Horizontal addressing mode
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,  # Column addr 127 mapped to SEG0
            SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08,  # Scan from COM[N-1] to COM0
            SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x12 if self.height == 64 else 0x02,
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0xF1,
            SET_VCOM_DESEL, 0x30,
            SET_CONTRAST, 0xFF,
            SET_ENTIRE_ON,  # Output follows RAM contents
            SET_NORM_INV,  # Not inverted
            SET_CHARGE_PUMP, 0x14,  # Enable charge pump
            SET_DISP | 0x01  # Display ein
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()
    
    def show(self):
        """Sendet den Framebuffer an das Display"""
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.width - 1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)


class SH1106(DisplayDriver):
    """SH1106 OLED Treiber"""
    
    def init_display(self):
        """Initialisiert das SH1106 Display"""
        for cmd in (
            SET_DISP | 0x00,  # Display aus
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,  # Column addr 127 mapped to SEG0
            SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08,  # Scan from COM[N-1] to COM0
            SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x12 if self.height == 64 else 0x02,
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0x22,
            SET_VCOM_DESEL, 0x35,
            SET_CONTRAST, 0xFF,
            SET_ENTIRE_ON,  # Output follows RAM contents
            SET_NORM_INV,  # Not inverted
            0xAD, 0x8B,  # Enable charge pump (SH1106-spezifisch)
            SET_DISP | 0x01  # Display ein
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()
    
    def show(self):
        """Sendet den Framebuffer an das Display (page by page für SH1106)"""
        for page in range(self.pages):
            # Setze Spaltenadresse (SH1106 hat einen Offset von 2)
            self.write_cmd(0x02 & 0x0F)  # Lower column address
            self.write_cmd(0x10 | (0x02 >> 4))  # Higher column address
            # Setze Page-Adresse
            self.write_cmd(0xB0 | page)
            # Sende Daten für diese Page
            start = page * self.width
            end = start + self.width
            self.write_data(self.buffer[start:end])

class OLED:
    """
    Stellt eine einfache API fuer Text- und Grafikdarstellung auf OLED bereit.

    Unterstuetzte Hardware:
    - SSD1306 OLED 128x64
    - SH1106 OLED 128x64

    Schnittstelle: I2C
    """

    # INIT Logo als Binärdaten im MONO_VLSB Format (128x64 Pixel)
    # Zeigt "INIT" Text zentriert auf dem Display
    LOGO_PBM = (
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0'
        b'\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0'
        b'\xe0\xe0\xe0\xf0\xf0\xf0\xf0\xf0\xf0\xf0\xf0\x70\x30\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x3f\xff\xff\xff\xff\xff\xff\xff\xff\xff\x07\x07\x07\x03\x03\x03'
        b'\x03\x03\x03\xc3\xc3\xc3\xc3\xc3\xc3\xc1\xc1\xc1\xc1\xc1\xc1\xc1'
        b'\x81\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc0'
        b'\xc0\xc0\xc0\xe0\xe0\xe0\xe0\xe0\xe0\x60\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xf0\xf0\xf0\x70'
        b'\x70\x60\x00\x00\x00\x00\x00\x00\xf0\xf0\xf0\xf0\xf0\xf0\xf0\xf0'
        b'\xf0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0'
        b'\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\xe0\x00\x00\x00\x00\x00'
        b'\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfc\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\x1f\x3f\xff\xff'
        b'\xff\xff\xfe\xfc\xf8\xf0\xe0\xc0\x80\x00\x00\x00\x80\xf8\xff\xff'
        b'\xff\xff\xff\xff\xff\xff\x7f\x1f\x03\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\xc0\xff\xff\xff\xff\xff\xff\xff\x3f\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x03'
        b'\x03\xff\xff\xff\xff\xff\xff\xff\xff\xff\x83\x03\x03\x03\x03\x03'
        b'\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x00\x00\x00\x00\x00\x00'
        b'\x00\x03\x07\x03\x03\x03\x03\x03\x03\x01\x01\x00\x00\x00\x00\x00'
        b'\x00\x00\xfc\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfc\x00\x00\x01'
        b'\x07\x0f\x1f\x7f\xff\xff\xff\xff\xff\xfe\xfc\xfc\xff\xff\xff\xff'
        b'\xff\xff\xff\x7f\x1f\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\x3f\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x80\xfe\xfe\xfe\xfc\xfc\xfc\xfc\xfc\x1c'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x03\x03\x03\x03\x07\x07\x07\x07\x07\x07\x0f\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x03\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07'
        b'\x07\x07\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0'
        b'\xc0\xc7\xc7\xc7\xc7\xc7\xc7\xc7\xc7\xc7\xc7\xc0\xc0\xc0\xc0\xc0'
        b'\xc0\xc0\xc0\xc0\xc0\xc0\xff\xff\xff\xff\xff\xff\xff\x7f\x03\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x08\x0e\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f'
        b'\x0f\x0f\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07'
        b'\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x07\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    )
    
    def __init__(self, scl=22, sda=21, chip='ssd1306', enabled=True, i2c_id=0, addr=0x3c, logo=True):
        """
        Initialisiert das OLED Display
        
        Args:
            scl: SCL Pin (Standard: GPIO 22)
            sda: SDA Pin (Standard: GPIO 21)
            chip: 'ssd1306' oder 'sh1106' (Standard: 'ssd1306')
            enabled: True um Display zu aktivieren, False um zu deaktivieren
            i2c_id: I2C Bus ID (Standard: 0)
            addr: I2C Adresse des Displays (Standard: 0x3c)
            logo: True zeigt das Startlogo, False deaktiviert es (Standard: True)
        """
        self.width = 128
        self.height = 64
        self.enabled = enabled
        self.chip = chip.lower()
        self.logo = bool(logo)
        
        if not self.enabled:
            self.display = None
            return
        
        # I2C initialisieren
        self.i2c = I2C(i2c_id, scl=Pin(scl), sda=Pin(sda), freq=400000)
        
        # Display-Treiber initialisieren
        if self.chip == 'sh1106':
            self.display = SH1106(self.width, self.height, self.i2c, addr=addr)
        else:
            self.display = SSD1306(self.width, self.height, self.i2c, addr=addr)
        
        # Logo beim Start anzeigen
        if self.logo:
            self._show_logo()
    
    def _show_logo(self):
        """Zeigt das INIT Logo für 2 Sekunden"""
        if not self.enabled:
            return
        
        # Option 1: Logo aus Binärdaten laden
        if len(self.LOGO_PBM) == self.width * self.height // 8:
            fb = framebuf.FrameBuffer(bytearray(self.LOGO_PBM), self.width, self.height, framebuf.MONO_VLSB)
            self.display.blit(fb, 0, 0)
        else:
            # Option 2: Als Text zeichnen (Fallback)
            self.display.fill(0)
            # "INIT" zentriert anzeigen (Großbuchstaben, 8x8 Font)
            text = "INIT"
            text_width = len(text) * 8
            x = (self.width - text_width) // 2
            y = (self.height - 8) // 2
            self.display.text(text, x, y, 1)
        
        self.display.show()
        time.sleep(2)
        self.clear()
    
    def _draw_glyph(self, glyph, x, y, scale=1, color=1):
        """Zeichnet eine Bitmap-Glyphe auf den Display-Buffer."""
        for row, row_bits in enumerate(glyph):
            for col, bit in enumerate(row_bits):
                if bit != '1':
                    continue
                px = x + col * scale
                py = y + row * scale
                if scale == 1:
                    if 0 <= px < self.width and 0 <= py < self.height:
                        self.display.pixel(px, py, color)
                    continue
                self.display.fill_rect(px, py, scale, scale, color)

    def _draw_text_with_font(self, text, x, y, font_map, font_width, font_height, scale=1, color=1):
        """Zeichnet Text mit externer Bitmap-Font."""
        cursor_x = x
        cursor_y = y
        spacing = scale

        for ch in str(text):
            if ch == '\n':
                cursor_x = x
                cursor_y += (font_height + 1) * scale
                continue

            glyph = font_map.get(ch)
            if glyph is None:
                glyph = font_map.get(' ')

            if glyph is not None:
                self._draw_glyph(glyph, cursor_x, cursor_y, scale=scale, color=color)
            cursor_x += font_width * scale + spacing

    def print(self, string, x=0, y=0, font='serif', scale=1, color=1):
        """
        Gibt Text auf dem Display aus
        
        Args:
            string: Der anzuzeigende Text
            x: X-Position (Standard: 0)
            y: Y-Position (Standard: 0)
            font: 'sans' (serifenlos) oder 'serif' (Systemschriftart, Standard: 'serif')
            scale: Vergrößerung für die Sans-Font (Standard: 1)
            color: 1 für an, 0 für aus (Standard: 1)
        
        Hinweis: Rufen Sie show() auf, um die Änderungen anzuzeigen
        """
        if not self.enabled:
            return

        font_name = str(font).lower()
        if scale < 1:
            scale = 1

        if font_name == 'sans' and FONT_SANS is not None:
            self._draw_text_with_font(str(string), x, y, FONT_SANS, FONT_SANS_WIDTH, FONT_SANS_HEIGHT, scale=scale, color=color)
        else:
            # Standard: MicroPython 8x8 Systemschriftart
            self.display.text(str(string), x, y, color)
    
    def pixel(self, x, y, color=1):
        """
        Setzt einen einzelnen Pixel
        
        Args:
            x: X-Position
            y: Y-Position
            color: 1 für an, 0 für aus (Standard: 1)
        
        Hinweis: Rufen Sie show() auf, um die Änderungen anzuzeigen
        """
        if not self.enabled:
            return
        
        self.display.pixel(x, y, color)
    
    def draw_rect(self, x1, y1, b, h, color=1):
        """
        Zeichnet einen Rechteck-Umriss
        
        Args:
            x1: X-Position der oberen linken Ecke
            y1: Y-Position der oberen linken Ecke
            b: Breite
            h: Höhe
            color: 1 für an, 0 für aus (Standard: 1)
        
        Hinweis: Rufen Sie show() auf, um die Änderungen anzuzeigen
        """
        if not self.enabled:
            return
        
        self.display.rect(x1, y1, b, h, color)
    
    def fill_rect(self, x1, y1, b, h, color=1):
        """
        Zeichnet ein gefülltes Rechteck
        
        Args:
            x1: X-Position der oberen linken Ecke
            y1: Y-Position der oberen linken Ecke
            b: Breite
            h: Höhe
            color: 1 für an, 0 für aus (Standard: 1)
        
        Hinweis: Rufen Sie show() auf, um die Änderungen anzuzeigen
        """
        if not self.enabled:
            return
        
        self.display.fill_rect(x1, y1, b, h, color)
    
    def draw_circle(self, x, y, r, color=1):
        """
        Zeichnet einen Kreis-Umriss (Bresenham-Algorithmus)
        
        Args:
            x: X-Position des Mittelpunkts
            y: Y-Position des Mittelpunkts
            r: Radius
            color: 1 für an, 0 für aus (Standard: 1)
        
        Hinweis: Rufen Sie show() auf, um die Änderungen anzuzeigen
        """
        if not self.enabled:
            return
        
        # Bresenham-Kreis-Algorithmus
        x_pos = 0
        y_pos = r
        d = 3 - 2 * r
        
        self._draw_circle_points(x, y, x_pos, y_pos, color)
        
        while y_pos >= x_pos:
            x_pos += 1
            if d > 0:
                y_pos -= 1
                d = d + 4 * (x_pos - y_pos) + 10
            else:
                d = d + 4 * x_pos + 6
            self._draw_circle_points(x, y, x_pos, y_pos, color)
    
    def fill_circle(self, x, y, r, color=1):
        """
        Zeichnet einen gefüllten Kreis
        
        Args:
            x: X-Position des Mittelpunkts
            y: Y-Position des Mittelpunkts
            r: Radius
            color: 1 für an, 0 für aus (Standard: 1)
        
        Hinweis: Rufen Sie show() auf, um die Änderungen anzuzeigen
        """
        if not self.enabled:
            return
        
        # Bresenham-Kreis-Algorithmus mit horizontalen Linien füllen
        x_pos = 0
        y_pos = r
        d = 3 - 2 * r
        
        # Mittellinie
        self.display.hline(x - r, y, 2 * r + 1, color)
        
        while y_pos >= x_pos:
            x_pos += 1
            if d > 0:
                y_pos -= 1
                d = d + 4 * (x_pos - y_pos) + 10
            else:
                d = d + 4 * x_pos + 6
            
            # Zeichne horizontale Linien für alle 8 Symmetrie-Positionen
            self.display.hline(x - x_pos, y + y_pos, 2 * x_pos + 1, color)
            self.display.hline(x - x_pos, y - y_pos, 2 * x_pos + 1, color)
            self.display.hline(x - y_pos, y + x_pos, 2 * y_pos + 1, color)
            self.display.hline(x - y_pos, y - x_pos, 2 * y_pos + 1, color)
    
    def _draw_circle_points(self, xc, yc, x, y, color):
        """Hilfsfunktion zum Zeichnen der 8 Kreispunkte"""
        points = [
            (xc + x, yc + y), (xc - x, yc + y),
            (xc + x, yc - y), (xc - x, yc - y),
            (xc + y, yc + x), (xc - y, yc + x),
            (xc + y, yc - x), (xc - y, yc - x)
        ]
        for px, py in points:
            if 0 <= px < self.width and 0 <= py < self.height:
                self.display.pixel(px, py, color)
    
    def line(self, x1, y1, x2, y2, color=1):
        """
        Zeichnet eine Linie
        
        Args:
            x1: X-Position des Startpunkts
            y1: Y-Position des Startpunkts
            x2: X-Position des Endpunkts
            y2: Y-Position des Endpunkts
            color: 1 für an, 0 für aus (Standard: 1)
        
        Hinweis: Rufen Sie show() auf, um die Änderungen anzuzeigen
        """
        if not self.enabled:
            return
        
        self.display.line(x1, y1, x2, y2, color)
    
    def hline(self, x, y, w, color=1):
        """
        Zeichnet eine horizontale Linie
        
        Args:
            x: X-Position des Startpunkts
            y: Y-Position (verläuft horizontal)
            w: Breite/Länge der Linie
            color: 1 für an, 0 für aus (Standard: 1)
        
        Hinweis: Rufen Sie show() auf, um die Änderungen anzuzeigen
        """
        if not self.enabled:
            return
        
        self.display.hline(x, y, w, color)
    
    def vline(self, x, y, h, color=1):
        """
        Zeichnet eine vertikale Linie
        
        Args:
            x: X-Position (verläuft vertikal)
            y: Y-Position des Startpunkts
            h: Höhe/Länge der Linie
            color: 1 für an, 0 für aus (Standard: 1)
        
        Hinweis: Rufen Sie show() auf, um die Änderungen anzuzeigen
        """
        if not self.enabled:
            return
        
        self.display.vline(x, y, h, color)
    
    def clear(self):
        """Löscht das Display"""
        if not self.enabled:
            return
        
        self.display.fill(0)
        self.display.show()
    
    def show(self):
        """Aktualisiert das Display (für manuelle Buffer-Verwaltung)"""
        if not self.enabled:
            return
        
        self.display.show()
    
    def map(self, value, in_min, in_max, out_min, out_max):
        """
        Bildet einen Wert aus einem Eingabebereich auf einen Ausgabebereich ab.
        Nützlich für Sensordaten (z.B. 10-Bit ADC auf Pixel-Breite abbilden)
        
        Args:
            value: Der abzubildende Wert
            in_min: Minimaler Eingabewert
            in_max: Maximaler Eingabewert
            out_min: Minimaler Ausgabewert
            out_max: Maximaler Ausgabewert
        
        Returns:
            Die abgebildete Ganzzahl
        
        Beispiel:
            # 10-Bit ADC (0-1023) auf Display-Breite (0-128) abbilden
            pixel_x = oled.map(adc_value, 0, 1023, 0, 128)
        """
        # Constraint Eingabewert
        if value < in_min:
            value = in_min
        if value > in_max:
            value = in_max
        
        # Lineare Abbildung
        return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
    
    def progress_bar(self, x, y, width, height, percent, color=1):
        """
        Zeichnet einen Fortschrittsbalken (z.B. für Batteriestand oder Download-Progress)
        
        Args:
            x: X-Position der oberen linken Ecke
            y: Y-Position der oberen linken Ecke
            width: Breite des Balkens
            height: Höhe des Balkens
            percent: Prozentwert (0-100)
            color: 1 für an, 0 für aus (Standard: 1)
        
        Hinweis: Rufen Sie show() auf, um die Änderungen anzuzeigen
        
        Beispiel:
            oled.progress_bar(10, 30, 108, 10, 75)  # 75% gefüllt
            oled.show()  # Anzeigen
        """
        if not self.enabled:
            return
        
        # Constraint Prozentwert
        if percent < 0:
            percent = 0
        if percent > 100:
            percent = 100
        
        # Äußerer Rahmen
        self.display.rect(x, y, width, height, color)
        
        # Gefüllter innerer Bereich
        fill_width = int((percent / 100.0) * (width - 2))
        self.display.fill_rect(x + 1, y + 1, fill_width, height - 2, color)
    
    def draw_bar(self, x, y, width, height, value_percent, color=1):
        """
        Zeichnet einen Balken basierend auf einem Prozentwert.
        Kann horizontal oder vertikal ausgerichtet sein (abhängig von width/height Verhältnis).
        
        Args:
            x: X-Position der oberen linken Ecke
            y: Y-Position der oberen linken Ecke
            width: Breite des Balkens
            height: Höhe des Balkens
            value_percent: Der Wert als Prozentsatz (0-100)
            color: 1 für an, 0 für aus (Standard: 1)
        
        Hinweis: Rufen Sie show() auf, um die Änderungen anzuzeigen
        
        Beispiel:
            # Vertikale Balken-Anzeige (Audio-Visualizer)
            oled.draw_bar(10, 10, 8, 50, 60)   # 60% gefüllt
            oled.draw_bar(25, 10, 8, 50, 80)   # 80% gefüllt
            oled.show()  # Alle Balken auf einmal anzeigen
            
            # Horizontale Balken-Anzeige
            oled.draw_bar(10, 30, 100, 10, 40)  # 40% gefüllt
            oled.show()  # Anzeigen
        """
        if not self.enabled:
            return
        
        # Constraint Prozentwert
        if value_percent < 0:
            value_percent = 0
        if value_percent > 100:
            value_percent = 100
        
        # Vertikale Ausrichtung (height > width)
        if height > width:
            fill_height = int((value_percent / 100.0) * height)
            # Balken von unten nach oben füllen
            self.display.fill_rect(x, y + height - fill_height, width, fill_height, color)
        else:
            # Horizontale Ausrichtung (width >= height)
            fill_width = int((value_percent / 100.0) * width)
            self.display.fill_rect(x, y, fill_width, height, color)


# Beispiel-Verwendung:
# oled = OLED(scl=22, sda=21, chip='ssd1306', enabled=True)
# 
# # Alle Zeichenbefehle schreiben in den Puffer
# oled.print("Hello World", 0, 0)  # mit Systemschriftart (Serif-Standard)
# oled.print("Hello World", 0, 10, font='sans')  # serifenlose Schrift
# oled.print("Hello World", 0, 20, font='sans', scale=2)  # größer
# oled.show()  # JETZT erst anzeigen - verhindert Flimmern!
# 
# # Grafik-Beispiel
# oled.clear()
# oled.draw_rect(10, 10, 50, 30)  # Rechteck-Umriss
# oled.fill_rect(70, 10, 50, 30)  # gefülltes Rechteck
# oled.draw_circle(40, 40, 15)  # Kreis-Umriss
# oled.fill_circle(90, 40, 15)  # gefüllter Kreis
# oled.line(0, 0, 127, 63)
# oled.show()  # Alles auf einmal anzeigen
#
# Für SH1106 Display:
# oled = OLED(scl=22, sda=21, chip='sh1106', enabled=True)
