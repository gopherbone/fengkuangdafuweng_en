"""Graphical-text patcher.

The game's pre-drawn text (menus, titles, labels) is stored as raw 2bpp tiles in the ROM. A spec in
gfx/specs.json names a save state (original ROM) and screen regions; for each region we look up which ROM tile
is shown in each cell, render English with the proportional font in the region's own colours, and emit
gfx/patch.json = {rom_offset_hex: tile_hex}. tools/build.py applies it.

  python3 tools/gfx.py [screen ...]      # regenerate patches (needs the local save states)
  python3 tools/gfx.py --preview NAME    # write gfx/preview_NAME.png (before | after)
"""
import sys, os, json, argparse
sys.path.insert(0, '/Users/nick/crazyrichman_claude/tools')
sys.path.insert(0, '/Users/nick/crazyrichman_claude/font')
from emu import boot
from en_font import GLYPHS
from PIL import Image

ROOT = '/Users/nick/crazyrichman_claude'
ROM = open(os.path.join(ROOT, 'orig', 'fkdfw.gbc'), 'rb').read()

def tile_px(t):
    """16 bytes 2bpp -> 8x8 colour indices"""
    return [[((t[2 * y] >> (7 - x)) & 1) | (((t[2 * y + 1] >> (7 - x)) & 1) << 1) for x in range(8)] for y in range(8)]

def px_tile(p):
    out = bytearray()
    for y in range(8):
        lo = hi = 0
        for x in range(8):
            c = p[y][x]
            lo |= (c & 1) << (7 - x); hi |= ((c >> 1) & 1) << (7 - x)
        out += bytes([lo, hi])
    return bytes(out)

class Screen:
    def __init__(self, state):
        g = boot(os.path.join(ROOT, 'orig', 'fkdfw.gbc')); g.snapshot_load(path=os.path.join(ROOT, state))
        self.lcdc = g.mem_read(0xFF40, 1)[0]
        self.vram = bytes.fromhex(g.cmd('mem.read', region='vram', offset=0, len=0x4000)['data'])
        self.maps = {L: g.tilemap(L) for L in ('bg', 'win')}
        self.shot = os.path.join(ROOT, 'gfx', '_shot.png'); g.run_frames(1); g.screenshot_png(self.shot); g.close()

    def cell(self, layer, r, c):
        t = self.maps[layer]
        ti = int(t['tiles'][r][2 * c:2 * c + 2], 16)
        a = int(t['attrs'][r][2 * c:2 * c + 2], 16) if t.get('attrs') else 0
        bank = (a >> 3) & 1
        if self.lcdc & 0x10: addr = ti * 16
        else: addr = 0x1000 + ti * 16 if ti < 0x80 else 0x800 + (ti - 0x80) * 16
        return self.vram[bank * 0x2000 + addr: bank * 0x2000 + addr + 16], (bank, addr), a

def findall(b):
    out = []; i = ROM.find(b)
    while i != -1: out.append(i); i = ROM.find(b, i + 1)
    return out

def text_width(s):
    return sum(GLYPHS[ch][1] + 1 for ch in s) - 1 if s else 0

def draw_text(canvas, s, x, y, col, bold=False):
    for ch in s:
        rows, w = GLYPHS[ch]
        for r in range(12):
            for b in range(w):
                if rows[r] & (0x80 >> b):
                    for dx in ((0, 1) if bold else (0,)):
                        if 0 <= y + r < len(canvas) and 0 <= x + b + dx < len(canvas[0]):
                            canvas[y + r][x + b + dx] = col
        x += w + 1 + (1 if bold else 0)

