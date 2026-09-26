# 字相 Zixiang — open-source Simplified Chinese fonts

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
| `src/pages/compare.astro` | Side-by-side comparison of pinned fonts |
| `src/lib/pins.ts` | The pinned-fonts list (max 4), saved in the browser's localStorage |
| `src/lib/pinTray.ts` | Draws the pinned tray + pairing preview (right column / bottom bar) |
| `src/lib/pinButtons.ts` | Keeps every 钉选 button in sync with the pinned list |
| `src/styles/pins.css` | Styles for pin buttons, the tray and the bottom bar |
| `src/components/` | Reusable pieces (font card, filters, version tags, pin button, pin bar) |

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

## Similar fonts pipeline (`similarity/`)

Each font gets six 0–1 scores; "similar" means close together on those scores.

| Step | Command | Output |
| --- | --- | --- |
| 0. One-time setup | `/usr/bin/python3 -m venv similarity/.venv && similarity/.venv/bin/pip install fonttools pillow numpy scipy scikit-image brotli py7zr` | Python tools in `similarity/.venv/` |
| 1. Download original font files | `similarity/.venv/bin/python similarity/scripts/fetch_fonts.py` | `fonts-src/` (~160 MB, not committed) |
| 2. Measure weight, contrast, 横竖对比, 笔形, tilt, roundness, 字宽, 字面 | `similarity/.venv/bin/python similarity/scripts/measure.py` | `similarity/measured.json` |
| 3. Specimen images (for scoring by eye) | `similarity/.venv/bin/python similarity/scripts/specimens.py` | `similarity/specimens/` |
| 4. Combine + find neighbours | `similarity/.venv/bin/python similarity/scripts/build_similar.py` | `src/data/similar.json`, `src/data/axes.json`, `similarity/review.html` (open it in a browser) |
| Slice fonts that have no web version | `similarity/.venv/bin/python similarity/scripts/slice_webfonts.py` | `public/fonts/<id>/<weight>/` |

- Formality and quirkiness are scored by eye in `similarity/subjective.json`.
- `similarity/overrides.json` always wins over automatic values.
- Axis weights and the same-category bonus are at the top of `build_similar.py`.
- Adding a font: add it to `src/data/fonts.json` and `similarity/sources.json`, score it in `subjective.json`, then run steps 1–4.

## Deploying (Cloudflare)

The site is fully static: `npm run build` writes everything to `dist/`, and
`wrangler.jsonc` tells Cloudflare to serve that folder.

1. In the Cloudflare dashboard: **Workers & Pages → Create → Import a repository**, pick this repository.
2. Build command `npm run build`; deploy command `npx wrangler deploy` (the default).
   The Node version comes from `.nvmrc` (22, which wrangler needs).
3. Every push to `main` redeploys automatically.

## License

The site's code is MIT-licensed (see `LICENSE`). Fonts are not covered by it:
each keeps its own license, in `public/fonts/<id>/LICENSE.txt`.

## Hosted fonts and licenses

Font files this site hosts itself live in the Cloudflare R2 bucket `open-chinese-fonts-files`
(public address in `.env.production`), not in git. They're generated locally into `public/fonts/`
(ignored by git), which `npm run dev` uses. After adding or re-slicing fonts, upload the changes:

```bash
npx -p node@22 -p wrangler@4 node scripts/upload-fonts.mjs open-chinese-fonts-files
```

(Only new or changed files are sent. Requires `npx -p node@22 -p wrangler@4 wrangler login` once.)

Fonts without a ready-made web version are sliced and hosted in `public/fonts/<id>/`
(`similarity/scripts/slice_webfonts.py`, using Google Fonts' character groups from `google_groups.py`).
Each folder has the font's `LICENSE.txt` (`license_files.py`). Fonts are only sliced when their license
allows it (checked for Reserved Font Name clauses; see `similarity/sources.json`).
