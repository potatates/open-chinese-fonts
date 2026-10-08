"""Slice fonts into small web-font pieces, for fonts with no ready-made web version.

Like Google Fonts: each piece holds a group of characters and is listed in a
stylesheet with its "unicode-range", so a browser downloads only the pieces
covering the text on screen. We reuse Google's own groups (fetched by
google_groups.py into similarity/google-slices.json), which put characters
that are used together in the same piece — so a sentence needs few pieces.

To keep what we host small, only characters a Simplified Chinese site needs
are kept: Latin letters, punctuation, and the 6,763 characters of GB2312
(the standard set that covers everyday modern Chinese).

Only fonts whose licenses allow this are listed with "web" entries in
similarity/sources.json (see the notes there).

Run:  similarity/.venv/bin/python similarity/scripts/slice_webfonts.py
Writes public/fonts/<id>/<weight>/result.css + *.woff2
"""
from __future__ import annotations

import io
import json
import shutil
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {k: v for k, v in json.loads((ROOT / "similarity/sources.json").read_text()).items() if not k.startswith("_")}
FONTS = {f["id"]: f for f in json.loads((ROOT / "src/data/fonts.json").read_text())}
sys.path.insert(0, str(Path(__file__).parent))
from measure import COMMON  # noqa: E402  (frequency-ordered common characters)
from rfn import rename  # noqa: E402  (Reserved Font Name fonts)

# Non-Chinese characters we keep: Latin, general punctuation, CJK punctuation, full-width forms
EXTRA_RANGES = [(0x20, 0x7E), (0xA0, 0xFF), (0x2010, 0x205E), (0x3000, 0x303F), (0xFF01, 0xFF5E), (0x2E80, 0x2EFF)]


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


def gb2312_order() -> list[str]:
    """GB2312's 6,763 characters, most common first."""
    level1, level2 = [], []
    for hi in range(0xB0, 0xF8):
        for lo in range(0xA1, 0xFF):
            try:
                ch = bytes([hi, lo]).decode("gb2312")
            except UnicodeDecodeError:
                continue
            (level1 if hi < 0xD8 else level2).append(ch)
    common = list(dict.fromkeys(COMMON))
    rest1 = [c for c in level1 if c not in set(common)]
    return common + rest1 + level2


def chunks(cjk: list[int]) -> list[list[int]]:
    """Small pieces for common characters (fast first paint), bigger for rare ones."""
    out, i = [], 0
    while i < len(cjk):
        size = 150 if i < 900 else 300 if i < 3755 else 600
        out.append(cjk[i : i + size])
        i += size
    return out


GOOGLE_GROUPS = json.loads((ROOT / "similarity/google-slices.json").read_text())
MIN_PIECE = 30  # merge smaller groups, so there aren't many tiny downloads


def google_pieces(keep: list[int]) -> list[list[int]]:
    """Split the characters we keep along Google's groups."""
    keep_set = set(keep)
    pieces, used = [], set()
    for group in GOOGLE_GROUPS:
        cps = [c for c in group if c in keep_set and c not in used]
        if not cps:
            continue
        used.update(cps)
        if pieces and len(cps) < MIN_PIECE:
            pieces[-1].extend(cps)  # too small on its own: add to the previous piece
        else:
            pieces.append(cps)
    leftover = [c for c in keep if c not in used]
    if leftover:
        pieces.append(leftover)
    return pieces


def to_ranges(cps: list[int]) -> str:
    cps = sorted(cps)
    parts, start, prev = [], cps[0], cps[0]
    for cp in cps[1:] + [None]:
        if cp is not None and cp == prev + 1:
            prev = cp
            continue
        parts.append(f"U+{start:X}" if start == prev else f"U+{start:X}-{prev:X}")
        if cp is not None:
            start = prev = cp
    return ", ".join(parts)


def slice_font(src: Path, out_dir: Path, family: str, weight: str, rename_as: str | None = None):
    base = TTFont(str(src))
    if rename_as:
        rename(base, rename_as)
    have = set(base.getBestCmap())
    extra = [cp for lo, hi in EXTRA_RANGES for cp in range(lo, hi + 1) if cp in have]
    cjk = [ord(c) for c in gb2312_order() if ord(c) in have]
    pieces = google_pieces(extra + cjk)

    # First cut the font down to everything we keep, so each piece loads faster
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.hinting = False  # hinting mostly matters on Windows at small sizes; it's large
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    opts.prune_unicode_ranges = False  # GNU Unifont marks an invalid range (123) that makes this step crash
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=extra + cjk)
    sub.subset(base)
    buf = io.BytesIO()
    base.save(buf)
    trimmed = buf.getvalue()

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    css, total = [], 0
    for i, cps in enumerate(pieces):
        font = TTFont(io.BytesIO(trimmed))
        opts.flavor = "woff2"
        s = subset.Subsetter(opts)
        s.populate(unicodes=cps)
        s.subset(font)
        drop_stray_private(font)
        name = f"{i:03d}.woff2"
        font.flavor = "woff2"
        font.save(str(out_dir / name))
        total += (out_dir / name).stat().st_size
        css.append(
            "@font-face {\n"
            f"  font-family: '{family}';\n  font-style: normal;\n  font-weight: {weight};\n  font-display: swap;\n"
            f"  src: url('./{name}') format('woff2');\n  unicode-range: {to_ranges(cps)};\n}}"
        )
    (out_dir / "result.css").write_text("\n".join(css) + "\n")
    print(f"  {src.name}: {len(pieces)} pieces, {total / 1e6:.1f} MB → {out_dir.relative_to(ROOT)}")


def main():
    only = set(sys.argv[1:])  # optionally: slice_webfonts.py <font-id> …
    for font_id, src in SOURCES.items():
        if "web" not in src or (only and font_id not in only):
            continue
        family = FONTS[font_id]["webfont"]["family"]  # "ZX <id>" for Reserved Font Name fonts
        for weight, entry in src["web"].items():
            slice_font(
                ROOT / "fonts-src" / entry["file"], ROOT / "public/fonts" / font_id / weight, family, weight,
                rename_as=font_id if src.get("rfn") else None,
            )


if __name__ == "__main__":
    main()
