import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

import requests
import yaml

from clients.feishu_client import FeishuContentStore
from utils import cli_error, load_config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")


def project_path(path: str | Path) -> Path:
    target = Path(path)
    if target.is_absolute():
        return target
    return PROJECT_ROOT / target


def load_project_config(path: str | Path) -> dict[str, Any]:
    return load_config(project_path(path))


def write_project_config(path: str | Path, config: dict[str, Any]) -> Path:
    target = project_path(path)
    target.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return target


def feishu_config(config: dict[str, Any]) -> dict[str, Any]:
    data = config.get("feishu", {})
    if not isinstance(data, dict):
        raise RuntimeError("config.yaml 中 feishu 配置格式不正确。")
    return data


def secret_env_name(config: dict[str, Any]) -> str:
    return str(feishu_config(config).get("app_secret_env", "FEISHU_APP_SECRET"))


def validate_feishu_auth_config(config: dict[str, Any]) -> str:
    feishu = feishu_config(config)
    secret_env = secret_env_name(config)

    if not feishu.get("enabled", False):
        raise RuntimeError(
            "feishu.enabled=false，当前无法执行飞书只读测试。\n"
            "请在 config.yaml 中启用 feishu.enabled=true；\n"
            "请填写 feishu.app_id、feishu.app_token、feishu.table_ids.ideas；\n"
            f"请设置 {secret_env} 环境变量。"
        )

    app_id = feishu.get("app_id")
    if not app_id or app_id == "your_feishu_app_id":
        raise RuntimeError("缺少 feishu.app_id，请在 config.yaml 中填写飞书应用 app_id。")

    if not os.getenv(secret_env):
        raise RuntimeError(
            f"缺少 {secret_env} 环境变量。\n"
            f"请先设置 {secret_env}，不要把 app secret 写入 config.yaml 或提交到 Git。"
        )

    return secret_env


def validate_readonly_config(config: dict[str, Any]) -> str:
    secret_env = validate_feishu_auth_config(config)
    feishu = feishu_config(config)
    missing = []

    if not feishu.get("app_token") or feishu.get("app_token") == "your_bitable_app_token":
        missing.append("feishu.app_token")

    table_ids = feishu.get("table_ids", {})
    ideas_table_id = table_ids.get("ideas") if isinstance(table_ids, dict) else None
    if not ideas_table_id or str(ideas_table_id).startswith("your_"):
        missing.append("feishu.table_ids.ideas")

    if missing:
        raise RuntimeError(
            "飞书只读测试配置不完整："
            + "、".join(missing)
            + "。\n请填写 app_id、app_token、table_ids.ideas，并确认 feishu.enabled=true。"
        )

    return secret_env


def parse_response(response: requests.Response, message: str) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"{message}：HTTP {response.status_code}，响应不是 JSON。") from exc
    if response.status_code >= 400 or payload.get("code", 0) != 0:
        raise RuntimeError(
            f"{message}：HTTP {response.status_code}，"
            f"code={payload.get('code')}，msg={payload.get('msg')}"
        )
    return payload.get("data", {})


def get_tenant_access_token(config: dict[str, Any]) -> str:
    feishu = feishu_config(config)
    secret_env = validate_feishu_auth_config(config)
    response = requests.post(
        f"{FEISHU_BASE_URL}/auth/v3/tenant_access_token/internal",
        json={"app_id": feishu.get("app_id"), "app_secret": os.getenv(secret_env)},
        timeout=20,
    )
    data = parse_response(response, "获取飞书 tenant_access_token 失败")
    token = data.get("tenant_access_token")
    if not token:
        raise RuntimeError("飞书返回中缺少 tenant_access_token。")
    return token


def auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }


def parse_wiki_token(wiki_url_or_token: str) -> str:
    value = wiki_url_or_token.strip()
    if not value:
        raise RuntimeError("wiki_url 为空，无法解析飞书 Wiki token。")
    match = re.search(r"/wiki/([^/?#]+)", value)
    if match:
        return match.group(1)
    return value


def resolve_wiki_bitable_app_token(wiki_url_or_token: str, token: str) -> str:
    wiki_token = parse_wiki_token(wiki_url_or_token)
    response = requests.get(
        f"{FEISHU_BASE_URL}/wiki/v2/spaces/get_node",
        headers=auth_headers(token),
        params={"token": wiki_token},
        timeout=20,
    )
    data = parse_response(response, "解析飞书 Wiki 节点失败")
    node = data.get("node") or data.get("space_node") or {}
    obj_type = str(node.get("obj_type") or "")
    obj_token = str(node.get("obj_token") or "")
    if not obj_token:
        raise RuntimeError("飞书 Wiki 节点响应中缺少 obj_token，无法得到多维表格 app_token。")
    if obj_type and obj_type not in {"bitable", "base"}:
        raise RuntimeError(f"该 Wiki 链接指向的对象类型是 {obj_type}，不是多维表格。")
    return obj_token


