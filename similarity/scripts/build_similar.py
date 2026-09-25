"""Combine measured + subjective scores, then find each font's nearest neighbours.

Inputs  (similarity/): measured.json, subjective.json, overrides.json
        (src/data/):   fonts.json (names, categories)
Outputs src/data/similar.json  each font's top 6 similar fonts, with a reason
        src/data/axes.json     each font's final 0–1 scores (for the site)
        similarity/review.html a visual review page (specimens + scores + neighbours)

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
#
# "contrast" (overall thick-vs-thin) is now mostly explained by two sharper
# axes — 横竖对比 (hv) and 笔形 (serif) — so it counts half.
# "serif" (笔形) is how shaped the stroke ENDS are (起笔/收笔). It's the axis
# that most changes how a font reads, so it counts double. It's scaled on a
# log curve ("scale": "log"): the eye compares these as ratios — 文楷's ends
# are ~2.6× as shaped as a 黑体's, 宋体's ~8× — not as differences.
# "hand" (手写感) is how far "horizontal" strokes lean: hand-written
# structure, whether pen or brush. Square-root scaled: the eye reads any lean
# over ~2° as handwritten, and the 12° of cursive shouldn't squash the 3° of
# 楷体 to nothing.
# "brush" (笔触) needs BOTH a hand-written lean AND shaped strokes
# (serif/modulation): brush calligraphy scores high, pen handwriting and 宋体 low.
AXES = {
    "weight":     {"zh": "字重",     "from": "weight",     "weight": 1.3},
    "contrast":   {"zh": "粗细对比", "from": "contrast",   "weight": 0.5},
    "hv":         {"zh": "横竖对比", "from": "hv",         "weight": 1.0},
    "serif":      {"zh": "笔形",     "from": "terminal",   "weight": 2.0, "scale": "log"},
    "hand":       {"zh": "手写感",   "from": "hand",       "weight": 1.0},  # derived, see above
    "brush":      {"zh": "笔触",     "from": "brush",      "weight": 1.0},  # derived, see above
    "roundness":  {"zh": "圆润度",   "from": "roundness",  "weight": 1.0},
    "width":      {"zh": "字宽",     "from": "aspect",     "weight": 0.7},
    "density":    {"zh": "字面",     "from": "footprint",  "weight": 0.6},
    "formality":  {"zh": "正式感",   "from": None,         "weight": 1.0},  # subjective
    "quirkiness": {"zh": "个性",     "from": None,         "weight": 1.0},  # subjective
    "display":    {"zh": "标题感",   "from": None,         "weight": 1.5},  # subjective: headline vs body text
}
SAME_CATEGORY_FACTOR = 0.75  # same category: distance × this (a small bonus)
TOP_N = 6  # show up to this many similar fonts…
MIN_SIMILARITY = 0.5  # …but only those at least this similar (0–1)…
MIN_SHOW = 2  # …and always at least this many
CHECK = ["noto-sans-sc", "noto-serif-sc", "lxgw-marker-gothic", "lxgw-wenkai", "ma-shan-zheng", "xiaolai", "zcool-kuaile", "resource-han-rounded"]

# How each axis is described in a reason, when both fonts are high / low / in between
PHRASES = {
    "weight":     ("都偏粗", "都偏细", "字重相近"),
    "contrast":   ("都有明显的粗细对比", "笔画都粗细均匀", "笔画对比相近"),
    "hv":         ("都是竖粗横细", "横竖一样粗", "横竖对比相近"),
    "serif":      ("笔画都有明显的起收笔", "笔画都干净利落", "笔形相近"),
    "hand":       ("都有手写感", "都是规整的印刷结构", "手写感相近"),
    "brush":      ("都有毛笔笔触", "都没有毛笔感", "笔触相近"),
    "width":      ("字形都偏宽", "字形都偏窄", "字宽相近"),
    "roundness":  ("都很圆润", "都棱角分明", "圆润度相近"),
    "density":    ("字面都饱满", "字面都紧凑", "字面大小相近"),
    "formality":  ("都端正正式", "都随性活泼", "正式感相近"),
    "quirkiness": ("都很有个性", "都中规中矩", "个性程度相近"),
    "display":    ("都是标题/展示用字体", "都适合正文阅读", "用途相近"),
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
    def minmax(raw):
        lo, hi = min(raw.values()), max(raw.values())
        return {i: (v - lo) / (hi - lo) if hi > lo else 0.5 for i, v in raw.items()}

    # Derived raw values: hand = √tilt; brush = √(hand × modulation), each scaled 0–1 first
    tilt_n = minmax({i: math.sqrt(max(measured[i]["tilt"], 0)) for i in ids})
    mod_n = minmax({i: measured[i]["modulation"] for i in ids})
    for i in ids:
        measured[i]["hand"] = tilt_n[i]
        measured[i]["brush"] = math.sqrt(tilt_n[i] * mod_n[i])

    scores = {i: {} for i in ids}
    for axis, cfg in AXES.items():
        if cfg["from"] is None:
            for i in ids:
                scores[i][axis] = float(subjective[i][axis])
            continue
        raw = {i: measured[i][cfg["from"]] for i in ids}
        if cfg.get("scale") == "log":
            raw = {i: math.log(max(v, 1e-6)) for i, v in raw.items()}
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

    def cats(i):
        return [fonts[i]["category"], *fonts[i].get("alsoIn", [])]

    def shared_category(a, b):
        return next((c for c in cats(a) if c in cats(b)), None)

    def distance(a, b):
        d = math.sqrt(sum(c["weight"] * (scores[a][ax] - scores[b][ax]) ** 2 for ax, c in AXES.items()) / total_w)
        if shared_category(a, b):
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
            # prefer axes that matter more (weight) and traits both fonts share strongly
            ranked.append(((abs(x - y) - 0.4 * notable) / c["weight"] ** 0.5, ax, mean))
        ranked.sort()
        parts = []
        for _, ax, mean in ranked[:2]:
            high, low, mid = PHRASES[ax]
            parts.append(high if mean > 0.67 else low if mean < 0.33 else mid)
        text = "、".join(parts)
        if shared := shared_category(a, b):
            text = f"同为{cat_zh[shared]} · {text}"
        return text

    # Turn distance into a 相似度 (similarity) percentage people can read:
    # 100% = identical; 0% = as far apart as the most different 10% of pairs.
    all_d = sorted(distance(a, b) for a in ids for b in ids if a < b)
    far = all_d[int(len(all_d) * 0.9)]

    def similarity(d):
        return max(0.0, 1 - d / far)

    similar = {}
    for a in ids:
        near = sorted((distance(a, b), b) for b in ids if b != a)
        keep = [(d, b) for d, b in near if similarity(d) >= MIN_SIMILARITY][:TOP_N]
        if len(keep) < MIN_SHOW:
            keep = near[:MIN_SHOW]
        similar[a] = [
            {"id": b, "similarity": round(similarity(d), 2), "distance": round(d, 3), "reason": reason(a, b)}
            for d, b in keep
        ]

    # 5. Write outputs
    (ROOT / "src/data/similar.json").write_text(json.dumps(similar, ensure_ascii=False, indent=2) + "\n")
    axes_out = {i: {ax: round(v, 3) for ax, v in scores[i].items()} for i in ids}
    (ROOT / "src/data/axes.json").write_text(json.dumps(axes_out, ensure_ascii=False, indent=2) + "\n")
    write_review(fonts, ids, measured, subjective, overrides, scores, similar)

    # 6. Sanity check
    print("\nMost similar fonts (相似度, most similar first):")
    for a in CHECK:
        if a not in similar:
            continue
        print(f"\n  {fonts[a]['name']['zh']} ({a})")
        for n in similar[a]:
            print(f"    {n['similarity']:>4.0%}  {fonts[n['id']]['name']['zh']:10}  {n['reason']}")
    print("\n→ src/data/similar.json, src/data/axes.json, similarity/review.html")


def write_review(fonts, ids, measured, subjective, overrides, scores, similar):
    """A visual review page: specimen, score bars and neighbours side by side."""
    from html import escape

    axes = list(AXES)
    SRC = {ax: ("看图打分" if AXES[ax]["from"] is None else "测量") for ax in axes}
    cat_zh = {"song": "宋体", "hei": "黑体", "kai": "楷体", "handwriting": "手写·书法", "rounded": "圆体", "display": "创意"}

    def cats(i):
        return " / ".join(cat_zh[c] for c in [fonts[i]["category"], *fonts[i].get("alsoIn", [])])

    def cell_bg(v):  # light → dark grey by value
        g = int(245 - v * 150)
        return f"rgb({g},{g},{g - 4})"

    # Overview grid
    head = "".join(f"<th title='{SRC[a]}'>{AXES[a]['zh']}<small>×{AXES[a]['weight']:g}</small></th>" for a in axes)
    rows = []
    for i in ids:
        tds = []
        for a in axes:
            v = scores[i][a]
            star = "*" if a in overrides.get(i, {}) else ""
            color = "#fff" if v > 0.55 else "#111"
            tds.append(f"<td style='background:{cell_bg(v)};color:{color}'>{v:.2f}{star}</td>")
        rows.append(f"<tr><th><a href='#{i}'>{escape(fonts[i]['name']['zh'])}</a></th>{''.join(tds)}</tr>")
    overview = f"<table class='grid'><tr><th></th>{head}</tr>{''.join(rows)}</table>"

    # One section per font
    sections = []
    for i in ids:
        f = fonts[i]
        bars = []
        for a in axes:
            v = scores[i][a]
            star = " <b class='ov'>你改的</b>" if a in overrides.get(i, {}) else ""
            bars.append(
                f"<div class='bar'><span class='lab'>{AXES[a]['zh']}</span>"
                f"<span class='track'><span class='fill' style='width:{v * 100:.0f}%'></span></span>"
                f"<span class='val'>{v:.2f}</span>{star}</div>"
            )
        s_ = subjective[i]
        why = escape(s_["why"])
        near = []
        for n in similar[i]:
            nf = fonts[n["id"]]
            near.append(
                f"<li><a href='#{n['id']}'><img src='specimens/thumb/{n['id']}.png' alt=''></a>"
                f"<div><a href='#{n['id']}'><b>{escape(nf['name']['zh'])}</b></a> <span class='pct'>相似度 {n['similarity']:.0%}</span><br>"
                f"<span class='why'>{escape(n['reason'])}</span></div></li>"
            )
        sections.append(f"""
