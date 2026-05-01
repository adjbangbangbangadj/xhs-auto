import argparse
from pathlib import Path

from services.pipeline_service import generate_post
from utils import cli_error


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="生成小红书草稿")
    parser.add_argument("--idea-id", required=True, help="选题 ID，例如 001")
    parser.add_argument("--dry-run", action="store_true", help="使用 mock 数据和 mock LLM")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    args = parser.parse_args()

    result = generate_post(args.idea_id, dry_run=args.dry_run, config_path=args.config)
    next_command = (
        f"python scripts/review_post.py --file "
        f"{result.draft_path.relative_to(PROJECT_ROOT)} "
        f"{'--dry-run' if args.dry_run else ''}"
    ).strip()
    print(f"已生成草稿：{result.draft_path}")
    print(f"下一步：{next_command}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        cli_error(exc)
