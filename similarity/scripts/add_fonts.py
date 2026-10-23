"""Helper for adding a batch of fonts: appends entries to similarity/sources.json
and src/data/fonts.json, keeping fonts.json's hand-made formatting.

Use from a small batch script:
    import sys; sys.path.insert(0, "similarity/scripts")
    from add_fonts import add, e, mk, q, commit
    add("my-font", "中文名", "English", "hei", [], "Designer", 2025, "OFL-1.1", "<license url>",
        "<homepage>", {"400": e("<download url>", "MyFont-Regular.ttf")})
    commit()
Then run the usual pipeline: fetch_fonts → slice_webfonts → license_files →
name_subsets → measure → specimens → (score by eye) → build_similar → added_dates.
"""
import json
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAOKEN = {"Referer": "https://www.maoken.com/"}  # 猫啃网 only serves files to requests from its pages
q = urllib.parse.quote
MAOKEN_BASE = "https://oss.maoken.com/" + q("猫啃字体/中国大陆/")
NEW: list[dict] = []


def e(url: str, file: str, **kw) -> dict:
    """One downloadable file (kw: member=…, headers=…, instance=…, repair=True)."""
    return dict(url=url, file=file, **kw)


def mk(zipname: str, member: str, file: str) -> dict:
    """A file inside a 猫啃网 zip."""
    return e(MAOKEN_BASE + q(zipname), file, member=member, headers=MAOKEN)


def add(id, zh, en, cat, also, designer, year, lic, lic_url, home, weights, download=None, tags=(), foundry=None, family=None, rfn=False):
    NEW.append(dict(id=id, zh=zh, en=en, cat=cat, also=list(also), designer=designer, year=year, lic=lic, lic_url=lic_url,
                    home=home, download=download or home, weights=weights, tags=list(tags), foundry=foundry,
                    family=family or (f"ZX {id}" if rfn else en), rfn=rfn))


def _j(v):
    s = json.dumps(v, ensure_ascii=False, separators=(", ", ": "))
    return "{ " + s[1:-1] + " }" if isinstance(v, dict) else s


def commit():
    sources = json.loads((ROOT / "similarity/sources.json").read_text())
    have = {f["id"] for f in json.loads((ROOT / "src/data/fonts.json").read_text())}
    blocks = []
    for n in NEW:
        assert n["id"] not in have and n["id"] not in sources, f"already in the catalog: {n['id']}"
        ws = n["weights"]
        reg = ws.get("400") or next(iter(ws.values()))
        sources[n["id"]] = {"url": reg["url"], "file": reg["file"], **{k: v for k, v in reg.items() if k not in ("url", "file")},
                            **({"rfn": True} if n["rfn"] else {}), "web": ws}
        css = ",\n".join(f'        "{w}": "/fonts/{n["id"]}/{w}/result.css"' for w in sorted(ws, key=int))
        blocks.append(f'''  {{
    "id": "{n['id']}",
    "name": {_j({"zh": n['zh'], "en": n['en']})},
    "category": "{n['cat']}",
    "alsoIn": {_j(n['also'])},
    "tags": {_j(n['tags'])},
    "weights": {_j(sorted(int(w) for w in ws))},
    "variants": [],
    "designer": {_j(n['designer'])},
    "foundry": {_j(n['foundry'])},
    "year": {n['year']},
    "license": {_j({"id": n['lic'], "url": n['lic_url']})},
    "source": {{
      "homepage": {_j(n['home'])},
      "download": {_j(n['download'])}
    }},
    "webfont": {{
      "provider": "css",
      "family": {_j(n['family'])},
      "css": {{
{css}
      }}
    }}
  }}''')
    (ROOT / "similarity/sources.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n")
    head = (ROOT / "src/data/fonts.json").read_text().rstrip()
    (ROOT / "src/data/fonts.json").write_text(head[:-1].rstrip() + ",\n" + ",\n".join(blocks) + "\n]\n")
    json.loads((ROOT / "src/data/fonts.json").read_text())
    print("added", len(NEW), [n["id"] for n in NEW])
