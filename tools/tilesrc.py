"""tilesrc.py rom state [state...] : for each on-screen BG/window tile, find where its 16 bytes live in the ROM.
Prints source blocks (contiguous runs) so we know which graphics are stored uncompressed."""
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys; sys.path.insert(0, _R + '/tools')
from emu import boot
rom = open(sys.argv[1], 'rb').read()
g = boot(sys.argv[1])
for st in sys.argv[2:]:
    g.snapshot_load(path=st)
    lcdc = g.mem_read(0xFF40, 1)[0]
    vram = bytes.fromhex(g.cmd('mem.read', region='vram', offset=0, len=0x4000)['data'])
    used = set()
    for L in ('bg', 'win'):
        t = g.tilemap(L)
        if L == 'win' and (t.get('wy') or 0) >= 144: continue
        attrs = t.get('attrs')
        for r, row in enumerate(t['tiles'][:18]):
            for c in range(20):
                ti = int(row[2 * c:2 * c + 2], 16)
                a = int(attrs[r][2 * c:2 * c + 2], 16) if attrs else 0
                bank = (a >> 3) & 1
                addr = (ti * 16) if (lcdc & 0x10) else (0x1000 + ((ti ^ 0x80) - 0x80) * 16 if ti < 0x80 else ti * 16)
                if not (lcdc & 0x10): addr = 0x1000 + ti * 16 if ti < 0x80 else 0x800 + (ti - 0x80) * 16
                used.add((bank, addr, L, r, c))
    found = {}; missing = 0
    for bank, addr, L, r, c in sorted(used):
        tile = vram[bank * 0x2000 + addr: bank * 0x2000 + addr + 16]
        if tile.count(tile[0]) == 16: continue
        i = rom.find(tile)
        if i < 0: missing += 1; continue
        found.setdefault(i // 0x4000, []).append(i)
    print(st, 'tiles not found in ROM (compressed/generated):', missing)
    for b, offs in sorted(found.items()):
        print('   bank %02X: %d tiles, range %05X-%05X' % (b, len(offs), min(offs), max(offs)))
