from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from clients.client_factory import AppClients
from utils import current_date_str, write_text

from .writer import output_path


@dataclass
class WeeklyResult:
    report_path: Path


def safe_rate(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def enrich_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for record in records:
        views = int(record.get("views", 0) or 0)
        item = dict(record)
        item["favorite_rate"] = safe_rate(record.get("favorites", 0), views)
        item["comment_rate"] = safe_rate(record.get("comments", 0), views)
        item["dm_rate"] = safe_rate(record.get("dm_count", 0), views)
        item["follow_rate"] = safe_rate(record.get("follows", 0), views)
        enriched.append(item)
    return enriched


def build_rule_based_report(records: list[dict[str, Any]]) -> str:
    enriched = enrich_records(records)
    total_views = sum(int(item.get("views", 0) or 0) for item in enriched)
    total_likes = sum(int(item.get("likes", 0) or 0) for item in enriched)
    total_favorites = sum(int(item.get("favorites", 0) or 0) for item in enriched)
    total_comments = sum(int(item.get("comments", 0) or 0) for item in enriched)
    total_dm = sum(int(item.get("dm_count", 0) or 0) for item in enriched)
    total_follows = sum(int(item.get("follows", 0) or 0) for item in enriched)
    best = max(enriched, key=lambda item: (item["favorite_rate"], item.get("views", 0)), default={})
    weak = min(enriched, key=lambda item: (item["favorite_rate"], item.get("views", 0)), default={})
    avg_favorite_rate = mean([item["favorite_rate"] for item in enriched]) if enriched else 0.0

    return f"""# 小红书内容周复盘 - {current_date_str()}

## 数据总览

- 发布数量：{len(enriched)}
- 总阅读量：{total_views}
- 总点赞数：{total_likes}
- 总收藏数：{total_favorites}
- 总评论数：{total_comments}
- 总私信数：{total_dm}
- 总关注数：{total_follows}
- 整体收藏率：{percent(safe_rate(total_favorites, total_views))}
- 整体评论率：{percent(safe_rate(total_comments, total_views))}
- 整体私信率：{percent(safe_rate(total_dm, total_views))}
- 整体转粉率：{percent(safe_rate(total_follows, total_views))}

## 表现最好的内容

- 标题：{best.get("title", "暂无")}
- 阅读量：{best.get("views", 0)}
- 收藏率：{percent(best.get("favorite_rate", 0.0))}
- 判断：模板、Prompt、可复制步骤类内容更容易被收藏。

## 表现较弱的内容

- 标题：{weak.get("title", "暂无")}
- 阅读量：{weak.get("views", 0)}
- 收藏率：{percent(weak.get("favorite_rate", 0.0))}
- 判断：如果标题偏泛或用户不能立刻照着做，收藏率容易低于平均值 {percent(avg_favorite_rate)}。

## 收藏率分析

收藏率高的内容通常提供明确模板、步骤或 Prompt。下周继续优先做“项目介绍模板”“导师追问 Prompt”“专业课问答清单”。

## 评论率分析

评论更容易出现在能让用户代入自身情况的内容里。标题和结尾可以引导用户留下项目关键词、复试专业方向或最担心的问题。

## 私信率分析

私信更可能来自诊断需求强的选题，例如项目介绍、自我介绍、跨考短板。表达要保持克制，只引导用户整理材料，不承诺结果。

## 转粉率分析

转粉来自稳定的人设和连续主题。建议把“复试项目准备”做成系列，不要每篇都换方向。

## 下周内容建议

- 继续写：项目介绍、AI 模拟追问、英文问答、专业课短期复盘；
- 减少写：只有情绪安慰、缺少模板和 Prompt 的泛经验；
- 每篇至少沉淀一个可复用模板。

## 下周 10 个新选题建议

1. 复试项目介绍 60 秒版本怎么准备？
2. 计算机复试被问数据库索引怎么答？
3. 计网 TCP 三次握手如何讲得像人话？
4. 操作系统进程线程怎么准备追问？
5. 跨考学生如何解释项目经历不足？
6. 英文问答如何避免背诵感？
7. 用 AI 把简历项目变成导师追问清单
8. 没有竞赛和论文，复试怎么讲优势？
9. 复试前一天应该检查哪 10 件事？
10. 项目难点不会讲，如何从代码里提炼？
"""


def generate_weekly_review(
    clients: AppClients,
    config: dict[str, Any],
) -> WeeklyResult:
    records = clients.content_store.get_published_records()
    report = build_rule_based_report(records)
    weekly_dir = output_path(config, "weekly_report_dir", "reports/weekly")
    report_path = weekly_dir / f"{current_date_str()}_weekly_review.md"
    write_text(report_path, report)
    return WeeklyResult(report_path=report_path)

