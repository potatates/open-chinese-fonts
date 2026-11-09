"""Write similarity/extremes.html: for every trait, the fonts at each end of
the scale, with their specimens, so wrong scores are easy to spot by eye.

Run after build_similar.py:  similarity/.venv/bin/python similarity/scripts/extremes.py
View it:  cd similarity && python3 -m http.server 4400  →  http://localhost:4400/extremes.html
"""
import html
import json

N = 10  # fonts shown at each end

axes = json.load(open("src/data/axes.json"))
scores = axes["scores"]
fonts = {f["id"]: f for f in json.load(open("src/data/fonts.json"))}
overrides = {k: v for k, v in json.load(open("similarity/overrides.json")).items() if not k.startswith("_")}


def row(i, axis):
    f = fonts[i]
    fixed = " <b>已手动修正</b>" if axis in overrides.get(i, {}) else ""
    return (
        f"<tr><td class=v>{scores[i][axis]:.2f}</td>"
        f"<td class=n><a href='https://zixiangfont.com/fonts/{i}/'>{html.escape(f['name']['zh'])}</a>{fixed}"
        f"<br><small>{i}</small></td>"
        f"<td><img src='specimens/thumb/{i}.png' loading=lazy></td></tr>"
    )


parts = []
for axis, info in axes["axes"].items():
    ids = sorted((i for i in scores if i in fonts and "pixel" not in fonts[i]["tags"]), key=lambda i: scores[i][axis])
    low, high = ids[:N], ids[-N:][::-1]
    parts.append(
        f"<section><h2>{info['zh']} <small>{axis}</small></h2><div class=cols>"
        f"<table><caption>最高</caption>{''.join(row(i, axis) for i in high)}</table>"
        f"<table><caption>最低</caption>{''.join(row(i, axis) for i in low)}</table>"
        f"</div></section>"
    )

open("similarity/extremes.html", "w").write(
    "<!doctype html><meta charset=utf-8><title>极端值检查</title>"
    "<style>body{font:14px -apple-system,'PingFang SC',sans-serif;margin:24px;background:#fafaf8;color:#1a1a1a}"
    "h2{margin:40px 0 8px;border-top:2px solid #1a1a1a;padding-top:12px}h2 small{color:#888;font-weight:400}"
    ".cols{display:grid;grid-template-columns:1fr 1fr;gap:32px}table{border-collapse:collapse;width:100%}"
    "caption{text-align:left;font-weight:600;padding:4px 0}td{border-top:1px solid #ddd;padding:4px 8px;vertical-align:middle}"
    "td.v{font-variant-numeric:tabular-nums;width:3em}td.n{width:11em}td small{color:#999}td b{color:#c23b22;font-size:12px}"
    "img{height:44px}a{color:inherit}</style>"
    "<h1>各项特征的极端值</h1><p>每项特征最高和最低的 10 款字体（不含像素字体）。红字表示已在 overrides.json 中手动修正过。"
    "看到不对的，告诉我字体名和哪一项即可。</p>" + "".join(parts)
)
print("→ similarity/extremes.html")
