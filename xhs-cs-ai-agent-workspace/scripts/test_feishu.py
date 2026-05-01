import argparse

from clients.feishu_client import FeishuContentStore
from utils import cli_error, load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="测试飞书连接")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--idea-id", default="001", help="仅读取测试用 idea_id")
    args = parser.parse_args()

    config = load_config(args.config)
    store = FeishuContentStore(config)
    idea = store.get_idea_by_id(args.idea_id)
    print(f"飞书连接成功，读取到选题：{idea.get('idea_id')} - {idea.get('theme')}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        cli_error(exc)
