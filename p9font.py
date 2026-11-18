"""Plan 9 subfont reader (compressed k1 images) -> {codepoint: (width, rows[list of str])}"""
import re, sys

def _num(b): return int(b.decode().strip())

def read_image(d):
    pos = 0
    comp = d.startswith(b'compressed\n')
    if comp: pos = 11
    chan = d[pos:pos+12].decode().strip()
    minx, miny, maxx, maxy = [_num(d[pos+12*i:pos+12*i+12]) for i in range(1,5)]
    pos += 60
    assert chan == 'k1', chan
    bpl = (maxx - minx + 7) // 8
    total = bpl * (maxy - miny)
    out = bytearray()
    if not comp:
        out = d[pos:pos+total]; pos += total
    else:
        while len(out) < total:
            ymax = _num(d[pos:pos+12]); nb = _num(d[pos+12:pos+24]); pos += 24
            blk = d[pos:pos+nb]; pos += nb
            i = 0
            while i < len(blk):
                c = blk[i]; i += 1
                if c & 0x80:
                    n = (c & 0x7f) + 1
                    out += blk[i:i+n]; i += n
                else:
                    n = ((c >> 2) & 0x1f) + 3
                    off = (((c & 3) << 8) | blk[i]) + 1; i += 1
                    for _ in range(n):
                        out.append(out[-off])
    return (minx, miny, maxx, maxy, bpl, bytes(out[:total])), pos

def read_subfont(path):
    d = open(path, 'rb').read()
    (minx, miny, maxx, maxy, bpl, px), pos = read_image(d)
    n, height, ascent = [_num(d[pos+12*i:pos+12*i+12]) for i in range(3)]
    pos += 36
    chars = []
    for i in range(n + 1):
        e = d[pos+6*i:pos+6*i+6]
        x = e[0] | (e[1] << 8)
        top, bottom, left, width = e[2], e[3], (e[4] - 256 if e[4] > 127 else e[4]), e[5]
        chars.append((x, top, bottom, left, width))
    def pix(x, y):
        return (px[y*bpl + x//8] >> (7 - x % 8)) & 1
    glyphs = []
    for i in range(n):
        x0 = chars[i][0]; x1 = chars[i+1][0]
        w = chars[i][4]
        rows = []
        for y in range(maxy - miny):
            rows.append(''.join('#' if pix(x, y) else '.' for x in range(x0, x1)))
        glyphs.append(dict(x0=x0, x1=x1, top=chars[i][1], bottom=chars[i][2], left=chars[i][3], width=w, rows=rows))
    return dict(n=n, height=height, ascent=ascent, glyphs=glyphs)

def load_font(fontfile):
    """Return {codepoint: glyph} using a .font index file."""
    import os
    base = os.path.dirname(fontfile)
    lines = open(fontfile).read().split('\n')
    height, ascent = map(int, lines[0].split())
    res = {}
    for ln in lines[1:]:
        p = ln.split()
        if len(p) < 3: continue
        lo, hi = int(p[0], 16), int(p[1], 16)
        off = int(p[3], 16) if len(p) > 3 else 0
        sf = read_subfont(os.path.join(base, p[2]))
        for i, g in enumerate(sf['glyphs']):
            cp = lo + i
            if cp > hi: break
            if i + off < len(sf['glyphs']):
                res[cp] = sf['glyphs'][i + off]
    return height, ascent, res
