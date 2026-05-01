#!/usr/bin/env python3
"""
小红书扫码登录脚本 —— 在你的终端手动运行。

用法：
    python mcp_xhs_publish/login.py

会打开一个浏览器窗口，用小红书 App 扫码即可。
登录成功后 Cookie 保存到 mcp_xhs_publish/.xhs_cookies.json
"""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from mcp_xhs_publish.publisher import xhs_login


async def main():
    print("=" * 50)
    print("  小红书创作者平台 - 扫码登录")
    print("=" * 50)
    print()
    print("  即将打开浏览器...")
    print("  请在 3 分钟内用小红书 App 扫码")
    print()
    result = await xhs_login(timeout_seconds=180)
    print()
    print(result)
    print()


if __name__ == "__main__":
    asyncio.run(main())
