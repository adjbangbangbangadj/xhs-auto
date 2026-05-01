import argparse

from services.weekly_service import generate_weekly_review
from utils import cli_error


def main() -> None:
    parser = argparse.ArgumentParser(description="生成小红书发布周复盘")
    parser.add_argument("--dry-run", action="store_true", help="使用 mock 发布数据")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    args = parser.parse_args()

    result = generate_weekly_review(dry_run=args.dry_run, config_path=args.config)
    print(f"已生成周复盘：{result.report_path}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        cli_error(exc)
