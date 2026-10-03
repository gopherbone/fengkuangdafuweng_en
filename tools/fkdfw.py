"""Text codec for Feng Kuang Da Fu Weng (GBC). Derived from the ROM's renderer at $0A3B/$0A43.

Byte stream semantics (see notes/text_engine.md):
  F0-F8 xx : select font page (byte & 0x0F), then draw glyph xx from it. Page is sticky.
  00-DF    : draw glyph from the current (sticky) page.
  E0-FF    : control codes.
Glyph (page p, index x) lives at file offset (9 + (p>>1))*0x4000 + (p&1)*0x2000 + 1 + x*32.
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ROM_PATH = os.path.join(ROOT, 'orig', 'fkdfw.gbc')

CTRL = {0xFF: 'END', 0xFE: 'FE', 0xFD: 'BOX', 0xFC: 'PAGE', 0xFB: 'NL', 0xFA: 'WAIT',
        0xF9: 'F9', 0xEF: 'EF', 0xEE: 'EE', 0xED: 'NOP', 0xEC: 'NUM', 0xEB: 'EB', 0xEA: 'EA',
        0xE9: 'E9', 0xE8: 'NAME_E8', 0xE1: 'NAME_E1', 0xE0: 'NAME', 0xE2: 'P0', 0xE3: 'P1',
        0xE4: 'P2', 0xE5: 'P3', 0xE6: 'P4', 0xE7: 'P5'}

def load_rom(path=ROM_PATH):
    return open(path, 'rb').read()

def load_table():
    t = {}
    for p in range(10):
        f = os.path.join(ROOT, 'font', f'table_p{p}.json')
        if os.path.exists(f):
            for k, v in json.load(open(f)).items():
                t[int(k, 16)] = v
    return t

def decode(rom, off, table, maxlen=4096, stop=(0xFF,), page=0):
    """Return (text, end_offset). Unknown glyphs -> {pXX}. Controls -> <NAME>."""
    s = []; i = off
    while i < off + maxlen:
        b = rom[i]
        if 0xF0 <= b <= 0xF8:
            page = b & 0x0F; c = rom[i + 1]; i += 2
            b = c  # engine re-dispatches the index byte through the control chain
        elif b >= 0xE0:
            i += 1
        else:
            c = b; i += 1
        if b >= 0xE0:
            s.append('<%s>' % CTRL.get(b, '%02X' % b))
            if b in stop: break
            continue
        g = page * 256 + c
        s.append(table.get(g, '{%X%02X}' % (page, c)))
    return ''.join(s), i
