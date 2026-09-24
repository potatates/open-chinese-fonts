// Types and shared helpers for the font catalog.
// The data itself lives in src/data/fonts.json — edit that file to add fonts.
import data from "../data/fonts.json";

export type Category = "song" | "hei" | "kai" | "handwriting" | "rounded" | "display";

export type Webfont =
  // Google Fonts: we build the CSS URL ourselves (see fontLoader.ts)
  | { provider: "google"; family: string }
  // Any other pre-sliced webfont: one stylesheet URL per weight
  | { provider: "css"; family: string; css: Record<string, string> };

export interface FontEntry {
  id: string;
  name: { zh: string; en: string };
  category: Category;
  tags: string[];
  weights: number[];
  variants: { type: string; zh: string }[];
  designer: string;
  foundry: string | null;
  year: number | null;
  license: { id: string; url: string };
  source: { homepage: string; download: string };
  webfont: Webfont;
}

export const fonts = data as FontEntry[];

export const CATEGORIES: { id: Category; zh: string }[] = [
  { id: "song", zh: "宋体" },
  { id: "hei", zh: "黑体" },
  { id: "kai", zh: "楷体" },
  { id: "handwriting", zh: "手写·书法" },
  { id: "rounded", zh: "圆体" },
  { id: "display", zh: "创意" },
];

export const categoryName = (id: Category) =>
  CATEGORIES.find((c) => c.id === id)?.zh ?? id;

export const WEIGHT_NAMES: Record<number, string> = {
  100: "极细", 200: "特细", 300: "细体", 400: "常规", 500: "中等",
  600: "半粗", 700: "粗体", 800: "特粗", 900: "极粗",
};

// The weight filter groups the nine CSS weights into five buckets.
// "prefer" is the weight a card switches to when that bucket is selected,
// so choosing 粗 actually shows you the bold version of each font.
export const WEIGHT_BUCKETS = [
  { id: "light", zh: "细", weights: [100, 200, 300], prefer: [300, 200, 100] },
  { id: "regular", zh: "常规", weights: [400], prefer: [400] },
  { id: "medium", zh: "中粗", weights: [500, 600], prefer: [500, 600] },
  { id: "bold", zh: "粗", weights: [700], prefer: [700] },
  { id: "heavy", zh: "特粗", weights: [800, 900], prefer: [900, 800] },
] as const;

export type WeightBucketId = (typeof WEIGHT_BUCKETS)[number]["id"];

/** The weight a font is shown in: its best match for the bucket, else Regular (or closest). */
export function displayWeight(weights: number[], bucket?: WeightBucketId | null): number {
  const b = WEIGHT_BUCKETS.find((x) => x.id === bucket);
  const match = b?.prefer.find((w) => weights.includes(w));
  if (match) return match;
  return [...weights].sort((a, b) => Math.abs(a - 400) - Math.abs(b - 400))[0];
}

export function hasWeightIn(weights: number[], bucket: WeightBucketId): boolean {
  const b = WEIGHT_BUCKETS.find((x) => x.id === bucket)!;
  return weights.some((w) => (b.weights as readonly number[]).includes(w));
}
