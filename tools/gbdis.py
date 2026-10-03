import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys; sys.path.insert(0,_R + '/tools')
from emu import boot
_g=None
def dis(bank, addr, n=40):
    global _g
    if _g is None:
        _g=boot(_R + '/orig/fkdfw.gbc'); _g.run_frames(400)
    _g.mem_write(0x2100, bytes([bank]))
    return _g.disasm(addr, n)
if __name__=='__main__':
    print(dis(int(sys.argv[1],16), int(sys.argv[2],16), int(sys.argv[3]) if len(sys.argv)>3 else 40))
