from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from clients.client_factory import AppClients
from utils import (
    current_date_str,
    extract_front_matter,
    extract_title_from_markdown,
    make_post_id,
    read_text,
    render_template,
    slugify,
    strip_front_matter,
    write_text,
)

from . import PROJECT_ROOT


@dataclass
class DraftResult:
    idea_id: str
    post_id: str
    title: str
    draft_path: Path


def output_path(config: dict[str, Any], key: str, default: str) -> Path:
    return PROJECT_ROOT / config.get("paths", {}).get(key, default)


def build_generation_messages(idea: dict[str, Any]) -> list[dict[str, str]]:
    prompt = read_text(PROJECT_ROOT / "prompts/generate_post.md")
    variables = {
        "idea_id": idea.get("idea_id", ""),
        "theme": idea.get("theme", ""),
        "audience": idea.get("audience", ""),
        "pain_point": idea.get("pain_point", ""),
        "content_type": idea.get("content_type", ""),
        "positioning": read_text(PROJECT_ROOT / "rules/positioning.md"),
        "xhs_style": read_text(PROJECT_ROOT / "rules/xhs_style.md"),
        "compliance": read_text(PROJECT_ROOT / "rules/compliance.md"),
    }
    return [{"role": "user", "content": render_template(prompt, variables)}]


def render_front_matter(markdown: str, metadata: dict[str, Any]) -> str:
    body = strip_front_matter(markdown)
    front_matter = yaml.safe_dump(
        metadata,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()
    return f"---\n{front_matter}\n---\n\n{body}"


def update_front_matter(markdown: str, updates: dict[str, Any]) -> str:
    metadata = extract_front_matter(markdown)
    metadata.update({key: "" if value is None else value for key, value in updates.items()})
    return render_front_matter(markdown, metadata)


def add_draft_front_matter(markdown: str, idea: dict[str, Any], post_id: str) -> str:
    metadata = {
        "idea_id": str(idea.get("idea_id", "")),
        "post_id": post_id,
        "status": "draft",
        "content_type": str(idea.get("content_type", "")),
        "target_audience": str(idea.get("audience", "")),
        "created_at": current_date_str(),
        "reviewed_at": "",
        "published_at": "",
    }
    return render_front_matter(markdown, metadata)


def write_draft(
    idea: dict[str, Any],
    clients: AppClients,
    config: dict[str, Any],
) -> DraftResult:
    idea_id = str(idea.get("idea_id", "")).strip()
    if not idea_id:
        raise RuntimeError("选题缺少 idea_id。")

    post_id = make_post_id(idea_id)
    markdown = clients.llm.chat(build_generation_messages(idea))
    markdown = add_draft_front_matter(markdown, idea, post_id)
    title = extract_title_from_markdown(markdown)

    filename = f"{current_date_str()}_{idea_id}_{slugify(idea.get('theme', title))}.md"
    draft_dir = output_path(config, "draft_dir", "content/drafts")
    draft_path = draft_dir / filename
    write_text(draft_path, markdown)

    record = {
        "post_id": post_id,
        "idea_id": idea_id,
        "title": title,
        "title_options": "",
        "cover_text": "",
        "markdown_path": str(draft_path.relative_to(PROJECT_ROOT)),
        "review_report_path": "",
        "risk_level": "low",
        "review_status": "未质检",
        "status": "草稿",
        "created_at": current_date_str(),
        "updated_at": current_date_str(),
    }
    clients.content_store.create_content_record(record)
    clients.content_store.update_idea_status(idea_id, "已生成")

    return DraftResult(
        idea_id=idea_id,
        post_id=post_id,
        title=title,
        draft_path=draft_path,
    )

