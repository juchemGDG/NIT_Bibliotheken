from PIL import Image
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
img = Image.open('NIT_100_32_mono_Line.png').convert('RGB')
w, h = img.size

red_cols = []
for x in range(w):
    r, g, b = img.getpixel((x, 0))
    if r > 200 and g < 100 and b < 100:
        red_cols.append(x)

print(f'Bild: {w}x{h}, Rote Spalten: {red_cols}')

char_x_starts = [rc + 1 for rc in red_cols if rc + 1 < w and rc + 1 not in red_cols]
print(f'Zeichen-Spalten: {char_x_starts}')
print(f'Anzahl Spalten: {len(char_x_starts)}, Zeilen: {h // 8}')
print()

for row in range(h // 8):
    for ci, xs in enumerate(char_x_starts):
        name = f'm{row}{ci}'
        rows = []
        for py in range(8):
            bits = ''
            for px in range(5):
                x = xs + px
                y = row * 8 + py
                r, g, b = img.getpixel((x, y))
                bits += '1' if (r + g + b) > 380 else '0'
            rows.append(bits)
        line = ','.join(rows)
        print(f'{name}={{{line}}}')

print(f'\nGesamt: {(h // 8) * len(char_x_starts)} Zeichen')
