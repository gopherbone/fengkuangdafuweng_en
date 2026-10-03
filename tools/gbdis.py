import sys; sys.path.insert(0,'/Users/nick/crazyrichman_claude/tools')
from emu import boot
_g=None
def dis(bank, addr, n=40):
    global _g
    if _g is None:
        _g=boot('/Users/nick/crazyrichman_claude/orig/fkdfw.gbc'); _g.run_frames(400)
    _g.mem_write(0x2100, bytes([bank]))
    return _g.disasm(addr, n)
if __name__=='__main__':
    print(dis(int(sys.argv[1],16), int(sys.argv[2],16), int(sys.argv[3]) if len(sys.argv)>3 else 40))
