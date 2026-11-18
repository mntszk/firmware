"""Read/write ThingPulse OLEDDisplay font arrays."""
import re

def parse_array(src, name):
    m = re.search(r'%s\[\]\s*PROGMEM\s*=\s*\{(.*?)\};' % re.escape(name), src, re.S)
    body = re.sub(r'//[^\n]*', '', m.group(1))
    return [int(t, 16) for t in re.findall(r'0x[0-9A-Fa-f]+', body)]

def decode(arr):
    """-> dict(height, first, glyphs={code: (width, cols)}) cols = list of int bitmasks (bit0=top)."""
    w, h, first, n = arr[:4]
    bpc = (h + 7) // 8
    jt = arr[4:4 + 4*n]
    data = arr[4 + 4*n:]
    glyphs = {}
    for i in range(n):
        msb, lsb, size, width = jt[4*i:4*i+4]
        code = first + i
        if msb == 0xFF and lsb == 0xFF:
            glyphs[code] = (width, None); continue
        off = (msb << 8) | lsb
        raw = data[off:off+size] + [0] * (bpc*width - size)
        cols = []
        for c in range(width):
            v = 0
            for b in range(bpc):
                v |= raw[c*bpc + b] << (8*b)
            cols.append(v)
        glyphs[code] = (width, cols)
    return dict(height=h, first=first, glyphs=glyphs)

def rows_to_cols(rows, yoff=0):
    """rows: list of '#.' strings -> cols bitmasks, shifted down by yoff."""
    width = len(rows[0]) if rows else 0
    cols = []
    for x in range(width):
        v = 0
        for y, r in enumerate(rows):
            if r[x] == '#':
                v |= 1 << (y + yoff)
        cols.append(v)
    return cols

def show(cols, h):
    return '\n'.join(''.join('#' if (c >> y) & 1 else '.' for c in cols) for y in range(h))

def encode(name, height, first, glyphs, comments):
    """glyphs: list for codes first..first+n-1 of (advance_width, cols or None)."""
    bpc = (height + 7) // 8
    n = len(glyphs)
    jt, data = [], []
    maxw = 0
    for (width, cols) in glyphs:
        maxw = max(maxw, width)
        if not cols or not any(cols):
            jt.append((0xFF, 0xFF, 0, width)); continue
        raw = []
        for v in cols:
            for b in range(bpc):
                raw.append((v >> (8*b)) & 0xFF)
        while raw and raw[-1] == 0:
            raw.pop()
        off = len(data)
        assert off < 0xFFFF and len(raw) < 256
        jt.append((off >> 8, off & 0xFF, len(raw), width))
        data += raw
    out = ['const uint8_t %s[] PROGMEM = {' % name,
           '    0x%02X, // Width: %d' % (maxw, maxw),
           '    0x%02X, // Height: %d' % (height, height),
           '    0x%02X, // First char: %d' % (first, first),
           '    0x%02X, // Number of chars: %d' % (n, n), '', '    // Jump Table:']
    for i, e in enumerate(jt):
        out.append('    0x%02X, 0x%02X, 0x%02X, 0x%02X, // %d %s' % (e + (first + i, comments.get(first + i, ''))))
    out += ['', '    // Font Data:']
    for i in range(0, len(data), 16):
        out.append('    ' + ', '.join('0x%02X' % b for b in data[i:i+16]) + ',')
    out.append('};')
    return '\n'.join(l.rstrip() for l in out) + '\n'
