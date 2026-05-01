from __future__ import annotations

import argparse
import sys

from utils import cli_error

from .runner import run_batch, run_single, run_weekly_review


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Content Factory Pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="生成、质检、评分并打包单篇内容")
    run_parser.add_argument("--idea-id", required=True, help="选题 ID，例如 001")
    run_parser.add_argument("--dry-run", action="store_true", help="使用 mock 数据和规则评分")
    run_parser.add_argument("--config", default="config.yaml", help="配置文件路径")

    batch_parser = subparsers.add_parser("batch", help="批量执行完整内容流水线")
    batch_parser.add_argument("--limit", type=int, default=3, help="最多处理几条待生成选题")
    batch_parser.add_argument("--dry-run", action="store_true", help="使用 mock 数据和规则评分")
    batch_parser.add_argument("--config", default="config.yaml", help="配置文件路径")

    weekly_parser = subparsers.add_parser("weekly-review", help="生成周复盘")
    weekly_parser.add_argument("--dry-run", action="store_true", help="使用 mock 发布数据")
    weekly_parser.add_argument("--config", default="config.yaml", help="配置文件路径")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "run":
            result = run_single(args.idea_id, dry_run=args.dry_run, config_path=args.config)
            print(f"draft: {result.generate.draft_path}")
            print(f"review: {result.review.report_path}")
            print(f"score: {result.score.report_path}")
            print(f"reviewed: {result.review.reviewed_path or ''}")
            print(f"package: {result.package.package_path if result.package else ''}")
            print("PIPELINE RUN PASSED")
        elif args.command == "batch":
            result = run_batch(args.limit, dry_run=args.dry_run, config_path=args.config)
            for item in result.successes:
                print(
                    "success: "
                    f"{item.generate.idea_id} "
                    f"draft={item.generate.draft_path} "
                    f"score={item.score.report_path} "
                    f"package={item.package.package_path if item.package else ''}"
                )
            for idea_id, reason in result.failures:
                print(f"failure: {idea_id} reason={reason}")
            print(
                f"PIPELINE BATCH FINISHED success={len(result.successes)} "
                f"failure={len(result.failures)}"
            )
        elif args.command == "weekly-review":
            result = run_weekly_review(dry_run=args.dry_run, config_path=args.config)
            print(f"weekly: {result.report_path}")
            print("PIPELINE WEEKLY REVIEW PASSED")
        else:
            parser.print_help()
            raise SystemExit(2)
    except RuntimeError as exc:
        cli_error(exc)


if __name__ == "__main__":
    main(sys.argv[1:])

