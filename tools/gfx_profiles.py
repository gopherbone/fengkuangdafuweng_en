"""Character profile screens (8 characters) -> gfx/patch.json["profiles"].

Layout of the original: a common screen (descriptor $4C:$4DD3, data in bank $4F) plus a per-character tile block
($4D0 bytes -> $8800, table $4F:$4909, copied by code at $4F:$4838). Text cells in the value and trait areas point
at shared tiles in places, so:
  * the common blocks are rebuilt into free space at the end of bank $4F (descriptor keeps bank $4F, whose code
    the screen far-calls), with every per-character text cell remapped to its own per-character tile index;
  * the 8 per-character blocks are rebuilt (extended) in bank $7C and copied by FarCopyProf ($2FF0).
"""
import sys, json, os
sys.path.insert(0, '/Users/nick/crazyrichman_claude/tools')
import gfx
from gfx import ROM, Rebuild, build_region

ROOT = '/Users/nick/crazyrichman_claude'
DESC = 0x130DD3
BANK = 0x4F
BASE_START = 0x6FA0          # free space at the end of bank $4F
CHAR_BANK = 0x7C
TABLE = 0x4909
COPY_CODE = 0x4838
FARCOPY = 0x1F00
OLD_LEN = 0x4D0

INFO = [('Meatball', 'Hell', '10', ['Can hold up to', '8 cards at once...']),
        ('Dubi', 'Heaven', '10', ['Investing often brings', 'lucky surprises...']),
        ('Penny Qian', 'Taiwan', '18', ['Gets surprise', 'allowance money...']),
        ('Wu No-Guts', 'Taiwan', '31', ['Loyal henchmen shield', 'him from dirty tricks...']),
        ('Sachiko', 'Japan', '21', ["Her husband's blessing", 'speeds her to the goal...']),
        ('Hanamura', 'Japan', '23', ['Can miraculously', 'roll a 7 on one die...']),
        ('Xianglan', 'China', '16', ['A kung fu master even', 'the Poverty God fears...']),
        ('Xiao Ming', 'China', '8', ['Plays pitiful to get', 'his fines waived...'])]

TOP = dict(rect=[2, 9, 5, 11], top=1, line_height=10, tab=32)        # labels cols 9-12 common, values 13-18 per char
HEAD = dict(rect=[9, 3, 2, 14], lines=['- Trait -'], align='center', top=1)
BTN_OK = dict(rect=[15, 10, 2, 4], lines=['OK'], align='center', bg=2, ink=0, shadow=3, erase=[0, 3], inset=[2, 2, 2, 2], top=1)
BTN_NO = dict(rect=[15, 16, 2, 4], lines=['Back'], align='center', bg=2, ink=0, shadow=3, erase=[0, 3], inset=[2, 2, 2, 2], top=1)
TRAIT = dict(rect=[11, 3, 3, 14], align='center', top=1, line_height=12)
PERCHAR_CELLS = [(r, c) for r in range(2, 7) for c in range(13, 20)] + [(r, c) for r in range(11, 14) for c in range(3, 17)]
COMMON_CELLS = [(r, c) for r in range(2, 7) for c in range(9, 13)] + [(r, c) for r in range(9, 11) for c in range(3, 17)] + \
               [(r, c) for r in (15, 16) for c in list(range(10, 14)) + list(range(16, 20))]

def rd(bank, addr, n):
    o = bank * 0x4000 + addr - 0x4000; return ROM[o:o + n]

