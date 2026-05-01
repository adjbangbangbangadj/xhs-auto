"""
Cookie manager for Xiaohongshu session persistence.

Stores Playwright browser cookies to `.xhs_cookies.json` so users
only need to scan the QR code once.
"""

import json
from pathlib import Path
from typing import Any


COOKIE_FILE = Path(__file__).resolve().parent / ".xhs_cookies.json"


def save_cookies(cookies: list[dict[str, Any]]) -> None:
    """Persist browser cookies to disk."""
    COOKIE_FILE.write_text(
        json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_cookies() -> list[dict[str, Any]]:
    """Load persisted cookies. Returns empty list if none found."""
    if not COOKIE_FILE.exists():
        return []
    try:
        return json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError):
        return []


def clear_cookies() -> None:
    """Delete the cookie file (forces re-login)."""
    if COOKIE_FILE.exists():
        COOKIE_FILE.unlink()


def cookie_status() -> str:
    """Return a human-readable status of the cookie."""
    cookies = load_cookies()
    if not cookies:
        return "未找到登录状态，需要执行 xhs_login。"
    # Check if any key cookie exists
    cookie_names = {c.get("name", "") for c in cookies}
    has_session = "web_session" in cookie_names or "a1" in cookie_names
    if has_session:
        return "已登录（cookie 有效）。"
    return "登录状态可能过期，建议重新执行 xhs_login。"
