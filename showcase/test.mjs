import { access, readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(fileURLToPath(new URL(".", import.meta.url)), "dist");
const required = [
  "index.html",
  "styles.css",
  "app.js",
  "_headers",
  "assets/crawl-zh.jpg",
  "assets/account-zh.jpg",
  "assets/detect-original-zh.jpg",
  "assets/video-01.mp4",
  "assets/video-02.mp4",
  "assets/video-03.mp4"
];

for (const path of required) {
  await access(join(root, path));
}

const textFiles = ["index.html", "styles.css", "app.js"];
const combined = (
  await Promise.all(textFiles.map((file) => readFile(join(root, file), "utf8")))
).join("\n");

const forbidden = ["localhost", "127.0.0.1", "fetch(\"/api", "fetch('/api", "/crawl/jobs"];
for (const fragment of forbidden) {
  if (combined.includes(fragment)) {
    throw new Error("Static site unexpectedly depends on " + fragment);
  }
}

const html = await readFile(join(root, "index.html"), "utf8");
for (const anchor of ["workflow", "generation", "detection", "architecture"]) {
  if (!html.includes('id="' + anchor + '"')) {
    throw new Error("Missing section: " + anchor);
  }
}

const outputFiles = await readdir(root, { recursive: true });
console.log("Verified " + required.length + " required outputs across " + outputFiles.length + " files.");
console.log("Verified static site has no local API dependency.");
