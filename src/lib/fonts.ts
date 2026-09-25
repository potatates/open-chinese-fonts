// Types and shared helpers for the font catalog.
// The data itself lives in src/data/fonts.json — edit that file to add fonts.
import data from "../data/fonts.json";

export type Category = "song" | "hei" | "kai" | "handwriting" | "rounded" | "display";

export type Webfont =
  // Google Fonts: we build the CSS URL ourselves (see fontLoader.ts)
  | { provider: "google"; family: string }
  // Any other pre-sliced webfont: one stylesheet URL per weight. If a weight's
  // stylesheet uses a different family name (e.g. "Yozai Light"), give
  // { href, family } instead of just the URL.
  | { provider: "css"; family: string; css: Record<string, string | { href: string; family: string }> };

export interface Variant {
  type: string;
  zh: string;
  sample?: string;
  webfont?: Webfont;
}

export interface FontEntry {
  id: string;
  name: { zh: string; en: string };
  category: Category; // main category
  alsoIn?: Category[]; // other categories it fits (e.g. 悠哉 is 圆体 and 手写)
  tags: string[];
  weights: number[];
  // Other versions of the family (e.g. a monospace cut). If the variant has
  // its own webfont, its tag can preview it. `sample` is shown instead of the
  // font's name when the name alone wouldn't show the difference.
  variants: Variant[];
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

/** All categories a font belongs to, main one first. */
export const categoriesOf = (font: FontEntry): Category[] => [font.category, ...(font.alsoIn ?? [])];

/** e.g. "圆体 · 手写·书法" */
export const categoryLabel = (font: FontEntry) => categoriesOf(font).map(categoryName).join(" / ");

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

/** What to load for a font, or for one of its variants (e.g. WenKai Mono). */
export function fontSource(font: FontEntry, variant?: Variant): Pick<FontEntry, "id" | "webfont"> {
  return variant?.webfont ? { id: `${font.id}-${variant.type}`, webfont: variant.webfont } : font;
}

// Plain-language summaries shown next to each license.
export const LICENSES: Record<string, { name: string; summary: string }> = {
  "OFL-1.1": {
    name: "SIL Open Font License 1.1",
    summary: "可免费商用，可嵌入网页与软件；不可单独售卖字体文件。",
  },
  "Apache-2.0": {
    name: "Apache License 2.0",
    summary: "开源授权，可免费商用、修改与再发布；须保留版权与授权声明。",
  },
  "Arphic-1999": {
    name: "Arphic Public License",
    summary: "文鼎公众授权：可免费使用、修改与再发布；不可对字体本身收费。",
  },
  IPA: {
    name: "IPA Font License 1.0",
    summary: "开源授权，可免费使用与再发布；修改后须以不同名称发布。",
  },
};

/** Everything a name search can match, lower-cased, spaces removed
 *  (so "wenkai" finds "LXGW WenKai" and "思源" finds 思源黑体). */
export function searchText(font: FontEntry): string {
  return [font.name.zh, font.name.en, font.designer, font.foundry ?? "", categoryLabel(font), ...font.tags]
    .join("|")
    .toLowerCase()
    .replace(/\s+/g, "");
}

export const normalizeQuery = (q: string) => q.toLowerCase().replace(/\s+/g, "");
