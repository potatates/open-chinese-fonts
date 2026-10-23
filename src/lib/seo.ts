// Text and metadata for search engines and AI answer engines: the Chinese
// "about this font" paragraph, page titles and descriptions, and the
// structured data (JSON-LD) that describes each page. Everything is built
// from the font data, so it stays correct as fonts are added.
import axesData from "../data/axes.json";
import similarData from "../data/similar.json";
import { FONT_BASE, SITE } from "./site";
import {
  fonts,
  categoriesOf,
  categoryName,
  LICENSES,
  WEIGHT_NAMES,
  type Category,
  type FontEntry,
} from "./fonts";

export const SITE_URL = "https://zixiangfont.com";

export const CATEGORY_TEXT: Record<Category, { what: string; use: string }> = {
  song: {
    what: "横画细、竖画粗，笔画末端有三角形的“字脚”（衬线）。源自雕版印刷。仿宋也归在这里：笔画更接近楷书、更秀气。",
    use: "书籍、报纸的正文；仿宋常用于公文。",
  },
  hei: {
    what: "笔画粗细基本一致，起笔收笔是平头，没有装饰。清晰、现代、中性。",
    use: "屏幕界面、标识、说明文字和标题。",
  },
  kai: {
    what: "源自毛笔楷书的规范写法，保留起笔、收笔和提按的笔意，端正易读，比宋体、黑体更有人情味。",
    use: "教材、语文类内容，以及需要亲切感的正文。",
  },
  handwriting: {
    what: "模仿手写或毛笔书法：从工整的钢笔字，到行书、草书。笔迹自然，个性强。",
    use: "标题、海报、贺卡和需要个人温度的地方。",
  },
  rounded: {
    what: "笔画末端和转角都是圆的，柔和、友好。",
    use: "儿童、生活类内容，以及想显得亲切的界面。",
  },
  display: {
    what: "为标题、标志和海报设计：造型大胆、风格鲜明，很多笔画粗重或经过重新设计。",
    use: "大字号的标题、品牌和海报；一般不适合长篇正文。",
  },
};

const byId = new Map(fonts.map((f) => [f.id, f]));
const scores = axesData.scores as Record<string, Record<string, number>>;
const similar = similarData as Record<string, { id: string; similarity: number }[]>;

/** "免费商用" unless the license only asks for non-commercial use. */
export const freeLabel = (font: FontEntry) => (font.license.id === "SHL-Open" ? "免费" : "免费商用");

/** "楷体" or "楷体、手写·书法" when a font sits in several categories. */
export const categoriesText = (font: FontEntry) => categoriesOf(font).map(categoryName).join("、");

/** A few plain-language traits, from the measured and scored features. */
export function traits(font: FontEntry): string[] {
  const s = scores[font.id];
  if (!s) return [];
  const t: string[] = [];
  if (s.weight > 0.7) t.push("笔画粗重");
  else if (s.weight < 0.2) t.push("笔画纤细");
  if (s.serif > 0.7) t.push("起笔收笔造型明显");
  else if (s.serif < 0.15) t.push("笔画末端干净利落");
  if (s.roundness > 0.75) t.push("转角圆润");
  else if (s.roundness < 0.15) t.push("棱角分明");
  if (s.hand > 0.6) t.push("带手写感");
  if (s.width > 0.8) t.push("字形偏宽");
  else if (s.width < 0.2) t.push("字形偏窄");
  if (s.quirkiness > 0.65) t.push("造型个性强烈");
  if (s.display > 0.7) t.push("适合标题与海报");
  else if (s.display < 0.3) t.push("适合正文排版");
  return t.slice(0, 5);
}

export function similarFonts(font: FontEntry, n = 3) {
  return (similar[font.id] ?? [])
    .slice(0, n)
    .map((s) => ({ font: byId.get(s.id)!, pct: Math.round(s.similarity * 100) }))
    .filter((s) => s.font);
}

function weightsText(font: FontEntry): string {
  if (font.weights.length === 1) return `提供${WEIGHT_NAMES[font.weights[0]]}一种字重`;
  return `提供 ${font.weights.length} 种字重（${font.weights.map((w) => WEIGHT_NAMES[w]).join("、")}）`;
}

/** The "关于这款字体" paragraph: facts a person (or an AI answer) can quote. */
export function aboutFont(font: FontEntry): string[] {
  const license = LICENSES[font.license.id];
  const alt = [font.name.en !== font.name.zh ? font.name.en : "", font.name.zhHant ? `繁体：${font.name.zhHant}` : ""].filter(Boolean).join("，");
  const en = alt ? `（${alt}）` : "";
  const made = font.foundry && font.foundry !== font.designer ? `${font.designer}设计，${font.foundry}出品` : `${font.designer}设计`;
  const p1 =
    `${font.name.zh}${en}是一款${freeLabel(font)}的${categoriesText(font)}字体，由${made}，${font.year} 年发布，` +
    `${weightsText(font)}。` +
    (license ? `采用 ${license.name} 授权：${license.summary}` : "");
  const out = [p1];
  const t = traits(font);
  const sim = similarFonts(font);
  let p2 = t.length ? `字形特点：${t.join("、")}。` : "";
  if (sim.length) p2 += `风格相近的字体有${sim.map((s) => `${s.font.name.zh}（相似度 ${s.pct}%）`).join("、")}。`;
  if (p2) out.push(p2);
  return out;
}

