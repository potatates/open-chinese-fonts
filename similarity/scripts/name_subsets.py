"""Tiny web fonts for text we know in advance: each font's own name, and the
sample sentences (src/data/samples.json) its detail page starts with.

Catalog cards show a font's name; a detail page first shows a sample sentence.
Google Fonts can serve just those characters on request; for all other fonts
we pre-build the same thing here, so the first view costs a few KB instead of
the several sliced pieces (hundreds of KB) the full font would need. As soon
as you type your own text, the page switches to the full sliced font.

Run:  similarity/.venv/bin/python similarity/scripts/name_subsets.py
Writes public/fonts/<id>/text/*.woff2 and src/data/name-subsets.json:
  { fontId: { weight: { text: url } } }
"""
import json
import shutil
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {k: v for k, v in json.loads((ROOT / "similarity/sources.json").read_text()).items() if not k.startswith("_")}
FONTS = json.loads((ROOT / "src/data/fonts.json").read_text())
SAMPLES = [s["text"] for s in json.loads((ROOT / "src/data/samples.json").read_text())]


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


def make_subset(src: Path, text: str, out: Path) -> None:
    font = TTFont(str(src))
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.hinting = False
    opts.name_IDs = ["*"]  # keep copyright and license info inside the file
    opts.desubroutinize = True  # CFF fonts otherwise keep shared drawing code for the whole font
    opts.layout_features = ["*"]
    opts.prune_unicode_ranges = False  # GNU Unifont marks an invalid range (123) that makes this step crash
    s = subset.Subsetter(opts)
    s.populate(text=text)
    s.subset(font)
    drop_stray_private(font)
    font.flavor = "woff2"
    font.save(str(out))


manifest: dict = {}
total = 0
for f in FONTS:
    if f["webfont"]["provider"] == "google":
        continue  # Google already does this (the "text=" option)
    if f["license"]["id"] == "IPA":
        continue  # IPA's rules for modified copies are stricter; keep using the full web font
    src = SOURCES.get(f["id"])
    if not src:
        print(f"  ! no source file for {f['id']}")
        continue
    # Which original file do we have for each weight? ("file" is the Regular)
    files = {"400": src["file"], **{w: e["file"] for w, e in src.get("web", {}).items()}}
    out_dir = ROOT / "public/fonts" / f["id"] / "text"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    old_name_file = ROOT / "public/fonts" / f["id"] / "name.woff2"
    old_name_file.unlink(missing_ok=True)
    manifest[f["id"]] = {}
    for weight, file in files.items():
        texts = {f["name"]["zh"]: f"{weight}-name.woff2"} if weight == "400" else {}
        texts.update({t: f"{weight}-s{i}.woff2" for i, t in enumerate(SAMPLES)})
        entry = manifest[f["id"]].setdefault(weight, {})
        for text, name in texts.items():
            make_subset(ROOT / "fonts-src" / file, text, out_dir / name)
            entry[text] = f"/fonts/{f['id']}/text/{name}"
            total += (out_dir / name).stat().st_size
    size = sum(p.stat().st_size for p in out_dir.iterdir()) / 1024
    print(f"  {f['id']:24} weights {','.join(files)}  {size:6.0f} KB total")

(ROOT / "src/data/name-subsets.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print(f"→ {total / 1e6:.1f} MB in public/fonts/*/text/, src/data/name-subsets.json")
