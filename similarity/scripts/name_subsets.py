"""Tiny web fonts holding only each font's own name, e.g. "霞鹜文楷".

Catalog cards, similar-font cards and the pin tray show a font's name in the
font itself. Google Fonts can serve just those characters on request; for all
other fonts we pre-build the same thing here, so a card costs a few KB
instead of a ~100 KB slice.

Run:  similarity/.venv/bin/python similarity/scripts/name_subsets.py
Writes public/fonts/<id>/name.woff2 and src/data/name-subsets.json
"""
import json
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {k: v for k, v in json.loads((ROOT / "similarity/sources.json").read_text()).items() if not k.startswith("_")}
FONTS = json.loads((ROOT / "src/data/fonts.json").read_text())

def drop_stray_private(font) -> None:
    """Some CID-keyed CFF fonts (e.g. 未来荧黑) keep an unused top-level Private
    dict with thousands of subroutines (~115 KB) that subsetting doesn't remove."""
    if "CFF " not in font:
        return
    td = font["CFF "].cff.topDictIndex[0]
    if hasattr(td, "FDArray") and "Private" in td.rawDict:
        del td.rawDict["Private"]
        if hasattr(td, "Private"):
            del td.Private


manifest = {}
for f in FONTS:
    if f["webfont"]["provider"] == "google":
        continue  # Google already does this (the "text=" option)
    src = SOURCES.get(f["id"])
    if not src:
        print(f"  ! no source file for {f['id']}")
        continue
    text = f["name"]["zh"]
    font = TTFont(str(ROOT / "fonts-src" / src["file"]))
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.hinting = False
    opts.desubroutinize = True  # CFF fonts otherwise keep shared drawing code for the whole font
    opts.layout_features = ["*"]
    s = subset.Subsetter(opts)
    s.populate(text=text)
    s.subset(font)
    drop_stray_private(font)
    out = ROOT / "public/fonts" / f["id"] / "name.woff2"
    out.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = "woff2"
    font.save(str(out))
    # The measured file is the Regular (400) weight
    manifest[f["id"]] = {"text": text, "weight": 400, "url": f"/fonts/{f['id']}/name.woff2"}
    print(f"  {f['id']:24} {out.stat().st_size / 1024:5.1f} KB  {text}")

(ROOT / "src/data/name-subsets.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print("→ public/fonts/*/name.woff2, src/data/name-subsets.json")
