// Print the messages sent with the 反馈 form (newest first).
// They live in the FEEDBACK Workers KV store (see wrangler.jsonc / worker/index.js).
//
// Run:  npm run feedback          (the 20 newest)
//       npm run feedback -- 100   (more)
// You can also see them in the Cloudflare dashboard: Storage & databases →
// Workers KV → FEEDBACK.
import { execFileSync } from "node:child_process";

const NAMESPACE = "2ec5f3b3e8ff4f068f2803d41ced7008";
const limit = Number(process.argv[2] ?? 20);
const wrangler = (...args) =>
  execFileSync("npx", ["wrangler", "kv", ...args, "--namespace-id", NAMESPACE, "--remote"], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "ignore"],
  });

const keys = JSON.parse(wrangler("key", "list", "--prefix", "fb:")).map((k) => k.name);
if (!keys.length) {
  console.log("还没有反馈。");
  process.exit(0);
}
console.log(`共 ${keys.length} 条反馈${keys.length > limit ? `，显示最新的 ${limit} 条` : ""}：\n`);
for (const key of keys.slice(0, limit)) {
  const m = JSON.parse(wrangler("key", "get", key, "--text"));
  const when = new Date(m.time).toLocaleString("zh-CN", { hour12: false });
  console.log(`— ${when} · ${m.kind}${m.country ? ` · ${m.country}` : ""}${m.page ? ` · ${m.page}` : ""}`);
  console.log(m.message.replace(/^/gm, "  "));
  if (m.contact) console.log(`  联系方式：${m.contact}`);
  console.log();
}
