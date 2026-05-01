from typing import Any, Protocol


class LLMClientProtocol(Protocol):
    def chat(self, messages: list[dict[str, str]]) -> str:
        ...


class ContentStoreProtocol(Protocol):
    def get_idea_by_id(self, idea_id: str) -> dict[str, Any]:
        ...

    def list_pending_ideas(self, limit: int) -> list[dict[str, Any]]:
        ...

    def create_content_record(self, record: dict[str, Any]) -> dict[str, Any]:
        ...

    def update_idea_status(self, idea_id: str, status: str) -> None:
        ...

    def update_content_review(self, post_id: str, review: dict[str, Any]) -> None:
        ...

    def get_published_records(self) -> list[dict[str, Any]]:
        ...
