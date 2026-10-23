// The order of fonts on the home page: well-known fonts first, then the
// categories take turns, so the page doesn't start with a wall of 黑体 then a
// wall of 宋体. Display fonts are spread out (at most about one card in four)
// and pixel fonts further still, so the top of the page stays readable.
import type { FontEntry } from "./fonts";

/** Hand-picked opening: popular fonts, mixed styles, few display fonts. */
const FEATURED = [
  "noto-sans-sc", // 思源黑体
  "lxgw-wenkai", // 霞鹜文楷
  "noto-serif-sc", // 思源宋体
  "smiley-sans", // 得意黑
  "lxgw-975yuan", // 霞鹜975圆体
  "ma-shan-zheng", // 马善政毛笔楷书
  "zhuque-fangsong", // 朱雀仿宋
  "glow-sans-sc", // 未来荧黑
  "xiaolai", // 小赖字体
  "lxgw-neo-zhisong", // 霞鹜新致宋
  "douyin-sans", // 抖音美好体
  "lxgw-zhenkai", // 霞鹜臻楷
  "resource-han-rounded", // 资源圆体
  "zhi-mang-xing", // 志莽行书
  "lxgw-975hei", // 霞鹜975黑
  "zcool-kuaile", // 站酷快乐体
  "chill-jinshu-song", // 寒蝉锦书宋
  "yozai", // 悠哉字体
];

const TURNS = ["hei", "song", "kai", "handwriting", "rounded"] as const;
const CALM_UNTIL = 60; // the first 60 cards: at most 1 display font in 4, no pixel fonts

/** Spread `extra` evenly between the items of `base`. */
function interleave<T>(base: T[], extra: T[]): T[] {
  if (!extra.length) return base;
  const out: T[] = [];
  const step = (base.length + extra.length) / extra.length;
  let next = step / 2;
  let b = 0;
  let e = 0;
  for (let i = 0; i < base.length + extra.length; i++) {
    if (e < extra.length && i >= next) {
      out.push(extra[e++]);
      next += step;
    } else out.push(base[b++] ?? extra[e++]);
  }
  return out;
}

export function homeOrder(all: FontEntry[]): FontEntry[] {
  const byId = new Map(all.map((f) => [f.id, f]));
  const out: FontEntry[] = FEATURED.map((id) => byId.get(id)).filter((f): f is FontEntry => !!f);
  const used = new Set(out.map((f) => f.id));
  const rest = all.filter((f) => !used.has(f.id));

  // Text-style fonts take turns by category (each in catalog order: the
  // earliest-added, best-known fonts first)
  const queues = TURNS.map((c) => rest.filter((f) => f.category === c && !f.tags.includes("pixel")));
  const textFonts: FontEntry[] = [];
  while (queues.some((q) => q.length)) for (const q of queues) if (q.length) textFonts.push(q.shift()!);
  const display = rest.filter((f) => f.category === "display" && !f.tags.includes("pixel"));
  const pixels = rest.filter((f) => f.tags.includes("pixel"));

  // Calm start: 3 text fonts, then 1 display font
  while (out.length < CALM_UNTIL && textFonts.length) {
    for (let i = 0; i < 3 && textFonts.length; i++) out.push(textFonts.shift()!);
    if (display.length) out.push(display.shift()!);
  }
  // The rest: display and pixel fonts spread evenly among the text fonts
  return [...out, ...interleave(textFonts, interleave(display, pixels))];
}
