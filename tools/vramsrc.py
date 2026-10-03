# vramsrc.py rom state [frames] : dump the visible BG/window tilemap and, per distinct tile, where its 16 bytes occur
# in the ORIGINAL rom (bank:addr). Helps find the source of pre-drawn graphics that are not loaded via $0F80.
import sys; sys.path.insert(0, '/Users/nick/crazyrichman_claude/tools')
from emu import boot
rom = open('/Users/nick/crazyrichman_claude/orig/fkdfw.gbc', 'rb').read()
g = boot(sys.argv[1]); g.snapshot_load(path=sys.argv[2]); g.input_set([]); g.run_frames(int(sys.argv[3]) if len(sys.argv) > 3 else 2)
lcdc = g.mem_read(0xFF40, 1)[0]; wy, wx = g.mem_read(0xFF4A, 1)[0], g.mem_read(0xFF4B, 1)[0]
use_win = bool(lcdc & 0x20) and wy < 144
mapb = (0x9C00 if lcdc & 0x40 else 0x9800) if use_win else (0x9C00 if lcdc & 8 else 0x9800)
scy, scx = g.mem_read(0xFF42, 1)[0], g.mem_read(0xFF43, 1)[0]
print('lcdc %02X win %s wy %d wx %d map %04X scy %d scx %d' % (lcdc, use_win, wy, wx, mapb, scy, scx))
m = g.mem_read(mapb, 0x400)
# CGB attributes (VRAM bank 1) to know tile banks
for r in range(18):
    print(' '.join('%02x' % m[r * 32 + c] for c in range(20)))
def taddr(t): return 0x8000 + t * 16 if lcdc & 0x10 else 0x9000 + ((t if t < 0x80 else t - 0x100) * 16)
seen = set()
for r in range(18):
    for c in range(20):
        t = m[r * 32 + c]
        if t in seen: continue
        seen.add(t)
        d = g.mem_read(taddr(t), 16)
        if d in (b'\0' * 16, b'\xff' * 16): continue
        locs = []; i = rom.find(d)
        while i != -1 and len(locs) < 4: locs.append('%02X:%04X' % (i // 0x4000, 0x4000 + i % 0x4000 if i >= 0x4000 else i)); i = rom.find(d, i + 1)
        print('tile %02x @r%dc%d %s' % (t, r, c, ' '.join(locs) or '-'))
