"""Download each font's original file (listed in similarity/sources.json) into fonts-src/.

Run:  similarity/.venv/bin/python similarity/scripts/fetch_fonts.py
Files already downloaded are skipped, so it's safe to run again.
"""
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = json.loads((ROOT / "similarity/sources.json").read_text())
OUT = ROOT / "fonts-src"
OUT.mkdir(exist_ok=True)

for font_id, src in SOURCES.items():
    if font_id.startswith("_"):
        continue
    target = OUT / src["file"]
    if target.exists():
        print(f"  skip  {font_id} (already have {target.name})")
        continue
    print(f"  get   {font_id} ← {src['url']}")
    data = urllib.request.urlopen(src["url"], timeout=300).read()
    if "member" in src:
        # The font is inside a zip: find the file with that name anywhere in it
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = [n for n in z.namelist() if n.endswith("/" + src["member"]) or n == src["member"]]
            if not names:
                sys.exit(f"{src['member']} not found in zip; contents: {z.namelist()[:20]}")
            data = z.read(names[0])
    target.write_bytes(data)
    print(f"        {len(data) / 1e6:.1f} MB → fonts-src/{target.name}")
