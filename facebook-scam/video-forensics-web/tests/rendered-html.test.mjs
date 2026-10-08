import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the FrameTrace application shell", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
  const html = await response.text();
  assert.match(html, /FrameTrace/);
  assert.match(html, /四条证据链/);
  assert.match(html, /本地浏览器运行/);
  assert.match(html, /向量二阶变化/);
  assert.match(html, /运动一致性/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|react-loading-skeleton/i);
});

test("keeps scientific boundary language in the product", async () => {
  const source = await readFile(new URL("../app/VideoLab.tsx", import.meta.url), "utf8");
  assert.match(source, /异常指数不是“AI概率”/);
  assert.match(source, /没有加载DINOv2或论文分类器/);
  assert.match(source, /视频不上传/);
  assert.match(source, /dctStats/);
  assert.match(source, /blockMotion/);
});
