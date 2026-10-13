// A tiny Worker in front of the static site. Cloudflare's static hosting
// removes ".html" from addresses (/x.html redirects to /x), but search-engine
// verification files must be served at their exact address with no redirect.
// Only the paths listed under "run_worker_first" in wrangler.jsonc reach this
// code; every other request is served straight from the static files.
const VERIFICATION = {
  "/google38ae56ad0c5892c8.html": "google-site-verification: google38ae56ad0c5892c8.html",
};

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (pathname in VERIFICATION) {
      return new Response(VERIFICATION[pathname], { headers: { "content-type": "text/html; charset=utf-8" } });
    }
    return env.ASSETS.fetch(request);
  },
};
