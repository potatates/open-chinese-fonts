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
  footprint  (extra, 字面) how much of the em square the character occupies

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

    return {
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


def main():
    fonts = {fid: (ROOT / "fonts-src" / s["file"]) for fid, s in SOURCES.items()}

    # Characters every font has
    shared = None
    for path in fonts.values():
        cmap = set(TTFont(str(path), lazy=True).getBestCmap())
        have = {ch for ch in COMMON if ord(ch) in cmap}
        shared = have if shared is None else shared & have
    chars = [ch for ch in dict.fromkeys(COMMON) if ch in shared][:N_CHARS]
    print(f"Using {len(chars)} characters shared by all {len(fonts)} fonts")

    out = {"_chars": "".join(chars)}
    for fid, path in fonts.items():
        font = load_font(path)
        images = [render(font, ch) for ch in chars]
        rows = [m for img in images if (m := glyph_metrics(img > 127))]
        med = {k: round(float(trim_mean([r[k] for r in rows], 0.1)), 5) for k in rows[0]}

        rates = [r for ch in chars if (r := sharp_turning(render_large(path, ch), med["weight"])) is not None]
        med["roundness"] = round(-float(trim_mean(rates, 0.1)), 5)  # fewer sharp corners = rounder
        out[fid] = med
        print(f"  {fid:22} " + "  ".join(f"{k}={v:.3f}" for k, v in med.items()))

    (ROOT / "similarity/measured.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print("→ similarity/measured.json")


if __name__ == "__main__":
    main()
