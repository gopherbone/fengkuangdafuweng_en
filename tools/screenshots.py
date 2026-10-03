"""Release screenshots: replay short input sequences from saved states on the English build -> docs/screenshots/.

Each recipe = (name, state, steps). A step is a key name (press for 5 frames, then wait 30), ('wait', n),
or ('setram', addr, bytes). The screenshot is taken after the last step, scaled 3x.
"""
import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys, os
sys.path.insert(0, _R + '/tools')
from emu import boot
from PIL import Image

ROOT = _R
OUT = os.path.join(ROOT, 'docs', 'screenshots')

def run(g, steps):
    for s in steps:
        if isinstance(s, tuple):
            if s[0] == 'wait': g.run_frames(s[1])
            elif s[0] == 'setram': g.mem_write(s[1], list(s[2]))
            elif s[0] == 'call': s[1](g)
            elif s[0] == 'hold':
                g.input_set([s[1]]); g.run_frames(4); g.input_set([]); g.run_frames(s[2])
        else:
            g.input_set([s]); g.run_frames(5); g.input_set([]); g.run_frames(30)

def force_sell(g):
    """Put the current player in debt and enter the forced-sale mode ($C22D = $51) at the $05:$548A dispatcher."""
    p = g.mem_read(0xC1D8, 2); p = p[0] | p[1] << 8
    g.mem_write(p - 1 + 0x3A, [1])
    g.break_add(0x548A, bank=5)
    for _ in range(300):
        if g.run_frames(1).get('stopped'): break
    g.break_clear(); g.mem_write(0xC22D, [0x51]); g.mem_write(0xD67F, [0])

RECIPES = [
    ('news', 'snaps/en_gamestart.state', [('hold', 'a', 36)] * 31),
    ('roulette', 'snaps/en_gamestart.state', [('hold', 'a', 36)] * 70),
    ('wish', 'snaps/wish.state', [('wait', 20)] + [('hold', 'a', 40)] * 3),
    ('month', 'snaps/release/m49.state', [('hold', 'a', 26)] * 3),
    ('assets', 'snaps/other.state', [('wait', 20), 'down', 'down', ('hold', 'a', 90)]),
    ('setup', 'snaps/other.state', [('wait', 20), 'down', 'down', 'down', ('hold', 'a', 90)]),
    ('turnmenu', 'snaps/turnmenu.state', [('wait', 60)]),
    ('profile', 'st/e_sel.state', [('hold', 'a', 60)]),
    ('charselect', 'st/e_sel.state', [('wait', 60)]),
    ('keyboard', 'st/k3.state', [('wait', 60)]),
    ('intro', 'snaps/en_bob.state', [('hold', 'a', 90)] * 2),
    ('cardhouse', 'snaps/release/ch12.state', [('hold', 'a', 35)] * 7),
    ('sell', 'snaps/turnmenu.state', [('call', force_sell)] + [('hold', 'a', 25)] * 24),
    ('popup', 'snaps/release/sell12.state', [('hold', 'a', 25)] * 11),
]

def main(names):
    g = boot(os.path.join(ROOT, 'build', 'fkdfw_en.gbc'))
    for name, st, steps in RECIPES:
        if names and name not in names: continue
        g.snapshot_load(path=st if st.startswith('/') else os.path.join(ROOT, st)); g.input_set([])
        run(g, steps)
        p = os.path.join(OUT, name + '.png'); g.screenshot_png(p)
        Image.open(p).resize((480, 432), Image.NEAREST).save(p)
        print(name)

if __name__ == '__main__':
    main(sys.argv[1:])
