from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from clients.client_factory import AppClients
from utils import (
    current_date_str,
    extract_front_matter,
    parse_json_response,
    read_text,
    render_template,
    write_json,
    write_text,
)

from . import PROJECT_ROOT
from .writer import output_path, update_front_matter


@dataclass
class ReviewResult:
    post_id: str
    report_path: Path
    reviewed_path: Path | None
    review: dict[str, Any]


def review_markdown(
    markdown_file: str | Path,
    clients: AppClients,
    config: dict[str, Any],
) -> ReviewResult:
    markdown_path = Path(markdown_file)
    if not markdown_path.is_absolute():
        markdown_path = PROJECT_ROOT / markdown_path

    markdown = read_text(markdown_path)
    front_matter = extract_front_matter(markdown)

    prompt = read_text(PROJECT_ROOT / "prompts/review_post.md")
    content = render_template(
        prompt,
        {
            "compliance": read_text(PROJECT_ROOT / "rules/compliance.md"),
            "post_markdown": markdown,
        },
    )
    review = parse_json_response(clients.llm.chat([{"role": "user", "content": content}]))

    post_id = front_matter.get("post_id", markdown_path.stem)
    report_dir = output_path(config, "review_report_dir", "reports/review")
    report_path = report_dir / f"{current_date_str()}_{post_id}_review.json"
    write_json(report_path, review)

    reviewed_path = None
    if review.get("passed") is True:
        reviewed_dir = output_path(config, "reviewed_dir", "content/reviewed")
        reviewed_dir.mkdir(parents=True, exist_ok=True)
        reviewed_path = reviewed_dir / markdown_path.name
        reviewed_markdown = update_front_matter(
            markdown,
            {
                "status": "reviewed",
                "reviewed_at": current_date_str(),
            },
        )
        write_text(reviewed_path, reviewed_markdown)
    else:
        # Keep old behavior for callers that may expect no reviewed file.
        reviewed_path = None

    if post_id:
        clients.content_store.update_content_review(post_id, review)

    return ReviewResult(
        post_id=post_id,
        report_path=report_path,
        reviewed_path=reviewed_path,
        review=review,
    )


def copy_reviewed_for_compatibility(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)

