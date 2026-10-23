// /llms.txt — a plain-text summary of the site for AI assistants and answer
// engines (the llms.txt convention): what 字相 is, the categories, and every
// font with its key facts, so an AI can answer "有哪些免费商用的楷体" from it.
import type { APIRoute } from "astro";
import { fonts, CATEGORIES, LICENSES, WEIGHT_NAMES } from "../lib/fonts";
import { CATEGORY_TEXT, fontsIn, freeLabel, traits, similarFonts, SITE_URL, USE_PAGES, useFonts } from "../lib/seo";
import { SITE } from "../lib/site";

export const GET: APIRoute = () => {
  const lines: string[] = [
    `# ${SITE.name}`,
    "",
    `> ${SITE.description} 收录 ${fonts.length} 款字体，每款都可在线输入文字预览，并按笔形、字重、圆润度、标题感等 12 项特征计算相似字体。`,
    "",
    "字相（zixiangfont.com）只收录授权允许免费使用的字体，并链接到每款字体的官方下载地址；网页预览用的字体文件是官方字体的子集。",
    "",
    "## 页面",
    "",
    `- [全部字体](${SITE_URL}/)：可搜索、按分类与字重筛选`,
    `- [指南](${SITE_URL}/guide/)：六个分类的说明，以及相似度用到的特征`,
    `- [对比](${SITE_URL}/compare/)：并排比较 2–4 款字体`,
    "",
    "## 分类",
    "",
    ...CATEGORIES.map(
      (c) => `- [${c.zh}（${fontsIn(c.id).length} 款）](${SITE_URL}/category/${c.id}/)：${CATEGORY_TEXT[c.id].what}`,
    ),
    "",
    "## 按用途",
    "",
    ...USE_PAGES.map((p) => `- [${p.title}（${useFonts(p).length} 款）](${SITE_URL}/use/${p.slug}/)：${p.intro}`),
    "",
    `- [新增字体](${SITE_URL}/new/)：最近收录的字体`,
    "",
    "## 字体",
    "",
  ];
  for (const f of fonts) {
    const en = (f.name.zhHant ? ` ${f.name.zhHant}` : "") + (f.name.en !== f.name.zh ? ` ${f.name.en}` : "");
    const sim = similarFonts(f).map((s) => `${s.font.name.zh} ${s.pct}%`);
    const t = traits(f);
    lines.push(
      `- [${f.name.zh}${en}](${SITE_URL}/fonts/${f.id}/)：${CATEGORIES.find((c) => c.id === f.category)!.zh}；` +
        `${f.designer}，${f.year} 年；字重 ${f.weights.map((w) => WEIGHT_NAMES[w]).join("、")}；` +
        `${freeLabel(f)}，${LICENSES[f.license.id]?.name ?? f.license.id}` +
        (t.length ? `；${t.join("、")}` : "") +
        (sim.length ? `；相似：${sim.join("、")}` : ""),
    );
  }
  return new Response(lines.join("\n") + "\n", { headers: { "Content-Type": "text/plain; charset=utf-8" } });
};
