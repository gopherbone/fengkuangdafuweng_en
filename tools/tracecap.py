import sys, json; sys.path.insert(0,'/Users/nick/crazyrichman_claude/tools')
def capture(g, frames, cap=4000000):
    g.cmd('trace.start', max=cap, with_regs=True, with_mem=True)
    g.run_frames(frames)
    r=g.cmd('trace.stop')
    total=min(r['total'],cap); out=[]
    off=0
    while off<total:
        d=g.cmd('trace.dump', limit=100000, offset=off)
        out+=d['entries']; off+=100000
        if not d['entries']: break
    return out
