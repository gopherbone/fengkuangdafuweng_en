"""Make the release IPS patch: original ROM -> English build.

    python tools/make_ips.py [orig.gbc] [build.gbc] [out.ips]

Plain IPS records (no RLE) for every changed byte run, split at 65,535 bytes; a run that would start at the
reserved offset 0x454F46 ("EOF") is started one byte earlier. Also checks the patch round-trips.
"""
import sys, os, zlib, hashlib, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def make_ips(a, b):
    assert len(a) == len(b), 'ROM sizes differ'
    out = bytearray(b'PATCH'); i = 0; n = len(a)
    while i < n:
        if a[i] == b[i]: i += 1; continue
        j = i
        while j < n and (a[j] != b[j] or (j + 1 < n and a[j + 1] != b[j + 1] and j - i < 0xFFFF)) and j - i < 0xFFFF:
            j += 1                                  # runs bridge single unchanged bytes (fewer records)
        start = i
        if start == 0x454F46: start -= 1
        out += start.to_bytes(3, 'big') + (j - start).to_bytes(2, 'big') + b[start:j]
        i = j
    return bytes(out + b'EOF')

def apply_ips(rom, ips):
    rom = bytearray(rom); p = 5
    assert ips[:5] == b'PATCH'
    while ips[p:p + 3] != b'EOF':
        off = int.from_bytes(ips[p:p + 3], 'big'); size = int.from_bytes(ips[p + 3:p + 5], 'big'); p += 5
        if size == 0:
            rl = int.from_bytes(ips[p:p + 2], 'big'); rom[off:off + rl] = ips[p + 2:p + 3] * rl; p += 3
        else:
            rom[off:off + size] = ips[p:p + size]; p += size
    return bytes(rom)

def info(d):
    return {'size': len(d), 'crc32': '%08X' % (zlib.crc32(d) & 0xFFFFFFFF), 'md5': hashlib.md5(d).hexdigest(),
            'sha1': hashlib.sha1(d).hexdigest()}

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'orig', 'fkdfw.gbc')
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'build', 'fkdfw_en.gbc')
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, 'docs', 'crazy-tycoon-en.ips')
    a, b = open(src, 'rb').read(), open(dst, 'rb').read()
    ips = make_ips(a, b)
    assert apply_ips(a, ips) == b, 'round trip failed'
    open(out, 'wb').write(ips)
    meta = {'source': info(a), 'patched': info(b), 'patch': info(ips)}
    json.dump(meta, open(os.path.splitext(out)[0] + '.json', 'w'), indent=1)
    print(out, len(ips), 'bytes'); print(json.dumps(meta, indent=1))

if __name__ == '__main__':
    main()