def main():
    rb = Rebuild(DESC, BANK)
    w, h, m = rb.map
    ptrs = [rd(BANK, TABLE + 2 * i, 2) for i in range(8)]
    ptrs = [p[0] | p[1] << 8 for p in ptrs]
    blocks = [bytearray(rd(BANK, p, OLD_LEN)) for p in ptrs]
    # common cells: private copies of shared base tiles
    rb.unshare([c for c in COMMON_CELLS if m[c[0] * w + c[1]] < 0x80])
    # per-character cells: each gets its own per-character tile index
    nxt = 0x80 + OLD_LEN // 16
    for (r, c) in PERCHAR_CELLS:
        ti = m[r * w + c]
        uses = sum(1 for k in range(w * h) if m[k] == ti)
        if ti >= 0x80 and uses == 1:
            continue
        old = rb.get_tile(ti) if ti < 0x80 else None
        m[r * w + c] = nxt
        for b, blk in enumerate(blocks):
            blk += old if old is not None else blk[(ti - 0x80) * 16:(ti - 0x80) * 16 + 16]
        nxt += 1
    assert nxt <= 0x100, hex(nxt)
    def tile(blk, ti):
        return bytes(rb.get_tile(ti)) if ti < 0x80 else bytes(blk[(ti - 0x80) * 16:(ti - 0x80) * 16 + 16])
    def cells_for(blk, rect):
        r0, c0, hh, ww = rect
        return {(r, c): (tile(blk, m[r * w + c]), m[r * w + c], 0) for r in range(r0, r0 + hh) for c in range(c0, c0 + ww)}
    common = {}
    for k, (name, frm, age, trait) in enumerate(INFO):
        blk = blocks[k]
        regs = [dict(TOP, lines=['Name:\t' + name, 'From:\t' + frm, 'Age:\t' + age]), HEAD, dict(TRAIT, lines=trait), BTN_OK, BTN_NO]
        for reg in regs:
            cells = cells_for(blk, reg['rect'])
            _, new = build_region(None, reg, cells)
            for cell, data in new.items():
                ti = cells[cell][1]
                if ti < 0x80:
                    if ti in common and common[ti] != data:
                        raise SystemExit('profile: common tile %02X differs between characters (cell %s)' % (ti, cell))
                    common[ti] = data
                else:
                    blk[(ti - 0x80) * 16:(ti - 0x80) * 16 + 16] = data
    for ti, data in common.items():
        rb.set_tile(ti, data)
    out = {}
    # common blocks at the end of bank $4F, descriptor repointed (bank unchanged)
    body = bytearray(); P = []
    def put(data):
        P.append(BASE_START + len(body)); body.extend(data)
    put(len(rb.t9000).to_bytes(2, 'little') + rb.t9000)
    put(len(rb.t8800).to_bytes(2, 'little') + rb.t8800)
    put(bytes([w, h]) + m)
    put(bytes(rb.attr[:2]) + rb.attr[2])
    assert BASE_START + len(body) <= 0x8000
    out['%06X' % (BANK * 0x4000 + BASE_START - 0x4000)] = bytes(body).hex()
    desc = bytearray(ROM[DESC:DESC + 13])
    for i, p in enumerate(P):
        desc[1 + 2 * i:3 + 2 * i] = p.to_bytes(2, 'little')
    out['%06X' % DESC] = bytes(desc).hex()
    # per-character blocks in bank $7C
    newlen = (nxt - 0x80) * 16
    cb = bytearray([CHAR_BANK]); tbl = bytearray()
    for blk in blocks:
        assert len(blk) == newlen
        tbl += (0x4000 + len(cb)).to_bytes(2, 'little'); cb += blk
    assert len(cb) <= 0x4000
    out['%06X' % (CHAR_BANK * 0x4000)] = bytes(cb).hex()
    out['%06X' % (BANK * 0x4000 + TABLE - 0x4000)] = bytes(tbl).hex()
    code = bytes([0x21, 0x00, 0x88, 0x01]) + newlen.to_bytes(2, 'little') + bytes([0xCD]) + FARCOPY.to_bytes(2, 'little')
    out['%06X' % (BANK * 0x4000 + COPY_CODE - 0x4000)] = code.hex()
    pf = os.path.join(ROOT, 'gfx', 'patch.json')
    patch = json.load(open(pf)); patch['profiles'] = out
    json.dump(dict(sorted(patch.items())), open(pf, 'w'), indent=1)
    print('profiles: common tiles', len(common), 'per-char block', hex(newlen), 'new indices', hex(nxt))

if __name__ == '__main__':
    main()
