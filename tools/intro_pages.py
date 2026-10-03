"""Character intro story pages (pre-rendered 12px text images). Shared helpers for reading and rebuilding them."""
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
from PIL import Image
ROM = open(_R + '/orig/fkdfw.gbc', 'rb').read()
B4C = 0x4C * 0x4000
TABLE = 0x562D          # 8 x [bank][page list ptr], indexed by player 1's character ($D400)
COUNTS = [5, 4, 5, 5, 6, 6, 4, 4]
def w4c(a): return ROM[B4C + a - 0x4000] | ROM[B4C + a - 0x4000 + 1] << 8
def entries():
    return [(ROM[B4C + TABLE - 0x4000 + 3 * k], w4c(TABLE + 1 + 3 * k)) for k in range(8)]
def pages():
    """-> list of (char, page_in_display_order, record_addr, bank, list_slot_addr)"""
    out = []
    for k, (bank, lst) in enumerate(entries()):
        slots = [(lst + 2 * i, w4c(lst + 2 * i)) for i in range(1, COUNTS[k] + 1)][::-1]
        for p, (slot, rec) in enumerate(slots):
            out.append((k, p, rec, bank, slot))
    return out
def blocks(bank, rec):
    B = bank * 0x4000; at = lambda a: B + a - 0x4000
    t9, t8, mp = w4c(rec), w4c(rec + 2), w4c(rec + 4)
    def blk(p):
        n = ROM[at(p)] | ROM[at(p) + 1] << 8; return ROM[at(p) + 2:at(p) + 2 + n]
    w, h = ROM[at(mp)], ROM[at(mp) + 1]
    return blk(t9), blk(t8), w, h, ROM[at(mp) + 2:at(mp) + 2 + w * h]
def render(bank, rec):
    t9, t8, w, h, m = blocks(bank, rec)
    pal = [0, 85, 170, 255]
    im = Image.new('L', (w * 8, h * 8), 0)
    for r in range(h):
        for c in range(w):
            ti = m[r * w + c]
            src, o = (t9, ti * 16) if ti < 0x80 else (t8, (ti - 0x80) * 16)
            if o + 16 > len(src): continue
            for y in range(8):
                lo, hi = src[o + 2 * y], src[o + 2 * y + 1]
                for x in range(8): im.putpixel((c * 8 + x, r * 8 + y), pal[((lo >> (7 - x)) & 1) | (((hi >> (7 - x)) & 1) << 1)])
    return im
