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

def build_region(scr, reg):
    """Return {cell: new_tile_bytes} for one region spec."""
    layer = reg.get('layer', 'bg'); r0, c0, h, w = reg['rect']
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
    # keep untouched pixels outside "clear" area? regions are fully redrawn.
    lines = reg['lines']
    bold = reg.get('bold', False)
    lh = reg.get('line_height', 16)
    top = reg.get('top', (H - lh * len(lines)) // 2 + (lh - 12) // 2 - 1)
    for i, s in enumerate(lines):
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

def run(names, preview=False):
    specs = json.load(open(os.path.join(ROOT, 'gfx', 'specs.json')))
    pfile = os.path.join(ROOT, 'gfx', 'patch.json')
    patch = json.load(open(pfile)) if os.path.exists(pfile) else {}
    patch = {k: v for k, v in patch.items() if isinstance(v, dict)}    # per-screen patches
    for name in names or [k for k in specs if not k.startswith('_')]:
        spec = specs[name]
        scr = Screen(spec['state'])
        mine = {}
        for reg in spec['regions']:
            cells, new = build_region(scr, reg)
            cand = {}
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
                cand[cell] = (src, vaddr)
            anchors = sorted(v[0][0] for v in cand.values() if len(v[0]) == 1)
            for cell, (src, vaddr) in cand.items():
                if len(src) > 1:
                    if not anchors:
                        raise SystemExit('%s: ambiguous tile at %s and no anchor' % (name, cell))
                    mid = anchors[len(anchors) // 2]
                    src = [min(src, key=lambda o: abs(o - mid))]
                if vaddr in mine and mine[vaddr][1] != new[cell]:
                    raise SystemExit('%s: tile %s shown in two cells with different English content' % (name, vaddr))
                mine[vaddr] = (src[0], new[cell])
        patch[name] = {'%06X' % off: data.hex() for _, (off, data) in mine.items()}
        print(name, len(mine), 'tiles')
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
