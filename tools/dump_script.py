"""Static scan: find plausible text strings in every bank and decode them."""
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys, json, collections; sys.path.insert(0, _R + '/tools')
import fkdfw
rom = fkdfw.load_rom(); tab = fkdfw.load_table()
valid = {k for k, v in tab.items() if v != '<blank>'}
def score(off, maxlen=600):
    """Walk a candidate string; return (end, nglyphs, nbad, nprefix) or None."""
    i = off; page = None; ng = nb = npf = 0
    while i < off + maxlen and i < len(rom):
        b = rom[i]
        if 0xF0 <= b <= 0xF5:
            page = b & 0xF; c = rom[i+1]; i += 2; npf += 1
            if c >= 0xE0: nb += 1; continue
        elif b in (0xF6, 0xF7, 0xF8): return None
        elif b >= 0xE0:
            i += 1
            if b in (0xFF, 0xFD): return (i, ng, nb, npf)
            continue
        else:
            if page is None: return None   # strings start with a page select
            c = b; i += 1
        ng += 1
        if page * 256 + c not in valid: nb += 1
    return None
out = []
for bank in range(len(rom) // 0x4000):
    if 9 <= bank <= 0xD: continue   # font banks
    base = bank * 0x4000; i = base
    while i < base + 0x4000:
        r = score(i) if 0xF0 <= rom[i] <= 0xF5 else None
        if r and r[1] >= 2 and r[2] <= r[1] * 0.05 and r[3] >= 1:
            out.append((i, r[0])); i = r[0]
        else: i += 1
by = collections.Counter(o // 0x4000 for o, _ in out)
print(len(out), sorted((hex(b), n) for b, n in by.items() if n >= 3))
with open(_R + '/script/static_dump.tsv', 'w') as f:
    for o, e in out:
        f.write('%06X\t%02X:%04X\t%s\n' % (o, o // 0x4000, 0x4000 + o % 0x4000 if o >= 0x4000 else o, fkdfw.decode(rom, o, tab, e - o)[0]))
