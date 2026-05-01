from dataclasses import dataclass
from pathlib import Path
from typing import Any

from clients.base import ContentStoreProtocol, LLMClientProtocol
from clients.mock_client import MockContentStore, MockLLMClient


@dataclass
class AppClients:
    llm: LLMClientProtocol
    content_store: ContentStoreProtocol


def create_clients(config: dict[str, Any], dry_run: bool) -> AppClients:
    project_root = Path(__file__).resolve().parents[2]
    if dry_run:
        return AppClients(
            llm=MockLLMClient(config),
            content_store=MockContentStore(config, project_root),
        )

    feishu_config = config.get("feishu", {})
    if not feishu_config.get("enabled", False):
        raise RuntimeError(
            "当前是非 dry-run 模式，但 feishu.enabled=false。"
            "请启用飞书配置，或添加 --dry-run 使用本地模拟数据。"
        )

    from clients.feishu_client import FeishuContentStore
    from clients.llm_client import OpenAICompatibleLLMClient

    return AppClients(
        llm=OpenAICompatibleLLMClient(config),
        content_store=FeishuContentStore(config),
    )
