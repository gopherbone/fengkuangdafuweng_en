# survey.py rom state outdir frames every  : autoplay (mostly A), screenshot every N frames, contact sheets of 16
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys, os, random; sys.path.insert(0, _R + '/tools')
from emu import boot
from PIL import Image
rom, st, out, frames, every = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
seed = int(sys.argv[6]) if len(sys.argv) > 6 else 7
os.makedirs(out, exist_ok=True)
g = boot(rom); g.snapshot_load(path=st); random.seed(seed)
shots = []; f = 0; nxt = every
while f < frames:
    k = 'a' if random.random() < float(os.environ.get('PA', '0.85')) else random.choice(['down', 'b', 'right', 'up', 'left'])
    g.input_press([k], frames=5); g.run_frames(25); f += 30
    if f >= nxt:
        p = f'{out}/f{f:06d}.png'; g.screenshot_png(p); shots.append(p); nxt += every
        g.snapshot_save(path=f'{out}/f{f:06d}.state')
g.snapshot_save(path=f'{out}/final.state'); g.close()
for s in range(0, len(shots), 16):
    ims = [Image.open(p) for p in shots[s:s + 16]]
    sh = Image.new('RGB', (4 * 164, 4 * 148), 'white')
    for i, im in enumerate(ims): sh.paste(im, ((i % 4) * 164, (i // 4) * 148))
    sh.save(f'{out}/sheet{s // 16:02d}.png')
print(len(shots))
