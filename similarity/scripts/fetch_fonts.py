"""Download each font's original files (listed in similarity/sources.json) into fonts-src/.

Run:  similarity/.venv/bin/python similarity/scripts/fetch_fonts.py
Files already downloaded are skipped, so it's safe to run again.
"""
import io
import json
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = json.loads((ROOT / "similarity/sources.json").read_text())
OUT = ROOT / "fonts-src"
OUT.mkdir(exist_ok=True)
_downloads: dict[str, bytes] = {}  # an archive used by several entries is downloaded once


def fetch(entry: dict, label: str):
    target = OUT / entry["file"]
    if target.exists():
        print(f"  skip  {label} (already have {target.name})")
        return
    url = entry["url"]
    cached = OUT / "_zips" / url.split("/")[-1]  # optional local copy of a big archive
    if url not in _downloads and cached.exists():
        _downloads[url] = cached.read_bytes()
    if url not in _downloads:
        print(f"  get   {label} ← {url}")
        _downloads[url] = urllib.request.urlopen(url, timeout=600).read()
    data = _downloads[url]
    member = entry.get("member")
    if member and url.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = [n for n in z.namelist() if n.endswith("/" + member) or n == member]
            if not names:
                sys.exit(f"{member} not found in {url}")
            data = z.read(names[0])
    elif member and url.endswith(".7z"):
        import py7zr  # only needed for .7z archives

        import tempfile

        with py7zr.SevenZipFile(io.BytesIO(data)) as z, tempfile.TemporaryDirectory() as tmp:
            found = [n for n in z.getnames() if n.endswith("/" + member) or n == member]
            if not found:
                sys.exit(f"{member} not found in {url}")
            z.extract(path=tmp, targets=[found[0]])
            data = (Path(tmp) / found[0]).read_bytes()
    elif member and ".tar" in url:
        with tarfile.open(fileobj=io.BytesIO(data)) as t:
            found = [m for m in t.getmembers() if m.name.endswith("/" + member) or m.name == member]
            if not found:
                sys.exit(f"{member} not found in {url}: {[m.name for m in t.getmembers()][:20]}")
            data = t.extractfile(found[0]).read()
    if "ttcIndex" in entry:
        # A .ttc holds several fonts; keep just the one we want
        from fontTools.ttLib import TTCollection

        buf = io.BytesIO()
        TTCollection(io.BytesIO(data)).fonts[entry["ttcIndex"]].save(buf)
        data = buf.getvalue()
    target.write_bytes(data)
    print(f"        {len(data) / 1e6:.1f} MB → fonts-src/{target.name}")


for font_id, src in SOURCES.items():
    if font_id.startswith("_"):
        continue
    fetch(src, font_id)
    for weight, entry in src.get("web", {}).items():
        fetch(entry, f"{font_id} {weight}")
