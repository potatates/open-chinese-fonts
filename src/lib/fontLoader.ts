// Loads catalog fonts on demand, in the browser.
//
// Two modes:
//  - subset: ask Google Fonts for ONLY the characters we need (the `text=`
//    parameter). A card showing "思源黑体" downloads ~5 KB instead of MB.
//  - full: load the font's complete stylesheet. Google and the jsDelivr
//    packages split each font into ~100 small files by "unicode-range", so
//    the browser still only downloads the pieces covering the text on screen.
import type { FontEntry } from "./fonts";

const stylesheets = new Map<string, Promise<void>>();

function addStylesheet(href: string): Promise<void> {
  let p = stylesheets.get(href);
  if (!p) {
    p = new Promise((resolve, reject) => {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      link.onload = () => resolve();
      link.onerror = () => reject(new Error(`stylesheet failed: ${href}`));
      document.head.append(link);
    });
    stylesheets.set(href, p);
    p.catch(() => stylesheets.delete(href)); // allow a retry later
  }
  return p;
}

// Subset CSS is fetched and re-registered under a unique family name.
// Otherwise several "Noto Sans SC" subsets (one per text) would fight over
// the same name and the browser might pick one missing our characters.
function addSubsetStyle(href: string, alias: string): Promise<void> {
  let p = stylesheets.get(href);
  if (!p) {
    p = fetch(href)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.text();
      })
      .then((css) => {
        const style = document.createElement("style");
        style.textContent = css.replace(/font-family:\s*['"][^'"]+['"]/g, `font-family: '${alias}'`);
        document.head.append(style);
      });
    stylesheets.set(href, p);
    p.catch(() => stylesheets.delete(href));
  }
  return p;
}

function googleUrl(family: string, weight: number, text?: string): string {
  const fam = encodeURIComponent(family).replace(/%20/g, "+");
  let url = `https://fonts.googleapis.com/css2?family=${fam}:wght@${weight}&display=swap`;
  if (text) url += `&text=${encodeURIComponent(text)}`;
  return url;
}

// Small, stable hash so each subset gets its own family name.
function hash(s: string): string {
  let h = 0;
  for (const ch of s) h = (Math.imul(h, 31) + ch.codePointAt(0)!) | 0;
  return (h >>> 0).toString(36);
}

const TIMEOUT_MS = 15000;

/**
 * Make sure `text` can be drawn in `font` at `weight`.
 * Resolves with the CSS font-family name to use; rejects on failure/timeout.
 */
export async function loadFont(
  font: Pick<FontEntry, "id" | "webfont">,
  weight: number,
  text: string,
  { subset = false } = {},
): Promise<string> {
  const wf = font.webfont;
  let family = wf.family;

  if (wf.provider === "google" && subset) {
    family = `sub-${font.id}-${weight}-${hash(text)}`;
    await addSubsetStyle(googleUrl(wf.family, weight, text), family);
  } else if (wf.provider === "google") {
    await addStylesheet(googleUrl(wf.family, weight));
  } else {
    const href = wf.css[String(weight)];
    if (!href) throw new Error(`${font.id} has no stylesheet for weight ${weight}`);
    await addStylesheet(href);
  }

  // The stylesheet only *declares* the font; this actually downloads the
  // pieces needed for `text` and waits until they are ready to draw.
  const load = document.fonts.load(`${weight} 48px "${family}"`, text);
  const timeout = new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error("font load timed out")), TIMEOUT_MS),
  );
  // An empty result is fine: it means none of the characters are in the font
  // (e.g. an emoji), and the browser will draw them with a fallback font.
  await Promise.race([load, timeout]);
  return family;
}
