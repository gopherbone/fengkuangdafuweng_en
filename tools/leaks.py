# leaks.py rom state outdir frames [seed] : autoplay the ENGLISH build and log every Chinese glyph drawn by the
# original renderer (bank, address of the glyph byte), grouped into runs. Also takes periodic screenshots.
import sys, os, json, random; sys.path.insert(0, '/Users/nick/crazyrichman_claude/tools')
from emu import boot
rom, st, out, frames = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
seed = int(sys.argv[5]) if len(sys.argv) > 5 else 11
os.makedirs(out, exist_ok=True)
g = boot(rom); g.snapshot_load(path=st); random.seed(seed)
hits = []
def start():
    g.cmd('trace.start', max=4000000, with_mem=True, pc_lo='$0aa6', pc_hi='$0aeb')
def drain():
    g.cmd('trace.stop'); n = g.cmd('trace.stop')['total'] if False else None
    off = 0; lo = hi = None
    while True:
        d = g.cmd('trace.dump', limit=100000, offset=off); off += 100000
        if not d['entries']: break
        for e in d['entries']:
            for m in e.get('mem', []):
                if m[0] == 'w' and m[1] == 'c0de': lo = int(m[2], 16)
                elif m[0] == 'w' and m[1] == 'c0df': hi = int(m[2], 16)
                elif m[0] == 'r' and m[1] == '4000' and lo is not None and hi is not None:
                    hits.append((int(m[2], 16), (hi << 8 | lo) - 1)); lo = hi = None
    start()
start(); f = 0; nshot = 0
while f < frames:
    k = 'a' if random.random() < 0.85 else random.choice(['down', 'b', 'right', 'up'])
    g.input_press([k], frames=5); g.run_frames(25); f += 30
    if f % 1500 < 30:
        drain(); g.screenshot_png(f'{out}/f{f:06d}.png'); g.snapshot_save(path=f'{out}/f{f:06d}.state')
drain()
json.dump(hits, open(f'{out}/hits.json', 'w'))
print('glyph hits', len(hits))
