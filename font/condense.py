"""Build a scaled, unhinted copy of a Bengali font for terminal use.

Usage: condense.py SRC.ttf OUT.ttf XFACTOR "Family Name" [YFACTOR]

Scales every horizontal metric (outlines, advances, side bearings, GPOS
placements/anchors, GDEF carets) by XFACTOR, and vertical ones by YFACTOR
(default 1), so marks stay attached. Bengali reads small next to Latin at the
same point size; a factor a little above 1 matches visual size, capped by the
terminal cell's ascent/descent. Check the fit with tools/fill_ratio.py.
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables, ttProgram
from fontTools.misc.fixedTools import otRound

src, out, factor, family = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
yfactor = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
font = TTFont(src)
sx = lambda v: otRound(v * factor)
sy = lambda v: otRound(v * yfactor)

glyf = font['glyf']
for name in font.getGlyphOrder():
    g = glyf[name]
    if g.isComposite():
        for c in g.components:
            c.x, c.y = sx(c.x), sy(c.y)
    elif g.numberOfContours > 0:
        g.coordinates.scale((factor, yfactor))
        g.coordinates.toInt()
    g.recalcBounds(glyf)

hmtx = font['hmtx'].metrics
for name, (adv, lsb) in hmtx.items():
    hmtx[name] = sx(adv), glyf[name].xMin if hasattr(glyf[name], 'xMin') else sx(lsb)

X_ATTRS = {otTables.ValueRecord: ('XAdvance', 'XPlacement'), otTables.Anchor: ('XCoordinate',),
           otTables.CaretValue: ('Coordinate',)}
Y_ATTRS = {otTables.ValueRecord: ('YAdvance', 'YPlacement'), otTables.Anchor: ('YCoordinate',)}
seen = set()

def walk(obj):
    if id(obj) in seen or obj is None or isinstance(obj, (int, float, str, bytes)):
        return
    seen.add(id(obj))
    if isinstance(obj, (list, tuple)):
        for o in obj: walk(o)
        return
    if isinstance(obj, dict):
        for o in obj.values(): walk(o)
        return
    for table, scale in ((X_ATTRS, sx), (Y_ATTRS, sy)):
        for cls, attrs in table.items():
            if isinstance(obj, cls):
                for a in attrs:
                    if getattr(obj, a, None) is not None:
                        setattr(obj, a, scale(getattr(obj, a)))
    if hasattr(obj, '__dict__'):
        for o in vars(obj).values(): walk(o)

# TrueType hinting snaps points to unscaled control values (cvt), dragging
# scaled glyphs and marks off their headline; drop it, FreeType autohints.
for tag in ('fpgm', 'prep', 'cvt '):
    if tag in font:
        del font[tag]
for name in font.getGlyphOrder():
    if glyf[name].numberOfContours:
        glyf[name].program = ttProgram.Program()
        glyf[name].program.fromBytecode(b'')

for tag in ('GPOS', 'GDEF'):
    if tag in font:
        walk(font[tag].table)

for attr in ('advanceWidthMax', 'minLeftSideBearing', 'minRightSideBearing', 'xMaxExtent'):
    setattr(font['hhea'], attr, sx(getattr(font['hhea'], attr)))
font['OS/2'].xAvgCharWidth = sx(font['OS/2'].xAvgCharWidth)
for attr in ('ascent', 'descent', 'lineGap'):
    setattr(font['hhea'], attr, sy(getattr(font['hhea'], attr)))
os2 = font['OS/2']
for attr in ('sTypoAscender', 'sTypoDescender', 'sTypoLineGap', 'usWinAscent', 'usWinDescent', 'sxHeight', 'sCapHeight'):
    setattr(os2, attr, sy(getattr(os2, attr)))

# Rename so it installs beside the original instead of shadowing it.
ps = family.replace(' ', '') + '-Regular'
for rec in font['name'].names:
    if rec.nameID in (1, 16):
        rec.string = family
    elif rec.nameID == 4:
        rec.string = family + ' Regular'
    elif rec.nameID == 6:
        rec.string = ps
    elif rec.nameID == 3:
        rec.string = f'{ps};bangla-term;condensed {factor}'
font.save(out)
print(f'wrote {out} ({family}, x{factor} y{yfactor})')
