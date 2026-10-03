# hudshot.py rom state out.png : play until the board HUD draws (bank 08:$505E), then screenshot it zoomed
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys,glob; sys.path.insert(0,_R + '/tools')
from emu import boot
from PIL import Image
g=boot(sys.argv[1]); g.snapshot_load(path=sys.argv[2])
g.break_add(0x505E, bank=0x08)
hit=False
for i in range(3000):
    r=g.run_frames(1)
    if r.get('stopped'): hit=True; break
    if i%40==0: g.input_press(['a'],frames=4)
g.break_clear(); g.run_frames(40)
g.screenshot_png(sys.argv[3],scale=2)
Image.open(sys.argv[3]).crop((0,160,320,288)).resize((960,384),Image.NEAREST).save(sys.argv[3])
print('hud hit',hit)
