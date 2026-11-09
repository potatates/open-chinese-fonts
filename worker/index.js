// A tiny Worker in front of the static site. Only the paths listed under
// "run_worker_first" in wrangler.jsonc reach this code; every other request
// is served straight from the static files.
//
// 1. Search-engine verification files. Cloudflare's static hosting removes
//    ".html" from addresses (/x.html redirects to /x), but these files must
//    be served at their exact address with no redirect.
// 2. POST /api/feedback: the 反馈 form (src/pages/feedback.astro). Messages are
//    saved in the FEEDBACK store (Workers KV); read them with `npm run feedback`.
const VERIFICATION = {
  "/google38ae56ad0c5892c8.html": "google-site-verification: google38ae56ad0c5892c8.html",
};

const KINDS = ["问题", "建议", "推荐字体", "其他"];
const PER_HOUR = 5; // messages one visitor may send per hour

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (pathname in VERIFICATION) {
      return new Response(VERIFICATION[pathname], { headers: { "content-type": "text/html; charset=utf-8" } });
    }
    if (pathname === "/api/feedback") return feedback(request, env);
    return env.ASSETS.fetch(request);
  },
};

async function feedback(request, env) {
  if (request.method !== "POST") return new Response("Method not allowed", { status: 405, headers: { allow: "POST" } });
  const isForm = !(request.headers.get("content-type") ?? "").includes("application/json");
  // A form sent without JavaScript gets a page back; the script gets JSON
  const reply = (ok, error) =>
    isForm
      ? Response.redirect(new URL(ok ? "/feedback/?sent=1" : `/feedback/?error=${error}`, request.url), 303)
      : Response.json(ok ? { ok: true } : { ok: false, error }, { status: ok ? 200 : 400 });

  let data;
  try {
    data = isForm ? Object.fromEntries(await request.formData()) : await request.json();
  } catch {
    return reply(false, "bad-request");
  }
  const text = (v, max) => (typeof v === "string" ? v.trim().slice(0, max) : "");
  // "website" is a hidden field people never see; spam robots fill it in
  if (text(data.website, 200)) return reply(true);
  const message = text(data.message, 3000);
  if (message.length < 2) return reply(false, "empty");

  // Rate limit by a hash of the visitor's address (the address itself is never stored)
  const ip = request.headers.get("cf-connecting-ip") ?? "";
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(ip + "zixiang"));
  const who = [...new Uint8Array(digest)].slice(0, 8).map((b) => b.toString(16).padStart(2, "0")).join("");
  const count = Number((await env.FEEDBACK.get(`rate:${who}`)) ?? 0);
  if (count >= PER_HOUR) return reply(false, "too-many");
  await env.FEEDBACK.put(`rate:${who}`, String(count + 1), { expirationTtl: 3600 });

  const now = new Date();
  const entry = {
    time: now.toISOString(),
    kind: KINDS.includes(data.kind) ? data.kind : "其他",
    message,
    contact: text(data.contact, 200),
    page: text(data.page, 200),
    country: request.cf?.country ?? "",
  };
  // Keys sort newest first: "fb:" + time counted down from far in the future
  const key = `fb:${String(9e15 - now.getTime()).padStart(16, "0")}:${crypto.randomUUID().slice(0, 8)}`;
  await env.FEEDBACK.put(key, JSON.stringify(entry));
  return reply(true);
}
