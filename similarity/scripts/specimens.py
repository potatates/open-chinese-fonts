"""Render one specimen image per font, plus a contact sheet of all fonts.

The images are what formality/quirkiness were scored from, and they're handy
for checking whether the measured numbers match what the fonts look like.

Run:  similarity/.venv/bin/python similarity/scripts/specimens.py
Writes similarity/specimens/<id>.png and similarity/specimens/_all.png
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {k: v for k, v in json.loads((ROOT / "similarity/sources.json").read_text()).items() if not k.startswith("_")}
FONTS = {f["id"]: f for f in json.loads((ROOT / "src/data/fonts.json").read_text())}
OUT = ROOT / "similarity/specimens"
OUT.mkdir(exist_ok=True)

LINES = [
    (150, "永和九年岁在"),  # 《兰亭集序》, large: overall shape
    (240, "口国回"),  # very large: corners and stroke endings
    (44, "山不在高，有仙则名。水不在深，有龙则灵。"),  # 《陋室铭》, text size: texture
    (44, "天地玄黄 宇宙洪荒 0123456789"),
]
W, PAD = 1400, 40
INK, PAPER, GREY = (20, 20, 20), (250, 250, 248), (120, 120, 115)


def load(path: Path, size: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(path), size)
    try:
        axes = font.get_variation_axes()
        font.set_variation_by_axes([400 if a.get("name") in (b"Weight", "Weight") else a["default"] for a in axes])
    except OSError:
        pass
    return font


label_font = load(ROOT / "fonts-src" / SOURCES["noto-sans-sc"]["file"], 26)


def specimen(font_id: str) -> Image.Image:
    path = ROOT / "fonts-src" / SOURCES[font_id]["file"]
    height = PAD * 2 + 50 + sum(int(size * 1.35) for size, _ in LINES)
    img = Image.new("RGB", (W, height), PAPER)
    d = ImageDraw.Draw(img)
    f = FONTS[font_id]
    d.text((PAD, PAD), f"{f['name']['zh']}  {f['name']['en']}   ·   {f['category']}", font=label_font, fill=GREY)
    y = PAD + 50
    for size, text in LINES:
        d.text((PAD, y), text, font=load(path, size), fill=INK)
        y += int(size * 1.35)
    return img


def main():
    sheets = []
    for font_id in SOURCES:
        img = specimen(font_id)
        img.save(OUT / f"{font_id}.png")
        sheets.append(img)
        print(f"  {font_id}")
    # Contact sheet: all specimens stacked, scaled down
    scale = 0.5
    small = [s.resize((int(s.width * scale), int(s.height * scale))) for s in sheets]
    sheet = Image.new("RGB", (small[0].width, sum(s.height for s in small)), PAPER)
    y = 0
    for s in small:
        sheet.paste(s, (0, y))
        y += s.height
    sheet.save(OUT / "_all.png")
    print("→ similarity/specimens/")


if __name__ == "__main__":
    main()
