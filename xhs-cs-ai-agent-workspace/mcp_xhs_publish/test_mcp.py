#!/usr/bin/env python3
"""
MCP XHS Publish Test Suite

Usage:
  python test_mcp.py              # Smoke tests (no browser needed)
  python test_mcp.py --login      # QR login test
  python test_mcp.py --publish-dry-run  # Publish dry-run test
  python test_mcp.py --all        # Full suite
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def test_cookie_manager() -> bool:
    """Test cookie manager (no browser needed). Preserves real cookies."""
    print("=" * 60)
    print("Test 1: Cookie Manager")
    print("=" * 60)
    from mcp_xhs_publish.cookie_manager import (
        clear_cookies,
        cookie_status,
        load_cookies,
        save_cookies,
    )

    # Backup real cookies
    real = load_cookies()

    # Test save/load with fake cookies
    fake = [{"name": "test", "value": "abc", "domain": ".xiaohongshu.com"}]
    save_cookies(fake)
    loaded = load_cookies()
    assert loaded == fake, "save/load mismatch"
    print("  OK save_cookies / load_cookies")

    # Test clear
    clear_cookies()
    assert load_cookies() == [], "clear failed"
    print("  OK clear_cookies")

    # Restore real cookies
    save_cookies(real)
    print(f"  cookie_status: {cookie_status()}")
    print("  OK Cookie Manager - all passed\n")
    return True


def test_parse_file() -> bool:
    """Test markdown parsing in dry-run mode (no browser)."""
    print("=" * 60)
    print("Test 2: Markdown Content Parsing (dry-run)")
    print("=" * 60)

    reviewed_dir = PROJECT_ROOT / "posts/reviewed"
    files = sorted(reviewed_dir.glob("*.md"))
    if not files:
        print("  SKIP: no reviewed files found\n")
        return False

    test_file = str(files[0])
    print(f"  File: {files[0].name}")

    import asyncio
    from mcp_xhs_publish.publisher import xhs_publish_from_file

    result = asyncio.run(xhs_publish_from_file(test_file, dry_run=True))
    print(f"  {result}")
    print("  OK Content Parsing\n")
    return True


def test_list_tools() -> bool:
    """Test MCP tool registration."""
    print("=" * 60)
    print("Test 3: MCP Tool Registration")
    print("=" * 60)

    import asyncio
    from mcp_xhs_publish.server import mcp

    tools = asyncio.run(mcp.list_tools())
    print(f"  Registered {len(tools)} tools:")
    for t in tools:
        print(f"    - {t.name}")
    assert len(tools) == 7, f"Expected 7 tools, got {len(tools)}"
    print("  OK Tool Registration\n")
    return True


def test_login() -> bool:
    """QR login test (needs browser + phone scan)."""
    print("=" * 60)
    print("Test 4: QR Login")
    print("=" * 60)
    print("  Opening browser...")
    print("  Scan QR code with XHS App within 120s\n")

    import asyncio
    from mcp_xhs_publish.publisher import xhs_login

    result = asyncio.run(xhs_login(timeout_seconds=120))
    print(f"  {result}\n")
    return "成功" in result


def test_check_login() -> bool:
    """Verify login status."""
    print("=" * 60)
    print("Test 5: Login Status Check")
    print("=" * 60)

    import asyncio
    from mcp_xhs_publish.publisher import xhs_check_login

    result = asyncio.run(xhs_check_login())
    print(f"  {result}\n")
    return "有效" in result


def test_publish_dry_run() -> bool:
    """Publish dry-run test (needs valid login)."""
    print("=" * 60)
    print("Test 6: Publish Dry-Run (headless)")
    print("=" * 60)

    reviewed_dir = PROJECT_ROOT / "posts/reviewed"
    files = sorted(reviewed_dir.glob("*.md"))
    if not files:
        print("  SKIP: no reviewed files\n")
        return False

    test_file = str(files[0])
    print(f"  File: {files[0].name}")

    import asyncio
    from mcp_xhs_publish.publisher import xhs_publish_from_file

    try:
        result = asyncio.run(
            xhs_publish_from_file(test_file, headless=True, dry_run=True)
        )
        print(f"  {result}")
        print("  OK Publish Dry-Run\n")
        return True
    except Exception as exc:
        print(f"  FAIL: {exc}\n")
        return False


def main():
    parser = argparse.ArgumentParser(description="XHS MCP Server Tests")
    parser.add_argument("--login", action="store_true")
    parser.add_argument("--publish-dry-run", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    run_all = args.all or (not args.login and not args.publish_dry_run)
    results: dict[str, bool] = {}

    # Tests that don't need browser
    if run_all:
        results["cookie_manager"] = test_cookie_manager()
        results["parse_file"] = test_parse_file()
        results["list_tools"] = test_list_tools()

    # Tests that need browser
    if args.login or args.all:
        results["login"] = test_login()
        results["check_login"] = test_check_login()

    if args.publish_dry_run or args.all:
        results["publish_dry_run"] = test_publish_dry_run()

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    all_ok = True
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"  {name}: {status}")

    if all_ok:
        print("\nAll tests passed.")
    else:
        print("\nSome tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
