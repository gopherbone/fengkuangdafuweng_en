# autoplay.py rom state outdir frames : press A periodically, log renderer string reads at $0A43
import sys, json, os, random; sys.path.insert(0,'/Users/nick/crazyrichman_claude/tools')
from emu import boot
rom, st, out, frames = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
os.makedirs(out, exist_ok=True)
g=boot(rom); g.snapshot_load(path=st)
random.seed(7)
starts=[]; last=None; shots=0
def drain():
    global last
    r=g.cmd('trace.stop'); n=r['total']; off=0
    while off<n:
        d=g.cmd('trace.dump',limit=100000,offset=off); off+=100000
        pend=None
        for e in d['entries']:
            for m in e.get('mem',[]):
                if m[0]!='r': continue
                if e['pc']=='0a43': pend=int(m[1],16)
                elif e['pc']=='0aad' and m[1]=='4000' and pend is not None:
                    key=(int(m[2],16),pend)  # [$4000] holds the mapped bank number
                    if last is None or not (last[0]==key[0] and 0< key[1]-last[1] <=3):
                        starts.append(key)
                    last=key; pend=None
    g.cmd('trace.start',max=4000000,with_mem=True,pc_lo='$0a43',pc_hi='$0aeb')
g.cmd('trace.start',max=4000000,with_mem=True,pc_lo='$0a43',pc_hi='$0aeb')
f=0
while f<frames:
    k = 'a' if random.random()<0.85 else random.choice(['down','b','right'])
    g.input_press([k],frames=5); g.run_frames(35); f+=40
    if f % 2000 < 40:
        drain(); g.screenshot_png(f'{out}/f{f:06d}.png'); g.snapshot_save(path=f'{out}/f{f:06d}.state')
drain()
json.dump(starts, open(f'{out}/starts.json','w'))
print(len(starts))
