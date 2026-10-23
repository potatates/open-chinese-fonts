"""When each font joined the catalog, for the 新增字体 page: src/data/added.json

Dates come from the git history (the first commit whose fonts.json mentions
the font's id). Fonts not committed yet get today's date. Existing dates are
kept, so run it after adding fonts:
  similarity/.venv/bin/python similarity/scripts/added_dates.py
"""
import datetime
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "src/data/added.json"
fonts = json.loads((ROOT / "src/data/fonts.json").read_text())
added = json.loads(OUT.read_text()) if OUT.exists() else {}
today = datetime.date.today().isoformat()

for f in fonts:
    if f["id"] in added:
        continue
    log = subprocess.run(
        ["git", "log", "--reverse", "--format=%as", "-S", f'"id": "{f["id"]}"', "--", "src/data/fonts.json"],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout.split()
    added[f["id"]] = log[0] if log else today

added = {f["id"]: added[f["id"]] for f in fonts}  # catalog order, drop removed fonts
OUT.write_text(json.dumps(added, indent=2) + "\n")
by_month = {}
for d in added.values():
    by_month[d[:7]] = by_month.get(d[:7], 0) + 1
print("→ src/data/added.json", dict(sorted(by_month.items())))
