"""Put each hosted font's license text next to its files: public/fonts/<id>/LICENSE.txt

We redistribute these fonts (sliced pieces and name-only files), and their
licenses ask for the license to travel with the font. The text is fetched
from each font's official source.

Run:  similarity/.venv/bin/python similarity/scripts/license_files.py
"""
from __future__ import annotations

import io
import json
import re
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FONTS = {f["id"]: f for f in json.loads((ROOT / "src/data/fonts.json").read_text())}
SOURCES = {k: v for k, v in json.loads((ROOT / "similarity/sources.json").read_text()).items() if not k.startswith("_")}

# License files to look for in a GitHub repository, most specific first
CANDIDATES = ["OFL.txt", "LICENSE-OFL", "OFL", "LICENSE", "LICENSE.txt", "LICENSE.md", "License", "license.txt", "OFL-1.1.txt"]
# For fonts from Debian archives: the license file inside the archive
# Fonts whose license text is a plain file somewhere else
DIRECT = {
    "fandol-hei": "https://mirrors.ctan.org/fonts/fandol/COPYING",
    "fandol-song": "https://mirrors.ctan.org/fonts/fandol/COPYING",
    "fandol-kai": "https://mirrors.ctan.org/fonts/fandol/COPYING",
    "fandol-fang": "https://mirrors.ctan.org/fonts/fandol/COPYING",
    "lxgw-975hazygo": "https://raw.githubusercontent.com/lxgw/975HazyGo/HEAD/SIL_Open_Font_License_1.1.txt",
}
IN_ARCHIVE = {
    "ar-pl-uming": "license/english/ARPHICPL.TXT",
    "ar-pl-ukai": "license/english/ARPHICPL.TXT",
    "ar-pl-sungti": "license/english/ARPHICPL.TXT",
    "wqy-microhei": "LICENSE_Apache2.txt",
}


def from_github(repo: str) -> str | None:
    for name in CANDIDATES:
        try:
            return urllib.request.urlopen(f"https://raw.githubusercontent.com/{repo}/HEAD/{name}", timeout=30).read().decode("utf-8", "replace")
        except Exception:
            continue
    return None


def from_archive(url: str, member: str) -> str:
    data = urllib.request.urlopen(url, timeout=300).read()
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        m = next(m for m in t.getmembers() if m.name.endswith(member))
        return t.extractfile(m).read().decode("utf-8", "replace")


def main():
    for folder in sorted((ROOT / "public/fonts").iterdir()):
        if not folder.is_dir():
            continue
        font_id = folder.name
        f = FONTS[font_id]
        if font_id in DIRECT:
            text = urllib.request.urlopen(DIRECT[font_id], timeout=60).read().decode("utf-8", "replace")
        elif font_id in IN_ARCHIVE:
            text = from_archive(SOURCES[font_id]["url"], IN_ARCHIVE[font_id])
        else:
            m = re.match(r"https://github\.com/([^/]+/[^/]+)", f["source"]["homepage"])
            text = from_github(m.group(1)) if m else None
        if not text:
            print(f"  ! {font_id}: no license file found — add one by hand")
            continue
        header = (
            f"{f['name']['zh']} / {f['name']['en']}\n"
            f"License: {f['license']['id']}  ({f['license']['url']})\n"
            f"Source:  {f['source']['homepage']}\n"
            "These web font files are subsets of the original font, made for web delivery.\n"
            + "-" * 72 + "\n\n"
        )
        (folder / "LICENSE.txt").write_text(header + text)
        print(f"  {font_id:22} {len(text):6} chars")


if __name__ == "__main__":
    main()
