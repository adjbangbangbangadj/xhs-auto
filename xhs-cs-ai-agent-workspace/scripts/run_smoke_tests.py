import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SmokeTestError(RuntimeError):
    pass


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise SmokeTestError(
            "Command failed: "
            + " ".join([sys.executable, *args])
            + "\nSTDOUT:\n"
            + result.stdout
            + "\nSTDERR:\n"
            + result.stderr
        )
    return result


def newest_file(directory: Path, pattern: str) -> Path:
    files = list(directory.glob(pattern))
    if not files:
        raise SmokeTestError(f"No files matched {directory / pattern}")
    return max(files, key=lambda path: path.stat().st_mtime)


def assert_contains(text: str, required: list[str], label: str) -> None:
    missing = [item for item in required if item not in text]
    if missing:
        raise SmokeTestError(f"{label} missing required content: {', '.join(missing)}")


def test_pipeline_run() -> tuple[Path, Path, Path, Path, Path]:
    run_command(["-m", "pipeline", "run", "--idea-id", "001", "--dry-run"])
    draft = newest_file(PROJECT_ROOT / "content/drafts", "*_001_*.md")
    reviewed = newest_file(PROJECT_ROOT / "content/reviewed", "*_001_*.md")
    review = newest_file(PROJECT_ROOT / "reports/review", "*_p001_review.json")
    score = newest_file(PROJECT_ROOT / "reports/score", "*_001_score.json")
    package = newest_file(PROJECT_ROOT / "content/packages", "*_001_publish_package.md")

    draft_text = draft.read_text(encoding="utf-8")
    assert_contains(
        draft_text,
        [
            "idea_id:",
            "post_id:",
            "status:",
            "content_type:",
            "target_audience:",
            "created_at:",
            "reviewed_at:",
            "published_at:",
            "标题备选",
            "封面文案",
            "正文",
            "标签",
            "评论区引导",
            "私信回复建议",
            "可复制 AI Prompt",
            "适合沉淀到资料包的片段",
            "适合 1v1 诊断服务的转化点",
        ],
        "draft markdown",
    )

    review_data = json.loads(review.read_text(encoding="utf-8"))
    for key in ["passed", "risk_level", "issues", "suggested_fixes", "final_comment"]:
        if key not in review_data:
            raise SmokeTestError(f"review JSON missing key: {key}")

    score_data = json.loads(score.read_text(encoding="utf-8"))
    for key in [
        "favorite_score",
        "comment_score",
        "dm_conversion_score",
        "specificity_score",
        "personal_experience_score",
        "ai_smell_risk",
        "compliance_risk",
        "publish_recommendation",
        "suggested_improvements",
    ]:
        if key not in score_data:
            raise SmokeTestError(f"score JSON missing key: {key}")

    package_text = package.read_text(encoding="utf-8")
    assert_contains(
        package_text,
        ["最终标题", "封面文案", "正文", "标签", "评论区引导", "私信回复建议", "人工发布前检查清单"],
        "publish package",
    )
    if "自动发布" in package_text:
        raise SmokeTestError("publish package should not contain auto-publish instructions")

    return draft, reviewed, review, score, package


def test_pipeline_batch() -> None:
    result = run_command(["-m", "pipeline", "batch", "--limit", "3", "--dry-run"])
    if "PIPELINE BATCH FINISHED" not in result.stdout:
        raise SmokeTestError("pipeline batch did not print completion marker")


def test_weekly() -> Path:
    run_command(["-m", "pipeline", "weekly-review", "--dry-run"])
    report = newest_file(PROJECT_ROOT / "reports/weekly", "*_weekly_review.md")
    text = report.read_text(encoding="utf-8")
    assert_contains(
        text,
        ["数据总览", "表现最好的内容", "下周 10 个新选题建议"],
        "weekly report",
    )
    return report


def main() -> None:
    try:
        draft, reviewed, review, score, package = test_pipeline_run()
        test_pipeline_batch()
        weekly = test_weekly()
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)

    print(f"draft: {draft}")
    print(f"reviewed: {reviewed}")
    print(f"review: {review}")
    print(f"score: {score}")
    print(f"package: {package}")
    print(f"weekly: {weekly}")
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
