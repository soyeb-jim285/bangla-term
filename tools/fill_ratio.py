"""Shaped width / allotted cells for each Bengali run (data for kitty#8533).

Usage: fill_ratio.py MONO.ttf BENGALI.ttf TEXT  [PHRASE=1: runs incl. single spaces] [BUN=1: Mc signs = 0]
"""
import sys, re, statistics, ctypes, ctypes.util
import uharfbuzz as hb
from fontTools.ttLib import TTFont
libc = ctypes.CDLL(ctypes.util.find_library('c')); libc.setlocale(6, b'C.UTF-8')
libc.wcswidth.argtypes = [ctypes.c_wchar_p, ctypes.c_size_t]
m = TTFont(sys.argv[1]); cell = m['hmtx'][m.getBestCmap()[ord('a')]][0] / m['head'].unitsPerEm
face = hb.Face(hb.Blob.from_file_path(sys.argv[2])); font = hb.Font(face)
text = open(sys.argv[3], encoding='utf-8').read()
import os
B = '[\u0980-\u09FF]+'
words = re.findall(B + '(?: ' + B + ')*' if os.environ.get('PHRASE') else B, text)
rs = []
for w in words:
    b = hb.Buffer(); b.add_str(w); b.guess_segment_properties(); hb.shape(font, b)
    nat = sum(p.x_advance for p in b.glyph_positions) / face.upem / cell
    cw = libc.wcswidth(w, len(w)) - (sum(c in "\u0982\u09BE\u09BF\u09C0\u09C7\u09C8\u09CB\u09CC\u09D7" for c in w) if os.environ.get("BUN") else 0)
    rs.append(nat / cw)
rs.sort()
q = lambda p: rs[int(p * (len(rs) - 1))]
print(f'{len(rs)} words  natural/cells: p10 {q(.1):.2f}  median {q(.5):.2f}  p90 {q(.9):.2f}  max {rs[-1]:.2f}')
