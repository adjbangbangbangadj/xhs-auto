import argparse

from clients.llm_client import OpenAICompatibleLLMClient
from utils import cli_error, load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="测试大模型连接")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    args = parser.parse_args()

    config = load_config(args.config)
    llm = OpenAICompatibleLLMClient(config)
    content = llm.chat(
        [
            {
                "role": "user",
                "content": "请只回复：LLM_CONNECTION_OK",
            }
        ]
    )
    print(f"大模型连接成功，返回：{content.strip()}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        cli_error(exc)