def build_region(scr, reg, cells=None):
    """Return (cells, {cell: new_tile_bytes}) for one region spec."""
    layer = reg.get('layer', 'bg'); r0, c0, h, w = reg['rect']
    if cells is None:
        cells = {(r, c): scr.cell(layer, r, c) for r in range(r0, r0 + h) for c in range(c0, c0 + w)}
    # colours: background = most common index in the region, ink = given or the least common non-bg
    hist = {}
    for (t, _, _) in cells.values():
        for row in tile_px(t):
            for v in row: hist[v] = hist.get(v, 0) + 1
    bg = reg.get('bg', max(hist, key=hist.get))
    ink = reg.get('ink', 3 if bg != 3 else 0)
    H, W = h * 8, w * 8
    canvas = [[bg] * W for _ in range(H)]
    if 'erase' in reg:
        # keep the original artwork; only pixels of the 'erase' colours inside the inset box become bg
        x0, y0, x1, y1 = reg.get('inset', [0, 0, 0, 0])
        for (r, c), (t, _, _) in cells.items():
            p = tile_px(t)
            for y in range(8):
                for x in range(8):
                    Y, X = (r - r0) * 8 + y, (c - c0) * 8 + x
                    v = p[y][x]
                    if v in reg['erase'] and x0 <= X < W - x1 and y0 <= Y < H - y1: v = bg
                    canvas[Y][X] = v
    # keep untouched pixels outside "clear" area? regions are fully redrawn.
    lines = reg['lines']
    bold = reg.get('bold', False)
    lh = reg.get('line_height', 16)
    top = reg.get('top', (H - lh * len(lines)) // 2 + (lh - 12) // 2 - 1)
    for i, s in enumerate(lines):
        if '\t' in s:                      # label<TAB>value: value starts at reg['tab'] px
            a, b = s.split('\t', 1)
            draw_text(canvas, a, reg.get('left', 0), top + i * lh, ink, bold)
            draw_text(canvas, b, reg['tab'], top + i * lh, ink, bold)
            continue
        tw = text_width(s) + (len(s) if bold else 0)
        al = reg.get('align', 'left')
        x = reg.get('left', 0) if al == 'left' else (W - tw) // 2 if al == 'center' else W - tw - reg.get('right', 0)
        draw_text(canvas, s, x, top + i * lh, ink, bold)
    # keep decorations (e.g. underlines) from the original in the bottom N pixel rows
    kb = reg.get('keep_bottom', 0)
    if kb:
        for (r, c), (t, _, _) in cells.items():
            p = tile_px(t)
            for y in range(8):
                Y = (r - r0) * 8 + y
                if Y >= H - kb:
                    for x in range(8):
                        canvas[Y][(c - c0) * 8 + x] = p[y][x]
    out = {}
    for (r, c) in cells:
        p = [row[(c - c0) * 8:(c - c0) * 8 + 8] for row in canvas[(r - r0) * 8:(r - r0) * 8 + 8]]
        out[(r, c)] = px_tile(p)
    return cells, out

class Rebuild:
    """A screen relocated into its own bank: descriptor = [bank][9000 tiles][8800 tiles][map][attr][pal][pal]."""
    def __init__(self, desc_off, bank):
        self.desc_off, self.bank = desc_off, bank
        d = ROM[desc_off:desc_off + 13]
        self.src_bank = d[0]
        self.ptr = [d[1 + 2 * i] | d[2 + 2 * i] << 8 for i in range(6)]
        rd = lambda a, n: ROM[self.src_bank * 0x4000 + a - 0x4000: self.src_bank * 0x4000 + a - 0x4000 + n]
        def blk(a):
            n = rd(a, 2); n = n[0] | n[1] << 8; return bytearray(rd(a + 2, n))
        def mp(a):
            w, h = rd(a, 2); return [w, h, bytearray(rd(a + 2, w * h))]
        self.t9000, self.t8800 = blk(self.ptr[0]), blk(self.ptr[1])
        self.map, self.attr = mp(self.ptr[2]), mp(self.ptr[3])
        self.pal = [rd(self.ptr[4], 64), rd(self.ptr[5], 64)]

    def tile_index_at(self, r, c):
        w = self.map[0]; return self.map[2][r * w + c]

    def unshare(self, cells):
        """Give each cell (r,c) its own copy of its tile (9000 block only). Returns {cell: new_index}."""
        w, h, m = self.map
        out = {}
        for (r, c) in cells:
            ti = m[r * w + c]
            uses = sum(1 for k in range(w * h) if m[k] == ti)
            if uses > 1 and ti < 0x80:
                ni = len(self.t9000) // 16
                if ni >= 0x80: raise SystemExit('rebuild: out of tile slots')
                self.t9000 += self.t9000[ti * 16: ti * 16 + 16]
                m[r * w + c] = ni
                out[(r, c)] = ni
        return out

    def set_tile(self, ti, data):
        if ti < 0x80: self.t9000[ti * 16: ti * 16 + 16] = data
        else: self.t8800[(ti - 0x80) * 16: (ti - 0x80) * 16 + 16] = data

    def get_tile(self, ti):
        return bytes(self.t9000[ti * 16: ti * 16 + 16]) if ti < 0x80 else bytes(self.t8800[(ti - 0x80) * 16: (ti - 0x80) * 16 + 16])

    def emit(self):
        """-> {rom_offset_hex: data_hex} for the new bank and the patched descriptor."""
        b = bytearray([self.bank]); ptrs = []
        def put(data):
            ptrs.append(0x4000 + len(b)); b.extend(data)
        put(len(self.t9000).to_bytes(2, 'little') + self.t9000)
        put(len(self.t8800).to_bytes(2, 'little') + self.t8800)
        put(bytes(self.map[:2]) + self.map[2]); put(bytes(self.attr[:2]) + self.attr[2])
        put(self.pal[0]); put(self.pal[1])
        assert len(b) <= 0x4000
        desc = bytes([self.bank]) + b''.join(p.to_bytes(2, 'little') for p in ptrs)
        return {'%06X' % (self.bank * 0x4000): bytes(b).hex(), '%06X' % self.desc_off: desc.hex()}

def render_1bpp(text, cells, align='left'):
    """16x16-glyph-format strip (per cell: left column 16 rows, right column 16 rows), 1bpp."""
    W = cells * 16
    canvas = [[0] * W for _ in range(16)]
    tw = text_width(text)
    x = 0 if align == 'left' else (W - tw) // 2 if align == 'center' else W - tw
    draw_text(canvas, text, max(0, x), 2, 1)
    out = bytearray()
    for cell in range(cells):
        for col in range(2):
            for r in range(16):
                b = 0
                for bit in range(8):
                    if canvas[r][cell * 16 + col * 8 + bit]: b |= 0x80 >> bit
                out.append(b)
    return bytes(out)

def run(names, preview=False):
    specs = json.load(open(os.path.join(ROOT, 'gfx', 'specs.json')))
    pfile = os.path.join(ROOT, 'gfx', 'patch.json')
    patch = json.load(open(pfile)) if os.path.exists(pfile) else {}
    patch = {k: v for k, v in patch.items() if isinstance(v, dict)}    # per-screen patches
    patch = {k: v for k, v in patch.items() if k in specs}           # drop patches of removed specs
    for name in names or [k for k in specs if not k.startswith('_')]:
        spec = specs[name]
        if 'generator' in spec:
            print(name, '(generated by %s)' % spec['generator']); continue
        if 'raw1bpp' in spec:
            patch[name] = {}
            for item in spec['raw1bpp']:
                patch[name][item['offset']] = render_1bpp(item['text'], item['cells'], item.get('align', 'left')).hex()
            print(name, len(spec['raw1bpp']), 'raw 1bpp strips')
            json.dump(dict(sorted(patch.items())), open(pfile, 'w'), indent=1)
            continue
        scr = Screen(spec['state'])
        mine = {}
        if 'rebuild' in spec:
            rb = Rebuild(int(spec['rebuild']['descriptor'], 16), int(spec['rebuild']['bank'], 16))
            for reg in spec['regions']:
                r0, c0, h, w = reg['rect']
                cells = [(r, c) for r in range(r0, r0 + h) for c in range(c0, c0 + w)]
                if reg.get('unshare'): rb.unshare(cells)
            # render each region from the (possibly unshared) tiles
            for reg in spec['regions']:
                r0, c0, h, w = reg['rect']
                fake = {}
                for r in range(r0, r0 + h):
                    for c in range(c0, c0 + w):
                        ti = rb.tile_index_at(r, c); fake[(r, c)] = (rb.get_tile(ti), ti, 0)
                _, new = build_region(scr, reg, fake)
                for cell, data in new.items():
                    ti = fake[cell][1]
                    if ti in mine and mine[ti] != data and fake[cell][0].count(fake[cell][0][0]) != 16:
                        raise SystemExit('%s: tile %02X still shared with different content (mark region unshare)' % (name, ti))
                    if fake[cell][0].count(fake[cell][0][0]) == 16 and data != fake[cell][0]:
                        raise SystemExit('%s: cell %s uses a blank shared tile; mark region unshare' % (name, cell))
                    mine[ti] = data
            for ti, data in mine.items(): rb.set_tile(ti, data)
            patch[name] = rb.emit()
            print(name, 'rebuilt into bank %02X, %d tiles changed' % (rb.bank, len(mine)))
            json.dump(dict(sorted(patch.items())), open(pfile, 'w'), indent=1)
            continue
        allcand = []
        for reg in spec['regions']:
            cells, new = build_region(scr, reg)
            for cell, (old, vaddr, attr) in cells.items():
                if old.count(old[0]) == 16:
                    if new[cell] != old:
                        print('  WARNING %s cell %s: blank tile would need ink (shared blank) - text clipped' % (name, cell))
                    continue
                src = findall(old)
                if reg.get('src_bank') is not None:
                    src = [i for i in src if i // 0x4000 == reg['src_bank']]
                if not src:
                    raise SystemExit('%s: tile at cell %s not found in ROM' % (name, cell))
                allcand.append((cell, src, vaddr, new[cell]))
        # resolve duplicates against the screen's unambiguous tiles (graphics for one screen sit together)
        anchors = sorted(c[1][0] for c in allcand if len(c[1]) == 1)
        for cell, src, vaddr, data in allcand:
            if len(src) > 1:
                if not anchors:
                    raise SystemExit('%s: ambiguous tile at %s and no anchor' % (name, cell))
                mid = anchors[len(anchors) // 2]
                src = [min(src, key=lambda o: abs(o - mid))]
            if vaddr in mine and mine[vaddr][1] != data:
                raise SystemExit('%s: tile %s shown in two cells with different English content' % (name, vaddr))
            mine[vaddr] = (src[0], data)
        patch[name] = {'%06X' % off: data.hex() for _, (off, data) in mine.items()}
        print(name, len(mine), 'tiles')
        json.dump(dict(sorted(patch.items())), open(pfile, 'w'), indent=1)
        if preview:
            make_preview(name, scr, mine)
    json.dump(dict(sorted(patch.items())), open(pfile, 'w'), indent=1)

def make_preview(name, scr, mine):
    """Render the screen tilemap twice: original and with patched tiles."""
    before = Image.open(scr.shot).convert('RGB')
    # Re-render patched tiles in greyscale over the screenshot cells that use them
    after = before.copy()
    shades = [(255, 255, 255), (170, 170, 170), (85, 85, 85), (0, 0, 0)]
    for layer in ('bg', 'win'):
        t = scr.maps[layer]
        if layer == 'win' and (t.get('wy') or 0) >= 144: continue
        oy = t.get('wy') or 0 if layer == 'win' else 0
        ox = (t.get('wx') or 7) - 7 if layer == 'win' else 0
        for r in range(18):
            for c in range(20):
                _, vaddr, _ = scr.cell(layer, r, c)
                if vaddr in mine:
                    p = tile_px(mine[vaddr][1])
                    for y in range(8):
                        for x in range(8):
                            X, Y = ox + c * 8 + x, oy + r * 8 + y
                            if X < 160 and Y < 144: after.putpixel((X, Y), shades[p[y][x]])
    im = Image.new('RGB', (330, 144), 'white'); im.paste(before, (0, 0)); im.paste(after, (170, 0))
    im.resize((660, 288), Image.NEAREST).save(os.path.join(ROOT, 'gfx', 'preview_%s.png' % name))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('names', nargs='*'); ap.add_argument('--preview', action='store_true')
    a = ap.parse_args(); run(a.names, a.preview)
