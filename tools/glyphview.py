"""glyphview.py OUT.png ID [ID ...]  — render glyphs (hex ids like 48F) enlarged, labelled, from the original ROM."""
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys
from PIL import Image, ImageDraw
rom = open(_R + '/orig/fkdfw.gbc', 'rb').read()
def glyph(idx):
    p, x = idx >> 8, idx & 0xff
    o = (9 + (p >> 1)) * 0x4000 + (p & 1) * 0x2000 + 1 + x * 32
    im = Image.new('L', (16, 16), 255)
    for col in range(2):
        for r in range(16):
            b = rom[o + col * 16 + r]
            for bit in range(8):
                if b & (0x80 >> bit): im.putpixel((col * 8 + bit, r), 0)
    return im
ids = [int(a, 16) for a in sys.argv[2:]]
S = 8; W = 16 * S + 20
out = Image.new('L', (W * len(ids), 16 * S + 30), 255); d = ImageDraw.Draw(out)
for i, g in enumerate(ids):
    out.paste(glyph(g).resize((16 * S, 16 * S), Image.NEAREST), (i * W + 10, 24))
    d.text((i * W + 10, 4), '%03X' % g, fill=0)
out.save(sys.argv[1])
