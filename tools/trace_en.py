# trace_en.py rom state frames : log each English string start (id, c0c8, d686, c12e, d66d, insert flag) with screenshots
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys, json; sys.path.insert(0, _R + '/tools')
from emu import boot
rom, st, frames = sys.argv[1], sys.argv[2], int(sys.argv[3])
sym = {l.split()[1]: int(l.split()[0].split(':')[1], 16) for l in open(_R + '/build/fkdfw_en.sym') if l[0] != ';' and ':' in l.split()[0]}
idx = json.load(open(_R + '/build/index.json'))['index']
rev = {v: k for k, v in idx.items()}
S = {x['id']: x for x in json.load(open(_R + '/script/strings.json'))}
g = boot(rom); g.snapshot_load(path=st)
g.break_add(sym['EnStart'])
f = 0; n = 0
while f < frames:
    r = g.run_frames(10); f += 10
    if r.get('stopped'):
        rg = g.regs(); hl = int(rg['hl'], 16)
        b = g.mem_read(hl, 3)
        rd = lambda a, k=2: g.mem_read(a, k)
        w = lambda a: rd(a)[0] | rd(a)[1] << 8
        i = b[1] | b[2] << 8 if b[0] == 0xF6 else None
        sid = rev.get(i, '?')
        print('%5d %-8s c0c8=%04X d686=%04X c12e=%04X d66d=%02X ins=%d hl=%04X  %s' % (f, sid, w(0xC0C8), w(0xD686), w(0xC12E), rd(0xD66D, 1)[0], rd(0xC798, 1)[0], hl, S.get(sid, {}).get('zh', '')[:30]))
        g.screenshot_png(_R + '/shots/te_%03d.png' % n); n += 1
        continue
    if (f // 10) % 3 == 0: g.input_press(['a'], frames=4)
