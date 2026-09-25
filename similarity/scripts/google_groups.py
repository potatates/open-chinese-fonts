"""Fetch the character groups Google Fonts uses to slice Chinese fonts.

Google splits each Chinese font into ~100 pieces, grouping characters that
tend to appear together (by real-world frequency). We reuse the same groups
for the fonts we slice ourselves, so a sentence needs only a few pieces.

Run:  similarity/.venv/bin/python similarity/scripts/google_groups.py
Writes similarity/google-slices.json (a list of groups of code points).
"""
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# A modern browser user agent, so Google returns its sliced woff2 stylesheet
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
req = urllib.request.Request("https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400", headers={"User-Agent": UA})
css = urllib.request.urlopen(req, timeout=60).read().decode()

groups = []
for idx, body in enumerate(re.findall(r"@font-face\s*\{(.*?)\}", css, re.S)):  # keep Google's order
    rng = re.search(r"unicode-range:\s*([^;]+);", body).group(1)
    cps = []
    for part in rng.split(","):
        part = part.strip().replace("U+", "")
        if "-" in part:
            a, b = part.split("-")
            cps.extend(range(int(a, 16), int(b, 16) + 1))
        else:
            cps.append(int(part, 16))
    groups.append((idx, cps))

groups.sort()
out = [cps for _, cps in groups]
(ROOT / "similarity/google-slices.json").write_text(json.dumps(out))
print(f"{len(out)} groups, {sum(map(len, out))} code points → similarity/google-slices.json")
