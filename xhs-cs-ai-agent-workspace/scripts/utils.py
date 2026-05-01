import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise RuntimeError(f"找不到配置文件：{config_path}")
    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"配置文件格式不正确：{config_path}")
    return data


def ensure_dir(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def read_text(path: str | Path) -> str:
    source = Path(path)
    if not source.exists():
        raise RuntimeError(f"找不到文本文件：{source}")
    return source.read_text(encoding="utf-8")


def write_text(path: str | Path, content: str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def write_json(path: str | Path, data: Any) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def read_json(path: str | Path) -> Any:
    source = Path(path)
    if not source.exists():
        raise RuntimeError(f"找不到 JSON 文件：{source}")
    return json.loads(source.read_text(encoding="utf-8"))


def slugify(text: str, max_length: int = 40) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.lower(), flags=re.UNICODE)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    if not cleaned:
        return "post"
    return cleaned[:max_length].strip("-") or "post"


def current_date_str() -> str:
    return date.today().isoformat()


def current_datetime_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def render_template(template: str, variables: dict[str, Any]) -> str:
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace("{{ " + key + " }}", str(value))
        rendered = rendered.replace("{{" + key + "}}", str(value))
    return rendered


def extract_title_from_markdown(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "未命名内容"


def extract_front_matter(markdown: str) -> dict[str, str]:
    if not markdown.startswith("---"):
        return {}
    parts = markdown.split("---", 2)
    if len(parts) < 3:
        return {}
    data = yaml.safe_load(parts[1]) or {}
    if not isinstance(data, dict):
        return {}
    return {str(key): "" if value is None else str(value) for key, value in data.items()}


def strip_front_matter(markdown: str) -> str:
    if not markdown.startswith("---"):
        return markdown
    parts = markdown.split("---", 2)
    if len(parts) < 3:
        return markdown
    return parts[2].lstrip()


def make_post_id(idea_id: str) -> str:
    return f"p{idea_id}"


def parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"质检模型没有返回合法 JSON：{exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("质检模型返回的 JSON 不是对象。")
    return data


def cli_error(exc: Exception) -> None:
    print(f"ERROR: {exc}", file=sys.stderr)
    raise SystemExit(1)
