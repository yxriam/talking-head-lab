"""Visible Facebook collection, adapted from yxriam/facebook-scam's Playwright pipeline."""

import hashlib
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, urljoin

import httpx


class LoginRequired(RuntimeError):
    pass


class Cancelled(RuntimeError):
    pass


def facebook_url(value):
    url = urlsplit(value.strip())
    host = (url.hostname or "").lower()
    if (url.scheme != "https" or host not in {"facebook.com", "www.facebook.com", "m.facebook.com", "web.facebook.com"}
            or url.username or url.password or url.port not in {None, 443}):
        raise ValueError("请输入 https://www.facebook.com/ 开头的 Facebook 链接")
    return urlunsplit(("https", host, url.path or "/", url.query, ""))


def media_url(value):
    try:
        url = urlsplit(value)
        host = (url.hostname or "").lower()
        allowed = any(host == domain or host.endswith("." + domain) for domain in ("fbcdn.net", "facebook.com", "fbsbx.com"))
        return bool(url.scheme == "https" and allowed and not url.username and not url.password and url.port in {None, 443})
    except ValueError:
        return False


EXTRACT_SCRIPT = r"""() => {
  const root = document.querySelector('[role="main"]') || document.body;
  const visible = el => {
    const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight && s.display !== 'none' && s.visibility !== 'hidden';
  };
  const clean = s => (s || '').replace(/\s+/g, ' ').trim();
  const text = Array.from(root.querySelectorAll('h1,h2,h3,p,[dir="auto"]')).filter(visible)
    .map(el => {
      const article = el.closest('[role="article"]');
      const comment = el.closest('[aria-label*="Comment"],[aria-label*="评论"]');
      const dateScope = comment || article;
      const dateElement = dateScope && Array.from(dateScope.querySelectorAll('time,abbr[title]')).find(visible);
      const content = article ? clean(article.innerText) : '';
      return {text:clean(el.innerText), source_url:el.closest('a')?.href || location.href,
        context:comment ? 'comment' : article ? 'post' : 'profile_or_page',
        date:dateElement ? (dateElement.getAttribute('datetime') || dateElement.getAttribute('title') || clean(dateElement.innerText)) : null,
        reposted:/^(?:转发|转载|分享自)|shared (?:a post|from)|reposted/i.test(content.slice(0,180))};
    })
    .filter(item => item.text.length >= 2 && item.text.length <= 1500);
  const mediaCaption = el => clean(el.closest('[role="article"]')?.innerText || '').slice(0,500);
  const images = Array.from(root.querySelectorAll('img')).filter(visible)
    .filter(el => el.getBoundingClientRect().width >= 40 && el.getBoundingClientRect().height >= 40)
    .map(el => ({kind:'image', src:el.currentSrc || el.src, name:el.alt || 'Facebook image', caption:mediaCaption(el), source_url:el.closest('a')?.href || location.href}));
  const videos = Array.from(root.querySelectorAll('video')).filter(visible)
    .map(el => ({kind:'video', src:el.currentSrc || el.src, name:'Facebook video', caption:mediaCaption(el), source_url:el.closest('a')?.href || location.href}));
  const links = Array.from(root.querySelectorAll('a[href]')).filter(visible)
    .filter(el => /\/watch\/|\/reel\/|\/videos\//.test(el.href))
    .map(el => ({kind:'video', src:'', name:clean(el.innerText) || 'Facebook video', source_url:el.href}));
  const audiences = Array.from(root.querySelectorAll('[aria-label],[title]')).filter(visible)
    .map(el=>el.getAttribute('aria-label') || el.getAttribute('title') || '')
    .filter(value=>/^(?:Public|Friends|Only me|公开|好友|朋友|仅自己|向公众分享|Shared with Public)$/i.test(value));
  const heading=root.querySelector('h1');
  return {title:document.title, display_name:heading && visible(heading) ? clean(heading.innerText) : '', text, audiences, media:images.concat(videos,links), y:scrollY, height:document.documentElement.scrollHeight};
}"""


def login_required(page):
    if any(marker in page.url.lower() for marker in ("/login", "/checkpoint", "/challenge", "/two_step_verification")):
        return True
    return page.locator('input[type="password"]:visible').count() > 0


def browser_channel():
    if Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe").exists():
        return "chrome"
    if Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe").exists():
        return "msedge"
    return None


