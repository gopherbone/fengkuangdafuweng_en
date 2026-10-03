# tomenu.py rom state out.state : play (A presses) until the turn menu (Move/Cards/Other) is up, save a state there
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys; sys.path.insert(0, _R + '/tools')
from emu import boot
from PIL import Image
rom, st, out = sys.argv[1:4]
g = boot(rom); g.snapshot_load(path=st); g.input_set([])
def menu_up():
    g.screenshot_png('/tmp/_tm.png'); im = Image.open('/tmp/_tm.png').convert('RGB')
    return im.getpixel((115, 3)) == (255, 198, 0) and im.getpixel((140, 10)) == (255, 255, 255) and im.getpixel((5, 140)) != im.getpixel((5, 60))
for i in range(400):
    g.run_frames(10)
    if menu_up():
        g.run_frames(30)
        if menu_up(): g.snapshot_save(path=out); print('menu at step', i); break
    if i % 3 == 0: g.input_set(['a']); g.run_frames(4); g.input_set([])
else: print('no menu')
