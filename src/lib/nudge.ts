// "More like this, but…": fonts that differ from the current one in ONE
// direction (bolder, rounder, …) while staying as close as possible on
// everything else. Uses the 0–1 scores from similarity/scripts/build_similar.py.
import data from "../data/axes.json";
import { fonts, categoriesOf } from "./fonts";

type Scores = Record<string, number>;
const AXES = data.axes as Record<string, { zh: string; weight: number }>;
const SCORES = data.scores as Record<string, Scores>;
const SAME_CATEGORY = data.sameCategoryFactor;
const byId = new Map(fonts.map((f) => [f.id, f]));

export const NUDGES = [
  { id: "bolder", axis: "weight", dir: 1, zh: "更粗", group: "字重", phrase: "更粗" },
  { id: "lighter", axis: "weight", dir: -1, zh: "更细", group: "字重", phrase: "更细" },
  { id: "rounder", axis: "roundness", dir: 1, zh: "更圆", group: "圆润", phrase: "更圆润" },
  { id: "sharper", axis: "roundness", dir: -1, zh: "更方", group: "圆润", phrase: "更方正、棱角更分明" },
  { id: "more-serif", axis: "serif", dir: 1, zh: "更多", group: "笔形", phrase: "起笔收笔更明显" },
  { id: "less-serif", axis: "serif", dir: -1, zh: "更少", group: "笔形", phrase: "笔画更干净利落" },
  { id: "more-hand", axis: "hand", dir: 1, zh: "更强", group: "手写感", phrase: "更有手写感" },
  { id: "less-hand", axis: "hand", dir: -1, zh: "更弱", group: "手写感", phrase: "结构更规整" },
  { id: "display", axis: "display", dir: 1, zh: "偏标题", group: "用途", phrase: "更适合做标题" },
  { id: "text", axis: "display", dir: -1, zh: "偏正文", group: "用途", phrase: "更适合正文阅读" },
] as const;

export type NudgeId = (typeof NUDGES)[number]["id"];

// A result must move at least MIN_STEP in the chosen direction; among those,
// ones that move about IDEAL_STEP are preferred over huge jumps.
const MIN_STEP = 0.1;
const IDEAL_STEP = 0.3;

export interface NudgeResult {
  id: string;
  from: number; // current font's score on the nudged axis
  to: number; // result's score on it
  reason: string; // which other traits stay close
}

export function nudge(fontId: string, nudgeId: NudgeId, limit = 6): NudgeResult[] {
  const n = NUDGES.find((x) => x.id === nudgeId)!;
  const self = SCORES[fontId];
  if (!self) return [];
  const target = Math.min(1, Math.max(0, self[n.axis] + n.dir * IDEAL_STEP));
  const others = Object.keys(AXES).filter((a) => a !== n.axis);
  const totalW = others.reduce((s, a) => s + AXES[a].weight, 0);
  const selfCats = categoriesOf(byId.get(fontId)!);

  const ranked = Object.entries(SCORES)
    .filter(([id, s]) => id !== fontId && (s[n.axis] - self[n.axis]) * n.dir >= MIN_STEP)
    .map(([id, s]) => {
      // how close it stays on every OTHER trait…
      let d = Math.sqrt(others.reduce((sum, a) => sum + AXES[a].weight * (s[a] - self[a]) ** 2, 0) / totalW);
      if (categoriesOf(byId.get(id)!).some((c) => selfCats.includes(c))) d *= SAME_CATEGORY;
      // …plus a small preference for a moderate step over a huge one
      return { id, s, score: d + 0.25 * Math.abs(s[n.axis] - target) };
    })
    .sort((a, b) => a.score - b.score)
    .slice(0, limit);

  return ranked.map(({ id, s }) => {
    const closest = others
      .map((a) => ({ a, diff: Math.abs(s[a] - self[a]) / Math.sqrt(AXES[a].weight) }))
      .sort((x, y) => x.diff - y.diff)
      .slice(0, 2)
      .map((x) => AXES[x.a].zh);
    return { id, from: self[n.axis], to: s[n.axis], reason: `${closest.join("、")}相近` };
  });
}

export const axisName = (axis: string) => AXES[axis]?.zh ?? axis;
