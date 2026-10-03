"""Sell-off screen (forced sale when in debt, bank $3D) -> gfx/patch.json["sell"].

1bpp 16x16-format glyph strips expanded by $3D:$57D7: $5E47 (10 cells: 持 有 金 億 萬 產 業 土 地 件) and $5F87
(3 cells: 手 自 動, the menu reads 手動 / 自動 sharing the 動 cell). Amounts are printed by the engine (SellAmount /
SellHeader) as dollars in the screen's big digits, using the 金 cell for '-' and the 億 cell for '$' and ','; the 萬 cell is blank.
"""
import sys, os, json
sys.path.insert(0, '/Users/nick/crazyrichman_claude/tools')
from gfx import render_1bpp

ROOT = '/Users/nick/crazyrichman_claude'
B3D = 0x3D * 0x4000 - 0x4000
# big-digit style glyphs, 8 x 16 (same bitmaps as the engine's PriceGlyphs)
DOLLAR = [0x0C, 0x3E, 0x7F, 0x6D, 0x6C, 0x7C, 0x3E, 0x1F, 0x0D, 0x6D, 0x7F, 0x3E, 0x0C, 0x0C, 0x00, 0x00]
COMMA = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x1C, 0x1C, 0x0C, 0x18, 0, 0]
MINUS = [0, 0, 0, 0, 0, 0, 0x7E, 0x7E, 0, 0, 0, 0, 0, 0, 0, 0]
BLANK = [0] * 16

def main():
    strip = (render_1bpp('Cash', 2) + bytes(MINUS + BLANK)        # 持有 / 金 ('-')
             + bytes(DOLLAR + COMMA) + bytes(BLANK + BLANK)         # 億 ('$' ',') / 萬 (blank: the layout draws it)
             + render_1bpp('Firms', 2) + render_1bpp('Lots', 2)    # 產業 / 土地
             + render_1bpp('', 1))                                  # 件
    menu = render_1bpp('Pick', 1) + render_1bpp('Auto', 1) + render_1bpp('', 1)
    assert len(strip) == 0x140 and len(menu) == 0x60
    out = {'%06X' % (B3D + 0x5E47): strip.hex(), '%06X' % (B3D + 0x5F87): menu.hex()}
    pf = os.path.join(ROOT, 'gfx', 'patch.json')
    patch = json.load(open(pf)); patch['sell'] = out
    json.dump(dict(sorted(patch.items())), open(pf, 'w'), indent=1)
    print('sell strips')

if __name__ == '__main__':
    main()
