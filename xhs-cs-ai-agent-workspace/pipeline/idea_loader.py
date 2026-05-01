from __future__ import annotations

from pathlib import Path
from typing import Any

from clients.client_factory import AppClients, create_clients
from utils import load_config

from . import PROJECT_ROOT


def load_pipeline_config(config_path: str = "config.yaml") -> dict[str, Any]:
    path = Path(config_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return load_config(path)


def create_pipeline_clients(config: dict[str, Any], dry_run: bool) -> AppClients:
    return create_clients(config, dry_run=dry_run)


def load_idea(clients: AppClients, idea_id: str) -> dict[str, Any]:
    return clients.content_store.get_idea_by_id(idea_id)


def list_pending_ideas(clients: AppClients, limit: int) -> list[dict[str, Any]]:
    return clients.content_store.list_pending_ideas(limit)

