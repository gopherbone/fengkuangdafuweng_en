import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import json, sys; sys.path.insert(0, _R + '/tools'); import fkdfw
rom = fkdfw.load_rom(); t = fkdfw.load_table()
h = json.load(open(sys.argv[1]))
runs = []
for b, a in h:
    if runs and runs[-1][0] == b and 0 < a - runs[-1][2] <= 3: runs[-1][2] = a
    else: runs.append([b, a, a])
u = {}
for b, a, e in runs: u.setdefault((b, a), e)
for (b, a), e in sorted(u.items()):
    s = fkdfw.decode(rom, b * 0x4000 + a - 0x4000, t, e - a + 2)[0] if 0x4000 <= a < 0x8000 else '(RAM/ROM0 %04X)' % a
    print('%02X:%04X' % (b, a), s[:60])
