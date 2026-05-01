#!/usr/bin/env python3
"""
MCP Server for Xiaohongshu (小红书) automated publishing.

Run via stdio (recommended):
    python -m mcp_xhs_publish.server

Configure in claude_desktop_config.json or .mcp.json:

{
  "mcpServers": {
    "xhs-publish": {
      "command": "python",
      "args": ["-m", "mcp_xhs_publish.server"],
      "cwd": "path/to/xhs-cs-ai-agent-workspace"
    }
  }
}
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

try:
    from .cookie_manager import clear_cookies, cookie_status
    from .publisher import (
        xhs_batch_publish,
        xhs_check_login,
        xhs_login,
        xhs_publish_from_file,
        xhs_publish_post,
    )
except ImportError:
    # Compatibility mode when the file is launched as a script path.
    from mcp_xhs_publish.cookie_manager import clear_cookies, cookie_status
    from mcp_xhs_publish.publisher import (
        xhs_batch_publish,
        xhs_check_login,
        xhs_login,
        xhs_publish_from_file,
        xhs_publish_post,
    )

mcp = FastMCP(
    name="xhs-publish",
    instructions="""
小红书自动发布 MCP Server。

工具列表：
  xhs_login           — 扫码登录，保存 cookie
  xhs_check_login     — 检查登录状态
  xhs_publish_post    — 发布单篇笔记（需提供 title, content, image_paths, tags）
  xhs_publish_from_file — 从项目 posts/reviewed/*.md 读取并发布
  xhs_batch_publish   — 批量发布待发布目录下所有内容

使用流程：
  1. 先执行 xhs_login 完成扫码登录
  2. 执行 xhs_check_login 确认状态
  3. 执行 xhs_publish_post 或 xhs_publish_from_file 发布内容
""",
)


# ── Tools ──────────────────────────────────────────────────────


@mcp.tool()
async def xhs_login_tool(timeout_seconds: int = 120) -> str:
    """打开浏览器窗口，扫码登录小红书创作者平台，并保存 Cookie。

    首次使用或 cookie 过期时调用。浏览器会打开登录页面，
    用户用小红书 App 扫码完成登录，cookie 自动保存到本地文件。

    Args:
        timeout_seconds: 等待扫码的超时秒数，默认 120 秒。
    """
    return await xhs_login(timeout_seconds=timeout_seconds)


@mcp.tool()
async def xhs_check_login_tool() -> str:
    """检查当前是否已登录小红书创作者平台。

    读取本地保存的 cookie，访问创作者中心验证是否仍有效。
    如果过期，会提示重新执行 xhs_login。
    """
    return await xhs_check_login()


@mcp.tool()
async def xhs_publish_post_tool(
    title: str,
    content: str,
    image_paths: str = "",
    tags: str = "",
    headless: bool = False,
    dry_run: bool = False,
) -> str:
    """发布一篇笔记到小红书创作者平台。

    使用 Playwright 打开浏览器，自动填写标题、正文、图片和标签并发布。

    Args:
        title: 笔记标题（最多 20 个字符）。
        content: 笔记正文内容。
        image_paths: 图片文件绝对路径，多个用逗号分隔。例如 "C:/images/1.jpg,C:/images/2.jpg"。
        tags: 标签，多个用逗号分隔。不需要带 # 前缀。例如 "计算机复试,考研"。
        headless: 是否无头模式运行浏览器（True=后台运行，False=显示窗口）。默认 False。
        dry_run: 是否为试运行（True=仅填写不发布，False=真正发布）。建议先 dry_run。
    """
    paths = [p.strip() for p in image_paths.split(",") if p.strip()] if image_paths else []
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    return await xhs_publish_post(
        title=title,
        content=content,
        image_paths=paths,
        tags=tag_list,
        headless=headless,
        dry_run=dry_run,
    )


@mcp.tool()
async def xhs_publish_from_file_tool(
    file_path: str,
    headless: bool = False,
    dry_run: bool = False,
) -> str:
    """从项目的 Markdown 文件读取内容并发布到小红书。

    解析 reviewed 目录下的 .md 文件，自动提取标题、正文、标签，然后发布。
    文件必须包含 YAML front matter 和结构化章节。

    Args:
        file_path: Markdown 文件的绝对路径。例如 "C:/Users/.../posts/reviewed/2026-04-30_001_xxx.md"。
        headless: 是否无头模式运行浏览器。默认 False（显示窗口便于确认）。
        dry_run: 是否为试运行（True=仅解析不发布）。建议先 dry_run 查看提取的内容。
    """
    return await xhs_publish_from_file(
        file_path=file_path,
        headless=headless,
        dry_run=dry_run,
    )


@mcp.tool()
async def xhs_batch_publish_tool(
    reviewed_dir: str = "posts/reviewed",
    headless: bool = False,
    dry_run: bool = False,
) -> str:
    """批量发布项目中所有已审核的内容到小红书。

    扫描 posts/reviewed/ 目录下的所有 .md 文件，逐一解析并发布。

    Args:
        reviewed_dir: reviewed 目录路径（相对于项目根目录）。默认 "posts/reviewed"。
        headless: 是否无头模式运行浏览器。默认 False。
        dry_run: 是否为试运行（True=仅列出文件不发布）。默认 False，强烈建议先 dry_run。
    """
    return await xhs_batch_publish(
        reviewed_dir=reviewed_dir,
        headless=headless,
        dry_run=dry_run,
    )


@mcp.tool()
async def xhs_clear_login_tool() -> str:
    """清除本地保存的小红书登录 Cookie，强制下次重新登录。"""
    clear_cookies()
    return "已清除登录状态。下次发布前需要重新执行 xhs_login。"


@mcp.tool()
async def xhs_cookie_status_tool() -> str:
    """查看当前 cookie 状态（是否存在、是否可能有效）。"""
    return cookie_status()


# ── Entry Point ─────────────────────────────────────────────────


def main() -> None:
    """Run the MCP server via stdio."""
    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
