// Upload public/fonts/ to the Cloudflare R2 bucket that serves the live site's fonts.
//
// Usage (after `npx wrangler login` once):
//   node scripts/upload-fonts.mjs <bucket-name>
//
// Only new or changed files are sent: what was uploaded is remembered (by
// content hash) in scripts/.uploaded-fonts.json. Needs Node 22 for wrangler;
// run it as:  npx -p node@22 -p wrangler@4 node scripts/upload-fonts.mjs <bucket>
import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const run = promisify(execFile);
const bucket = process.argv[2];
if (!bucket) {
  console.error("Usage: node scripts/upload-fonts.mjs <bucket-name>");
  process.exit(1);
}
const ROOT = fileURLToPath(new URL("..", import.meta.url)); // handles the space in "Font Website"
const FONTS = join(ROOT, "public/fonts");
const LOG = join(ROOT, "scripts/.uploaded-fonts.json");
const uploaded = existsSync(LOG) ? JSON.parse(readFileSync(LOG, "utf8")) : {};
const TYPES = { ".woff2": "font/woff2", ".css": "text/css; charset=utf-8", ".txt": "text/plain; charset=utf-8" };

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* walk(p);
    else yield p;
  }
}

const todo = [];
for (const file of walk(FONTS)) {
  const key = "fonts/" + relative(FONTS, file);
  const hash = createHash("sha1").update(readFileSync(file)).digest("hex");
  if (uploaded[key] !== hash) todo.push({ file, key, hash });
}
console.log(`${todo.length} files to upload (${Object.keys(uploaded).length} already uploaded)`);

// Network hiccups happen over thousands of uploads; try each file a few times
async function putWithRetry(args, key, tries = 4) {
  for (let i = 1; ; i++) {
    try {
      return await run("wrangler", args);
    } catch (err) {
      if (i >= tries) throw err;
      console.log(`  retry ${i} for ${key}`);
      await new Promise((r) => setTimeout(r, 2000 * i));
    }
  }
}

let done = 0;
const failed = [];
async function worker() {
  while (todo.length) {
    const { file, key, hash } = todo.shift();
    const ext = file.slice(file.lastIndexOf("."));
    const ok = await putWithRetry([
      "r2", "object", "put", `${bucket}/${key}`,
      "--file", file, "--remote",
      "--content-type", TYPES[ext] ?? "application/octet-stream",
      // One day: re-slicing a font replaces files under the same names, so
      // browsers must not keep an old mix of pieces for long
      "--cache-control", "public, max-age=86400",
    ], key).then(() => true, (err) => {
      // Give up on this file for now; it isn't marked uploaded, so the next run tries again
      failed.push(key);
      console.log(`  FAILED ${key}: ${String(err.message ?? err).split("\n")[0]}`);
      return false;
    });
    if (!ok) continue;
    uploaded[key] = hash;
    if (++done % 50 === 0) {
      writeFileSync(LOG, JSON.stringify(uploaded, null, 1));
      console.log(`  ${done} uploaded…`);
    }
  }
}
const PARALLEL = Number(process.env.PARALLEL ?? 8); // uploads at a time
await Promise.all(Array.from({ length: PARALLEL }, worker));
writeFileSync(LOG, JSON.stringify(uploaded, null, 1));
console.log(`Done: ${done} uploaded.`);
if (failed.length) {
  console.log(`${failed.length} failed; run the script again to retry them.`);
  process.exitCode = 1;
}
