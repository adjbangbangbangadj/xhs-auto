import argparse
from pathlib import Path
from typing import Any

from clients.llm_client import OpenAICompatibleLLMClient
from utils import cli_error, load_config, read_json, read_text, render_template, write_text


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def project_path(path: str | Path) -> Path:
    target = Path(path)
    if target.is_absolute():
        return target
    return PROJECT_ROOT / target


def load_project_config(path: str | Path) -> dict[str, Any]:
    return load_config(project_path(path))


def load_local_idea(config: dict[str, Any], idea_id: str) -> dict[str, Any]:
    ideas_path = project_path(config.get("paths", {}).get("mock_ideas", "mock/ideas.json"))
    ideas = read_json(ideas_path)
    for idea in ideas:
        if str(idea.get("idea_id", "")).strip() == idea_id:
            return idea
    raise RuntimeError(f"Cannot find idea_id={idea_id} in {ideas_path}")


def build_generation_messages(idea: dict[str, Any]) -> list[dict[str, str]]:
    prompt = read_text(PROJECT_ROOT / "prompts/generate_post.md")
    variables = {
        "idea_id": idea.get("idea_id", ""),
        "theme": idea.get("theme", ""),
        "audience": idea.get("audience", ""),
        "pain_point": idea.get("pain_point", ""),
        "content_type": idea.get("content_type", ""),
        "positioning": read_text(PROJECT_ROOT / "rules/positioning.md"),
        "xhs_style": read_text(PROJECT_ROOT / "rules/xhs_style.md"),
        "compliance": read_text(PROJECT_ROOT / "rules/compliance.md"),
    }
    return [{"role": "user", "content": render_template(prompt, variables)}]


def run_ping(llm: OpenAICompatibleLLMClient) -> None:
    content = llm.chat(
        [
            {
                "role": "user",
                "content": "Reply with exactly: LLM_CONNECTION_OK",
            }
        ]
    )
    print(f"LLM ping succeeded: {content.strip()}")


def run_generation(
    llm: OpenAICompatibleLLMClient,
    config: dict[str, Any],
    idea_id: str,
    output: str | None,
    preview_chars: int,
) -> None:
    idea = load_local_idea(config, idea_id)
    content = llm.chat(build_generation_messages(idea))
    stripped = content.strip()
    if not stripped:
        raise RuntimeError("LLM returned empty generated content.")

    print("LLM generation succeeded")
    print(f"idea_id: {idea_id}")
    print(f"characters: {len(stripped)}")

    if output:
        output_path = project_path(output)
        write_text(output_path, stripped + "\n")
        print(f"output: {output_path}")

    print("preview:")
    print(stripped[:preview_chars])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test the real LLM only. This script does not read or write Feishu."
    )
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument(
        "--mode",
        choices=["ping", "generate"],
        default="ping",
        help="ping checks connectivity; generate asks the LLM to draft content from local mock data",
    )
    parser.add_argument("--idea-id", default="001", help="Local mock idea id for generate mode")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional local output path for generated Markdown; Feishu is never written",
    )
    parser.add_argument(
        "--preview-chars",
        type=int,
        default=1200,
        help="Number of generated characters to print as a preview",
    )
    args = parser.parse_args()

    config = load_project_config(args.config)
    llm = OpenAICompatibleLLMClient(config)

    if args.mode == "ping":
        run_ping(llm)
    else:
        run_generation(
            llm=llm,
            config=config,
            idea_id=args.idea_id,
            output=args.output,
            preview_chars=args.preview_chars,
        )


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        cli_error(exc)
