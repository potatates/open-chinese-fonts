// The site's name and description, in one place so renaming is a one-line change.
export const SITE = {
  name: "字相",
  description: "字相：浏览、对比可免费使用的简体中文字体，找到风格相近的字体。",
};

/**
 * Where the fonts this site hosts itself live (sliced pieces, name/sample files).
 * Empty = this site's own /fonts/ folder (used during development).
 * The live site sets PUBLIC_FONT_BASE (in .env.production) to the Cloudflare R2
 * bucket's public address, so font files don't have to live in the git repo.
 */
export const FONT_BASE: string = (import.meta.env.PUBLIC_FONT_BASE ?? "").replace(/\/$/, "");

/** Turn a site path like "/fonts/x/400/result.css" into its real address. */
export const fontUrl = (path: string) => (path.startsWith("/fonts/") ? FONT_BASE + path : path);