export function fontTitle(font: FontEntry): string {
  const en = font.name.en !== font.name.zh ? ` ${font.name.en}` : "";
  const hant = font.name.zhHant ? ` ${font.name.zhHant}` : "";
  return `${font.name.zh}${hant}${en}：${freeLabel(font)}${categoryName(font.category)}字体在线预览与下载`;
}

export function fontDescription(font: FontEntry): string {
  const alt = [font.name.zhHant, font.name.en !== font.name.zh ? font.name.en : ""].filter(Boolean).join("，");
  const en = alt ? `（${alt}）` : "";
  const t = traits(font).slice(0, 2).join("、");
  return (
    `${font.name.zh}${en}，${freeLabel(font)}${categoriesText(font)}字体，${font.designer}设计，${weightsText(font)}` +
    (t ? `，${t}` : "") +
    `。在线输入文字预览，查看授权、相似字体与官方下载地址。`
  );
}

/** Share image (made by similarity/scripts/og_images.py, hosted with the fonts). */
export const ogImage = (id: string) => `${FONT_BASE || SITE_URL}/og/${id}.png`;

export function fontJsonLd(font: FontEntry, pageUrl: string) {
  const license = LICENSES[font.license.id];
  return [
    {
      "@context": "https://schema.org",
      "@type": "CreativeWork",
      name: font.name.zh,
      alternateName: [font.name.en, ...(font.name.zhHant ? [font.name.zhHant] : [])],
      genre: categoriesText(font),
      description: aboutFont(font).join(""),
      url: pageUrl,
      image: ogImage(font.id),
      inLanguage: "zh-Hans",
      isAccessibleForFree: true,
      datePublished: String(font.year),
      creator: { "@type": font.foundry ? "Organization" : "Person", name: font.designer },
      license: font.license.url,
      ...(license ? { usageInfo: license.summary } : {}),
      sameAs: [font.source.homepage],
    },
    breadcrumbs([
      ["全部字体", "/"],
      [categoryName(font.category), `/category/${font.category}/`],
      [font.name.zh, `/fonts/${font.id}/`],
    ]),
  ];
}

export function breadcrumbs(items: [string, string][]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map(([name, path], i) => ({
      "@type": "ListItem",
      position: i + 1,
      name,
      item: SITE_URL + path,
    })),
  };
}

export const siteJsonLd = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: SITE.name,
  url: SITE_URL + "/",
  description: SITE.description,
  inLanguage: "zh-Hans",
  potentialAction: {
    "@type": "SearchAction",
    target: SITE_URL + "/?q={search_term_string}",
    "query-input": "required name=search_term_string",
  },
};

export const fontsIn = (cat: Category) => fonts.filter((f) => categoriesOf(f).includes(cat));

/**
 * Pages for what people search for by purpose ("适合标题的字体", "毛笔字体" …),
 * filled from the scores and tags, so they stay current as fonts are added.
 */
export const USE_PAGES = [
  {
    slug: "headline",
    title: "适合标题与海报的免费字体",
    short: "标题·海报",
    intro: "造型鲜明、在大字号下最出彩的字体：海报、封面、标题、品牌字。按「标题感」从高到低排列。",
    pick: (f: FontEntry) => !f.tags.includes("pixel") && (scores[f.id]?.display ?? 0) >= 0.75,
    sort: (a: FontEntry, b: FontEntry) => (scores[b.id]?.display ?? 0) - (scores[a.id]?.display ?? 0),
  },
  {
    slug: "body",
    title: "适合正文排版的免费字体",
    short: "正文排版",
    intro: "适合长篇阅读的字体：结构端正、笔画均衡，小字号下依然清晰。适合文章、书籍、网页正文和界面文字。",
    pick: (f: FontEntry) =>
      !f.tags.includes("pixel") && (scores[f.id]?.display ?? 1) <= 0.3 && (scores[f.id]?.formality ?? 0) >= 0.75,
    sort: (a: FontEntry, b: FontEntry) => (scores[b.id]?.formality ?? 0) - (scores[a.id]?.formality ?? 0),
  },
  {
    slug: "brush",
    title: "免费毛笔书法字体",
    short: "毛笔·书法",
    intro: "带毛笔笔意的字体：从端正的楷书，到行书、草书和榜书大字。适合国风设计、标题和贺卡。",
    pick: (f: FontEntry) => f.tags.includes("brush"),
  },
  {
    slug: "cute",
    title: "免费商用可爱字体",
    short: "可爱",
    intro: "圆润、俏皮、有手写温度的字体：适合儿童、生活方式、美食、社交媒体和轻松的品牌。",
    pick: (f: FontEntry) => f.tags.includes("cute"),
  },
  {
    slug: "pixel",
    title: "免费像素字体与点阵字体",
    short: "像素·点阵",
    intro: "由方格或圆点组成的字体，带着复古游戏和电子屏的感觉。适合游戏界面、像素风插画和复古设计。",
    pick: (f: FontEntry) => f.tags.includes("pixel"),
  },
] as const;

export const useFonts = (page: (typeof USE_PAGES)[number]) => {
  const list = fonts.filter(page.pick);
  return "sort" in page ? [...list].sort(page.sort) : list;
};
