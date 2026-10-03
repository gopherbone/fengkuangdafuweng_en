"""Character intro story pages -> gfx/patch.json["intro"].

Original: table $4C:$562D = 8 x [bank][page list]; each page record (bank $4C) = [$9000 tiles][$8800 tiles][map]
pointers into that bank; pages are pre-rendered 12px text. We render script/intro_en.json with the VWF font
(white on black, word-wrapped to 144 px), dedupe tiles, and give character k its own bank $70+k.
"""
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys, os, json
sys.path.insert(0, _R + '/tools')
sys.path.insert(0, _R + '/font')
import intro_pages as ip
from gfx import draw_text, text_width, px_tile
from en_font import GLYPHS

ROOT = _R
FIRST_BANK = 0x70
W, LEFT, TEXTW, PITCH, TOP = 20, 8, 144, 13, 2

def wrap(text):
    lines, cur = [], ''
    for word in text.split(' '):
        t = (cur + ' ' + word) if cur else word
        if text_width(t) <= TEXTW: cur = t
        else: lines.append(cur); cur = word
    if cur: lines.append(cur)
    return lines

def page_data(text):
    lines = wrap(text)
    rows = (TOP + len(lines) * PITCH + 7) // 8
    canvas = [[3] * (W * 8) for _ in range(rows * 8)]     # bg = colour 3 (black)
    for i, l in enumerate(lines):
        draw_text(canvas, l, LEFT, TOP + i * PITCH, 0)       # ink = colour 0 (white)
    tiles, idx, m = [], {}, []
    blank = b'\xff' * 16; tiles.append(blank); idx[blank] = 0
    for r in range(rows):
        for c in range(W):
            t = px_tile([row[c * 8:c * 8 + 8] for row in canvas[r * 8:r * 8 + 8]])
            if t not in idx:
                idx[t] = len(tiles); tiles.append(t)
            m.append(idx[t])
    assert len(tiles) <= 256, len(tiles)
    t9 = b''.join(tiles[:128]); t8 = b''.join(tiles[128:])
    return t9, t8, rows, bytes(m), len(lines)

def main():
    en = json.load(open(os.path.join(ROOT, 'script', 'intro_en.json')))
    out = {}
    pages = ip.pages()
    for k in range(8):
        bank = FIRST_BANK + k
        body = bytearray([bank])
        mine = [p for p in pages if p[0] == k]
        assert len(mine) == len(en[str(k)]), (k, len(mine), len(en[str(k)]))
        for (_, p, rec, _, _), text in zip(mine, en[str(k)]):
            t9, t8, rows, m, nl = page_data(text)
            ptrs = []
            for blk in (len(t9).to_bytes(2, 'little') + t9, len(t8).to_bytes(2, 'little') + t8, bytes([W, rows]) + m):
                ptrs.append(0x4000 + len(body)); body += blk
            rec_off = ip.B4C + rec - 0x4000
            out['%06X' % rec_off] = b''.join(x.to_bytes(2, 'little') for x in ptrs).hex()
        assert len(body) <= 0x4000, (k, len(body))
        out['%06X' % (bank * 0x4000)] = bytes(body).hex()
        out['%06X' % (ip.B4C + ip.TABLE - 0x4000 + 3 * k)] = bytes([bank]).hex()
        print('char', k, 'bank %02X' % bank, len(body), 'bytes')
    pf = os.path.join(ROOT, 'gfx', 'patch.json')
    patch = json.load(open(pf)); patch['intro'] = out
    json.dump(dict(sorted(patch.items())), open(pf, 'w'), indent=1)

if __name__ == '__main__':
    main()
