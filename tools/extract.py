"""Build script/strings.json: every string entry point in the text banks, from the game's own tables.

Text banks use a two-level table: top[group] -> subtable, subtable[index] -> string (bank-local address).
Strings are terminated by FD (end of message) or FF (end).
"""
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys, json; sys.path.insert(0, _R + '/tools')
import fkdfw
rom = fkdfw.load_rom(); tab = fkdfw.load_table()

def w(b, a):
    o = b * 0x4000 + a - 0x4000; return rom[o] | rom[o + 1] << 8

def seg_end(b, a):
    """Address just past the terminator of the string at a."""
    o = b * 0x4000 + a - 0x4000; i = o; page = None
    while True:
        x = rom[i]
        if 0xF0 <= x <= 0xF8: i += 2; continue
        i += 1
        if x in (0xFD, 0xFF): return a + (i - o)

# (bank, top-table address, group index RAM var, entry index RAM var)
TWO_LEVEL = [(0x06, 0x4068, 'D685', 'C0DD'), (0x27, 0x4051, 'D685', 'C0DD'),
             (0x42, 0x4175, 'D685', 'C0DD')]

entries = {}   # (bank, addr) -> dict
def add(b, a, ref):
    e = entries.setdefault((b, a), {'bank': b, 'addr': a, 'refs': []})
    e['refs'].append(ref)

for b, top, gv, iv in TWO_LEVEL:
    a = top; subs = []
    while True:
        lim = min([s for s in subs if s > top] or [0x8000])
        if a >= lim: break
        subs.append(w(b, a)); a += 2
    starts = sorted(set(s for s in subs if s > top))
    for g, s in enumerate(subs):
        if s <= top: continue           # dummy group
        nxt = min([x for x in starts if x > s] + [0x8000])
        i = 0
        while s + 2 * i < nxt:
            p = w(b, s + 2 * i)
            if not (0x4000 <= p < 0x8000) or p < s: break
            add(b, p, 'T%02X:%d:%d' % (top & 0xFF, g, i)); i += 1
            nxt = min(nxt, p)   # subtable can't extend past the strings it points to

# Bank $4C: character names, single-level table of 8 pointers at $4D58 (index $D67C).
for i in range(8):
    add(0x4C, w(0x4C, 0x4D58 + 2 * i), 'T58:%d' % i)

# Bank $38: goal-city and town names (pointer lists at $71E4 / $72A5), copied 7 bytes at a time to $D6D4.
for lst, n in ((0x71E4, 29), (0x72A5, 31)):
    for i in range(n):
        add(0x38, w(0x38, lst + 2 * i), 'names38')

# Bank $30: region names (North/Central/South/East) for disaster events, table $433B, copied 7 bytes to $D6D4.
for i in range(4):
    add(0x30, w(0x30, 0x433B + 2 * i), 'regions30')

# Bank $25: property-name strings (record table at $455E). Take every FD-terminated name in the name block.
b = 0x25; a = 0x4785
while a < 0x4C1D:
    add(b, a, 'names25'); a = seg_end(b, a)

# Fill gaps: any terminator-delimited run between known strings that nobody points to (kept, flagged orphan)
for b in sorted(set(k[0] for k in entries) & {0x06, 0x27, 0x42}):
    addrs = sorted(a for (bb, a) in entries if bb == b)
    for a in addrs:
        e = seg_end(b, a)
        if e not in [x for x in addrs] and e < max(addrs) and (b, e) not in entries:
            # walk forward through orphans until we hit a known start
            x = e
            while x < max(addrs) and (b, x) not in entries:
                entries[(b, x)] = {'bank': b, 'addr': x, 'refs': ['orphan']}
                x = seg_end(b, x)

out = []
for (b, a), e in sorted(entries.items()):
    end = seg_end(b, a); o = b * 0x4000 + a - 0x4000
    raw = rom[o: o + (end - a)]
    e.update(end=end, raw=raw.hex(), zh=fkdfw.decode(rom, o, tab, end - a)[0])
    e['id'] = '%02X:%04X' % (b, a)
    out.append(e)
# mark entries that start inside another string (shared tails)
spans = [(x['bank'], x['addr'], x['end']) for x in out]
for x in out:
    x['inside'] = [ '%02X:%04X' % (b, a) for b, a, e in spans if b == x['bank'] and a < x['addr'] < e ]
json.dump(out, open(_R + '/script/strings.json', 'w'), ensure_ascii=False, indent=1)
import collections
print(len(out), collections.Counter(x['bank'] for x in out), 'orphans', sum(1 for x in out if x['refs'] == ['orphan']),
      'inside', sum(1 for x in out if x['inside']))