def list_bitable_tables(app_token: str, token: str) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    page_token = ""
    while True:
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token
        response = requests.get(
            f"{FEISHU_BASE_URL}/bitable/v1/apps/{app_token}/tables",
            headers=auth_headers(token),
            params=params,
            timeout=20,
        )
        data = parse_response(response, "读取飞书多维表格 table 列表失败")
        tables.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = str(data.get("page_token") or "")
        if not page_token:
            break
    return tables


def find_ideas_table(tables: list[dict[str, Any]], table_name: str) -> dict[str, Any] | None:
    for table in tables:
        if table.get("name") == table_name:
            return table
    for table in tables:
        if "选题" in str(table.get("name", "")):
            return table
    return None


def print_table_summary(tables: list[dict[str, Any]]) -> None:
    print("Feishu bitable tables:")
    for table in tables:
        print(f"- name={table.get('name')} table_id={table.get('table_id')}")


def resolve_from_wiki(
    config: dict[str, Any],
    config_path: str | Path,
    wiki_url: str,
    ideas_table_name: str,
    save_config: bool,
) -> tuple[str, str]:
    token = get_tenant_access_token(config)
    print("Tenant access token acquired")
    app_token = resolve_wiki_bitable_app_token(wiki_url, token)
    print(f"Resolved app_token: {app_token}")

    tables = list_bitable_tables(app_token, token)
    print_table_summary(tables)
    ideas_table = find_ideas_table(tables, ideas_table_name)
    if not ideas_table:
        raise RuntimeError(
            f"没有在该多维表格中找到“{ideas_table_name}”表。\n"
            "请确认飞书中存在“选题库”表，或通过 --ideas-table-name 指定真实表名。"
        )

    ideas_table_id = str(ideas_table.get("table_id"))
    print(f"Resolved ideas table: {ideas_table.get('name')} / {ideas_table_id}")

    if save_config:
        feishu = config.setdefault("feishu", {})
        feishu["app_token"] = app_token
        table_ids = feishu.setdefault("table_ids", {})
        table_ids["ideas"] = ideas_table_id
        path = write_project_config(config_path, config)
        print(f"Updated local config: {path}")

    print("FEISHU_RESOLVE_OK")
    return app_token, ideas_table_id


def format_value(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else "(empty)"


def print_idea_summary(idea: dict[str, Any]) -> None:
    fields = [
        "idea_id",
        "theme",
        "audience",
        "pain_point",
        "content_type",
        "priority",
        "status",
        "source",
        "notes",
        "_record_id",
    ]
    print("Feishu idea fields:")
    for field in fields:
        print(f"- {field}: {format_value(idea.get(field))}")


def read_idea(config: dict[str, Any], idea_id: str) -> None:
    secret_env = validate_readonly_config(config)
    store = FeishuContentStore(config, required_table_ids=("ideas",))
    try:
        idea = store.get_idea_by_id(idea_id)
    except RuntimeError as exc:
        message = str(exc)
        if f"idea_id={idea_id}" in message:
            raise RuntimeError(
                f"飞书“选题库”中找不到 idea_id={idea_id}。\n"
                f"请确认飞书“选题库”中存在 idea_id={idea_id}；\n"
                "请确认字段名和代码映射一致，例如 idea_id、选题、目标用户、痛点、内容类型、优先级、状态、来源、备注；\n"
                "请确认 config.yaml 中 feishu.table_ids.ideas 填写正确。"
            ) from exc
        raise

    print(f"Feishu app secret env: {secret_env} is configured")
    print_idea_summary(idea)
    print("FEISHU_READ_OK")


def main() -> None:
    configure_stdout()
    parser = argparse.ArgumentParser(
        description="Read-only Feishu test. Reads idea_id=001 from the ideas table only."
    )
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--idea-id", default="001", help="Read-only test idea_id")
    parser.add_argument(
        "--wiki-url",
        default="",
        help="Optional Feishu Wiki/Bitable URL used to resolve app_token and table_ids.ideas",
    )
    parser.add_argument(
        "--ideas-table-name",
        default="选题库",
        help="Feishu table name used as the ideas table when resolving from a wiki URL",
    )
    parser.add_argument(
        "--save-config",
        action="store_true",
        help="Update local config.yaml with resolved app_token and table_ids.ideas",
    )
    parser.add_argument(
        "--resolve-only",
        action="store_true",
        help="Only resolve app_token/table_id from --wiki-url; do not read idea_id",
    )
    args = parser.parse_args()

    config = load_project_config(args.config)

    if args.wiki_url:
        resolve_from_wiki(
            config=config,
            config_path=args.config,
            wiki_url=args.wiki_url,
            ideas_table_name=args.ideas_table_name,
            save_config=args.save_config,
        )
        if args.save_config:
            config = load_project_config(args.config)
        if args.resolve_only:
            return

    read_idea(config, args.idea_id)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        cli_error(exc)
