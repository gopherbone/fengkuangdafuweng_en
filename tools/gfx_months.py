"""Month splash screens: remove the 月 ("month") glyph after the big month number -> gfx/patch.json["months"].

Table $42:$4057 -> 12 entries of [2-byte ptr][13-byte screen descriptor] (banks $3E-$41). The number and 月 sit in
map rows 2-3, columns 1-4; 月 is the rightmost shape there. We erase it (paint the surrounding background colour)
in the tiles in place; the English month name is already drawn at the bottom of each picture.
"""
import sys, os, json
sys.path.insert(0, '/Users/nick/crazyrichman_claude/tools')
from gfx import ROM, Rebuild

ROOT = '/Users/nick/crazyrichman_claude'
B42 = 0x42 * 0x4000 - 0x4000
ROWS, COLS = (2, 3), (1, 2, 3, 4)

def tile_px(t): return [[((t[2 * y] >> (7 - x)) & 1) | (((t[2 * y + 1] >> (7 - x)) & 1) << 1) for x in range(8)] for y in range(8)]
def px_tile(p):
    out = bytearray()
    for y in range(8):
        lo = hi = 0
        for x in range(8): lo |= (p[y][x] & 1) << (7 - x); hi |= (p[y][x] >> 1) << (7 - x)
        out += bytes([lo, hi])
    return bytes(out)

def main():
    out = {}
    for k in range(12):
        desc = B42 + 0x4071 + 15 * k + 2
        rb = Rebuild(desc, 0)
        w, h, m = rb.map
        cells = [(r, c) for r in ROWS for c in COLS]
        canvas = [[0] * 32 for _ in range(16)]
        for (r, c) in cells:
            p = tile_px(rb.get_tile(m[r * w + c]))
            for y in range(8):
                for x in range(8): canvas[(r - 2) * 8 + y][(c - 1) * 8 + x] = p[y][x]
        bg = canvas[0][31]
        # connected components of non-background pixels; 月 = the one reaching furthest right
        seen = set(); comps = []
        for y in range(16):
            for x in range(32):
                if canvas[y][x] != bg and (y, x) not in seen:
                    st = [(y, x)]; comp = []; seen.add((y, x))
                    while st:
                        cy, cx = st.pop(); comp.append((cy, cx))
                        for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1), (cy + 1, cx + 1), (cy - 1, cx - 1), (cy + 1, cx - 1), (cy - 1, cx + 1)):
                            if 0 <= ny < 16 and 0 <= nx < 32 and (ny, nx) not in seen and canvas[ny][nx] != bg:
                                seen.add((ny, nx)); st.append((ny, nx))
                    comps.append(comp)
        moon = max(comps, key=lambda cp: min(x for _, x in cp))
        assert min(x for _, x in moon) >= 16, (k, min(x for _, x in moon))   # never touch the number
        for (y, x) in moon: canvas[y][x] = bg
        for (r, c) in cells:
            if c < 3: continue
            ti = m[r * w + c]
            assert sum(1 for i in range(w * h) if m[i] == ti) == 1 or ti == m[0], (k, r, c, hex(ti))
            p = [canvas[(r - 2) * 8 + y][(c - 1) * 8:(c - 1) * 8 + 8] for y in range(8)]
            blk = rb.ptr[0] if ti < 0x80 else rb.ptr[1]
            idx = ti if ti < 0x80 else ti - 0x80
            off = rb.src_bank * 0x4000 + blk - 0x4000 + 2 + idx * 16
            new = px_tile(p)
            if new != ROM[off:off + 16]: out['%06X' % off] = new.hex()
        print('month', k + 1, 'bank %02X' % rb.src_bank)
    pf = os.path.join(ROOT, 'gfx', 'patch.json')
    patch = json.load(open(pf)); patch['months'] = out
    json.dump(dict(sorted(patch.items())), open(pf, 'w'), indent=1)
    print(len(out), 'tiles')

if __name__ == '__main__':
    main()
