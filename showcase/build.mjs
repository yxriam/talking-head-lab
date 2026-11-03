import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const showcaseRoot = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(showcaseRoot, "..");
const sourceRoot = join(showcaseRoot, "src");
const outputRoot = join(showcaseRoot, "dist");

const assets = {
  "crawl-zh.jpg": "docs/showcase/crawl-zh.jpg",
  "account-zh.jpg": "docs/showcase/account-zh.jpg",
  "detect-original-zh.jpg": "docs/showcase/detect-original-zh.jpg",
  "portrait-01-thumb.jpg": "docs/showcase/gallery/portrait-01-thumb.jpg",
  "portrait-02-thumb.jpg": "docs/showcase/gallery/portrait-02-thumb.jpg",
  "portrait-03-thumb.jpg": "docs/showcase/gallery/portrait-03-thumb.jpg",
  "video-01.mp4": "docs/showcase/sadtalker-original-demo.mp4",
  "video-02.mp4": "docs/showcase/gallery/video-02.mp4",
  "video-03.mp4": "docs/showcase/gallery/video-03.mp4"
};

await rm(outputRoot, { recursive: true, force: true });
await mkdir(join(outputRoot, "assets"), { recursive: true });
await cp(sourceRoot, outputRoot, { recursive: true });

for (const [target, source] of Object.entries(assets)) {
  await cp(join(repositoryRoot, source), join(outputRoot, "assets", target));
}

const headers = [
  "/*",
  "  X-Content-Type-Options: nosniff",
  "  Referrer-Policy: strict-origin-when-cross-origin",
  "  Permissions-Policy: camera=(), microphone=(), geolocation=()",
  "  X-Frame-Options: DENY",
  "",
  "/assets/*",
  "  Cache-Control: public, max-age=31536000, immutable",
  ""
].join("\n");
await writeFile(join(outputRoot, "_headers"), headers, "utf8");

const html = await readFile(join(outputRoot, "index.html"), "utf8");
if (!html.includes("Talking Head Lab")) {
  throw new Error("Generated page is missing the project title.");
}

console.log("Built Cloudflare Pages site: " + outputRoot);
console.log("Copied " + Object.keys(assets).length + " public showcase assets.");
