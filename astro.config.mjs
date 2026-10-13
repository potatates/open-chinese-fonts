// @ts-check
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

// A fully static site: `npm run build` writes plain HTML/CSS/JS into dist/.
export default defineConfig({
  site: "https://zixiangfont.com", // the site's public address
  // sitemap-index.xml lists every page for search engines (the 404 page left out)
  integrations: [sitemap({ filter: (page) => !page.includes("/404") })],
});
