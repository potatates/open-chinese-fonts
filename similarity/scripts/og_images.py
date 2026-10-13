"""Share images (1200×630) for link previews: each font's name and a sample
line drawn in that font, plus one for the site itself.

Rendering a font into a picture is allowed by every license in the catalog.
Run:  similarity/.venv/bin/python similarity/scripts/og_images.py [font-id …]
Writes public/og/<id>.png and public/og/site.png (uploaded to R2 with the fonts).
"""
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONTS = json.loads((ROOT / "src/data/fonts.json").read_text())
SOURCES = {k: v for k, v in json.loads((ROOT / "similarity/sources.json").read_text()).items() if not k.startswith("_")}
OUT = ROOT / "public/og"
UI = ROOT / "fonts-src/NotoSansSC-VF.ttf"  # labels
CATS = {"song": "宋体", "hei": "黑体", "kai": "楷体", "handwriting": "手写·书法", "rounded": "圆体", "display": "创意"}
W, H, PAD = 1200, 630, 80
PAPER, INK, GREY, RED = "#FAFAF8", "#1A1A1A", "#7A7A75", "#C23B22"
SAMPLE = "春眠不觉晓，处处闻啼鸟"


def fit(path: Path, text: str, max_w: int, start: int) -> ImageFont.FreeTypeFont:
    size = start
    while size > 24:
        f = ImageFont.truetype(str(path), size)
        if f.getlength(text) <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(str(path), size)


def card(font: dict) -> None:
    path = ROOT / "fonts-src" / SOURCES[font["id"]]["file"]
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 12, H), fill=RED)
    label = ImageFont.truetype(str(UI), 28)
    d.text((PAD, PAD - 10), CATS[font["category"]], font=label, fill=GREY)
    name = fit(path, font["name"]["zh"], W - 2 * PAD, 180)
    d.text((PAD, 150), font["name"]["zh"], font=name, fill=INK)
    if font["name"]["en"] != font["name"]["zh"]:
        d.text((PAD, 150 + name.size + 30), font["name"]["en"], font=ImageFont.truetype(str(UI), 34), fill=GREY)
    # leave out characters the font doesn't have (some lack Chinese punctuation)
    cmap = TTFont(str(path), lazy=True).getBestCmap()
    text = "".join(c if ord(c) in cmap else " " for c in SAMPLE)
    sample = fit(path, text, W - 2 * PAD, 56)
    d.text((PAD, H - PAD - 120), text, font=sample, fill=INK)
    d.text((PAD, H - PAD - 20), "字相 · zixiangfont.com", font=label, fill=GREY)
    im.save(OUT / f"{font['id']}.png", optimize=True)


def site_card() -> None:
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 12, H), fill=RED)
    d.text((PAD, 150), "字相", font=ImageFont.truetype(str(UI), 200), fill=INK)
    d.text((PAD, 400), f"{len(FONTS)} 款免费中文字体 · 在线预览 · 相似字体", font=ImageFont.truetype(str(UI), 44), fill=GREY)
    d.text((PAD, H - PAD - 20), "zixiangfont.com", font=ImageFont.truetype(str(UI), 28), fill=GREY)
    im.save(OUT / "site.png", optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    todo = [f for f in FONTS if (not only or f["id"] in only) and f["id"] in SOURCES]
    with ProcessPoolExecutor() as pool:
        list(pool.map(card, todo))
    site_card()
    print(f"→ {len(todo)} share images in public/og/")
