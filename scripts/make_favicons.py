"""Make the site icons from one design: a white 字 on a red rounded square.

The character is drawn from Noto Sans SC (OFL) and stored as an outline, so
the icon looks the same everywhere. The old favicon.svg asked for a system
font (PingFang SC), which Google's servers don't have, so search results
showed a blank globe instead.

Writes public/favicon.svg, favicon.ico (16/32/48), favicon-96.png (Google
wants a multiple of 48 px), apple-touch-icon.png (180) and icon-192.png.

Run: similarity/.venv/bin/python scripts/make_favicons.py
"""
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
RED, WHITE = "#c23b22", "#ffffff"
SIZE, RADIUS = 32, 4          # the SVG's own units (same as the old icon)
GLYPH_HEIGHT = 21 * 0.88      # about the old 21px text's ink height

font = instantiateVariableFont(TTFont(ROOT / "fonts-src/NotoSansSC-VF.ttf"), {"wght": 600})
glyphs = font.getGlyphSet()
name = font.getBestCmap()[ord("字")]

bounds = BoundsPen(glyphs)
glyphs[name].draw(bounds)
x0, y0, x1, y1 = bounds.bounds
scale = GLYPH_HEIGHT / (y1 - y0)
# centre the ink in the square; font y points up, SVG y points down
dx = SIZE / 2 - (x0 + x1) / 2 * scale
dy = SIZE / 2 + (y0 + y1) / 2 * scale

svg_pen = SVGPathPen(glyphs)
glyphs[name].draw(TransformPen(svg_pen, (scale, 0, 0, -scale, dx, dy)))
path = svg_pen.getCommands()

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}">'
    f'<rect width="{SIZE}" height="{SIZE}" rx="{RADIUS}" fill="{RED}"/>'
    f'<path fill="{WHITE}" d="{path}"/></svg>\n'
)
(ROOT / "public/favicon.svg").write_text(svg)


def png(px: int) -> Image.Image:
    """Draw the same icon at px × px (4× oversampled for smooth edges)."""
    k = px * 4 / SIZE
    img = Image.new("RGBA", (px * 4, px * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, px * 4 - 1, px * 4 - 1), radius=RADIUS * k, fill=RED)

    class Collect:  # flatten the outline into polygons for PIL
        def __init__(self):
            self.polys, self.cur = [], []

        def moveTo(self, p):
            self.cur = [p]

        def lineTo(self, p):
            self.cur.append(p)

        def curveTo(self, *ps):
            self._bez([self.cur[-1], *ps])

        def qCurveTo(self, *ps):
            from fontTools.pens.basePen import decomposeQuadraticSegment
            for b, c in decomposeQuadraticSegment(ps):
                self._bez([self.cur[-1], b, c])

        def _bez(self, ctrl, steps=12):
            for s in range(1, steps + 1):
                t = s / steps
                pts = ctrl
                while len(pts) > 1:
                    pts = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(pts, pts[1:])]
                self.cur.append(pts[0])

        def closePath(self):
            self.polys.append(self.cur)

        endPath = closePath

        def addComponent(self, *a):
            raise NotImplementedError

    c = Collect()
    glyphs[name].draw(TransformPen(c, (scale * k, 0, 0, -scale * k, dx * k, dy * k)))
    # The font builds 字 from overlapping pieces, and 字 has no enclosed
    # holes, so every piece is simply filled (the SVG's default nonzero rule
    # does the same).
    mask = Image.new("1", img.size, 0)
    for poly in c.polys:
        ImageDraw.Draw(mask).polygon(poly, fill=1)
    img.paste(Image.new("RGBA", img.size, WHITE), mask=mask)
    return img.resize((px, px), Image.LANCZOS)


png(96).save(ROOT / "public/favicon-96.png")
png(180).save(ROOT / "public/apple-touch-icon.png")
png(192).save(ROOT / "public/icon-192.png")
png(48).save(ROOT / "public/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
print("→ public/favicon.svg, favicon.ico, favicon-96.png, apple-touch-icon.png, icon-192.png")