def open_context(playwright, profile, headless=False):
    return playwright.chromium.launch_persistent_context(
        str(profile), channel=browser_channel(), headless=headless,
        viewport={"width": 1280, "height": 900}, accept_downloads=False,
    )


def check_cancel(stop):
    if stop.is_set():
        raise Cancelled("已停止采集")


def login(profile, stop, update):
    check_cancel(stop)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        context = open_context(playwright, profile)
        try:
            page = context.pages[0] if context.pages else context.new_page()
            update(stage="login", message="请在打开的浏览器中登录 Facebook", progress=0)
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=60000)
            deadline = time.monotonic() + 600
            while time.monotonic() < deadline:
                check_cancel(stop)
                if not context.pages:
                    raise LoginRequired("登录窗口已关闭，请重新打开")
                if (any(cookie.get("name") == "c_user" for cookie in context.cookies("https://www.facebook.com/"))
                        and not login_required(page)):
                    return {"message": "Facebook 登录会话已保存在本机"}
                page.wait_for_timeout(500)
            raise LoginRequired("登录等待超时，请重新打开登录窗口")
        finally:
            context.close()


def download(context, item, directory, stop, budget=500 * 1024 * 1024):
    """Stream bounded media; check each redirect before requesting it."""
    parts = urlsplit(item["src"])
    # Preserve signed query encoding byte-for-byte except the optional range fields.
    query = "&".join(part for part in parts.query.split("&")
                     if part.split("=", 1)[0].lower() not in {"bytestart", "byteend"})
    url = urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))
    maximum = min(budget, 20 * 1024 * 1024 if item["kind"] == "image" else 100 * 1024 * 1024)
    suffixes = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
                "video/mp4": ".mp4", "audio/mp4": ".m4a", "audio/mpeg": ".mp3"}
    identifier = uuid.uuid4().hex
    temporary = directory / (identifier + ".part")
    try:
        with httpx.Client(timeout=30, follow_redirects=False, trust_env=False) as client:
            for _ in range(6):
                check_cancel(stop)
                if not media_url(url):
                    raise ValueError("媒体地址不属于 Facebook")
                cookies = {cookie["name"]: cookie["value"] for cookie in context.cookies(url)}
                with client.stream("GET", url, headers={"Referer": "https://www.facebook.com/"}, cookies=cookies) as response:
                    if response.is_redirect:
                        url = urljoin(url, response.headers["location"])
                        continue
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "").split(";")[0].lower()
                    suffix = suffixes.get(content_type)
                    if item["kind"] == "image" and not content_type.startswith("image/"):
                        raise ValueError("下载内容与图片类型不匹配")
                    if item["kind"] != "image" and not content_type.startswith(("video/", "audio/")):
                        raise ValueError("下载内容与音视频类型不匹配")
                    if not suffix or response.status_code == 206:
                        raise ValueError("来源只提供片段或不支持的媒体格式")
                    if int(response.headers.get("content-length", "0")) > maximum:
                        raise ValueError("媒体超过单文件下载上限")
                    digest, size, prefix = hashlib.sha256(), 0, b""
                    with temporary.open("wb") as output:
                        for chunk in response.iter_bytes(65536):
                            check_cancel(stop)
                            size += len(chunk)
                            if size > maximum:
                                raise ValueError("媒体超过单文件下载上限")
                            prefix = (prefix + chunk)[:32]
                            digest.update(chunk)
                            output.write(chunk)
                    valid = (prefix.startswith(b"\xff\xd8\xff") if suffix == ".jpg" else
                             prefix.startswith(b"\x89PNG\r\n\x1a\n") if suffix == ".png" else
                             prefix.startswith(b"RIFF") and prefix[8:12] == b"WEBP" if suffix == ".webp" else
                             b"ftyp" in prefix if suffix in {".mp4", ".m4a"} else
                             prefix.startswith(b"ID3") or prefix[:1] == b"\xff")
                    if not valid or not size:
                        raise ValueError("下载内容不是有效媒体文件")
                    filename = identifier + suffix
                    temporary.replace(directory / filename)
                    return {"id": identifier, "filename": filename, "size": size,
                            "kind": "audio" if content_type.startswith("audio/") else item["kind"],
                            "sha256": digest.hexdigest(), "status": "downloaded"}
            raise ValueError("媒体重定向次数过多")
    finally:
        temporary.unlink(missing_ok=True)


