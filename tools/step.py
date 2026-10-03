# step.py rom in_state out_state 'seq' [shot.png]; seq tokens: key, key*N(hold frames), wN
import sys; sys.path.insert(0,'/Users/nick/crazyrichman_claude/tools')
from emu import boot
rom, ins, outs, seq = sys.argv[1:5]; shot = sys.argv[5] if len(sys.argv)>5 else outs.replace('.state','.png')
g=boot(rom); g.snapshot_load(path=ins)
for t in seq.split(','):
    t=t.strip()
    if not t: continue
    if t[0]=='w' and t[1:].isdigit(): g.run_frames(int(t[1:]))
    else:
        k,_,n=t.partition('*'); g.input_press([k],frames=int(n or 6)); g.run_frames(12)
g.snapshot_save(path=outs); g.screenshot_png(shot,scale=2); g.close()
