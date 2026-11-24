// @ts-check
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

// A fully static site: `npm run build` writes plain HTML/CSS/JS into dist/.
export default defineConfig({
  site: "https://zixiangfont.com", // the site's public address
  // sitemap-index.xml lists every page for search engines (the 404 page left out)
  integrations: [sitemap({ filter: (page) => !page.includes("/404") })],
  // Put each page's CSS (~15 KB, ~4 KB compressed) inside the HTML instead of
  // separate files. Then the page is never laid out unstyled while a stylesheet
  // is still downloading (browser extensions can force that, and visitors saw
  // the whole page jump into place), and the first paint skips a round trip.
  build: { inlineStylesheets: "always" },
  // Write the site's scripts in 2019-era JavaScript. Some browsers in China
  // (and older Chrome, before version 80) can't read newer syntax like ?. and ??,
  // and then a page's script doesn't run at all (PostHog saw this on /use/).
  vite: { build: { target: "es2019" } },
});
