from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .idea_loader import (
    create_pipeline_clients,
    list_pending_ideas,
    load_idea,
    load_pipeline_config,
)
from .packager import PackageResult, build_publish_package
from .reviewer import ReviewResult, review_markdown
from .scorer import ScoreResult, score_markdown
from .weekly_review import WeeklyResult, generate_weekly_review as generate_weekly
from .writer import DraftResult, write_draft


@dataclass
class PipelineRunResult:
    generate: DraftResult
    review: ReviewResult
    score: ScoreResult
    package: PackageResult | None


@dataclass
class BatchRunResult:
    successes: list[PipelineRunResult]
    failures: list[tuple[str, str]]


def generate_draft_only(
    idea_id: str,
    dry_run: bool,
    config_path: str = "config.yaml",
) -> DraftResult:
    config = load_pipeline_config(config_path)
    clients = create_pipeline_clients(config, dry_run=dry_run)
    idea = load_idea(clients, idea_id)
    return write_draft(idea, clients, config)


def review_file(
    markdown_file: str | Path,
    dry_run: bool,
    config_path: str = "config.yaml",
) -> ReviewResult:
    config = load_pipeline_config(config_path)
    clients = create_pipeline_clients(config, dry_run=dry_run)
    return review_markdown(markdown_file, clients, config)


def run_single(
    idea_id: str,
    dry_run: bool,
    config_path: str = "config.yaml",
) -> PipelineRunResult:
    config = load_pipeline_config(config_path)
    clients = create_pipeline_clients(config, dry_run=dry_run)
    idea = load_idea(clients, idea_id)

    draft = write_draft(idea, clients, config)
    review = review_markdown(draft.draft_path, clients, config)
    score_source = review.reviewed_path or draft.draft_path
    score = score_markdown(
        score_source,
        clients,
        config,
        dry_run=dry_run,
        review=review.review,
    )

    package = None
    if review.reviewed_path and review.review.get("passed") is True:
        package = build_publish_package(review.reviewed_path, config, score=score.score)

    return PipelineRunResult(
        generate=draft,
        review=review,
        score=score,
        package=package,
    )


def run_batch(
    limit: int,
    dry_run: bool,
    config_path: str = "config.yaml",
) -> BatchRunResult:
    config = load_pipeline_config(config_path)
    clients = create_pipeline_clients(config, dry_run=dry_run)
    ideas = list_pending_ideas(clients, limit)
    successes: list[PipelineRunResult] = []
    failures: list[tuple[str, str]] = []

    for idea in ideas:
        idea_id = str(idea.get("idea_id", "")).strip()
        try:
            successes.append(run_single(idea_id, dry_run=dry_run, config_path=config_path))
        except RuntimeError as exc:
            failures.append((idea_id or "unknown", str(exc)))

    return BatchRunResult(successes=successes, failures=failures)


def run_weekly_review(
    dry_run: bool,
    config_path: str = "config.yaml",
) -> WeeklyResult:
    config = load_pipeline_config(config_path)
    clients = create_pipeline_clients(config, dry_run=dry_run)
    return generate_weekly(clients, config)

