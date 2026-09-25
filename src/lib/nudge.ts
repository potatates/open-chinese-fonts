// "More like this, but…": fonts that differ from the current one in the
// directions you pick (e.g. rounder AND bolder) while staying as close as
// possible on everything else. Uses the 0–1 scores from
// similarity/scripts/build_similar.py.
import data from "../data/axes.json";
import { fonts, categoriesOf } from "./fonts";

type Scores = Record<string, number>;
const AXES = data.axes as Record<string, { zh: string; weight: number }>;
const SCORES = data.scores as Record<string, Scores>;
const SAME_CATEGORY = data.sameCategoryFactor;
const byId = new Map(fonts.map((f) => [f.id, f]));

/** The traits you can steer, each with its two directions. */
export const DIALS = [
  { axis: "weight", zh: "字重", less: "更细", more: "更粗", lessPhrase: "更细", morePhrase: "更粗" },
  { axis: "roundness", zh: "圆润", less: "更方", more: "更圆", lessPhrase: "更方正", morePhrase: "更圆润" },
  { axis: "serif", zh: "笔形", less: "更少", more: "更多", lessPhrase: "笔画更干净", morePhrase: "起收笔更明显" },
  { axis: "hand", zh: "手写感", less: "更弱", more: "更强", lessPhrase: "更规整", morePhrase: "更有手写感" },
  { axis: "width", zh: "字宽", less: "更窄", more: "更宽", lessPhrase: "更窄", morePhrase: "更宽" },
  { axis: "display", zh: "用途", less: "偏正文", more: "偏标题", lessPhrase: "更适合正文", morePhrase: "更适合做标题" },
] as const;

export type Axis = (typeof DIALS)[number]["axis"];
/** axis → -1 (less) or +1 (more). Axes left out are "不限". */
export type Wishes = Partial<Record<Axis, -1 | 1>>;

// A result must move at least MIN_STEP in each chosen direction; among those,
// ones that move about IDEAL_STEP are preferred over huge jumps.
const MIN_STEP = 0.1;
const IDEAL_STEP = 0.3;

export interface NudgeResult {
  id: string;
  changes: { axis: Axis; from: number; to: number; ok: boolean }[];
  reason: string; // which other traits stay close
}

export interface NudgeOutcome {
  results: NudgeResult[];
  /** false when no font goes in every chosen direction and we show the best partial matches */
  complete: boolean;
}

export function nudge(fontId: string, wishes: Wishes, limit = 6): NudgeOutcome {
  const self = SCORES[fontId];
  const chosen = Object.entries(wishes) as [Axis, -1 | 1][];
  if (!self || chosen.length === 0) return { results: [], complete: true };

  const others = Object.keys(AXES).filter((a) => !(a in wishes));
  const totalW = others.reduce((s, a) => s + AXES[a].weight, 0) || 1;
  const selfCats = categoriesOf(byId.get(fontId)!);

  const candidates = Object.entries(SCORES)
    .filter(([id]) => id !== fontId)
    .map(([id, s]) => {
      const met = chosen.filter(([a, dir]) => (s[a] - self[a]) * dir >= MIN_STEP).length;
      // how close it stays on every trait you didn't ask to change…
      let d = Math.sqrt(others.reduce((sum, a) => sum + AXES[a].weight * (s[a] - self[a]) ** 2, 0) / totalW);
      if (categoriesOf(byId.get(id)!).some((c) => selfCats.includes(c))) d *= SAME_CATEGORY;
      // …plus a small preference for moderate steps over huge jumps
      const overshoot =
        chosen.reduce((sum, [a, dir]) => sum + Math.abs(s[a] - Math.min(1, Math.max(0, self[a] + dir * IDEAL_STEP))), 0) /
        chosen.length;
      return { id, s, met, score: d + 0.25 * overshoot };
    })
    .filter((c) => c.met > 0);

  const best = Math.max(0, ...candidates.map((c) => c.met));
  const complete = best === chosen.length;
  const picked = candidates
    .filter((c) => c.met === best) // all wishes if possible, otherwise as many as possible
    .sort((a, b) => a.score - b.score)
    .slice(0, limit);

  return {
    complete,
    results: picked.map(({ id, s }) => ({
      id,
      changes: chosen.map(([a, dir]) => ({ axis: a, from: self[a], to: s[a], ok: (s[a] - self[a]) * dir >= MIN_STEP })),
      reason:
        others
          .map((a) => ({ a, diff: Math.abs(s[a] - self[a]) / Math.sqrt(AXES[a].weight) }))
          .sort((x, y) => x.diff - y.diff)
          .slice(0, 2)
          .map((x) => AXES[x.a].zh)
          .join("、") + "相近",
    })),
  };
}

export const axisName = (axis: string) => AXES[axis]?.zh ?? axis;
