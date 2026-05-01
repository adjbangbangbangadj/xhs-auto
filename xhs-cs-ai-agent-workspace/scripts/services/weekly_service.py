from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.runner import run_weekly_review  # noqa: E402
from pipeline.weekly_review import WeeklyResult  # noqa: E402


def generate_weekly_review(dry_run: bool, config_path: str = "config.yaml") -> WeeklyResult:
    return run_weekly_review(dry_run=dry_run, config_path=config_path)
