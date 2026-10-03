"""Build the English ROM: original + engine overlay + English string banks + in-place redirects.

  python3 tools/build.py [-o out.gbc]
"""
import sys, os, re, json, glob, subprocess, argparse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'font'))
from en_font import GLYPHS

ORIG = os.path.join(ROOT, 'orig', 'fkdfw.gbc')
TBL_BANK = 0x58
DATA_BANKS = list(range(0x59, 0x7E))

# Entries we must not redirect (fixed-offset label strips, keyboard layouts, bare name inserts)
SKIP = {'06:6E50', '06:6E52'}

CARD_NAMES = ['No cards', 'Turtle', 'Fart Sage', 'Rally', 'Hibernate', 'Pass-Off', 'Robbery', 'Master Thief',
    'Old Man', 'Seal', 'Scandal', 'Honeymoon', 'Horror', 'Force', 'Landmine', 'Catastrophe', 'Fire', 'Earthquake',
    'Pickpocket', 'Spendthrift', 'Move 1', 'Move 2', 'Move 3', 'Move 4', 'Move 5', 'Move 6', 'Car', 'Plane',
    'Sprint', 'Teleport', 'Cash Warp', 'North', 'Central', 'South', 'East', '<P0>', '<P1>', '<P2>', '<P3>', '<P4>',
    'Tank', 'Submarine', 'Long Shot', 'Tagalong', 'Stock Bus', 'Trade Bus', 'Swap', 'Bull Market', 'Bear Market',
    'Inflation', 'Boom', 'Panic', 'Silver', 'Gold', 'Diamond', 'Upgrade', 'Strongarm', 'Insurance', 'Thrift',
    'Pardon', 'Imp', 'Demon', 'Satan', 'Hungry Ghost', 'Blessing God', 'Wealth God', 'Birthday', 'Gamble',
    'Money Fairy', 'Lucky Break', 'Christmas', 'Treasure', 'Anti-Theft', 'VF Superman', 'Hero Luke', 'VF Iron Z',
    'Reflect', 'Guard', 'Washbasin', 'Exorcise', 'Protect', 'IOU', 'Mystery', 'Forgery', 'Collectible', 'Comeback',
    'Goal Shift', 'Share Wealth']
CHAR_NAMES = ['Meatball', 'Dubi', 'Penny Qian', 'Wu No-Guts', 'Sachiko', 'Hanamura', 'Xianglan', 'Xiao Ming']

TOK = {'NAME': [0xE0], 'NAME_E1': [0xE1], 'NAME_E8': [0xE8], 'E9': [0xE9], 'FE': [0xFE], 'NUM': [0xEC],
       'EE': [0xEE], 'EA': [0xEA], 'EB': [0xEB], 'EF': [0xEF], 'END': [0xFF], 'NL': [0xFB], 'PAGE': [0xFA, 0xFC],
       'P0': [0xE2], 'P1': [0xE3], 'P2': [0xE4], 'P3': [0xE5], 'P4': [0xE6], 'P5': [0xE7], 'NOP': [], 'BS': [0x80], 'M': [0x81]}
TAIL_CODES = {0xFA, 0xFB, 0xFC, 0xF9, 0xFD, 0xED}

def encode(text, problems, sid):
    out = []
    for part in re.split(r'(<[^>]+>)', text):
        if not part:
            continue
        if part.startswith('<'):
            name = part[1:-1]
            if name not in TOK:
                problems.append((sid, 'unknown token ' + part)); continue
            out += TOK[name]
        else:
            for ch in part:
                if ch not in GLYPHS:
                    problems.append((sid, 'no glyph for %r' % ch)); ch = '?'
                out.append(ord(ch))
    return out

def zh_tail(raw):
    """Trailing control bytes (waits/pages/scroll) up to and including FD, from the original string."""
    i = len(raw)
    while i > 0 and raw[i - 1] in TAIL_CODES:
        i -= 1
    tail = list(raw[i:])
    return tail if tail and tail[-1] == 0xFD else [0xFD]

def load_translations():
    """First draft (script/tl_out) overridden by review corrections (script/tl_review)."""
    tl = {}
    for d in ('tl_out', 'tl_review'):
        for f in sorted(glob.glob(os.path.join(ROOT, 'script', d, 'batch*.json'))):
            for k, v in json.load(open(f)).items():
                if not k.startswith('_'):
                    tl[k] = v
    return tl

