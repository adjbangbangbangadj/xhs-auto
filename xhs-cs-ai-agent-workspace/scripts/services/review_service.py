from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.reviewer import ReviewResult  # noqa: E402
from pipeline.runner import review_file  # noqa: E402


def review_post(
    markdown_file: str | Path, dry_run: bool, config_path: str = "config.yaml"
) -> ReviewResult:
    return review_file(markdown_file, dry_run=dry_run, config_path=config_path)