def collect(options, profile, directory, stop, update):
    check_cancel(stop)
    from playwright.sync_api import sync_playwright
    started = time.monotonic()
    result = {"source_url": facebook_url(options["url"]), "title": "", "text": [], "media": [], "warnings": [],
              "scope": {"audiences": [], "coverage": "visible_page_only"}}
    seen_text, seen_media, observed, hashes = set(), set(), [], set()
    with sync_playwright() as playwright:
        context = open_context(playwright, profile)
        try:
            page = context.new_page()
            def route_document(route):
                if route.request.is_navigation_request() and route.request.frame == page.main_frame:
                    try:
                        facebook_url(route.request.url)
                    except ValueError:
                        route.abort()
                        return
                route.fallback()
            page.route("**/*", route_document)
            def observe(response):
                content_type = response.headers.get("content-type", "")
                if response.request.resource_type == "media" and media_url(response.url) and len(observed) < 100:
                    kind = "audio" if content_type.startswith("audio/") else "video"
                    observed.append({"kind": kind, "src": response.url, "source_url": result["source_url"], "name": "Facebook " + kind})
            page.on("response", observe)
            update(stage="opening", progress=5, message="正在打开 Facebook 页面")
            page.goto(result["source_url"], wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)
            stable, previous = 0, None
            for index in range(options["max_scrolls"]):
                check_cancel(stop)
                if login_required(page):
                    raise LoginRequired("Facebook 需要登录或验证，请先打开登录窗口")
                snapshot = page.evaluate(EXTRACT_SCRIPT)
                result["title"] = snapshot["title"]
                if snapshot.get('display_name'):
                    result['display_name']=snapshot['display_name']
                result["scope"]["audiences"] = sorted(set(result["scope"]["audiences"] + snapshot.get("audiences", [])))
                for item in snapshot["text"]:
                    key = item["text"].casefold()
                    if key not in seen_text and len(result["text"]) < 2000:
                        seen_text.add(key)
                        result["text"].append(item)
                for item in snapshot["media"] + observed:
                    key = item.get("src") or item["source_url"]
                    if key not in seen_media and len(result["media"]) < 300:
                        seen_media.add(key)
                        result["media"].append(item)
                position = (round(snapshot["y"]), round(snapshot["height"]), len(seen_text), len(seen_media))
                stable = stable + 1 if position == previous else 0
                previous = position
                update(stage="extracting", progress=10 + (index + 1) * 50 // options["max_scrolls"],
                       message="正在提取可见内容", counts={"text": len(result["text"]), "media": len(result["media"]), "scrolls": index + 1})
                if stable >= 3:
                    break
                page.mouse.wheel(0, 700)
                page.wait_for_timeout(1200)
            counts = {"image": 0, "video": 0, "audio": 0}
            total_bytes = 0
            for index, item in enumerate(result["media"]):
                check_cancel(stop)
                item.setdefault("status", "link_only")
                limit = options["max_images"] if item["kind"] == "image" else options["max_videos"]
                if not options["download_media"] or counts[item["kind"]] >= limit:
                    item["reason"] = "未启用下载或已达到本次下载数量上限"
                    continue
                if total_bytes >= 500 * 1024 * 1024:
                    item["reason"] = "已达到本次 500 MB 下载总量上限"
                    continue
                if not media_url(item.get("src", "")):
                    item["reason"] = "页面只提供链接，未发现可下载的原始文件"
                    continue
                try:
                    saved = download(context, item, directory, stop, 500 * 1024 * 1024 - total_bytes)
                    if saved["sha256"] in hashes:
                        (directory / saved["filename"]).unlink()
                        item["status"] = "duplicate"
                        continue
                    hashes.add(saved["sha256"])
                    item.update(saved)
                    total_bytes += saved["size"]
                    counts[item["kind"]] += 1
                except Cancelled:
                    raise
                except Exception as error:
                    item.update(status="failed", reason=f"下载失败：{type(error).__name__}")
                update(stage="downloading", progress=60 + (index + 1) * 35 // max(1, len(result["media"])),
                       message="正在保存原始媒体", counts={"text": len(result["text"]), **counts})
            if not result["text"] and not result["media"]:
                result["warnings"].append("页面没有可提取内容；可能需要登录、页面不可用或布局已变化")
            result["elapsed_seconds"] = round(time.monotonic() - started, 1)
            return result
        finally:
            context.close()
