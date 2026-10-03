"""gridshot.py rom state out.png [win] : screenshot x4 with the BG tilemap grid (scroll applied) labelled in
TILEMAP coordinates (row,col) - the coordinates tools/gfx.py specs use. With 'win', grid the window instead."""
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys; sys.path.insert(0, _R + '/tools')
from emu import boot
from PIL import Image, ImageDraw
g = boot(sys.argv[1]); g.snapshot_load(path=sys.argv[2]); g.run_frames(1)
win = len(sys.argv) > 4 and sys.argv[4] == 'win'
scy, scx = g.mem_read(0xFF42, 2)
wy, wx = g.mem_read(0xFF4A, 2)
g.screenshot_png(sys.argv[3])
S = 4
im = Image.open(sys.argv[3]).convert('RGB').resize((160 * S, 144 * S), Image.NEAREST)
out = Image.new('RGB', (160 * S + 40, 144 * S + 30), 'white'); out.paste(im, (30, 20)); d = ImageDraw.Draw(out)
if win: ox, oy = wx - 7, wy
else: ox, oy = -scx, -scy
for C in range(32):
    x = (C * 8 + ox) % 256
    if x <= 160:
        d.line([(30 + x * S, 20), (30 + x * S, 20 + 144 * S)], fill=(255, 0, 0) if C % 5 == 0 else (255, 160, 160))
        if x + 4 < 160: d.text((32 + x * S + 8, 4), str(C), fill=(0, 0, 0))
for R in range(32):
    y = (R * 8 + oy) % 256
    if y <= 144:
        d.line([(30, 20 + y * S), (30 + 160 * S, 20 + y * S)], fill=(255, 0, 0) if R % 5 == 0 else (255, 160, 160))
        if y + 4 < 144: d.text((4, 20 + y * S + 10), str(R), fill=(0, 0, 0))
out.save(sys.argv[3])
print('scy,scx', scy, scx, 'wy,wx', wy, wx)
