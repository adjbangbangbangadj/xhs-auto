import argparse

from services.review_service import review_post
from utils import cli_error


def main() -> None:
    parser = argparse.ArgumentParser(description="质检小红书草稿")
    parser.add_argument("--file", required=True, help="待质检 Markdown 文件")
    parser.add_argument("--dry-run", action="store_true", help="使用 mock LLM")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    args = parser.parse_args()

    result = review_post(args.file, dry_run=args.dry_run, config_path=args.config)
    print(f"质检报告：{result.report_path}")
    print(
        f"质检结果：passed={result.review.get('passed')} "
        f"risk_level={result.review.get('risk_level')}"
    )
    if result.reviewed_path:
        print(f"已复制到 reviewed：{result.reviewed_path}")
    else:
        print("未复制到 reviewed：质检未通过或需要先修改。")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        cli_error(exc)
