import json
from pathlib import Path
from typing import Any


class MockLLMClient:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def chat(self, messages: list[dict[str, str]]) -> str:
        text = "\n".join(message.get("content", "") for message in messages)
        if "只输出 JSON" in text or "质检" in text:
            return json.dumps(
                {
                    "passed": True,
                    "risk_level": "low",
                    "issues": [],
                    "suggested_fixes": ["人工发布前再核对学校、导师和个人经历是否准确。"],
                    "final_comment": "dry-run 模拟质检通过：内容具体、无夸大承诺，仍建议人工复核。",
                    "needs_human_review": True,
                },
                ensure_ascii=False,
                indent=2,
            )

        theme = self._extract_field(text, "theme") or "计算机复试准备"
        audience = self._extract_field(text, "audience") or "复试学生"
        pain_point = self._extract_field(text, "pain_point") or "不知道如何准备"
        content_type = self._extract_field(text, "content_type") or "方法论"
        return f"""# {theme}

## 标题备选 3 个

1. {theme}，别再写成流水账了
2. 复试前把这个问题准备到能追问
3. 我会这样帮{audience}梳理这个复试问题

## 封面文案

{theme}
一页讲清楚准备思路

## 正文

很多同学卡在这里，不是完全不会，而是准备方式太散。典型痛点是：{pain_point}

我建议按 4 步准备：

1. 先写真实经历，不要一上来追求漂亮表达。
2. 把内容拆成“背景、动作、难点、复盘”四块。
3. 每块准备 1 个老师可能追问的问题。
4. 用 AI 做两轮模拟追问，再把答不上来的地方补成笔记。

一个可直接套用的小模板：

- 背景：我为什么做这件事？
- 动作：我具体负责了哪一部分？
- 难点：过程中遇到的技术或表达问题是什么？
- 复盘：如果重做一次，我会怎么改？

这个方法适合{content_type}类内容，重点不是包装，而是把真实经历讲清楚。

## 标签

#计算机复试 #考研复试 #项目介绍 #AI学习 #面试准备

## 评论区引导

如果你愿意，可以在评论区写下你的项目关键词，我可以用公开信息的角度帮你拆一下准备方向。

## 私信回复建议

可以先让对方发“项目背景、自己负责的部分、最担心被问的问题”三项，再判断是否适合做进一步诊断。

## 可复制 AI Prompt

```text
你现在扮演计算机复试导师。我的准备主题是：{theme}。
我的目标用户/场景是：{audience}。
请你按“背景、动作、难点、复盘”四个维度追问我，每次只问一个问题。
如果我的回答空泛，请指出具体缺口，并给我一个更清楚的回答结构。
不要替我编造经历。
```

## 适合沉淀到资料包的片段

“背景、动作、难点、复盘”四段式可以沉淀为项目介绍和自我介绍的通用准备模板。

## 适合 1v1 诊断服务的转化点

适合引导用户整理自己的项目材料，并做一次真实追问模拟，重点检查表达是否具体、边界是否诚实。
"""

    @staticmethod
    def _extract_field(text: str, field_name: str) -> str:
        prefix = f"- {field_name}:"
        for line in text.splitlines():
            if line.strip().startswith(prefix):
                return line.split(":", 1)[1].strip()
        return ""


class MockContentStore:
    def __init__(self, config: dict[str, Any], project_root: Path) -> None:
        self.config = config
        self.project_root = project_root
        paths = config.get("paths", {})
        self.ideas_path = project_root / paths.get("mock_ideas", "mock/ideas.json")
        self.content_records_path = project_root / paths.get(
            "mock_content_records", "mock/content_records.json"
        )
        self.published_records_path = project_root / paths.get(
            "mock_published_records", "mock/published_records.json"
        )

    def get_idea_by_id(self, idea_id: str) -> dict[str, Any]:
        ideas = self._read_json(self.ideas_path)
        for idea in ideas:
            if idea.get("idea_id") == idea_id:
                return idea
        raise RuntimeError(f"mock/ideas.json 中找不到 idea_id={idea_id} 的选题。")

    def list_pending_ideas(self, limit: int) -> list[dict[str, Any]]:
        ideas = self._read_json(self.ideas_path)
        pending = [
            idea for idea in ideas if str(idea.get("status", "")).strip() in {"待生成", ""}
        ]
        pending.sort(
            key=lambda idea: (
                -int(idea.get("priority", 0) or 0),
                str(idea.get("idea_id", "")),
            )
        )
        return pending[:limit]

    def create_content_record(self, record: dict[str, Any]) -> dict[str, Any]:
        records = self._read_json(self.content_records_path)
        records.append(record)
        self._write_json(self.content_records_path, records)
        print(f"[dry-run] 已模拟创建内容记录：{record.get('post_id')}")
        return record

    def update_idea_status(self, idea_id: str, status: str) -> None:
        print(f"[dry-run] 已模拟更新选题 {idea_id} 状态为：{status}")

    def update_content_review(self, post_id: str, review: dict[str, Any]) -> None:
        print(
            f"[dry-run] 已模拟回写内容 {post_id} 质检结果："
            f"{review.get('risk_level')} / passed={review.get('passed')}"
        )

    def get_published_records(self) -> list[dict[str, Any]]:
        return self._read_json(self.published_records_path)

    @staticmethod
    def _read_json(path: Path) -> Any:
        if not path.exists():
            raise RuntimeError(f"找不到 mock 文件：{path}")
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