<section id='{i}'>
  <h2>{escape(f['name']['zh'])} <span>{escape(f['name']['en'])} · {cats(i)}</span></h2>
  <div class='row'>
    <img class='spec' src='specimens/{i}.png' alt=''>
    <div class='bars'>{''.join(bars)}<p class='note'>看图打分理由：{why}</p></div>
    <ol class='near'>{''.join(near)}</ol>
  </div>
</section>""")

    legend = "".join(f"<li><b>{AXES[a]['zh']}</b> — {SRC[a]}，权重 ×{AXES[a]['weight']:g}</li>" for a in axes)
    html = f"""<!doctype html><html lang='zh-Hans'><meta charset='utf-8'>
<title>相似字体评审</title>
<style>
  body {{ font: 14px/1.5 -apple-system, 'PingFang SC', sans-serif; margin: 32px 48px; color: #141414; background: #fafaf8; }}
  h1 {{ font-size: 24px; margin: 0 0 4px; }}
  .intro {{ color: #6b6b66; max-width: 60em; }}
  .grid {{ border-collapse: collapse; margin: 16px 0 32px; font-variant-numeric: tabular-nums; }}
  .grid th, .grid td {{ padding: 4px 8px; font-size: 12px; text-align: right; border-bottom: 1px solid #e3e3df; }}
  .grid th:first-child {{ text-align: left; }}
  .grid th small {{ display: block; color: #999; font-weight: normal; }}
  .grid a {{ color: inherit; text-decoration: none; }}
  section {{ border-top: 1px solid #c9c9c4; padding: 16px 0 24px; }}
  h2 {{ font-size: 18px; margin: 0 0 8px; }} h2 span {{ font-size: 13px; color: #6b6b66; font-weight: normal; }}
  .row {{ display: grid; grid-template-columns: 520px 300px 1fr; gap: 32px; align-items: start; }}
  .spec {{ width: 520px; border: 1px solid #e3e3df; }}
  .bar {{ display: grid; grid-template-columns: 4.5em 1fr 3em auto; gap: 8px; align-items: center; font-size: 12px; margin: 3px 0; }}
  .track {{ height: 8px; background: #e3e3df; }} .fill {{ display: block; height: 100%; background: #141414; }}
  .val {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .ov {{ color: #c23b22; font-weight: normal; font-size: 11px; }}
  .note {{ font-size: 12px; color: #6b6b66; margin-top: 12px; }}
  .near {{ list-style: none; margin: 0; padding: 0; }}
  .near li {{ display: grid; grid-template-columns: 240px 1fr; gap: 12px; align-items: center; padding: 4px 0; border-bottom: 1px solid #eee; }}
  .near img {{ width: 240px; display: block; }}
  .near a {{ color: inherit; }} .pct {{ color: #c23b22; font-size: 12px; font-weight: 600; }} .why {{ color: #6b6b66; font-size: 12px; }}
</style>
<h1>相似字体评审</h1>
<p class='intro'>每一行：字体样张 · 各项分数（0–1，在本字体库中从最低到最高） · 相似字体（相似度越高越像，最像的在最上面；只列出相似度 ≥ 50% 的，至少 2 款；点击可跳转）。
要修改分数，请编辑 <code>similarity/overrides.json</code>，然后重新运行 <code>build_similar.py</code>。</p>
<ul class='intro'>{legend}</ul>
{overview}
{''.join(sections)}
</html>"""
    (ROOT / "similarity/review.html").write_text(html)


if __name__ == "__main__":
    main()
