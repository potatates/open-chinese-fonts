# Getting zixiangfont.com into Baidu, Chinese browsers and Chinese AI search

Interfaces on these webmaster platforms change often. Check the current steps on each one.

## What the site already has
- Chinese-language pages with `lang="zh-Hans"`, per-page titles, descriptions and canonical URLs
- `sitemap-index.xml` (`/sitemap.xml` redirects to it) and a `robots.txt` that allows every crawler
- JSON-LD, share images, category pages, and `/llms.txt` (a text summary for AI assistants)

## Do this week
1. **Baidu 搜索资源平台** (ziyuan.baidu.com): log in with a Baidu account, add `https://zixiangfont.com`, and verify it. A file or an HTML meta tag works. Then:
   - submit `https://zixiangfont.com/sitemap-index.xml` under 普通收录 → sitemap
   - use 链接提交 → 手动提交 for the home page, the 6 category pages, `/guide/` and `/compare/`
   - Baidu's AI search draws on Baidu's own index, so being indexed there is the step that matters
2. **Other Chinese engines**, same pattern (verify, then submit the sitemap):
   - 360: zhanzhang.so.com
   - 搜狗: zhanzhang.sogou.com
   - 神马 (UC browser): zhanzhang.sm.cn
3. **Bing Webmaster Tools** (bing.com/webmasters): Edge and several other browsers and tools in China use Bing. You can import the site from Google Search Console, which you already verified.
4. **Google Search Console**: submit the sitemap if you haven't (the verification file is already in place).
5. **Backlinks Baidu trusts**: post to 知乎, 掘金, 少数派, V2EX, 简书, 站酷, and the 小红书 post. Baidu indexes these quickly. Link to a specific page, such as `/category/kai/`, in the text.
6. **Chinese AI assistants** (豆包, Kimi, DeepSeek, 通义, 元宝, 文心): there is no submission form. They answer from web search indexes and their own crawlers. What helps: being indexed in Baidu/Bing/Sogou, content on 知乎 and 小红书, and the existing `/llms.txt`. To check, ask them "有哪些免费商用的楷体字体" a few weeks from now.

## Bigger issues
- **Speed from mainland China.** Cloudflare is reachable but can be slow there. If Baidu crawling or loading is poor, test from China at itdog.cn or 17ce.com.
- **Google Fonts is blocked in mainland China.** 10 of the 237 fonts load their preview from Google Fonts (e.g. 思源黑体, 思源宋体, 站酷快乐体, 马善政毛笔楷书), and the page preconnects to `fonts.googleapis.com`. For readers in China those cards will show 字体载入失败. Self-hosting those 10 on `fonts.zixiangfont.com`, the same way the other fonts are hosted, would fix it. 14 more entries point at `cdn.jsdelivr.net`, which is sometimes slow in China.
- **ICP 备案.** It is not required to be indexed by Baidu, but Baidu tends to favour 备案 sites. It needs a server in mainland China, so skip it unless you move hosting.
- **Baidu crawls slowly for new sites.** Expect days to weeks before pages show up. Searching `site:zixiangfont.com` on Baidu shows what is indexed.
- **Brand name.** 字相 is a common word. Add "字相字体" or "zixiangfont" to the 小红书 and 知乎 profiles and posts so people can search for the site by name.
