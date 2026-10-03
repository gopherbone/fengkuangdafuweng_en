"""find_desc.py rom state 'keys' : run inputs (tokens: key, wN) and report every screen descriptor loaded
(the generic loader at $0F80 copies it to $C100), with its ROM location."""
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys; sys.path.insert(0, _R + '/tools')
from emu import boot
rom = open(sys.argv[1], 'rb').read()
g = boot(sys.argv[1]); g.snapshot_load(path=sys.argv[2])
g.break_add(0x0F8B)
def run(n):
    for _ in range(n):
        r = g.run_frames(1)
        if r.get('stopped'):
            d = g.mem_read(0xC100, 13); locs = []
            i = rom.find(d)
            while i != -1: locs.append('%06X' % i); i = rom.find(d, i + 1)
            print(d.hex(), 'at', locs)
for t in sys.argv[3].split(','):
    if t.startswith('w'): run(int(t[1:]))
    else:
        g.input_set([t]); run(6); g.input_set([]); run(12)
