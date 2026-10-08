"""Renaming for fonts with a Reserved Font Name (RFN).

Under the SIL Open Font License, an author can reserve the font's name: a
modified copy (and our web subsets are modified copies) must not use it. The
fix the license itself allows is to give our copies a different internal name.
The site still shows the original name as a label, which is fine: that's
referring to the original font, not naming our copy.

In sources.json, a font with "rfn": true gets its internal names replaced by
"ZX <font-id>" in every file we make from it.
"""
from fontTools.ttLib import TTFont

# name-table entries that hold the font's name: family (1, 16, 21), unique ID (3),
# full name (4), PostScript name (6), Mac compatible full name (18), variations prefix (25).
# Style names like "Regular" (2, 17, 22) are left alone.
NAME_IDS = [1, 3, 4, 6, 16, 18, 21, 25]


def rename(font: TTFont, font_id: str) -> None:
    family = f"ZX {font_id}"
    ps = f"ZX-{font_id}"
    table = font["name"]
    for rec in list(table.names):
        if rec.nameID not in NAME_IDS:
            continue
        new = ps if rec.nameID in (6, 25) else family
        table.setName(new, rec.nameID, rec.platformID, rec.platEncID, rec.langID)
    if "CFF " in font:  # CFF outlines carry their own copy of the name
        cff = font["CFF "].cff
        cff.fontNames = [ps]
        td = cff.topDictIndex[0]
        for key in ("FullName", "FamilyName"):
            if hasattr(td, key):
                setattr(td, key, family)
        if hasattr(td, "FDArray"):
            for fd in td.FDArray:
                if hasattr(fd, "FontName"):
                    fd.FontName = ps
