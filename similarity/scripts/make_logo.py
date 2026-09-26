"""Seal (印章) favicon candidates for 字相, drawn from real font outlines.

The characters' outlines come from open-source fonts in the catalog (their
licenses allow using the shapes in artwork like a logo), placed into a seal
layout and saved as SVG, so the logo looks the same everywhere without
loading any font.

Run:  similarity/.venv/bin/python similarity/scripts/make_logo.py
Writes similarity/logo/*.svg and similarity/logo/_preview.svg
"""
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "similarity/logo"
OUT.mkdir(exist_ok=True)
RED = "#C23B22"  # the site's accent (朱红)
PAPER = "#FAFAF8"
S = 100  # the seal is drawn in a 100 × 100 box

FONTS = {
    "glow-light": ROOT / "fonts-src/GlowSansSC-Normal-Light.otf",  # 未来荧黑 Light
    "glow": ROOT / "fonts-src/GlowSansSC-Normal-Regular.otf",  # 未来荧黑 Regular
    "song": ROOT / "fonts-src/FandolSong-Regular.otf",  # Fandol 宋体
    "round": ROOT / "fonts-src/ResourceHanRoundedCN-Regular.ttf",  # 资源圆体 Regular
}


def glyph(font_key: str, ch: str, cx: float, cy: float, size: float) -> str:
    """SVG path of `ch` at its natural proportions (no stretching), scaled so
    its larger side is `size`, centred on (cx, cy)."""
    font = TTFont(str(FONTS[font_key]))
    gs = font.getGlyphSet()
    name = font.getBestCmap()[ord(ch)]
    bp = BoundsPen(gs)
    gs[name].draw(bp)
    x0, y0, x1, y1 = bp.bounds
    k = size / max(x1 - x0, y1 - y0)  # one scale for both directions
    w, h = (x1 - x0) * k, (y1 - y0) * k
    # font units have y pointing up; SVG has y pointing down
    t = (k, 0, 0, -k, cx - w / 2 - x0 * k, cy - h / 2 + y1 * k)
    pen = SVGPathPen(gs)
    gs[name].draw(TransformPen(pen, t))
    return pen.getCommands()


BLACK = "#141414"


def svg(body: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}">{body}</svg>'


def paths(parts, fill):
    return "".join(f'<path d="{p}" fill="{fill}"/>' for p in parts)


def design(kind: str, font_key: str = "glow") -> str:
    """Seal-like marks that don't read as app icons: real seal shapes, and the
    background showing through around them. Characters never stretched."""
    if kind == "circle":  # 圆印: white 相 on a red circle
        return svg(f'<circle cx="50" cy="50" r="48" fill="{RED}"/>' + paths([glyph(font_key, "相", 50, 50, 58)], PAPER))
    if kind == "oval":  # tall oval seal, 字 above 相
        return svg(
            f'<ellipse cx="50" cy="50" rx="31" ry="48" fill="{RED}"/>'
            + paths([glyph(font_key, "字", 50, 29, 34), glyph(font_key, "相", 50, 71, 34)], PAPER)
        )
    if kind == "tall":  # rectangular name seal, sharp corners, 字 above 相
        return svg(
            f'<rect x="24" y="2" width="52" height="96" fill="{RED}"/>'
            + paths([glyph(font_key, "字", 50, 28, 36), glyph(font_key, "相", 50, 72, 36)], PAPER)
        )
    if kind == "black":  # red 相 on black, sharp corners
        return svg(f'<rect width="{S}" height="{S}" fill="{BLACK}"/>' + paths([glyph(font_key, "相", 50, 50, 66)], RED))
    if kind == "frame":  # 朱文: red 相 inside a thin red square outline, open background
        return svg(
            f'<rect x="5" y="5" width="90" height="90" fill="none" stroke="{RED}" stroke-width="7"/>'
            + paths([glyph(font_key, "相", 50, 50, 58)], RED)
        )
    if kind == "mark":  # just the character, like a stamped mark
        return svg(paths([glyph(font_key, "相", 50, 50, 92)], RED))
    raise ValueError(kind)


VARIANTS = {
    "a-circle": ("circle",),
    "b-oval": ("oval",),
    "c-tall": ("tall",),
    "d-black": ("black",),
    "e-frame": ("frame",),
    "f-mark": ("mark", "song"),
}

for old in OUT.glob("*.svg"):
    old.unlink()
cells = []
for i, (name, args) in enumerate(VARIANTS.items()):
    code = design(*args)
    (OUT / f"{name}.svg").write_text(code)
    inner = code.split(">", 1)[1].rsplit("</svg>", 1)[0]
    x = 30 + i * 200
    for row, (bg, fg) in enumerate([("#ffffff", "#333"), ("#202124", "#ddd")]):  # light and dark tabs
        y = row * 290
        cells.append(
            f'<rect x="{x - 15}" y="{y + 15}" width="190" height="270" fill="{bg}"/>'
            f'<g transform="translate({x},{y + 30}) scale(1.4)">{inner}</g>'
            f'<g transform="translate({x},{y + 200}) scale(0.32)">{inner}</g>'
            f'<g transform="translate({x + 48},{y + 208}) scale(0.16)">{inner}</g>'
            f'<text x="{x}" y="{y + 268}" font-family="sans-serif" font-size="18" fill="{fg}">{name.split("-")[0]}</text>'
        )
W = 30 + len(VARIANTS) * 200
preview = (
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 590" width="{W}" height="590">'
    f'<rect width="{W}" height="590" fill="#e8e8e4"/>{"".join(cells)}</svg>'
)
(OUT / "_preview.svg").write_text(preview)
print("→", *sorted(p.name for p in OUT.iterdir()))
