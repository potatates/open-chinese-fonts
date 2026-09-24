# 开源中文字体 — Open-source Simplified Chinese fonts

Browse, compare and discover similar open-source Simplified Chinese fonts.
A fully static site built with [Astro](https://astro.build).

## Run it locally

Needs Node.js 20+.

```bash
npm install      # first time only
npm run dev      # then open http://localhost:4321
```

`npm run build` writes the finished static site to `dist/`; `npm run preview` serves that build.

## Where things live

| Path | What it is |
| --- | --- |
| `src/data/fonts.json` | The font catalog. **Add a font by adding an entry here.** |
| `src/lib/fonts.ts` | Types for the catalog, category and weight names, weight-filter logic |
| `src/lib/fontLoader.ts` | Loads fonts in the browser, on demand |
| `src/styles/tokens.css` | Design tokens: colors, type sizes, spacing (light + dark) |
| `src/data/samples.json` | Preview sentences used by "换一句" (shuffle) |
| `src/pages/index.astro` | Catalog page |
| `src/pages/fonts/[id].astro` | Detail page template; one page is generated per font |
| `src/components/` | Reusable pieces (font card, filters, version tags) |

## Adding a font

Add an object to `src/data/fonts.json`:

- `category`: one of `song` 宋体, `hei` 黑体, `kai` 楷体, `handwriting` 手写·书法, `rounded` 圆体, `display` 创意
- `weights`: the CSS weights that exist (100–900)
- `variants`: other versions, e.g. `{ "type": "mono", "zh": "等宽版", "sample": "等宽 iiii WWWW", "webfont": {…} }`. `sample` is shown when the tag is pressed, for versions whose difference doesn't show in Chinese text (Chinese characters are already all the same width).
- `webfont`: how the browser gets the font
  - Google Fonts: `{ "provider": "google", "family": "Noto Sans SC" }`
  - A pre-sliced CSS webfont: `{ "provider": "css", "family": "…", "css": { "400": "https://…/regular.css" } }`

Only add fonts with an open-source license (e.g. SIL OFL 1.1) that allows web embedding.

## How font loading works

Chinese fonts are 5–20 MB each, so nothing is downloaded until a card scrolls into view.

- Catalog cards showing a font's own name request just those few characters from Google Fonts (`text=`), about 2–4 KB each.
- When you type your own text, the full font stylesheet is used instead. It is split into ~100 pieces by `unicode-range`, so the browser only downloads the pieces your text needs.
