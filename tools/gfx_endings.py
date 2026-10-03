"""Winner's wish scene (ending) text pages -> gfx/patch.json["endings"].

Original: per-character record table $0C:$40E7 -> [bank][part A page list][part B page list]; each list entry points
to a 4-byte page record in bank $0C = [tile block ptr][map ptr] in that character's bank. $0C:$4072 copies the
record into the screen descriptor ($C101 / $C105) and calls $1A31, which loads the tiles to $8800 and the map
(16 x up to 5) to $9982, the inside of the text box. Pages are pre-rendered 12px text.

We render script/endings_en.json with the VWF font (white on black, as the original), give character k its own
bank $60+k, and repoint the records there. The engine's EndPage (hooked at $0C:$4091) swaps in that bank for the
load.
"""
import sys, os, json
sys.path.insert(0, '/Users/nick/crazyrichman_claude/tools')
from gfx import ROM, draw_text, text_width, px_tile

ROOT = '/Users/nick/crazyrichman_claude'
FIRST_BANK = 0x60
BC = 0x0C * 0x4000 - 0x4000
TABLE = 0x40E7
W, ROWS, LEFT, TEXTW, PITCH = 16, 5, 4, 120, 13

def w(a): return ROM[BC + a] | ROM[BC + a + 1] << 8

def page_records():
    """-> {char: [record addr, ...]} (every page of parts A and B; list slot 0 is unused by the game)."""
    starts = sorted({w(w(TABLE + 2 * j) + o) for j in range(8) for o in (1, 3)}) + [0x41F7]
    out = {}
    for k in range(8):
        r = w(TABLE + 2 * k)
        recs = []
        for lst in (w(r + 1), w(r + 3)):
            end = min(s for s in starts if s > lst)
            recs += [w(a) for a in range(lst + 2, end, 2)]
        out[k] = recs
    return out

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
    h = len(lines) * PITCH - 1
    assert h <= ROWS * 8, (text, lines)
    rows = ROWS
    top = (ROWS * 8 - h) // 2                                # centred vertically in the box
    canvas = [[3] * (W * 8) for _ in range(rows * 8)]       # bg = colour 3 (black)
    for i, l in enumerate(lines):
        draw_text(canvas, l, LEFT, top + i * PITCH, 0)       # ink = colour 0 (white)
    tiles, idx, m = [], {}, []
    for r in range(rows):
        for c in range(W):
            t = px_tile([row[c * 8:c * 8 + 8] for row in canvas[r * 8:r * 8 + 8]])
            if t not in idx:
                idx[t] = len(tiles); tiles.append(t)
            m.append(0x80 + idx[t])                          # block is loaded to $8800 (tiles $80+)
    assert len(tiles) <= 128, len(tiles)
    blk = b''.join(tiles)
    return len(blk).to_bytes(2, 'little') + blk, bytes([W, rows]) + bytes(m)

def preview(path):
    from PIL import Image
    en = {k: v for k, v in json.load(open(os.path.join(ROOT, 'script', 'endings_en.json'))).items() if not k.startswith('_')}
    ims = []
    for k, recs in page_records().items():
        for rec in dict.fromkeys(recs):
            tb, mp = page_data(en['%04x' % rec]); t = tb[2:]; m = mp[2:]
            im = Image.new('L', (W * 8, ROWS * 8))
            for i, ti in enumerate(m):
                o = (ti - 0x80) * 16
                for y in range(8):
                    lo, hi = t[o + 2 * y], t[o + 2 * y + 1]
                    for x in range(8):
                        im.putpixel(((i % W) * 8 + x, (i // W) * 8 + y), [255, 170, 85, 0][((lo >> (7 - x)) & 1) | (((hi >> (7 - x)) & 1) << 1)])
            ims.append(im)
    cols = 6; s = Image.new('L', (cols * (W * 8 + 6), ((len(ims) + cols - 1) // cols) * (ROWS * 8 + 6)), 128)
    for i, im in enumerate(ims): s.paste(im, ((i % cols) * (W * 8 + 6), (i // cols) * (ROWS * 8 + 6)))
    s.resize((s.width * 2, s.height * 2)).save(path)

def main():
    en = {k: v for k, v in json.load(open(os.path.join(ROOT, 'script', 'endings_en.json'))).items()
          if not k.startswith('_')}
    out = {}
    for k, recs in page_records().items():
        bank = FIRST_BANK + k
        body = bytearray([bank])                             # banks carry their own number at $4000
        for rec in dict.fromkeys(recs):
            tb, mp = page_data(en['%04x' % rec])
            ta = 0x4000 + len(body); body += tb
            ma = 0x4000 + len(body); body += mp
            out['%06X' % (BC + rec)] = (ta.to_bytes(2, 'little') + ma.to_bytes(2, 'little')).hex()
        assert len(body) <= 0x4000, (k, len(body))
        out['%06X' % (bank * 0x4000)] = bytes(body).hex()
        print('char', k, 'bank %02X' % bank, len(recs), 'pages', len(body), 'bytes')
    pf = os.path.join(ROOT, 'gfx', 'patch.json')
    patch = json.load(open(pf)); patch['endings'] = out
    json.dump(dict(sorted(patch.items())), open(pf, 'w'), indent=1)

if __name__ == '__main__':
    preview(sys.argv[1]) if len(sys.argv) > 1 else main()
