"""Measure each font's visual style from rendered characters.

Every font draws the SAME ~300 common characters, so we compare style, not
content. For each character we measure, then average per font (a 10%
trimmed mean, which ignores the most extreme characters):

  weight     typical stroke thickness, as a fraction of the character size
  contrast   how much thick and thin strokes differ (log of 80th/20th percentile width)
  density    ink ÷ the character's bounding box (how "filled" each character is)
  roundness  how little the edge turns outward at TIGHT spots (square
             corners, pointed tips) — round stroke ends don't count.
             Stored as a negative number: closer to 0 = rounder.
  footprint  字面: how much of the em square the character occupies
  hv         横竖对比: log(vertical stroke width ÷ horizontal stroke width)
  modulation 笔形: width variation WITHIN strokes, after removing the
             difference between stroke directions (serif triangles, brush
             swelling, tapering), as log(95th ÷ 10th percentile)
  terminal   笔形: how shaped the stroke ENDS are (起笔/收笔: 宋体 triangles,
             楷 pressed starts, tapered 撇/捺) vs plain square or round ends.
             Mean |log(width ÷ same-direction stroke width)| near each end.
  aspect     字宽: character width ÷ height
  tilt       how far "horizontal" strokes lean (degrees); 楷书/仿宋/brush
             strokes rise to the right, 黑体/宋体 are level. Combined with
             modulation into 笔触 (brush feel) in build_similar.py.

Run:  similarity/.venv/bin/python similarity/scripts/measure.py
Writes similarity/measured.json (raw, un-normalized values).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from skimage.feature import structure_tensor
from skimage.measure import find_contours
from scipy.stats import trim_mean
from skimage.morphology import skeletonize

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {k: v for k, v in json.loads((ROOT / "similarity/sources.json").read_text()).items() if not k.startswith("_")}

EM = 256  # render size in px; large enough that thin strokes are several px wide
N_CHARS = 300

# Very common Simplified Chinese characters (roughly frequency order).
# Only characters present in EVERY font are used, and the first 300 kept.
COMMON = (
    "的一是不了人我在有他这中大来上个国到说们为子和你地出道也时年得就那要下以生会自着去之过家学对可她里后小么心多天而能好都然没日于起还发成事只作当想看文无开手十用主行方又如前所本见经头面公同三已老从动两长知民样现分将外但身些与高意进把法此实回二理美点月明其种声全工己话儿者向情部正名定女问力机给等几很业最间新什打便位因重被走电四第门相次东政海口使教西再平真听世气信北少关并内加化由却代军产入先山五太水万市眼体别处总才场师书比住员九笑性通目华报立马命张活难神数件安表原车白应路期叫死常提感金何更反合放做系计或司利受光王果亲界及今京务制解各任至清物台象记边共风战干接它许八特觉望直服毛林题建南度统色字请交爱让认算论百吃义科怎元社术结六功指思非流每青管夫连远资队跟带花快条院变联言权往展该领传近留红治决周保达办运武半候七必城父强步完革深区即求品士转量空甚众技轻程告江语英基派满式李息写呢识极令黄德收脸钱党倒未持取设始版双历越史商千片容研像找友孩站广改议形委早房音火际则首单据导影失拿网香似斯专石若兵弟谁校读志飞观争究包组造落视济喜离虽坏兴具存底"
)


def load_font(path: Path, size: int = EM) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(path), size)
    try:
        # Variable fonts (Noto Sans/Serif SC) default to their lightest master; use Regular.
        axes = font.get_variation_axes()
        font.set_variation_by_axes([400 if a.get("name") in (b"Weight", "Weight") else a["default"] for a in axes])
    except OSError:
        pass  # not a variable font
    return font


def render(font: ImageFont.FreeTypeFont, ch: str) -> np.ndarray:
    """The character drawn white-on-black, as a 0–255 grayscale array."""
    img = Image.new("L", (EM * 2, EM * 2), 0)
    ImageDraw.Draw(img).text((EM * 0.5, EM * 1.4), ch, font=font, fill=255, anchor="ls")
    return np.asarray(img)


def glyph_metrics(ink: np.ndarray) -> dict | None:
    if ink.sum() < 50:
        return None
    ys, xs = np.nonzero(ink)
    bw, bh = np.ptp(xs) + 1, np.ptp(ys) + 1

    dist = ndimage.distance_transform_edt(ink)  # distance from each ink pixel to the edge
    skel = skeletonize(ink)  # 1-px centre lines of the strokes
    half = dist[skel]  # half stroke width along the centre lines
    half = half[half >= 1]
    if len(half) < 10:
        return None
    widths = 2 * half

    # --- Stroke direction at each centre-line point (structure tensor) ---
    # The tensor finds the main direction of brightness change around a point;
    # a stroke runs perpendicular to that. sigma ≈ half the stroke width.
    sigma = max(1.5, float(np.median(half)))
    Arr, Arc, Acc = structure_tensor(ink.astype(float), sigma=sigma, order="rc")
    rr, cc = np.nonzero(skel & (dist >= 1))
    a_rr, a_rc, a_cc = Arr[rr, cc], Arc[rr, cc], Acc[rr, cc]
    grad_angle = 0.5 * np.arctan2(2 * a_rc, a_cc - a_rr)  # 0 = gradient along columns (x)
    coherence = np.sqrt((a_cc - a_rr) ** 2 + 4 * a_rc**2) / np.maximum(a_cc + a_rr, 1e-9)
    stroke_angle = np.degrees(grad_angle) + 90  # direction the stroke runs, in degrees
    stroke_angle = (stroke_angle + 90) % 180 - 90  # fold to -90..90 (0 = horizontal)
    w_here = 2 * dist[rr, cc]
    straight = coherence > 0.5
    horiz = straight & (np.abs(stroke_angle) < 25)
    vert = straight & (np.abs(stroke_angle) > 65)

    hv = float(np.log(np.median(w_here[vert]) / np.median(w_here[horiz]))) if horiz.sum() >= 8 and vert.sum() >= 8 else np.nan

    # Modulation: compare each point's width with the typical width of strokes
    # running the SAME direction (15° bins), so thick-verticals/thin-horizontals
    # (that's hv) doesn't count — only variation within strokes does.
    bins = ((stroke_angle + 90) // 15).astype(int)
    rel = np.empty_like(w_here)
    for b in np.unique(bins):
        sel = bins == b
        rel[sel] = w_here[sel] / np.median(w_here[sel])
    modulation = float(np.log(np.percentile(rel, 95) / np.percentile(rel, 10))) if len(rel) >= 20 else np.nan
    # lean of horizontal strokes: image rows grow downward, so "rising to the right" is a negative angle here
    tilt = float(np.median(np.abs(stroke_angle[horiz]))) if horiz.sum() >= 8 else np.nan

    # --- Stroke ends (起笔/收笔) ---
    # Trim the centre lines by half a stroke width first: a square end's centre
    # line forks into its two corners, and those tiny forks aren't real shapes.
    w = 2 * float(np.median(half))
    kernel = np.ones((3, 3))
    kernel[1, 1] = 0
    sk = skel.copy()
    for _ in range(max(1, round(w / 2))):
        nb = ndimage.convolve(sk.astype(int), kernel, mode="constant")
        sk &= ~((nb == 1) & sk)
    nb = ndimage.convolve(sk.astype(int), kernel, mode="constant")
    region = (nb == 1) & sk  # the ends
    for _ in range(round(1.5 * w)):  # grow along the centre line ~1.5 stroke widths
        region = ndimage.binary_dilation(region, structure=np.ones((3, 3))) & sk
    full_angle = (np.degrees(0.5 * np.arctan2(2 * Arc, Acc - Arr)) + 180) % 180
    fbins = (full_angle // 15).astype(int)
    rel_end = []
    for b in np.unique(fbins[sk]):
        sel = sk & (fbins == b)
        ref = np.median(dist[sel])
        rel_end.append(dist[sel & region] / ref)
    rel_end = np.concatenate(rel_end) if rel_end else np.array([])
    terminal = float(np.mean(np.abs(np.log(np.maximum(rel_end, 0.1))))) if len(rel_end) else np.nan

    return {
        "terminal": terminal,
        "hv": hv,
        "modulation": float(modulation),
        "aspect": float(bw / bh),
        "tilt": tilt,
        "weight": float(np.median(widths) / EM),
        "contrast": float(np.log(np.percentile(widths, 80) / max(np.percentile(widths, 20), 1))),
        "density": float(ink.sum() / (bw * bh)),
        "footprint": float(np.sqrt(bw * bh) / EM),
    }


# Roundness is measured on the visible EDGE of each rendered character (traced
# from the image, so overlapping strokes inside the font don't matter).
# We add up how much the edge turns OUTWARD at tight spots — places whose
# radius of curvature is under a quarter of the stroke width. So:
#   - a square corner contributes its full 90°
#   - a pointed brush tip or serif point contributes a lot
#   - a round stroke end (radius = half the stroke width) contributes nothing
# Inward turns (where two strokes join) exist in every font and are ignored.
# Result: sharp turning (radians) per em of edge length. Lower = rounder.
EM_ROUND = 512  # rendered larger than EM for smoother edges
TIGHT = 0.25  # "tight" = radius of curvature under 0.25 × stroke width
STEP_PX = 0.5  # sample the edge every half pixel


def render_large(font_path: Path, ch: str) -> np.ndarray:
    font = load_font(font_path, EM_ROUND)
    img = Image.new("L", (EM_ROUND * 2, EM_ROUND * 2), 0)
    ImageDraw.Draw(img).text((EM_ROUND * 0.5, EM_ROUND * 1.4), ch, font=font, fill=255, anchor="ls")
    return np.asarray(img)


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def sharp_turning(gray: np.ndarray, stroke: float) -> float | None:
    """Outward turning at tight spots, in radians per em of edge.
    `gray` is the character rendered at EM_ROUND; `stroke` the font's typical
    stroke width as a fraction of the em."""
    ink = gray > 127
    w_px = stroke * EM_ROUND
    h = max(2, round(TIGHT * w_px / 2 / STEP_PX))  # half-window: total window = TIGHT × stroke
    total_turn, length = 0.0, 0.0
    for c in find_contours(gray.astype(float), 127.5):
        if len(c) < 8 or not np.allclose(c[0], c[-1]):
            continue
        seg = np.linalg.norm(np.diff(c, axis=0), axis=1)
        cum = np.concatenate([[0], np.cumsum(seg)])
        s = np.arange(0, cum[-1], STEP_PX)
        if len(s) < 6 * h:
            continue
        pts = np.column_stack([np.interp(s, cum, c[:, 0]), np.interp(s, cum, c[:, 1])])
        # direction of travel, smoothed over ±2 samples (±1 px) to ignore pixel noise
        d = np.roll(pts, -2, axis=0) - np.roll(pts, 2, axis=0)
        ang = np.arctan2(d[:, 1], d[:, 0])
        step_turn = wrap(np.roll(ang, -1) - ang)  # turning at each step
        window_turn = wrap(np.roll(ang, -h) - np.roll(ang, h))  # turning across the window

        # Which side is the ink on? Look to the left of travel.
        left = np.column_stack([-d[:, 1], d[:, 0]]) / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
        probe = np.clip(np.round(pts + 2 * left).astype(int), 0, np.array(ink.shape) - 1)
        sign = 1 if ink[probe[:, 0], probe[:, 1]].mean() > 0.5 else -1  # outward turns have this sign

        # tight: turning more than 1 radian within the window ⇔ radius < window length
        tight = (window_turn * sign) > 1.0
        total_turn += float(np.abs(step_turn[tight & (step_turn * sign > 0)]).sum())
        length += cum[-1] / EM_ROUND
    return total_turn / length if length else None


# Bump this when the measuring code changes, so every font is re-measured
METHOD_VERSION = 3


def measure_font(args):
    """Measure one font (runs in its own process, so several fonts at once)."""
    fid, path, chars = args
    font = load_font(path)
    images = [render(font, ch) for ch in chars]
    rows = [m for img in images if (m := glyph_metrics(img > 127))]
    med = {}
    for k in rows[0]:
        vals = np.array([r[k] for r in rows], dtype=float)
        med[k] = round(float(trim_mean(vals[~np.isnan(vals)], 0.1)), 5)
    rates = [r for ch in chars if (r := sharp_turning(render_large(path, ch), med["weight"])) is not None]
    med["roundness"] = round(-float(trim_mean(rates, 0.1)), 5)  # fewer sharp corners = rounder
    return fid, med


def main():
    import os
    from concurrent.futures import ProcessPoolExecutor, as_completed

    fonts = {fid: (ROOT / "fonts-src" / s["file"]) for fid, s in SOURCES.items()}

    # Characters every font has
    shared = None
    for path in fonts.values():
        cmap = set(TTFont(str(path), lazy=True).getBestCmap())
        have = {ch for ch in COMMON if ord(ch) in cmap}
        shared = have if shared is None else shared & have
    chars = [ch for ch in dict.fromkeys(COMMON) if ch in shared][:N_CHARS]
    print(f"Using {len(chars)} characters shared by all {len(fonts)} fonts")

    # Reuse earlier results when nothing that affects them changed:
    # same characters, same measuring method, same font file (size + date).
    out_path = ROOT / "similarity/measured.json"
    old = json.loads(out_path.read_text()) if out_path.exists() else {}
    same_setup = old.get("_chars") == "".join(chars) and old.get("_method") == METHOD_VERSION
    old_files = old.get("_files", {})

    def stamp(path: Path) -> str:
        st = path.stat()
        return f"{st.st_size}-{int(st.st_mtime)}"

    out = {"_chars": "".join(chars), "_method": METHOD_VERSION, "_files": {}}
    todo = []
    for fid, path in fonts.items():
        out["_files"][fid] = stamp(path)
        if same_setup and fid in old and old_files.get(fid) == stamp(path):
            out[fid] = old[fid]
        else:
            todo.append((fid, path, chars))
    print(f"{len(fonts) - len(todo)} unchanged (reused), {len(todo)} to measure")

    # Several fonts at once, one per processor core (leaving one free)
    workers = max(1, (os.cpu_count() or 2) - 1)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for fut in as_completed([pool.submit(measure_font, t) for t in todo]):
            fid, med = fut.result()
            out[fid] = med
            print(f"  {fid:22} " + "  ".join(f"{k}={v:.3f}" for k, v in med.items()), flush=True)

    # keep the catalog's order in the file
    ordered = {k: out[k] for k in ("_chars", "_method", "_files")}
    ordered.update({fid: out[fid] for fid in fonts})
    out_path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n")
    print("→ similarity/measured.json")


if __name__ == "__main__":
    main()
