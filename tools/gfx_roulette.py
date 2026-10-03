"""Goal-roulette screen (bank $39) -> gfx/patch.json["roulette"].

The screen descriptor ($39:$4430) carries the frame; the 4x4 city grid tiles ($1F-$7A, 92 tiles) come from a
separate block (table $39:$50CB entry 0 -> $50DD, copied to $91F0 with BC=$05C0 at $4046). A few grid tiles are
shared between cells, so: four cells get private copies in slots $7B-$7E, the grid block is re-emitted (96 tiles)
in free space, the copy length is patched, and the descriptor map is rebuilt in-bank.
"""
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys, os, json
sys.path.insert(0, _R + '/tools')
from gfx import ROM, Rebuild, build_region

ROOT = _R
BANK = 0x39
DESC = 0x0E4430
FREE = 0x5C40
TABLE0 = 0x50CB
GRID = 0x50DD
GRID_N = 92
FIRST = 0x1F
LEN_PATCH = 0x4046          # LD BC,$05C0
CODES = ["TPE", "TXG", "CYI", "KHH", "TTT", "MZG", "SNW", "KEL", "CHW", "TNN", "HUN", "GNI", "NTO", "JDE", "TYN", "ILN"]

def off(addr): return BANK * 0x4000 + addr - 0x4000

def main():
    rb = Rebuild(DESC, 0)
    w, h, m = rb.map
    grid = bytearray(ROM[off(GRID):off(GRID) + GRID_N * 16])
    cells = []
    for k in range(16):
        r0, c0 = 4 + 2 * (k // 4), 1 + 3 * (k % 4)
        cells.append([(r, c) for r in (r0, r0 + 1) for c in range(c0, c0 + 3)])
    allcells = [c for cc in cells for c in cc]
    nxt = FIRST + GRID_N
    def get(ti): return bytes(grid[(ti - FIRST) * 16:(ti - FIRST) * 16 + 16])
    for (r, c) in allcells:
        ti = m[r * w + c]
        if sum(1 for (rr, cc) in allcells if m[rr * w + cc] == ti) > 1:
            data = get(ti); m[r * w + c] = nxt; grid += data; nxt += 1
    assert nxt <= 0x80, hex(nxt)
    for k, cc in enumerate(cells):
        r0, c0 = cc[0]
        fake = {(r, c): (get(m[r * w + c]), m[r * w + c], 0) for (r, c) in cc}
        reg = dict(rect=[r0, c0, 2, 3], lines=[CODES[k]], align='center', bg=2, ink=0, shadow=1, erase=[0, 1],
                   inset=[1, 1, 1, 1], top=1)
        _, new = build_region(None, reg, fake)
        for cell, data in new.items():
            ti = fake[cell][1]; grid[(ti - FIRST) * 16:(ti - FIRST) * 16 + 16] = data
    out = rb.emit(FREE)
    body_end = FREE + len(bytes.fromhex(out['%06X' % off(FREE)]))
    gaddr = (body_end + 0xF) & ~0xF
    assert gaddr + len(grid) <= 0x8000
    # the code reads the byte right after the copied block as the grid's CGB palette (attribute fill)
    attr = ROM[off(GRID) + GRID_N * 16]
    out['%06X' % off(gaddr)] = (bytes(grid) + bytes([attr])).hex()
    out['%06X' % off(TABLE0)] = gaddr.to_bytes(2, 'little').hex()
    out['%06X' % off(LEN_PATCH)] = bytes([0x01]).hex() + len(grid).to_bytes(2, 'little').hex()
    pf = os.path.join(ROOT, 'gfx', 'patch.json')
    patch = json.load(open(pf)); patch['roulette'] = out
    json.dump(dict(sorted(patch.items())), open(pf, 'w'), indent=1)
    print('roulette: grid tiles', len(grid) // 16, 'private copies', nxt - FIRST - GRID_N)

if __name__ == '__main__':
    main()
