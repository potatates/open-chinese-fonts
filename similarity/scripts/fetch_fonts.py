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


def zip_name(info: zipfile.ZipInfo) -> str:
    """Zips often store Chinese file names without saying which encoding (GBK
    from Chinese Windows, or UTF-8), and Python then reads them as cp437.
    Undo that so we can match Chinese names: try UTF-8 first, then GBK."""
    if info.flag_bits & 0x800:  # the name is marked as UTF-8
        return info.filename
    raw = info.filename.encode("cp437", errors="ignore")
    for enc in ("utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return info.filename


def repair(data: bytes) -> bytes:
    """A few fonts ship with one damaged table, which makes subsetting crash.
    A truncated OS/2 table (browsers need it) is padded back to full length;
    any other broken table (optional extras such as gasp or GSUB) is dropped."""
    from fontTools.ttLib import TTFont, newTable

    font = TTFont(io.BytesIO(data))
    for tag in list(font.keys()):
        try:
            font[tag]
        except Exception:
            if tag == "OS/2":
                raw = font.reader["OS/2"]
                table = newTable("OS/2")
                table.decompile(raw + bytes(100), font)  # missing fields read as 0
                table.version = min(table.version, 4)
                font["OS/2"] = table
            else:
                del font[tag]
            print(f"        repaired a damaged {tag} table")
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


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
        # Some hosts (猫啃网) only serve files to requests that say which page linked them
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", **entry.get("headers", {})})
        _downloads[url] = urllib.request.urlopen(req, timeout=600).read()
    data = _downloads[url]
    member = entry.get("member")
    if member and url.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = [i for i in z.infolist() if zip_name(i).endswith("/" + member) or zip_name(i) == member]
            if not names:
                sys.exit(f"{member} not found in {url}: {[zip_name(i) for i in z.infolist()][:20]}")
            try:
                data = z.read(names[0])
            except NotImplementedError:  # Deflate64 compression: Python can't read it, macOS unzip can
                import subprocess
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
                    tmp.write(_downloads[url])
                    tmp.flush()
                    data = subprocess.run(["unzip", "-p", tmp.name, names[0].filename], capture_output=True, check=True).stdout
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
    if "instance" in entry:
        # A variable font holds every weight; cut out the one we want, e.g. {"wght": 400}
        from fontTools.ttLib import TTFont
        from fontTools.varLib.instancer import instantiateVariableFont

        font = instantiateVariableFont(TTFont(io.BytesIO(data)), entry["instance"])
        buf = io.BytesIO()
        font.save(buf)
        data = buf.getvalue()
    if entry.get("repair"):
        data = repair(data)
    target.write_bytes(data)
    print(f"        {len(data) / 1e6:.1f} MB → fonts-src/{target.name}")


failed = []
for font_id, src in SOURCES.items():
    if font_id.startswith("_"):
        continue
    try:
        fetch(src, font_id)
        for weight, entry in src.get("web", {}).items():
            fetch(entry, f"{font_id} {weight}")
    except (Exception, SystemExit) as err:  # one broken download shouldn't stop the rest
        print(f"  !! {font_id}: {err}")
        failed.append(font_id)
if failed:
    print("FAILED:", " ".join(failed))
