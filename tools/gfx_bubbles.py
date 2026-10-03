"""Board town-name bubbles (sprites, 4 x 8x16 = 32x16) -> gfx/patch.json["bubbles"].

Table $03:$40AC: 60 x [board space][tile data ptr (0x80 bytes, bank 3)][OBJ palette ptr]. We keep each bubble's
outline and tail, clear the inside (wider text area than the original's inner accents allowed) and draw the
English name with a condensed version of the VWF font, black for cities and grey for towns as in the original.
"""
import sys, os, json
sys.path.insert(0, '/Users/nick/crazyrichman_claude/font')
from en_font import GLYPHS

ROOT = '/Users/nick/crazyrichman_claude'
ROM = open(os.path.join(ROOT, 'orig', 'fkdfw.gbc'), 'rb').read()
B3 = 0x3 * 0x4000
TABLE, COUNT, FIRST_BLOCK = 0x40AC, 60, 0x4058
# Chinese names of bubble blocks 3..62 in ROM order (read off the bubble graphics)
ORDER = ("桃園 台中 彰化 嘉義 台南 高雄 台東 花蓮 宜蘭 基隆 台北 雪山 南投 玉山 綠島 馬公 中壢 布袋 永康 屏東 蘇澳 中賽 斗六 "
         "新營 旗山 瑞芳 池上 吉貝 太魯閣 士林 松山 關西 三星 東山 三義 大甲 三重 竹東 南澳 羅東 造橋 苗栗 大里 太平 員林 關山 "
         "民雄 岡山 沙鹿 斗南 卑南 白河 瑞穗 西螺 太麻里 玉井 玉里 鹿港 水上 善化").split()
SHORT = {'Snow Mtn.': 'Snow Mt', 'Jade Mtn.': 'Jade Mt', 'Green Island': 'Green Is.'}
X0, X1 = 3, 29          # text may use columns X0..X1 inclusive
MAXW = X1 - X0 + 1
YOFF = 1                # glyph row r is drawn on bubble row r + YOFF

def condense(rows, w):
    if w < 4: return rows, w
    cols = [[(r >> (7 - x)) & 1 for r in rows] for x in range(w)]
    best = None
    for x in range(1, w - 1):
        diff = sum(a != b for a, b in zip(cols[x], cols[x - 1])) + sum(a != b for a, b in zip(cols[x], cols[x + 1]))
        if best is None or diff < best[0]: best = (diff, x)
    nc = cols[:best[1]] + cols[best[1] + 1:]
    return [sum(nc[i][r] << (7 - i) for i in range(len(nc))) for r in range(12)], w - 1

CF = {ch: condense(*GLYPHS[ch]) for ch in GLYPHS}

def layout(name):
    """-> list of (char, x) with total width <= MAXW, removing gaps (after narrow glyphs first) if needed."""
    gaps = [1] * (len(name) - 1)
    width = lambda: sum(CF[c][1] for c in name) + sum(gaps)
    order = sorted(range(len(gaps)), key=lambda i: (CF[name[i]][1] > 1, CF[name[i + 1]][1] > 1, abs(i - len(gaps) / 2)))
    k = 0
    while width() > MAXW and k < len(order):
        gaps[order[k]] = 0; k += 1
    if width() > MAXW: print('  too wide: %r (%d)' % (name, width())); return None
    x = X0 + (MAXW - width()) // 2; out = []
    for i, c in enumerate(name):
        out.append((c, x)); x += CF[c][1] + (gaps[i] if i < len(gaps) else 0)
    return out

def get_px(block):
    px = [[0] * 32 for _ in range(16)]
    for s in range(4):
        for half in (0, 1):
            t = ROM[B3 + block - 0x4000 + s * 32 + half * 16:][:16]
            for y in range(8):
                for x in range(8):
                    px[half * 8 + y][s * 8 + x] = ((t[2 * y] >> (7 - x)) & 1) | (((t[2 * y + 1] >> (7 - x)) & 1) << 1)
    return px

def put_px(px):
    out = bytearray()
    for s in range(4):
        for half in (0, 1):
            for y in range(8):
                lo = hi = 0
                for x in range(8):
                    v = px[half * 8 + y][s * 8 + x]; lo |= (v & 1) << (7 - x); hi |= (v >> 1) << (7 - x)
                out += bytes([lo, hi])
    return bytes(out)

def main():
    places = json.load(open(os.path.join(ROOT, 'script', 'tl_out', 'places.json')))
    out = {}
    w = lambda a: ROM[B3 + a - 0x4000] | ROM[B3 + a - 0x4000 + 1] << 8
    seen = set()
    for i in range(COUNT):
        e = TABLE + 5 * i
        block = w(e + 1)
        if block in seen: continue
        seen.add(block)
        k = (block - FIRST_BLOCK) // 0x80 - 3
        zh = ORDER[k]; en = places[zh]; en = SHORT.get(en, en)
        px = get_px(block)
        ink = 3 if any(px[y][x] == 3 for y in range(2, 12) for x in range(4, 28)) else 2
        for y in range(1, 13):                  # clear accents and old text; keep the outline and tail
            for x in range(1, 31):
                if px[y][x] == 2 or (px[y][x] == 3 and 2 <= y <= 12 and 3 <= x <= 29): px[y][x] = 1
        lay = layout(en)
        if lay is None: continue
        for c, x in lay:
            rows, cw = CF[c]
            for r in range(12):
                for b in range(cw):
                    if rows[r] & (0x80 >> b): px[r + YOFF][x + b] = ink     # caps on rows 3-10: centred in the fill (rows 1-12)
        out['%06X' % (B3 + block - 0x4000)] = put_px(px).hex()
    pf = os.path.join(ROOT, 'gfx', 'patch.json')
    patch = json.load(open(pf)); patch['bubbles'] = out
    json.dump(dict(sorted(patch.items())), open(pf, 'w'), indent=1)
    print('bubbles:', len(out))

if __name__ == '__main__':
    main()
