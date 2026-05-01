import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table


PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from clients.client_factory import create_clients  # noqa: E402
from services.health_service import run_smoke_tests  # noqa: E402
from services.pipeline_service import generate_and_review  # noqa: E402
from services.weekly_service import generate_weekly_review  # noqa: E402
from utils import extract_front_matter, load_config, read_text  # noqa: E402


cli = typer.Typer(add_completion=False)
console = Console()


def ask_dry_run() -> bool:
    return Confirm.ask("是否使用 dry-run（不调用真实 API）？", default=True)


def print_menu() -> None:
    console.print(
        Panel.fit(
            "\n".join(
                [
                    "[bold]1.[/] 生成并质检一篇内容",
                    "[bold]2.[/] 批量生成本周内容",
                    "[bold]3.[/] 查看发布包 / 待人工审核内容",
                    "[bold]4.[/] 生成周复盘",
                    "[bold]5.[/] 运行项目健康检查",
                    "[bold]6.[/] 测试飞书连接",
                    "[bold]7.[/] 测试大模型连接",
                    "[bold]0.[/] 退出",
                ]
            ),
            title="小红书计算机复试 AI 内容 Agent 工作台",
            border_style="cyan",
        )
    )


def show_pipeline_result(result) -> None:
    console.print("[green]生成并质检完成[/green]")
    console.print(f"Draft: [bold cyan]{result.generate.draft_path}[/bold cyan]")
    if result.review.reviewed_path:
        console.print(f"Reviewed: [bold cyan]{result.review.reviewed_path}[/bold cyan]")
    else:
        console.print("[yellow]Reviewed: 质检未通过，未生成 reviewed 文件[/yellow]")
    console.print(f"Score: [bold cyan]{result.score.report_path}[/bold cyan]")
    if result.package:
        console.print(f"Package: [bold cyan]{result.package.package_path}[/bold cyan]")
    console.print(
        "质检结果："
        f"passed=[bold]{result.review.review.get('passed')}[/bold] "
        f"risk_level=[bold]{result.review.review.get('risk_level')}[/bold]"
    )


def generate_one() -> None:
    idea_id = Prompt.ask("请输入 idea_id", default="001").strip()
    dry_run = ask_dry_run()
    try:
        result = generate_and_review(idea_id, dry_run=dry_run)
        show_pipeline_result(result)
    except RuntimeError as exc:
        console.print(f"[red]失败：{exc}[/red]")


def batch_generate() -> None:
    limit = IntPrompt.ask("请输入生成数量 limit", default=3)
    dry_run = ask_dry_run()
    successes = []
    failures = []

    try:
        config = load_config(PROJECT_ROOT / "config.yaml")
        clients = create_clients(config, dry_run=dry_run)
        ideas = clients.content_store.list_pending_ideas(limit)
    except RuntimeError as exc:
        console.print(f"[red]读取待生成选题失败：{exc}[/red]")
        return

    if not ideas:
        console.print("[yellow]没有找到待生成选题。[/yellow]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("批量生成中", total=len(ideas))
        for idea in ideas:
            idea_id = str(idea.get("idea_id", ""))
            progress.update(task, description=f"处理 idea_id={idea_id}")
            try:
                successes.append(generate_and_review(idea_id, dry_run=dry_run))
            except RuntimeError as exc:
                failures.append((idea_id or "unknown", str(exc)))
            progress.advance(task)

    table = Table(title="批量生成结果")
    table.add_column("状态")
    table.add_column("idea_id")
    table.add_column("路径/原因")
    for item in successes:
        table.add_row(
            "[green]成功[/green]",
            item.generate.idea_id,
            str(item.review.reviewed_path or item.generate.draft_path),
        )
    for idea_id, reason in failures:
        table.add_row("[red]失败[/red]", idea_id, reason)
    console.print(table)


def list_reviewed() -> None:
    reviewed_dir = PROJECT_ROOT / "content/reviewed"
    package_dir = PROJECT_ROOT / "content/packages"
    files = sorted(reviewed_dir.glob("*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    table = Table(title="发布包 / 待人工审核内容")
    table.add_column("文件名", style="cyan")
    table.add_column("idea_id")
    table.add_column("post_id")
    table.add_column("创建时间")
    table.add_column("状态")
    table.add_column("发布包")

    for file_path in files:
        meta = extract_front_matter(read_text(file_path))
        idea_id = meta.get("idea_id", "")
        packages = sorted(package_dir.glob(f"*_{idea_id}_publish_package.md"))
        package_name = packages[-1].name if packages else ""
        table.add_row(
            file_path.name,
            idea_id,
            meta.get("post_id", ""),
            meta.get("created_at", ""),
            meta.get("status", ""),
            package_name,
        )

    console.print(table)
    console.print(
        f"请打开 [bold cyan]{package_dir}[/bold cyan] 中的发布包，人工审核后再手动发布。"
    )


def weekly_review() -> None:
    dry_run = ask_dry_run()
    try:
        result = generate_weekly_review(dry_run=dry_run)
        console.print(f"[green]周复盘已生成：[/green][bold cyan]{result.report_path}[/bold cyan]")
    except RuntimeError as exc:
        console.print(f"[red]失败：{exc}[/red]")


def health_check() -> None:
    result = run_smoke_tests()
    if result.passed:
        console.print("[green]项目健康检查通过[/green]")
    else:
        console.print("[red]项目健康检查失败[/red]")
    console.print(result.output.replace("\ufffd", "?"))


def run_script(script_name: str) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script_name)],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode == 0:
        console.print("[green]测试通过[/green]")
        console.print(result.stdout.strip().replace("\ufffd", "?"))
    else:
        console.print("[red]测试失败[/red]")
        console.print((result.stdout + "\n" + result.stderr).strip().replace("\ufffd", "?"))


def interactive_loop() -> None:
    while True:
        print_menu()
        choice = Prompt.ask("请选择操作", choices=["1", "2", "3", "4", "5", "6", "7", "0"])
        if choice == "1":
            generate_one()
        elif choice == "2":
            batch_generate()
        elif choice == "3":
            list_reviewed()
        elif choice == "4":
            weekly_review()
        elif choice == "5":
            health_check()
        elif choice == "6":
            run_script("test_feishu.py")
        elif choice == "7":
            run_script("test_llm.py")
        elif choice == "0":
            console.print("[green]已退出。[/green]")
            break


@cli.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        interactive_loop()


if __name__ == "__main__":
    cli()
