import os
from typing import Any


class OpenAICompatibleLLMClient:
    def __init__(self, config: dict[str, Any]) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "缺少 openai SDK。请先运行 pip install -r requirements.txt，"
                "或使用 --dry-run 跑本地模拟流程。"
            ) from exc

        llm_config = config.get("llm", {})
        api_key_env = llm_config.get("api_key_env", "LLM_API_KEY")
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise RuntimeError(
                f"缺少大模型 API key：请先设置环境变量 {api_key_env}，"
                "或使用 --dry-run 跑本地模拟流程。"
            )

        self.model = llm_config.get("model", "gpt-4.1-mini")
        self.temperature = float(llm_config.get("temperature", 0.7))
        self.max_tokens = int(llm_config.get("max_tokens", 3000))
        self.client = OpenAI(
            api_key=api_key,
            base_url=llm_config.get("base_url", "https://api.openai.com/v1"),
        )

    def chat(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("大模型返回了空内容，请检查模型配置或重试。")
        return content
