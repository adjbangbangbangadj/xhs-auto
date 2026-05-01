from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.runner import (  # noqa: E402
    BatchRunResult as BatchResult,
    PipelineRunResult as PipelineResult,
    generate_draft_only,
    run_batch,
    run_single,
)
from pipeline.writer import DraftResult as GenerateResult  # noqa: E402


def generate_post(idea_id: str, dry_run: bool, config_path: str = "config.yaml") -> GenerateResult:
    return generate_draft_only(idea_id, dry_run=dry_run, config_path=config_path)


def generate_and_review(
    idea_id: str, dry_run: bool, config_path: str = "config.yaml"
) -> PipelineResult:
    return run_single(idea_id, dry_run=dry_run, config_path=config_path)


def batch_generate_and_review(
    limit: int, dry_run: bool, config_path: str = "config.yaml"
) -> BatchResult:
    return run_batch(limit, dry_run=dry_run, config_path=config_path)

