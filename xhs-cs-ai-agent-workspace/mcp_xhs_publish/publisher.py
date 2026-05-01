"""
Xiaohongshu (小红书) publisher via Playwright browser automation.

Uses creator.xiaohongshu.com — the official creator platform.
Supports: QR login, cookie persistence, note publishing.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from playwright.async_api import BrowserContext, async_playwright

from .cookie_manager import load_cookies, save_cookies

CREATOR_URL = "https://creator.xiaohongshu.com"
PUBLISH_URL = f"{CREATOR_URL}/publish/publish"
LOGIN_URL = f"{CREATOR_URL}/login"
USER_DIR = Path(__file__).resolve().parent / ".xhs_browser_data"


# ─── helpers ────────────────────────────────────────────────────


@asynccontextmanager
async def _browser_session(headless: bool = False) -> AsyncIterator[BrowserContext]:
    """Async context manager: yields BrowserContext and ensures cleanup."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = await browser.new_context()
        cookies = load_cookies()
        if cookies:
            await context.add_cookies(cookies)
        try:
            yield context
        finally:
            await browser.close()


def _norm_tag(tag: str) -> str:
    """Normalize a tag: strip '#' and whitespace."""
    return tag.strip().lstrip("#").strip()


# ─── public APIs ─────────────────────────────────────────────────


