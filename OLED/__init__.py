"""
OLED Display Driver für ESP32 mit MicroPython
Unterstützt SSD1306 und SH1106 Displays

Vereinfachter Import:
    from OLED import OLED
"""

from .oled import OLED

__all__ = ['OLED']
__version__ = '1.0.0'
