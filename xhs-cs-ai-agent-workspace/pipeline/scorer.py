from __future__ import annotations

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
)

from . import PROJECT_ROOT
from .writer import output_path


@dataclass
class ScoreResult:
    report_path: Path
    score: dict[str, Any]


REQUIRED_SCORE_KEYS = [
    "favorite_score",
    "comment_score",
    "dm_conversion_score",
    "specificity_score",
    "personal_experience_score",
    "ai_smell_risk",
    "compliance_risk",
    "publish_recommendation",
    "suggested_improvements",
]


def _clamp_score(value: int) -> int:
    return max(0, min(10, value))


def rule_based_score(markdown: str, review: dict[str, Any] | None = None) -> dict[str, Any]:
    review = review or {}
    text = markdown
    favorite_score = 5
    comment_score = 5
    dm_conversion_score = 5
    specificity_score = 5
    personal_experience_score = 5
    ai_smell_risk = 4

    if any(token in text for token in ["模板", "清单", "Prompt", "步骤", "可复制"]):
        favorite_score += 2
    if "评论区引导" in text or "评论区" in text:
        comment_score += 2
    if "私信回复建议" in text or "1v1" in text or "诊断" in text:
        dm_conversion_score += 2
    if any(token in text for token in ["项目", "复试", "导师", "专业课", "英文问答"]):
        specificity_score += 2
    if any(token in text for token in ["我", "真实", "经历", "负责", "复盘"]):
        personal_experience_score += 1
    if any(token in text for token in ["万能", "保过", "必中", "内部资料", "百分百"]):
        ai_smell_risk += 4
    if "不要替我编造" in text or "不夸大" in text or "真实经历" in text:
        ai_smell_risk -= 1

    risk_level = str(review.get("risk_level", "low"))
    compliance_risk = "high" if risk_level == "high" else "medium" if risk_level == "medium" else "low"
    if any(token in text for token in ["保过", "必中", "代写", "代做", "伪造"]):
        compliance_risk = "high"

    favorite_score = _clamp_score(favorite_score)
    comment_score = _clamp_score(comment_score)
    dm_conversion_score = _clamp_score(dm_conversion_score)
    specificity_score = _clamp_score(specificity_score)
    personal_experience_score = _clamp_score(personal_experience_score)
    ai_smell_risk = _clamp_score(ai_smell_risk)

    suggested_improvements: list[str] = []
    if specificity_score < 7:
        suggested_improvements.append("补充更具体的复试场景、项目背景或老师追问情境。")
    if favorite_score < 7:
        suggested_improvements.append("增加可复制模板、检查清单或 Prompt，提升收藏价值。")
    if personal_experience_score < 6:
        suggested_improvements.append("增加真实个人经验或复盘表达，降低泛泛而谈的感觉。")
    if ai_smell_risk >= 7:
        suggested_improvements.append("删掉过度模板化或夸张表达，改成更克制的个人经验。")
    if compliance_risk != "low":
        suggested_improvements.append("人工复核合规风险，避免承诺结果、代写代做或伪造经历。")

    if compliance_risk == "high":
        recommendation = "reject"
    elif ai_smell_risk >= 7 or review.get("passed") is False:
        recommendation = "revise"
    else:
        recommendation = "publish"

    return {
        "favorite_score": favorite_score,
        "comment_score": comment_score,
        "dm_conversion_score": dm_conversion_score,
        "specificity_score": specificity_score,
        "personal_experience_score": personal_experience_score,
        "ai_smell_risk": ai_smell_risk,
        "compliance_risk": compliance_risk,
        "publish_recommendation": recommendation,
        "suggested_improvements": suggested_improvements,
    }


def llm_score(
    markdown: str,
    clients: AppClients,
    review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prompt = read_text(PROJECT_ROOT / "prompts/scorer.md")
    content = render_template(
        prompt,
        {
            "post_markdown": markdown,
            "review_json": review or {},
        },
    )
    data = parse_json_response(clients.llm.chat([{"role": "user", "content": content}]))
    missing = [key for key in REQUIRED_SCORE_KEYS if key not in data]
    if missing:
        raise RuntimeError("评分 JSON 缺少字段：" + "、".join(missing))
    return data


def score_markdown(
    markdown_file: str | Path,
    clients: AppClients,
    config: dict[str, Any],
    dry_run: bool,
    review: dict[str, Any] | None = None,
) -> ScoreResult:
    markdown_path = Path(markdown_file)
    if not markdown_path.is_absolute():
        markdown_path = PROJECT_ROOT / markdown_path
    markdown = read_text(markdown_path)
    front_matter = extract_front_matter(markdown)
    idea_id = front_matter.get("idea_id", markdown_path.stem)
    post_id = front_matter.get("post_id", "")

    score = rule_based_score(markdown, review) if dry_run else llm_score(markdown, clients, review)
    score = {"idea_id": idea_id, "post_id": post_id, **score}

    report_dir = output_path(config, "score_report_dir", "reports/score")
    report_path = report_dir / f"{current_date_str()}_{idea_id}_score.json"
    write_json(report_path, score)
    return ScoreResult(report_path=report_path, score=score)

