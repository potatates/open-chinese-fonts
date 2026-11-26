# 字相 change log

Every change to zixiangfont.com, newest first, in plain words.
Each date lists what visitors would notice first, then behind-the-scenes work.
The short codes in brackets (like `efdfdf2`) are the matching git commits, for looking up exact details.

---

## 26 Nov 2026
- **Downloads work in mainland China for 10 more fonts.** Their 获取字体 button used to go to Google Fonts, which is blocked in China (14 of 17 clicks on it came from China). It now goes to the font's page on 猫啃网 (maoken.com), like our other 140 fonts. Fonts: 思源黑体, 思源宋体, 站酷快乐体, 站酷庆科黄油体, 站酷小薇体, 马善政毛笔楷书, 志莽行书, 流江毛草, 龙藏体, 霞鹜漫黑.

## 24 Nov 2026
- **Older browsers work again.** Some browsers in China (and Chrome older than v80) couldn't run the site's scripts on pages like /use/. The scripts are now written in older-style JavaScript they can read. (`5cc4a65`)
- **PostHog now tracks more actions:** searches (and which ones find nothing), typing your own preview text, saving or copying a 搭配 pairing, and opening 对比 from pinned fonts. (`5cc4a65`)
- **PostHog recognises returning visitors.** It keeps a random visitor ID in the browser (like the pins do), still with no cookies. Returning-visitor counts are only accurate from this day on. (`efdfdf2`)

## 22 Nov 2026
- **PostHog analytics added**, to see what visitors click, pin, compare and download. It loads in the background so pages aren't slower, goes through zixiangfont.com so it works in mainland China, uses no cookies and records no screens. Download clicks are tracked per font. (`5148b37`)

## 13 Nov 2026
- **Brand name in search results:** the home page title starts with 字相, and a new 关于字相 page explains the site. (`bcb5822`)

## 12 Nov 2026
- **风格 pages redesigned as a poster wall;** /use/ is calmer, and 展开 opens a compact panel. (`2102a92`)

## 9 Nov 2026
- **反馈 page:** a feedback form, saved in Cloudflare. Visitors choose a contact type (邮箱, 微信, 小红书, X / Twitter). (`35a388a`, `6102b56`, `1346da1`)
- **对比 add-font list:** similar fonts suggested first, plus search; the full list is folded away. Footer reorganised into labelled groups. (`ccbdc00`, `76b6336`)
- **搭配 saved picture:** back to the branded frame (stripe, font names, address), with text wrapped as in the box. (`b3ba2e9`, `9616ebf`)
- **New site icon:** 字 as an outline, working on every device. (`67713ee`)
- **Site check fixes:** lighter scripts, better accessibility, fuller page descriptions. (`9c4f2f9`)
- **拼音 风格 page;** pinyin fonts no longer have their pinyin cut off. (`2243ad3`, `b5265e9`)
- **Similarity scores corrected:** textured fonts (glitch, grunge, cracked, hollow) were measured wrong and are fixed. Two rounds of the user's by-eye score corrections were applied, and 演示佛系体 is now the least formal font. (`7a5f788`, `4ad8b40`, `7e692f3`, `35d39d0`, `4a06093`, `6a736cc`, `de968ee`)
- Behind the scenes: an "extremes" table for checking scores by eye. (`28fc45a`, `ce45ff5`)

## 2 Nov 2026
- **21 more fonts (282 total),** scored by eye. The brush page is sorted by how brush-like each font is. (`f1deb7f`)

## 30 Oct 2026
- **Font pages answer 能商用吗？ (can I use it commercially?) at the top,** and search descriptions lead with it. (`bcdfa79`)
- **4 more 风格 pages.** Fonts show their other names (又名: renames, Source Han names, foundry prefixes), so search finds them. (`25b956e`, `3688adc`)

## 27 Oct 2026
- **Pages no longer jump around while loading.** (`233574d`)

## 23 Oct 2026
- **Search finds traditional-character (繁体) font names.** (`a9cefbb`)
- **Share pairings, save comparisons as images,** plus 新增字体, use pages and the 风格 tab. (`57e5efb`, `469d7a3`)
- **24 more fonts (261 total),** scored by eye. (`3bbb97f`)

## 13 Oct 2026
- **Findable by search engines and AI:** sitemap, share images, structured data, category pages, llms.txt. Google Search Console set up. (`541a04c`, `180a44a`, `701e622`, `8f7af51`)
- **Similar fonts:** pixel fonts are only matched with other pixel fonts, there are page arrows, and a clear notice when nothing matches. (`9edfb62`, `3b90694`)
- **指南 page:** hovering a dot shows the font's name in its own font, and overlapping dots spread out. (`a87e9e6`, `235c6f2`, `ccf52f5`)
- **Font pages:** 关于这款字体 moved under the font info. (`b14284f`)

## 8 Oct 2026
- **180 more fonts (235 total),** all scored by eye; the two 庞门正道 fonts are back. (`867890c`, `b13f1d4`)
- **Font pages get 字号一览,** so fonts with only one weight don't leave an empty column. (`6f71238`)

## 26–27 Sep 2026
- **25 more fonts (55 total),** including free-for-commercial-use ones. (`eeb87e7`, `d36c85c`)
- **Phone fixes:** the pinned panel and similar-font switches work properly, and phones no longer zoom in when you change a pairing font. (`1096685`, `dc0b75f`)

## 25 Sep 2026: the site goes live
- **Launched on Cloudflare as 字相 at zixiangfont.com,** with fonts served from fonts.zixiangfont.com. The site's code is MIT-licensed. (`682dd43`, `64260e1`, `f955697`, `c49ccfe`)
- **Similar fonts:** new measures (stroke ends 笔形, 标题感, 相似度 %) and the "more like this, but…" control. (`3e38dff`, `e6a35da`, `f011bde`, `f376a15`)
- **Light/dark theme switch, name search and the 指南 page.** (`0cb1525`, `7178bbf`)
- **Much smaller font downloads,** and licence info for every font. (`3a7997d`)
- **36 fonts total.** (`fe65eae`, `4233652`)

## 24 Sep 2026: first build
- **Font catalog, font detail pages, pinning, pairing preview and comparison page.** (`dbd2601`, `6791b20`, `57e5efb`)
- **First similar-fonts feature,** based on measuring each font. (`17ecb83`, `06d76d4`)
