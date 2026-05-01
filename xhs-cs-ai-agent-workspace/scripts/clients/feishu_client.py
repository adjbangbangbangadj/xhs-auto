import os
from typing import Any

import requests


class FeishuContentStore:
    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self, config: dict[str, Any]) -> None:
        feishu_config = config.get("feishu", {})
        if not feishu_config.get("enabled", False):
            raise RuntimeError("feishu.enabled=false，请启用飞书配置或使用 --dry-run。")

        self.app_id = feishu_config.get("app_id")
        secret_env = feishu_config.get("app_secret_env", "FEISHU_APP_SECRET")
        self.app_secret = os.getenv(secret_env)
        self.app_token = feishu_config.get("app_token")
        self.table_ids = feishu_config.get("table_ids", {})
        self._tenant_access_token: str | None = None

        missing = []
        if not self.app_id or self.app_id == "your_feishu_app_id":
            missing.append("feishu.app_id")
        if not self.app_secret:
            missing.append(f"环境变量 {secret_env}")
        if not self.app_token or self.app_token == "your_bitable_app_token":
            missing.append("feishu.app_token")
        for key in ("ideas", "contents", "publishing"):
            if not self.table_ids.get(key) or str(self.table_ids.get(key)).startswith("your_"):
                missing.append(f"feishu.table_ids.{key}")
        if missing:
            raise RuntimeError("飞书配置不完整：" + "、".join(missing))

    def get_idea_by_id(self, idea_id: str) -> dict[str, Any]:
        records = self._list_records("ideas", filter_formula=f'CurrentValue.[idea_id] = "{idea_id}"')
        if not records:
            raise RuntimeError(f"飞书选题库中找不到 idea_id={idea_id} 的记录。")
        return self._normalize_idea(records[0])

    def list_pending_ideas(self, limit: int) -> list[dict[str, Any]]:
        records = self._list_records("ideas", filter_formula='CurrentValue.[状态] = "待生成"')
        ideas = [self._normalize_idea(record) for record in records]
        ideas.sort(
            key=lambda idea: (
                -int(idea.get("priority", 0) or 0),
                str(idea.get("idea_id", "")),
            )
        )
        return ideas[:limit]

    def _normalize_idea(self, record: dict[str, Any]) -> dict[str, Any]:
        fields = record.get("fields", {})
        return {
            "idea_id": fields.get("idea_id", ""),
            "theme": fields.get("选题", ""),
            "audience": self._single_select_value(fields.get("目标用户")),
            "pain_point": fields.get("痛点", ""),
            "content_type": self._single_select_value(fields.get("内容类型")),
            "priority": fields.get("优先级", 0),
            "status": self._single_select_value(fields.get("状态")),
            "source": self._single_select_value(fields.get("来源")),
            "notes": fields.get("备注", ""),
            "_record_id": record.get("record_id"),
        }

    def create_content_record(self, record: dict[str, Any]) -> dict[str, Any]:
        fields = {
            "post_id": record.get("post_id"),
            "idea_id": record.get("idea_id"),
            "标题": record.get("title"),
            "标题备选": record.get("title_options", ""),
            "封面文案": record.get("cover_text", ""),
            "正文文件路径": record.get("markdown_path"),
            "质检报告路径": record.get("review_report_path", ""),
            "风险等级": record.get("risk_level", "low"),
            "质检状态": record.get("review_status", "未质检"),
            "状态": record.get("status", "草稿"),
            "创建时间": record.get("created_at"),
            "更新时间": record.get("updated_at"),
        }
        data = self._create_record("contents", fields)
        return {"record_id": data.get("record", {}).get("record_id"), **record}

    def update_idea_status(self, idea_id: str, status: str) -> None:
        idea = self.get_idea_by_id(idea_id)
        record_id = idea.get("_record_id")
        if not record_id:
            raise RuntimeError(f"无法更新选题状态：未找到 idea_id={idea_id} 的 record_id。")
        self._update_record("ideas", record_id, {"状态": status})

    def update_content_review(self, post_id: str, review: dict[str, Any]) -> None:
        records = self._list_records(
            "contents", filter_formula=f'CurrentValue.[post_id] = "{post_id}"'
        )
        if not records:
            raise RuntimeError(f"飞书内容库中找不到 post_id={post_id} 的记录。")
        status = "通过" if review.get("passed") else "需修改"
        content_status = "已质检" if review.get("passed") else "草稿"
        self._update_record(
            "contents",
            records[0]["record_id"],
            {
                "风险等级": review.get("risk_level", "medium"),
                "质检状态": status,
                "状态": content_status,
            },
        )

    def get_published_records(self) -> list[dict[str, Any]]:
        records = self._list_records("publishing")
        normalized = []
        for item in records:
            fields = item.get("fields", {})
            normalized.append(
                {
                    "post_id": fields.get("post_id", ""),
                    "title": fields.get("标题", ""),
                    "published_at": fields.get("发布时间", ""),
                    "platform": self._single_select_value(fields.get("发布平台")),
                    "url": fields.get("小红书链接", {}).get("link", "")
                    if isinstance(fields.get("小红书链接"), dict)
                    else fields.get("小红书链接", ""),
                    "views": int(fields.get("阅读量", 0) or 0),
                    "likes": int(fields.get("点赞数", 0) or 0),
                    "favorites": int(fields.get("收藏数", 0) or 0),
                    "comments": int(fields.get("评论数", 0) or 0),
                    "follows": int(fields.get("关注数", 0) or 0),
                    "dm_count": int(fields.get("私信数", 0) or 0),
                    "notes": fields.get("复盘备注", ""),
                }
            )
        return normalized

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_tenant_access_token()}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _get_tenant_access_token(self) -> str:
        if self._tenant_access_token:
            return self._tenant_access_token
        url = f"{self.BASE_URL}/auth/v3/tenant_access_token/internal"
        response = requests.post(
            url,
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=20,
        )
        data = self._parse_response(response, "获取飞书 tenant_access_token 失败")
        token = data.get("tenant_access_token")
        if not token:
            raise RuntimeError("飞书返回中缺少 tenant_access_token。")
        self._tenant_access_token = token
        return token

    def _list_records(
        self, table_key: str, filter_formula: str | None = None
    ) -> list[dict[str, Any]]:
        table_id = self.table_ids[table_key]
        url = f"{self.BASE_URL}/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/search"
        payload: dict[str, Any] = {"page_size": 100}
        if filter_formula:
            payload["filter"] = {"conjunction": "and", "conditions": []}
            payload["automatic_fields"] = False
            payload["filter_formula"] = filter_formula
        response = requests.post(url, headers=self._headers(), json=payload, timeout=20)
        data = self._parse_response(response, f"读取飞书表 {table_key} 失败")
        return data.get("items", [])

    def _create_record(self, table_key: str, fields: dict[str, Any]) -> dict[str, Any]:
        table_id = self.table_ids[table_key]
        url = f"{self.BASE_URL}/bitable/v1/apps/{self.app_token}/tables/{table_id}/records"
        response = requests.post(
            url, headers=self._headers(), json={"fields": fields}, timeout=20
        )
        return self._parse_response(response, f"创建飞书表 {table_key} 记录失败")

    def _update_record(self, table_key: str, record_id: str, fields: dict[str, Any]) -> None:
        table_id = self.table_ids[table_key]
        url = (
            f"{self.BASE_URL}/bitable/v1/apps/{self.app_token}/tables/"
            f"{table_id}/records/{record_id}"
        )
        response = requests.put(
            url, headers=self._headers(), json={"fields": fields}, timeout=20
        )
        self._parse_response(response, f"更新飞书表 {table_key} 记录失败")

    @staticmethod
    def _parse_response(response: requests.Response, message: str) -> dict[str, Any]:
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

    @staticmethod
    def _single_select_value(value: Any) -> str:
        if isinstance(value, dict):
            return str(value.get("text") or value.get("name") or value.get("value") or "")
        return str(value or "")