def font_inc(path):
    chars = [chr(c) for c in range(0x20, 0x7F)]
    with open(path, 'w') as f:
        f.write('SECTION "en_font", ROM0[$3800]\nFontWidths::\n')
        f.write('    db ' + ', '.join(str(GLYPHS[c][1]) for c in chars) + '\n')
        f.write('FontRows::\n')
        for c in chars:
            f.write('    db ' + ', '.join('$%02X' % r for r in GLYPHS[c][0]) + '  ; %r\n' % c)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-o', default=os.path.join(ROOT, 'build', 'fkdfw_en.gbc'))
    args = ap.parse_args()
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    S = json.load(open(os.path.join(ROOT, 'script', 'strings.json')))
    byid = {x['id']: x for x in S}
    order = [x['id'] for x in S]
    tl = load_translations()
    places = json.load(open(os.path.join(ROOT, 'script', 'tl_out', 'places.json')))
    problems = []

    # English text per entry (before chaining)
    en = {}
    for x in S:
        sid, refs = x['id'], x['refs']
        if sid in SKIP:
            continue
        if x['bank'] == 0x4C:
            en[sid] = CHAR_NAMES[int(refs[0].split(':')[1])] + '<BOX>'
        elif refs[0].startswith('T68:1:'):
            en[sid] = CARD_NAMES[int(refs[0].split(':')[2])] + '<BOX>'
        elif refs[0] in ('names25', 'names38', 'regions30'):
            zh = x['zh'].replace('<BOX>', '')
            if zh in places:
                en[sid] = places[zh] + '<BOX>'
            else:
                problems.append((sid, 'no place translation for ' + zh))
        elif sid in tl:
            en[sid] = tl[sid]
    # fixed-slot label strips
    strips = {k: v for k, v in json.load(open(os.path.join(ROOT, 'script', 'strips.json'))).items() if not k.startswith('_')}
    # chain <END> continuations and encode
    entries = []           # (sid, bytes, flags)
    for sid, spec in strips.items():
        center = isinstance(spec, dict) and spec.get('center')
        slots = spec['slots'] if isinstance(spec, dict) else spec
        b = []; col = 0
        for cols, label in slots:
            c1 = center or label.startswith('^')        # '^label' = centre this slot, '>label' = right-align
            r1 = label.startswith('>')
            label = label.lstrip('^>')
            if (c1 or r1) and label:
                w = sum(GLYPHS[ch][1] + 1 for ch in label) - 1
                pad = max(0, (cols * 8 - w) // (1 if r1 else 2))
                if pad: b += [0x82, pad]
            b += encode(label, problems, sid)
            col += cols
            b += [0xF8, col]
        b += [0xFD]                     # final tab blanks the rest of the last slot
        entries.append((sid, b, 0x20))
        en.pop(sid, None)
    for i, sid in enumerate(order):
        if sid not in en or byid[sid]['refs'] == ['orphan']:
            continue
        x = byid[sid]
        parts = [en[sid]]; zhs = [x]
        j = i
        while parts[-1].rstrip().endswith('<END>') and j + 1 < len(order):
            j += 1
            nid = order[j]
            if nid not in en:
                problems.append((sid, 'continuation %s untranslated' % nid)); break
            parts.append(en[nid]); zhs.append(byid[nid])
        text = ''.join(parts)
        # game-printed numbers are right-aligned in a padded field: a '$' in front would float away, and the
        # unit after them is tucked back against the digits with the $80 backspace control.
        # money: the engine prints game numbers x10,000 with separators when prefixed by <M> ($81);
        # translators marked money as <CODE>0K (or 0,000 for counts of people)
        text = re.sub(r'\$\s+(?=<(END|NUM|EE|EA|EB|EC)>)', '$', text)
        text = re.sub(r'(<(?:END|NUM|EE|EA|EB|EC)>)\s*0(?:K|,000)', r'<M>\1', text)
        # the engine prints numbers without padding: keep a space between a word and a number
        text = re.sub(r'([A-Za-z])(<M>)?(<(?:END|NUM|EE|EA|EB|EC)>)', r'\1 \2\3', text)
        last = zhs[-1]
        text = re.sub(r'(\s|<PAGE>)*<BOX>\s*$', '', text)
        text = re.sub(r'<END>\s*$', '<END>', text)
        b = encode(text, problems, sid)
        if not text.endswith('<END>'):
            b += zh_tail(bytes.fromhex(last['raw']))
        # TV-news window: strings that scroll (F9) or open with a news anchor's label
        news = any('<F9>' in z['zh'] for z in zhs) or zhs[0]['zh'].startswith(('尤莉雅：', '拳四郎：'))
        flags = 0x02 if news else 0
        if x['bank'] in (0x4C, 0x25, 0x38, 0x30) or x['refs'][0].startswith('T68:1:'):
            flags |= 0x40       # names (characters, places, cards): drawn instantly into label slots, no margin
        if x['bank'] == 0x4C:
            flags |= 0x04       # character names: small left pad when drawn standalone (portrait label)
        if x['refs'][0].startswith('T68:1:'):
            flags |= 0x80       # card names: centred in 8 columns when drawn standalone (card popup)
        entries.append((sid, b, flags))

    # stable string indices: saved games keep F6 redirects in RAM (player names, place names), so an id's index
    # must never change between builds. New ids are appended to the lock file.
    lock_path = os.path.join(ROOT, 'script', 'index_lock.json')
    lock = json.load(open(lock_path)) if os.path.exists(lock_path) else {}
    for sid, _, _ in entries:
        if sid not in lock:
            lock[sid] = max(lock.values(), default=0) + 1
    json.dump(lock, open(lock_path, 'w'), indent=0, sort_keys=True)
    entries.sort(key=lambda e: lock[e[0]])
    # lay out data banks
    ORIG_ROM = open(ORIG, 'rb').read()
    rom = bytearray(ORIG_ROM)
    nmax = max(lock.values())
    table = bytearray(4 * (nmax + 1))
    bank_i, addr = 0, 0x4001
    index = {}
    for sid, b, flags in entries:
        n = lock[sid]
        if addr + len(b) > 0x8000:
            bank_i += 1; addr = 0x4001
        bank = DATA_BANKS[bank_i]
        off = bank * 0x4000 + addr - 0x4000
        rom[off:off + len(b)] = bytes(b)
        index[sid] = n
        table[4 * n:4 * n + 4] = bytes([addr & 0xFF, addr >> 8, bank, flags])
        addr += len(b)
    assert len(table) < 0x3FFF
    t0 = TBL_BANK * 0x4000 + 1
    rom[t0:t0 + len(table)] = table
    # redirects in the original strings
    for sid, n in index.items():
        x = byid[sid]
        off = x['bank'] * 0x4000 + x['addr'] - 0x4000
        assert x['end'] - x['addr'] >= 3, sid
        rom[off:off + 3] = bytes([0xF6, n & 0xFF, n >> 8])
    # other copies of place names (other banks keep their own FD-terminated copies that get copied into the
    # place-name buffer): point each at the English entry of the same name
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import fkdfw
    tab = fkdfw.load_table(); inv = {}
    for k, v in tab.items(): inv.setdefault(v, k)
    known = {(x['bank'], x['addr']) for x in S}
    aliases = 0
    for x in S:
        if not (x['refs'][0] == 'names38' or x['refs'][0].startswith('T68:1:')) or x['id'] not in index: continue
        pat = bytes.fromhex(x['raw']); n = index[x['id']]
        if len(pat) < 4: continue
        i = ORIG_ROM.find(pat)
        while i != -1:
            bk = i // 0x4000; ad = 0x4000 + i % 0x4000 if i >= 0x4000 else i
            if (bk, ad) not in known:
                rom[i:i + 3] = bytes([0xF6, n & 0xFF, n >> 8]); aliases += 1
            i = ORIG_ROM.find(pat, i + 1)
    print('place-name aliases redirected:', aliases)
    # graphical text (pre-drawn tiles redrawn in English)
    gp = os.path.join(ROOT, 'gfx', 'patch.json')
    if os.path.exists(gp):
        specs = [k for k in json.load(open(os.path.join(ROOT, 'gfx', 'specs.json'))) if not k.startswith('_')]
        missing = sorted(set(specs) - set(json.load(open(gp))))
        if missing:
            raise SystemExit('gfx/patch.json lacks %s: run tools/gfx.py / the generators' % ', '.join(missing))
        owner = {}
        for screen, chunks in json.load(open(gp)).items():
            for off, data in chunks.items():
                o = int(off, 16); d = bytes.fromhex(data)
                for k in range(o, o + len(d)):
                    if k in owner and owner[k] != screen:
                        raise SystemExit('gfx conflict at %06X: %s vs %s' % (k, owner[k], screen))
                    owner[k] = screen
                rom[o:o + len(d)] = d
    base = os.path.join(ROOT, 'build', 'base.gbc')
    open(base, 'wb').write(rom)

    # engine overlay
    asm = os.path.join(ROOT, 'asm')
    font_inc(os.path.join(asm, 'font.inc'))
    obj = os.path.join(ROOT, 'build', 'engine.o')
    src = os.path.join(asm, 'engine.asm')
    for attempt in range(20):
        subprocess.run(['rgbasm', '-Wno-obsolete', '-I', asm, '-o', obj, src], check=True)
        r = subprocess.run(['rgblink', '-O', base, '-o', args.o, '-m', args.o.replace('.gbc', '.map'),
                            '-n', args.o.replace('.gbc', '.sym'), obj], capture_output=True, text=True)
        if r.returncode == 0: break
        # relative jumps that grew out of range: turn them into absolute jumps and retry
        err = re.sub(r'\x1b\[[0-9;]*m', '', r.stderr)
        bad = [int(m) for m in re.findall(r'engine\.asm\((\d+)\)', err)] if '`JR` target' in err else []
        if not bad: sys.exit(r.stderr)
        lines = open(src).read().split('\n')
        for n in bad:
            lines[n - 1] = lines[n - 1].replace('jr ', 'jp ', 1)
            print('  jr->jp at engine.asm:%d' % n)
        open(src, 'w').write('\n'.join(lines))
    subprocess.run(['rgbfix', '-v', args.o], check=True)
    json.dump({'index': index, 'banks_used': bank_i + 1}, open(os.path.join(ROOT, 'build', 'index.json'), 'w'), indent=0)
    print('entries', len(entries), 'data banks', bank_i + 1, 'problems', len(problems))
    for p in problems[:40]:
        print('  ', *p)

if __name__ == '__main__':
    main()
