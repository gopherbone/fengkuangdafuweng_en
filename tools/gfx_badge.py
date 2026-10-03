"""Other > Setup screen: the 電腦 ("computer") player badge -> gfx/patch.json["setup_badge"].

Raw 2bpp tiles at $08:$679F (copied to $9560 by $08:$5FF8): 4 columns x (top, bottom) tiles, a 32x16 rounded
badge drawn in colour 2. We keep the border, clear the inside and write "CPU".
"""
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys, os, json
sys.path.insert(0, _R + '/tools')
from gfx import ROM, draw_text, text_width

ROOT = _R
OFF = 0x08 * 0x4000 + 0x679F - 0x4000

def main():
    px = [[0] * 32 for _ in range(16)]
    for col in range(4):
        for half in range(2):
            t = ROM[OFF + (col * 2 + half) * 16:][:16]
            for y in range(8):
                for x in range(8):
                    px[half * 8 + y][col * 8 + x] = ((t[2 * y] >> (7 - x)) & 1) | (((t[2 * y + 1] >> (7 - x)) & 1) << 1)
    for y in range(2, 14):
        for x in range(4, 28): px[y][x] = 0
    draw_text(px, 'CPU', (32 - text_width('CPU')) // 2, 2, 2)
    out = bytearray()
    for col in range(4):
        for half in range(2):
            for y in range(8):
                lo = hi = 0
                for x in range(8):
                    v = px[half * 8 + y][col * 8 + x]; lo |= (v & 1) << (7 - x); hi |= (v >> 1) << (7 - x)
                out += bytes([lo, hi])
    pf = os.path.join(ROOT, 'gfx', 'patch.json')
    patch = json.load(open(pf)); patch['setup_badge'] = {'%06X' % OFF: bytes(out).hex()}
    json.dump(dict(sorted(patch.items())), open(pf, 'w'), indent=1)
    print('setup badge')

if __name__ == '__main__':
    main()
