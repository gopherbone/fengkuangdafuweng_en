import sys, json; sys.path.insert(0,'/Users/nick/crazyrichman_claude/tools')
from emu import boot
from PIL import Image
# usage: play.py rom outprefix 'seq'  seq: tokens like a,b,start,up,down,w60 (wait frames), s (shot)
rom, pre, seq = sys.argv[1], sys.argv[2], sys.argv[3]
snap = sys.argv[4] if len(sys.argv)>4 else None
g = boot(rom)
if snap: g.snapshot_load(path=snap)
shots=[]
for t in seq.split(','):
    t=t.strip()
    if not t: continue
    if t.startswith('w'): g.run_frames(int(t[1:]))
    elif t=='s':
        p=f'{pre}_{len(shots):02d}.png'; g.screenshot_png(p,scale=2); shots.append(p)
    elif t.startswith('save:'): g.snapshot_save(path=t[5:])
    else:
        g.input_tap(t); g.run_frames(20)
g.close()
if shots:
    ims=[Image.open(p) for p in shots]; w,h=ims[0].size; cols=min(4,len(ims)); rows=(len(ims)+cols-1)//cols
    s=Image.new('RGB',(cols*(w+6),rows*(h+6)),'white')
    for i,im in enumerate(ims): s.paste(im,((i%cols)*(w+6),(i//cols)*(h+6)))
    s.save(f'{pre}_sheet.png')
