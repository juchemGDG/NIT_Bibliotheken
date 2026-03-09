from oled import OLED

# Display initialisieren (SSD1306)
oled = OLED(scl=22, sda=21, chip='ssd1306')

# Text ausgeben und anzeigen
oled.print('Hello World', 0, 0)
oled.show()

# Display loeschen
oled.clear()