async def xhs_login(timeout_seconds: int = 120) -> str:
    """
    Open a browser window for the user to scan QR code and log in.
    Saves cookies on success.
    """
    async with _browser_session(headless=False) as context:
        page = await context.new_page()
        await page.goto(LOGIN_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        # Wait for login to complete — detect dashboard redirect
        start = time.time()
        logged_in = False
        while time.time() - start < timeout_seconds:
            url = page.url
            if "/creator" in url and "/login" not in url:
                logged_in = True
                break
            if "publish" in url or "dashboard" in url.lower():
                logged_in = True
                break
            await page.wait_for_timeout(2000)

        if not logged_in:
            return f"登录超时（{timeout_seconds}s）。请确认已扫码并完成登录。"

        await page.wait_for_timeout(3000)
        cookies = await context.cookies()
        save_cookies(cookies)

    return "登录成功！Cookie 已保存，后续可直接调用发布工具。"


async def xhs_check_login() -> str:
    """Check if stored cookies are still valid by visiting the creator page."""
    cookies = load_cookies()
    if not cookies:
        return "✗ 未找到登录凭据，请先执行 xhs_login。"

    try:
        async with _browser_session(headless=True) as context:
            page = await context.new_page()
            await page.goto(CREATOR_URL, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(3000)
            url = page.url
            if "/login" in url or "passport" in url.lower():
                return "✗ 登录已过期，请重新执行 xhs_login。"
            return "✓ 登录有效，cookie 正常。"
    except Exception as exc:
        return f"✗ 检查失败：{exc}"


async def xhs_publish_post(
    title: str,
    content: str,
    image_paths: list[str] | None = None,
    tags: list[str] | None = None,
    topic: str = "",
    headless: bool = False,
    dry_run: bool = False,
) -> str:
    """
    Publish a note to Xiaohongshu using the creator platform.

    Parameters
    ----------
    title : str
        Note title (max 20 characters on XHS).
    content : str
        Full body text.
    image_paths : list[str] | None
        Absolute paths to 1–9 image files (required for XHS).
    tags : list[str] | None
        Tags (without # prefix).
    topic : str
        Topic / category (optional).
    headless : bool
        Run browser hidden. Default visible so you can verify.
    dry_run : bool
        If True, fill everything but don't click publish.
    """
    if not image_paths:
        return "✗ 小红书发布至少需要 1 张图片。请提供 image_paths。"

    if len(title) > 20:
        return f"✗ 标题超过 20 字符限制（当前 {len(title)} 字）。请精简标题。"

    image_paths = [Path(p) for p in image_paths]
    for p in image_paths:
        if not p.exists():
            return f"✗ 图片文件不存在：{p}"

    result = ""
    async with _browser_session(headless=headless) as context:
        page = await context.new_page()

        # ── Step 1: Go to publish page ──
        await page.goto(PUBLISH_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

        if "/login" in page.url or "passport" in page.url.lower():
            return "✗ 需要重新登录，请执行 xhs_login。"

        # ── Step 2: Switch to 图文 (image+text) mode ──
        # Default is video mode; click the "上传图文" tab
        try:
            el = page.locator("text=上传图文").nth(1)
            box = await el.bounding_box()
            if box:
                await page.mouse.click(
                    box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                )
                await page.wait_for_timeout(4000)
        except Exception:
            pass  # may already be in 图文 mode

        # ── Step 3: Upload images ──
        try:
            file_input = page.locator('input[type="file"]').first
            await file_input.set_input_files([str(p) for p in image_paths])
            await page.wait_for_timeout(8000)  # wait for upload + processing
        except Exception as exc:
            return f"✗ 图片上传失败：{exc}"

        # ── Step 4: Fill title ──
        # Placeholder: "填写标题会有更多赞哦"
        try:
            title_input = page.locator('[placeholder*="标题"]').first
            if await title_input.count() > 0:
                await title_input.click()
                await title_input.fill(title)
                await page.wait_for_timeout(500)
        except Exception as exc:
            return f"✗ 填写标题失败：{exc}"

        # ── Step 5: Fill content ──
        # Use contenteditable div (shows "0/1000" counter when empty)
        try:
            body_input = page.locator('[contenteditable="true"]').first
            if await body_input.count() > 0:
                await body_input.click()
                await body_input.fill(content)
                await page.wait_for_timeout(1000)
        except Exception as exc:
            return f"✗ 填写正文失败：{exc}"

        # ── Step 6: Add tags ──
        # Click the "话题" button, then type tag name
        if tags:
            try:
                for tag in tags:
                    tag = _norm_tag(tag)
                    if not tag:
                        continue
                    topic_btn = page.locator('button:has-text("话题")').first
                    if await topic_btn.count() == 0:
                        topic_btn = page.locator('button:has-text("添加话题")').first
                    if await topic_btn.count() > 0:
                        await topic_btn.click()
                        await page.wait_for_timeout(2000)
                        # After clicking, a popover appears with tag suggestions
                        # Type the tag name
                        tag_input = page.locator('[placeholder*="搜索"]').first
                        if await tag_input.count() == 0:
                            tag_input = page.locator('[placeholder*="话题"]').first
                        if await tag_input.count() > 0:
                            await tag_input.fill(tag)
                            await page.wait_for_timeout(2000)
                            await tag_input.press("Enter")
                            await page.wait_for_timeout(1500)
            except Exception as exc:
                # Tags are optional; don't fail the whole publish
                pass

        # ── Step 7: Publish ──
        if dry_run:
            result = (
                f"✓ [dry-run] 内容已填写完毕（未实际发布）。\n"
                f"  标题：{title}\n"
                f"  图片数：{len(image_paths)}\n"
                f"  标签：{', '.join(tags or []) or '无'}\n"
                f"  请人工复核后点击发布。"
            )
        else:
            try:
                publish_btn = page.locator('button:has-text("发布")').last
                if await publish_btn.count() > 0:
                    await publish_btn.click()
                    await page.wait_for_timeout(8000)
                    result = (
                        f"✓ 已点击发布按钮！\n"
                        f"  标题：{title}\n"
                        f"  请打开小红书 App 确认发布结果。"
                    )
                else:
                    return "✗ 未找到发布按钮。"
            except Exception as exc:
                return f"✗ 点击发布按钮失败：{exc}"

        if not headless:
            await page.wait_for_timeout(10000)

    return result


async def xhs_publish_from_file(
    file_path: str,
    headless: bool = False,
    dry_run: bool = False,
) -> str:
    """
    Parse a reviewed markdown file and publish it to Xiaohongshu.

    Reads front-matter and structured sections to extract:
    - title (from `# ` heading)
    - content (body section)
    - tags (from `## 标签` section)
    - cover_text (from `## 封面文案` section)

    Parameters
    ----------
    file_path : str
        Path to the reviewed .md file.
    headless : bool
        Run browser hidden.
    dry_run : bool
        If True, parse only — do not publish.
    """
    import yaml

    path = Path(file_path)
    if not path.exists():
        return f"✗ 文件不存在：{file_path}"

    text = path.read_text(encoding="utf-8")

    # ── Parse front matter ──
    fm: dict[str, Any] = {}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = yaml.safe_load(parts[1]) or {}
            body = parts[2]
        else:
            body = text
    else:
        body = text

    # ── Extract title ──
    title = ""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped[2:].strip()
            break
    if not title:
        title = fm.get("title", "")

    # ── Extract tags ──
    tags: list[str] = []
    tag_section = False
    for line in body.splitlines():
        if line.strip().startswith("## 标签") or line.strip().startswith("## 话题"):
            tag_section = True
            continue
        if tag_section and line.strip().startswith("##"):
            break
        if tag_section and line.strip().startswith("#"):
            tags.extend(
                _norm_tag(t) for t in line.strip().split() if t.startswith("#")
            )

    # ── Build content for XHS ──
    # Strip YAML front matter and structured section headers;
    # keep the main body + AI prompt section as XHS body text.
    content_parts: list[str] = []
    skip_sections = {"## 封面文案", "## 标签", "## 评论区引导", "## 私信回复建议",
                     "## 适合沉淀", "## 适合1v1", "## 标题备选"}
    in_skip = False
    for line in body.splitlines():
        stripped = line.strip()
        # Check if entering a skip section
        if any(stripped.startswith(s) for s in skip_sections):
            in_skip = True
            continue
        # Check if entering a new non-skip section
        if stripped.startswith("## ") and not any(stripped.startswith(s) for s in skip_sections):
            in_skip = False
        if in_skip:
            continue
        if stripped.startswith("# ") or stripped.startswith("---"):
            continue
        if stripped:
            content_parts.append(stripped)

    content = "\n".join(content_parts)

    if dry_run:
        return (
            f"✓ [dry-run] 已解析文件内容：\n"
            f"  文件：{path.name}\n"
            f"  标题：{title}\n"
            f"  标签：{', '.join(tags) or '无'}\n"
            f"  正文长度：{len(content)} 字\n"
            f"  未执行实际发布。"
        )

    # ── Auto-detect cover image ──
    covers_dir = PROJECT_ROOT / "posts" / "covers"
    cover_file = covers_dir / f"{path.stem}_cover.png"
    image_paths = [str(cover_file)] if cover_file.exists() else []

    return await xhs_publish_post(
        title=title,
        content=content,
        image_paths=image_paths,
        tags=tags,
        headless=headless,
        dry_run=False,
    )


async def xhs_batch_publish(
    reviewed_dir: str = "posts/reviewed",
    headless: bool = False,
    dry_run: bool = False,
) -> str:
    """
    Publish all reviewed markdown files in a directory.

    Parameters
    ----------
    reviewed_dir : str
        Path to reviewed posts directory.
    headless : bool
        Run browser hidden.
    dry_run : bool
        If True, list files without publishing.
    """
    from pathlib import Path

    dir_path = Path(reviewed_dir)
    if not dir_path.exists():
        # Try relative to project root
        project_root = Path(__file__).resolve().parents[1]
        dir_path = project_root / reviewed_dir
    if not dir_path.exists():
        return f"✗ 目录不存在：{reviewed_dir}"

    files = sorted(dir_path.glob("*.md"), key=lambda p: p.stat().st_mtime)
    if not files:
        return "✗ 目录中没有 .md 文件。"

    if dry_run:
        file_list = "\n".join(f"  - {f.name}" for f in files)
        return f"✓ [dry-run] 共找到 {len(files)} 篇待发布内容：\n{file_list}"

    results: list[str] = []
    for i, f in enumerate(files, 1):
        results.append(f"[{i}/{len(files)}] {f.name}")
        r = await xhs_publish_from_file(str(f), headless=headless, dry_run=False)
        results.append(f"  → {r}")

    return "\n".join(results)
