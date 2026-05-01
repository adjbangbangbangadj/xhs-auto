from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from utils import current_date_str, extract_front_matter, extract_title_from_markdown, read_text, write_text

from . import PROJECT_ROOT
from .writer import output_path


@dataclass
class PackageResult:
    package_path: Path


def _section(markdown: str, heading: str) -> str:
    marker = f"## {heading}"
    lines = markdown.splitlines()
    capture = False
    collected: list[str] = []
    for line in lines:
        if line.strip() == marker:
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            collected.append(line)
    return "\n".join(collected).strip()


def build_package_markdown(markdown: str, score: dict[str, Any] | None = None) -> str:
    meta = extract_front_matter(markdown)
    title = extract_title_from_markdown(markdown)
    cover = _section(markdown, "封面文案")
    body = _section(markdown, "正文")
    tags = _section(markdown, "标签")
    comment = _section(markdown, "评论区引导")
    dm = _section(markdown, "私信回复建议")
    score = score or {}

    return f"""# 发布包：{title}

## 基本信息

- idea_id：{meta.get("idea_id", "")}
- post_id：{meta.get("post_id", "")}
- 生成日期：{current_date_str()}
- 发布建议：{score.get("publish_recommendation", "publish")}
- 合规风险：{score.get("compliance_risk", "low")}

## 最终标题

{title}

## 封面文案

{cover or "请人工补充封面文案。"}

## 正文

{body or "请人工从 reviewed Markdown 中确认正文。"}

## 标签

{tags or "请人工补充标签。"}

## 评论区引导

{comment or "请人工补充评论区引导。"}

## 私信回复建议

{dm or "请人工补充私信回复建议。"}

## 人工发布前检查清单

- [ ] 是否没有“保过”“必中”“内部资料”等夸大承诺
- [ ] 是否没有代写、代做、伪造项目或作弊暗示
- [ ] 是否没有泄露真实学生隐私
- [ ] 是否核对了学校、导师、项目信息准确性
- [ ] 是否检查标题、封面、正文、标签一致
- [ ] 是否确认最终发布由人工完成
"""


def build_publish_package(
    reviewed_file: str | Path,
    config: dict[str, Any],
    score: dict[str, Any] | None = None,
) -> PackageResult:
    reviewed_path = Path(reviewed_file)
    if not reviewed_path.is_absolute():
        reviewed_path = PROJECT_ROOT / reviewed_path
    markdown = read_text(reviewed_path)
    meta = extract_front_matter(markdown)
    idea_id = meta.get("idea_id", reviewed_path.stem)
    package_dir = output_path(config, "package_dir", "content/packages")
    package_path = package_dir / f"{current_date_str()}_{idea_id}_publish_package.md"
    write_text(package_path, build_package_markdown(markdown, score=score))
    return PackageResult(package_path=package_path)

