"""Generate OLEDDisplayFontsJA.cpp/.h for Meshtastic (half-width katakana, JIS X 0201).

Usage: python3 gen_ja_font.py <firmware checkout> <plan9port>/font/shinonome <output dir>
  The Shinonome font comes from https://github.com/9fans/plan9port (font/shinonome, Plan 9 subfonts).
  Run clang-format (.trunk/configs/.clang-format) on the output before committing.

Sources:
  - Latin glyphs 0x20-0x7F and 0xE0-0xFF, and the degree sign: ArialMT_Plain_*_PL
    from src/graphics/fonts/OLEDDisplayFontsPL.cpp (Meshtastic firmware)
  - Katakana glyphs: Shinonome font 0.9.11 (6x12r, 8x16r), public domain,
    read from the Plan 9 conversion in plan9port (font/shinonome)
Code layout (font index):
  0x20-0x7F  ASCII (Arial)
  0x80-0x99  pre-combined dakuten/handakuten kana (26)
  0x9A       GETA MARK (U+3013), shown for characters that cannot be displayed
  0x9B       DEGREE SIGN (U+00B0)
  0x9C-0xA0  blank
  0xA1-0xDF  JIS X 0201 half-width katakana (U+FF61-U+FF9F)
  0xE0-0xFF  Latin-1 lowercase accented letters (Arial)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oledfont as o, p9font as p

FW = sys.argv[1]
SHN = sys.argv[2]
OUT = sys.argv[3]
os.makedirs(OUT, exist_ok=True)

pl_src = open(FW + '/src/graphics/fonts/OLEDDisplayFontsPL.cpp').read()

# (base kana code, mark code) for the pre-combined glyphs at 0x80..
COMBOS = [(c, 0xDE) for c in list(range(0xB6, 0xC5)) + list(range(0xCA, 0xCF))]  # ｶﾞ..ﾄﾞ, ﾊﾞ..ﾎﾞ (20)
COMBOS += [(c, 0xDF) for c in range(0xCA, 0xCF)]                                   # ﾊﾟ..ﾎﾟ (5)
COMBOS += [(0xB3, 0xDE)]                                                            # ｳﾞ
assert len(COMBOS) == 26
GETA, DEG, CELSIUS = 0x9A, 0x9B, 0x9C
ARROWS = {  # code: (6x12 rows, 8x16 rows); left, up, right, down in Unicode order
    0x9D: (["......", "......", "......", "......", "..#...", ".#....", "######", ".#....", "..#...", "......", "......", "......"],
           ["........"] * 5 + ["..#.....", ".#......", "########", ".#......", "..#....."] + ["........"] * 6),
    0x9E: (["......", "......", "..#...", ".###..", "#.#.#.", "..#...", "..#...", "..#...", "..#...", "..#...", "......", "......"],
           ["........"] * 2 + ["...#....", "..###...", ".#.#.#..", "#..#..#."] + ["...#...."] * 8 + ["........"] * 2),
    0x9F: (["......", "......", "......", "......", "...#..", "....#.", "######", "....#.", "...#..", "......", "......", "......"],
           ["........"] * 5 + [".....#..", "......#.", "########", "......#.", ".....#.."] + ["........"] * 6),
    0xA0: (["......", "......", "..#...", "..#...", "..#...", "..#...", "..#...", "#.#.#.", ".###..", "..#...", "......", "......"],
           ["........"] * 2 + ["...#...."] * 8 + ["#..#..#.", ".#.#.#..", "..###...", "...#...."] + ["........"] * 2),
}

def geta_rows(w, h, scale):
    rows = ['.' * w for _ in range(h)]
    bars = [(2, 4), (6, 8)] if h == 12 else [(3, 6), (8, 11)]
    for a, b in bars:
        for y in range(a, b + 1):
            rows[y] = '#' * (w - 1) + '.'
    return rows

def scale_rows(rows, k):
    out = []
    for r in rows:
        rr = ''.join(ch * k for ch in r)
        out += [rr] * k
    return out

def trim(cols):
    used = [i for i, c in enumerate(cols) if c]
    return cols[used[0]:used[-1] + 1] if used else []

def build(size):
    arial_name = 'ArialMT_Plain_%d_PL' % size
    ar = o.decode(o.parse_array(pl_src, arial_name))
    H = ar['height']
    if size == 10:
        sf, k, yoff = p.read_subfont(SHN + '/6x12r.0001'), 1, 0
    elif size == 16:
        sf, k, yoff = p.read_subfont(SHN + '/8x16r.0001'), 1, 1
    else:
        sf, k, yoff = p.read_subfont(SHN + '/6x12r.0001'), 2, 2
    def kana(code):
        rows = sf['glyphs'][code - 1]['rows']
        if k > 1:
            rows = scale_rows(rows, k)
        return o.rows_to_cols(rows, yoff)
    g = {}
    for c in range(0x20, 0x100):
        g[c] = (ar['glyphs'][0x20][0], None)  # default: blank, space width
    for c in list(range(0x20, 0x80)) + list(range(0xE0, 0x100)):
        g[c] = ar['glyphs'][c]
    g[DEG] = ar['glyphs'][0xB0]
    dw, dcols = ar['glyphs'][0xB0]
    cw, ccols = ar['glyphs'][ord('C')]
    g[CELSIUS] = (dw + cw, list(dcols) + [0] * (dw - len(dcols)) + list(ccols))
    for c in range(0xA1, 0xE0):
        cols = kana(c)
        g[c] = (len(cols), cols)
    for i, (base, mark) in enumerate(COMBOS):
        cols = kana(base) + trim(kana(mark)) + [0]
        g[0x80 + i] = (len(cols), cols)
    base_h = 12 if size != 16 else 16
    base_w = 6 if size != 16 else 8
    rows = geta_rows(base_w, base_h, k)
    if k > 1:
        rows = scale_rows(rows, k)
    cols = o.rows_to_cols(rows, yoff)
    g[GETA] = (len(cols), cols)
    for code, (r12, r16) in ARROWS.items():
        rows = r16 if size == 16 else r12
        assert len(rows) == base_h and all(len(r) == base_w for r in rows), hex(code)
        if k > 1:
            rows = scale_rows(rows, k)
        cols = o.rows_to_cols(rows, yoff)
        g[code] = (len(cols), cols)
    for c, (w, cols) in g.items():
        if cols:
            assert max(cols) < (1 << H), (size, hex(c))
    comments = {}
    for c in range(0xA1, 0xE0):
        comments[c] = chr(0xFF61 + c - 0xA1)
    for i, (base, mark) in enumerate(COMBOS):
        comments[0x80 + i] = chr(0xFF61 + base - 0xA1) + chr(0xFF61 + mark - 0xA1)
    comments[GETA] = '〓'
    comments[DEG] = '°'
    for c in range(0xE0, 0x100):
        comments[c] = chr(c)
    glyphs = [g[c] for c in range(0x20, 0x100)]
    return o.encode('ArialMT_Plain_%d_JA' % size, H, 0x20, glyphs, comments), g, H

HDR = '''// Latin glyphs: ArialMT_Plain_10/16/24. Katakana: Shinonome Font 0.9.11 (shnm6x12r, shnm8x16r) by
// Yasuyuki Furukawa and the /efont/ project, public domain; the 24px kana are the 12px glyphs doubled.
'''

parts, previews = [], {}
for size in (10, 16, 24):
    src, g, H = build(size)
    parts.append(src)
    previews[size] = (g, H)

cpp = '#ifdef OLED_JA\n\n' + HDR + '\n#include "OLEDDisplayFontsJA.h"\n\n' + '\n'.join(parts) + '\n#endif // OLED_JA\n'
h = '''#ifndef OLEDDISPLAYFONTSJA_h
#define OLEDDISPLAYFONTSJA_h

#ifdef ARDUINO
#include <Arduino.h>
#elif __MBED__
#define PROGMEM
#endif

extern const uint8_t ArialMT_Plain_10_JA[] PROGMEM;
extern const uint8_t ArialMT_Plain_16_JA[] PROGMEM;
extern const uint8_t ArialMT_Plain_24_JA[] PROGMEM;
#endif
'''
open(OUT + '/OLEDDisplayFontsJA.cpp', 'w').write(cpp)
open(OUT + '/OLEDDisplayFontsJA.h', 'w').write(h)

# preview: render a sample string per size to text
import json
def render(codes, size):
    g, H = previews[size]
    cols = []
    for c in codes:
        w, cs = g[c]
        cols += (cs or [0] * w)
    return o.show(cols, H)
sample = [0xD2, 0xAF, 0xBC, 0xAD, 0xC0, 0xBD, 0xC3, 0xA8, 0xAF, 0xB8, 0x20, 0x80+0, 0x80+25, 0x80+20, 0x20, ord('J'), ord('A'), ord('1'), 0x9B, 0x9A, 0xE9]
with open(OUT + '/preview.txt', 'w') as f:
    for s in (10, 16, 24):
        f.write('== %d ==\n%s\n' % (s, render(sample, s)))
print('ok')
