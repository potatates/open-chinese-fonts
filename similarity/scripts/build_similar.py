"""Combine measured + subjective scores, then find each font's nearest neighbours.

Inputs  (similarity/): measured.json, subjective.json, overrides.json
        (src/data/):   fonts.json (names, categories)
Outputs src/data/similar.json  each font's top 6 similar fonts, with a reason
        src/data/axes.json     each font's final 0–1 scores (for the site)
        similarity/review.md   a readable table of every score, for checking

Run:  similarity/.venv/bin/python similarity/scripts/build_similar.py
No external libraries needed.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# ---- Tune here ------------------------------------------------------------
# weight: how much each axis counts in the distance (0 = ignore it).
# "density" is measured as 字面 (footprint: how much of the square a character
# fills). The other candidate, ink-per-box, ranked fonts 93% the same as
# weight, so it would just count weight twice. Switch "from" to "density" to
# use it anyway.
AXES = {
    "weight":     {"zh": "字重",     "from": "weight",    "weight": 1.0},
    "contrast":   {"zh": "笔画对比", "from": "contrast",  "weight": 1.0},
    "roundness":  {"zh": "圆润度",   "from": "roundness", "weight": 1.0},
    "density":    {"zh": "字面",     "from": "footprint", "weight": 0.6},
    "formality":  {"zh": "正式感",   "from": None,        "weight": 1.0},  # subjective
    "quirkiness": {"zh": "个性",     "from": None,        "weight": 1.0},  # subjective
}
SAME_CATEGORY_FACTOR = 0.75  # same category: distance × this (a small bonus)
TOP_N = 6
CHECK = ["noto-sans-sc", "noto-serif-sc", "lxgw-wenkai", "ma-shan-zheng", "xiaolai", "zcool-kuaile"]

# How each axis is described in a reason, when both fonts are high / low / in between
PHRASES = {
    "weight":     ("都偏粗", "都偏细", "字重相近"),
    "contrast":   ("都有明显的粗细对比", "笔画都粗细均匀", "笔画对比相近"),
    "roundness":  ("都很圆润", "都棱角分明", "圆润度相近"),
    "density":    ("字面都饱满", "字面都紧凑", "字面大小相近"),
    "formality":  ("都端正正式", "都随性活泼", "正式感相近"),
    "quirkiness": ("都很有个性", "都中规中矩", "个性程度相近"),
}
# ---------------------------------------------------------------------------


def load(path):
    return json.loads((ROOT / path).read_text())


def main():
    fonts = {f["id"]: f for f in load("src/data/fonts.json")}
    measured = {k: v for k, v in load("similarity/measured.json").items() if not k.startswith("_")}
    subjective = {k: v for k, v in load("similarity/subjective.json").items() if not k.startswith("_")}
    overrides = {k: v for k, v in load("similarity/overrides.json").items() if not k.startswith("_")}
    ids = [i for i in fonts if i in measured and i in subjective]
    missing = set(fonts) - set(ids)
    if missing:
        print(f"! skipped (not measured or not scored yet): {sorted(missing)}")

    # 1. Scale each measured axis to 0–1 across the catalog (min → 0, max → 1).
    #    Plain min–max keeps real gaps (e.g. the three very round fonts stay far
    #    from the rest), which rank-based scaling would erase.
    scores = {i: {} for i in ids}
    for axis, cfg in AXES.items():
        if cfg["from"] is None:
            for i in ids:
                scores[i][axis] = float(subjective[i][axis])
            continue
        raw = {i: measured[i][cfg["from"]] for i in ids}
        lo, hi = min(raw.values()), max(raw.values())
        for i in ids:
            scores[i][axis] = (raw[i] - lo) / (hi - lo) if hi > lo else 0.5

    # 2. Your overrides always win
    for i, vals in overrides.items():
        for axis, v in vals.items():
            if i in scores and axis in AXES:
                scores[i][axis] = float(v)

    # 3. Weighted distance between every pair of fonts
    total_w = sum(c["weight"] for c in AXES.values())

    def distance(a, b):
        d = math.sqrt(sum(c["weight"] * (scores[a][ax] - scores[b][ax]) ** 2 for ax, c in AXES.items()) / total_w)
        if fonts[a]["category"] == fonts[b]["category"]:
            d *= SAME_CATEGORY_FACTOR
        return d

    # 4. A one-line reason: the two axes where the pair agrees most, preferring
    #    traits that are distinctive (both very high or both very low).
    def reason(a, b):
        cat_zh = {"song": "宋体", "hei": "黑体", "kai": "楷体", "handwriting": "手写·书法", "rounded": "圆体", "display": "创意"}
        ranked = []
        for ax, c in AXES.items():
            if c["weight"] == 0:
                continue
            x, y = scores[a][ax], scores[b][ax]
            mean = (x + y) / 2
            notable = abs(mean - 0.5)  # 0 in the middle, 0.5 at the extremes
            ranked.append((abs(x - y) - 0.4 * notable, ax, mean))
        ranked.sort()
        parts = []
        for _, ax, mean in ranked[:2]:
            high, low, mid = PHRASES[ax]
            parts.append(high if mean > 0.67 else low if mean < 0.33 else mid)
        text = "、".join(parts)
        if fonts[a]["category"] == fonts[b]["category"]:
            text = f"同为{cat_zh[fonts[a]['category']]} · {text}"
        return text

    similar = {}
    for a in ids:
        near = sorted((distance(a, b), b) for b in ids if b != a)[:TOP_N]
        similar[a] = [{"id": b, "distance": round(d, 3), "reason": reason(a, b)} for d, b in near]

    # 5. Write outputs
    (ROOT / "src/data/similar.json").write_text(json.dumps(similar, ensure_ascii=False, indent=2) + "\n")
    axes_out = {i: {ax: round(v, 3) for ax, v in scores[i].items()} for i in ids}
    (ROOT / "src/data/axes.json").write_text(json.dumps(axes_out, ensure_ascii=False, indent=2) + "\n")
    write_review(fonts, ids, measured, subjective, overrides, scores, similar)

    # 6. Sanity check
    print("\nNearest neighbours (closest first):")
    for a in CHECK:
        if a not in similar:
            continue
        print(f"\n  {fonts[a]['name']['zh']} ({a})")
        for n in similar[a]:
            print(f"    {n['distance']:.3f}  {fonts[n['id']]['name']['zh']:10}  {n['reason']}")
    print("\n→ src/data/similar.json, src/data/axes.json, similarity/review.md")


def write_review(fonts, ids, measured, subjective, overrides, scores, similar):
    axes = list(AXES)
    lines = [
        "# Similarity scores — review",
        "",
        "Generated by `similarity/scripts/build_similar.py`. Don't edit this file;",
        "edit `subjective.json` or `overrides.json`, then run the script again.",
        "",
        "All scores are 0–1 across this catalog (0 = lowest in the set, 1 = highest).",
        "An asterisk * marks a value that comes from `overrides.json`.",
        "",
        "| Axis | Meaning | Source |",
        "| --- | --- | --- |",
        "| 字重 weight | stroke thickness | measured |",
        "| 笔画对比 contrast | thick-vs-thin stroke difference | measured |",
        "| 圆润度 roundness | round stroke ends and corners (vs sharp) | measured |",
        "| 字面 density | how much of the square a character fills | measured |",
        "| 正式感 formality | printed/orderly (1) vs casual/calligraphic (0) | scored by eye |",
        "| 个性 quirkiness | stylized/decorative (1) vs standard (0) | scored by eye |",
        "",
        "## Final scores",
        "",
        "| Font | 类别 | " + " | ".join(f"{AXES[a]['zh']}" for a in axes) + " |",
        "| --- | --- | " + " | ".join("---:" for _ in axes) + " |",
    ]
    for i in ids:
        cells = []
        for a in axes:
            star = "*" if a in overrides.get(i, {}) else ""
            cells.append(f"{scores[i][a]:.2f}{star}")
        lines.append(f"| {fonts[i]['name']['zh']} {fonts[i]['name']['en']} | {fonts[i]['category']} | " + " | ".join(cells) + " |")

    lines += ["", "## Why each font got its formality / quirkiness score", ""]
    for i in ids:
        s = subjective[i]
        lines.append(f"- **{fonts[i]['name']['zh']}** — 正式感 {s['formality']:.2f}, 个性 {s['quirkiness']:.2f}. {s['why']}")

    lines += ["", "## Nearest neighbours", ""]
    for i in ids:
        names = "；".join(f"{fonts[n['id']]['name']['zh']}（{n['reason']}）" for n in similar[i])
        lines.append(f"- **{fonts[i]['name']['zh']}** → {names}")

    lines += ["", "## Raw measurements (before scaling)", "", "| Font | weight | contrast | roundness | footprint | ink/box density |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for i in ids:
        m = measured[i]
        lines.append(f"| {fonts[i]['name']['zh']} | {m['weight']:.3f} | {m['contrast']:.3f} | {m['roundness']:.2f} | {m['footprint']:.3f} | {m['density']:.3f} |")
    lines.append("")
    (ROOT / "similarity/review.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
