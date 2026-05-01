import subprocess
import sys
import os
from pathlib import Path
from typing import Any

import gradio as gr


PROJECT_ROOT = Path(__file__).resolve().parent
COVERS_DIR = PROJECT_ROOT / "posts" / "covers"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from clients.client_factory import create_clients  # noqa: E402
from services.health_service import run_smoke_tests  # noqa: E402
from services.pipeline_service import generate_and_review  # noqa: E402
from services.weekly_service import generate_weekly_review  # noqa: E402
from utils import extract_front_matter, load_config, read_text  # noqa: E402


def _rel(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _status(ok: bool, message: str) -> str:
    color = "#15803d" if ok else "#b91c1c"
    return f"<div style='color:{color};font-weight:600'>{message}</div>"


def _mask_secret(value: str | None) -> str:
    if not value:
        return "未配置"
    if len(value) <= 8:
        return "已配置（****）"
    return f"已配置（{value[:4]}...{value[-4:]}）"


def package_for_reviewed(md_filename: str) -> Path | None:
    reviewed_path = PROJECT_ROOT / "content" / "reviewed" / md_filename
    if not reviewed_path.exists():
        return None
    meta = extract_front_matter(read_text(reviewed_path))
    idea_id = meta.get("idea_id", "")
    if not idea_id:
        return None
    package_dir = PROJECT_ROOT / "content" / "packages"
    matches = sorted(package_dir.glob(f"*_{idea_id}_publish_package.md"))
    return matches[-1] if matches else None


def config_summary() -> str:
    config = load_config(PROJECT_ROOT / "config.yaml")
    llm = config.get("llm", {})
    feishu = config.get("feishu", {})
    llm_env = llm.get("api_key_env", "LLM_API_KEY")
    feishu_env = feishu.get("app_secret_env", "FEISHU_APP_SECRET")
    return "\n".join(
        [
            f"模型：{llm.get('model', '')}",
            f"Base URL：{llm.get('base_url', '')}",
            f"LLM key 环境变量：{llm_env}，{_mask_secret(os.getenv(llm_env))}",
            f"飞书 secret 环境变量：{feishu_env}，{_mask_secret(os.getenv(feishu_env))}",
            f"飞书启用状态：{feishu.get('enabled', False)}",
        ]
    )


def apply_llm_key(api_key: str) -> tuple[str, str, str]:
    api_key = (api_key or "").strip()
    if not api_key:
        return _status(False, "请输入 LLM API key。"), "", config_summary()
    config = load_config(PROJECT_ROOT / "config.yaml")
    env_name = config.get("llm", {}).get("api_key_env", "LLM_API_KEY")
    os.environ[env_name] = api_key
    return (
        _status(True, f"已写入当前 Web 会话环境变量：{env_name}。不会保存到磁盘。"),
        "",
        config_summary(),
    )


def clear_llm_key() -> tuple[str, str]:
    config = load_config(PROJECT_ROOT / "config.yaml")
    env_name = config.get("llm", {}).get("api_key_env", "LLM_API_KEY")
    os.environ.pop(env_name, None)
    return _status(True, f"已清除当前 Web 会话中的 {env_name}。"), config_summary()


def apply_feishu_secret(secret: str) -> tuple[str, str, str]:
    secret = (secret or "").strip()
    if not secret:
        return _status(False, "请输入飞书 app secret。"), "", config_summary()
    config = load_config(PROJECT_ROOT / "config.yaml")
    env_name = config.get("feishu", {}).get("app_secret_env", "FEISHU_APP_SECRET")
    os.environ[env_name] = secret
    return (
        _status(True, f"已写入当前 Web 会话环境变量：{env_name}。不会保存到磁盘。"),
        "",
        config_summary(),
    )


def clear_feishu_secret() -> tuple[str, str]:
    config = load_config(PROJECT_ROOT / "config.yaml")
    env_name = config.get("feishu", {}).get("app_secret_env", "FEISHU_APP_SECRET")
    os.environ.pop(env_name, None)
    return _status(True, f"已清除当前 Web 会话中的 {env_name}。"), config_summary()


def generate_one(idea_id: str, dry_run: bool) -> tuple[str, str, str, str, str, str]:
    idea_id = (idea_id or "").strip()
    if not idea_id:
        return _status(False, "请输入 idea_id。"), "", "", "", "", ""
    try:
        result = generate_and_review(idea_id, dry_run=dry_run)
        review = result.review.review
        issues = "\n".join(f"- {item}" for item in review.get("issues", [])) or "无"
        fixes = "\n".join(f"- {item}" for item in review.get("suggested_fixes", [])) or "无"
        return (
            _status(True, "生成并质检完成"),
            _rel(result.generate.draft_path),
            _rel(result.review.reviewed_path),
            str(review.get("passed")),
            str(review.get("risk_level")),
            f"### 问题\n{issues}\n\n### 修改建议\n{fixes}\n\n### 总评\n{review.get('final_comment', '')}",
        )
    except RuntimeError as exc:
        return _status(False, f"失败：{exc}"), "", "", "", "", ""


def batch_generate(limit: int, dry_run: bool) -> tuple[str, list[list[str]]]:
    limit = max(int(limit or 1), 1)
    try:
        config = load_config(PROJECT_ROOT / "config.yaml")
        clients = create_clients(config, dry_run=dry_run)
        ideas = clients.content_store.list_pending_ideas(limit)
    except RuntimeError as exc:
        return _status(False, f"读取待生成选题失败：{exc}"), []

    if not ideas:
        return _status(False, "没有找到待生成选题。"), []

    rows: list[list[str]] = []
    success_count = 0
    for idea in ideas:
        idea_id = str(idea.get("idea_id", ""))
        try:
            result = generate_and_review(idea_id, dry_run=dry_run)
            review = result.review.review
            success_count += 1
            rows.append(
                [
                    idea_id,
                    result.generate.title,
                    "成功",
                    _rel(result.generate.draft_path),
                    _rel(result.review.reviewed_path),
                    str(review.get("risk_level")),
                    "",
                ]
            )
        except RuntimeError as exc:
            rows.append([idea_id, str(idea.get("theme", "")), "失败", "", "", "", str(exc)])

    return _status(True, f"批量生成完成：成功 {success_count} / 共 {len(rows)}"), rows


def reviewed_rows() -> list[list[str]]:
    reviewed_dir = PROJECT_ROOT / "content" / "reviewed"
    reviewed_dir.mkdir(parents=True, exist_ok=True)
    rows: list[list[str]] = []
    for file_path in sorted(
        reviewed_dir.glob("*.md"), key=lambda path: path.stat().st_mtime, reverse=True
    ):
        meta = extract_front_matter(read_text(file_path))
        rows.append(
            [
                file_path.name,
                meta.get("idea_id", ""),
                meta.get("post_id", ""),
                meta.get("created_at", ""),
                meta.get("status", ""),
            ]
        )
    return rows


def refresh_reviewed() -> tuple[str, list[list[str]], str]:
    rows = reviewed_rows()
    return _status(True, f"共找到 {len(rows)} 篇 reviewed 内容。"), rows, ""


def preview_reviewed(evt: gr.SelectData) -> str:
    if evt.index is None:
        return ""
    row_index = evt.index[0] if isinstance(evt.index, tuple) else evt.index
    rows = reviewed_rows()
    if row_index >= len(rows):
        return ""
    path = PROJECT_ROOT / "content" / "reviewed" / rows[row_index][0]
    return read_text(path)


def preview_package(evt: gr.SelectData) -> str:
    if evt.index is None:
        return ""
    row_index = evt.index[0] if isinstance(evt.index, tuple) else evt.index
    rows = reviewed_rows()
    if row_index >= len(rows):
        return ""
    package_path = package_for_reviewed(rows[row_index][0])
    if not package_path:
        return "未找到发布包。请先运行 pipeline 生成通过质检的内容。"
    return read_text(package_path)


def make_weekly(dry_run: bool) -> tuple[str, str, str]:
    try:
        result = generate_weekly_review(dry_run=dry_run)
        return (
            _status(True, "周复盘已生成"),
            _rel(result.report_path),
            read_text(result.report_path),
        )
    except RuntimeError as exc:
        return _status(False, f"失败：{exc}"), "", ""


def health_check() -> str:
    result = run_smoke_tests()
    prefix = "健康检查通过" if result.passed else "健康检查失败"
    return f"{prefix}\n\n{result.output}"


def run_script(script_name: str) -> str:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script_name)],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )
    output = (result.stdout + "\n" + result.stderr).strip()
    prefix = "测试通过" if result.returncode == 0 else "测试失败"
    return f"{prefix}\n\n{output}"


def test_feishu() -> str:
    return run_script("test_feishu.py")


def test_llm() -> str:
    return run_script("test_llm.py")


CSS = """
/* ========== Design System ========== */
:root {
  --bg-body: #f0f2f5;
  --bg-card: #ffffff;
  --bg-subtle: #f8faff;
  --bg-brand-soft: #eef2ff;
  --line: #e2e8f0;
  --line-focus: #a5b4fc;
  --text-primary: #0f172a;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --brand-gradient: linear-gradient(135deg, #6366f1, #8b5cf6);
  --brand-from: #6366f1;
  --brand-to: #8b5cf6;
  --accent: #06b6d4;
  --success: #10b981;
  --success-bg: #ecfdf5;
  --danger: #ef4444;
  --danger-bg: #fef2f2;
  --warning: #f59e0b;
  --warning-bg: #fffbeb;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.03);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 40px rgba(99, 102, 241, 0.10);
  --shadow-xl: 0 20px 60px rgba(99, 102, 241, 0.15);
  --font-sans: "Inter", "Segoe UI", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", -apple-system, sans-serif;
}

/* ========== Body & Container ========== */
body, .gradio-container {
  font-family: var(--font-sans) !important;
  background:
    radial-gradient(1000px 600px at 0% 0%, #eef2ff 0%, transparent 60%),
    radial-gradient(800px 500px at 100% 0%, #f5f3ff 0%, transparent 60%),
    var(--bg-body) !important;
  color: var(--text-primary);
  line-height: 1.6;
}

.gradio-container {
  max-width: 1140px !important;
  margin: 0 auto !important;
  padding: 20px 20px 32px 20px !important;
  background: transparent !important;
}

/* ========== Custom Header ========== */
.app-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}

.app-header-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: var(--brand-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.30);
  flex-shrink: 0;
}

.app-header-text h1 {
  font-size: 1.65rem !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em !important;
  margin: 0 0 2px 0 !important;
  background: var(--brand-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.3 !important;
}

.app-header-text p {
  margin: 0 !important;
  color: var(--text-secondary) !important;
  font-size: 14px !important;
  font-weight: 400;
}

.app-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 999px;
  background: var(--bg-brand-soft);
  color: #4f46e5;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid #c7d2fe;
  margin-left: auto;
  flex-shrink: 0;
}

.app-badge::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  display: inline-block;
}

/* ========== Headings & Text ========== */
h1, h2, h3, h4 {
  font-weight: 600 !important;
  letter-spacing: -0.01em !important;
}

p {
  color: var(--text-secondary);
}

/* ========== Cards & Panels ========== */
.gr-box, .block, .gr-panel, .tabs {
  border-radius: var(--radius-lg) !important;
  border: 1px solid var(--line) !important;
  box-shadow: var(--shadow-md) !important;
  background: var(--bg-card) !important;
  transition: box-shadow 0.2s ease;
}

.gr-box:hover, .block:hover {
  box-shadow: var(--shadow-lg) !important;
}

/* ========== Tabs ========== */
.tabs {
  overflow: hidden;
}

[role="tablist"] {
  background: var(--bg-subtle) !important;
  border-bottom: 1px solid var(--line) !important;
  padding: 8px 12px !important;
  gap: 4px !important;
  display: flex !important;
  flex-wrap: wrap !important;
}

[role="tablist"] button {
  border-radius: var(--radius-sm) !important;
  padding: 8px 16px !important;
  font-size: 13.5px !important;
  font-weight: 500 !important;
  border: 1px solid transparent !important;
  color: var(--text-secondary) !important;
  background: transparent !important;
  transition: all 0.2s ease !important;
  cursor: pointer !important;
  position: relative !important;
}

[role="tablist"] button:hover {
  background: rgba(99, 102, 241, 0.06) !important;
  color: var(--text-primary) !important;
}

[role="tablist"] button[aria-selected="true"] {
  background: var(--bg-card) !important;
  border-color: var(--line) !important;
  color: var(--brand-from) !important;
  font-weight: 600 !important;
  box-shadow: var(--shadow-sm) !important;
}

[role="tablist"] button[aria-selected="true"]::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 2.5px;
  border-radius: 2px;
  background: var(--brand-gradient);
}

/* ========== Buttons ========== */
button, .gr-button {
  font-family: var(--font-sans) !important;
  font-weight: 500 !important;
  border-radius: var(--radius-sm) !important;
  transition: all 0.18s ease !important;
  cursor: pointer !important;
}

button.primary,
.gr-button-primary {
  background: var(--brand-gradient) !important;
  border: none !important;
  color: #fff !important;
  font-weight: 600 !important;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25) !important;
}

button.primary:hover,
.gr-button-primary:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.35) !important;
}

button.primary:active,
.gr-button-primary:active {
  transform: translateY(0) !important;
}

.gr-button:not(.primary):not(.secondary):not([class*="lg"]) {
  background: var(--bg-card) !important;
  border: 1px solid var(--line) !important;
  color: var(--text-secondary) !important;
}

.gr-button:not(.primary):not(.secondary):hover {
  border-color: var(--line-focus) !important;
  color: var(--brand-from) !important;
  background: var(--bg-brand-soft) !important;
}

/* ========== Textbox, Number, Textarea ========== */
.gr-textbox, .gr-number, textarea, input[type="text"], input[type="password"] {
  border-radius: var(--radius-sm) !important;
  border: 1.5px solid var(--line) !important;
  background: var(--bg-card) !important;
  transition: all 0.2s ease !important;
  font-family: var(--font-sans) !important;
}

.gr-textbox:focus-within, .gr-number:focus-within,
textarea:focus, input[type="text"]:focus, input[type="password"]:focus {
  border-color: var(--line-focus) !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.10) !important;
}

.gr-textbox label, .gr-number label, label {
  font-weight: 500 !important;
  font-size: 13px !important;
  color: var(--text-secondary) !important;
  margin-bottom: 4px !important;
}

/* ========== Checkbox ========== */
.gr-checkbox {
  accent-color: var(--brand-from) !important;
}

.gr-checkbox label {
  font-weight: 400 !important;
}

/* ========== Dataframe / Table ========== */
.gr-dataframe {
  border-radius: var(--radius-md) !important;
  overflow: hidden !important;
  border: 1px solid var(--line) !important;
}

.gr-dataframe table {
  width: 100% !important;
  border-collapse: collapse !important;
  font-size: 13px !important;
}

.gr-dataframe table th {
  background: var(--bg-subtle) !important;
  color: var(--text-primary) !important;
  font-weight: 600 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.04em !important;
  padding: 10px 14px !important;
  border-bottom: 1px solid var(--line) !important;
}

.gr-dataframe table td {
  padding: 9px 14px !important;
  border-bottom: 1px solid var(--line) !important;
  color: var(--text-primary) !important;
}

.gr-dataframe table tr:last-child td {
  border-bottom: none !important;
}

.gr-dataframe table tr:hover td {
  background: var(--bg-brand-soft) !important;
}

/* ========== Markdown ========== */
.gr-markdown {
  padding: 4px 0 !important;
  line-height: 1.7 !important;
}

.gr-markdown code {
  background: var(--bg-brand-soft) !important;
  border-radius: 6px !important;
  padding: 2px 8px !important;
  font-size: 0.875em !important;
  color: #4f46e5 !important;
  border: 1px solid #e0e7ff !important;
}

.gr-markdown pre code {
  background: #1e293b !important;
  color: #e2e8f0 !important;
  border: none !important;
  border-radius: var(--radius-sm) !important;
}

/* ========== Status Messages ========== */
.app-note {
  color: var(--text-secondary);
  font-size: 14px;
  padding: 12px 16px !important;
  background: var(--bg-subtle) !important;
  border-radius: var(--radius-sm) !important;
  border-left: 3px solid var(--accent) !important;
  margin: 12px 0 !important;
}

/* ========== Scrollbar ========== */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* ========== Status Badge Styling ========== */
.status-ok {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  background: var(--success-bg);
  color: #065f46;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid #a7f3d0;
}

.status-ok::before {
  content: "✓";
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--success);
  color: white;
  font-size: 11px;
  font-weight: 700;
}

.status-fail {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  background: var(--danger-bg);
  color: #991b1b;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid #fecaca;
}

.status-fail::before {
  content: "✕";
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--danger);
  color: white;
  font-size: 11px;
  font-weight: 700;
}

/* ========== Animation ========== */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.tabs {
  animation: fadeIn 0.3s ease;
}

/* ========== Responsive ========== */
@media (max-width: 768px) {
  .gradio-container {
    padding: 12px !important;
  }
  .app-header {
    flex-wrap: wrap;
  }
  .app-badge {
    margin-left: 0;
  }
  [role="tablist"] button {
    padding: 6px 12px !important;
    font-size: 12.5px !important;
  }
}
"""


with gr.Blocks(title="小红书计算机复试 AI 内容工作台") as demo:
    gr.HTML(
        """
<div class="app-header">
  <div class="app-header-icon">📝</div>
  <div class="app-header-text">
    <h1>AI 内容工作台</h1>
    <p>小红书计算机复试 · 生成 · 质检 · 复盘</p>
  </div>
  <div class="app-badge">本地运行</div>
</div>
"""
    )
    gr.Markdown(
        "<div class='app-note'>💡 建议先用 <strong>dry-run</strong> 验证流程，再切换真实 API。所有正文与报告仍落在本地文件，便于长期沉淀和复盘。</div>"
    )

    with gr.Tabs():
        with gr.Tab("选题生成"):
            with gr.Row():
                idea_id_input = gr.Textbox(label="idea_id", value="001", scale=2)
                single_dry_run = gr.Checkbox(label="dry-run（不调用真实 API）", value=True, scale=1)
            generate_btn = gr.Button("生成并质检", variant="primary")
            single_status = gr.HTML()
            with gr.Row():
                draft_path = gr.Textbox(label="draft 文件路径")
                reviewed_path = gr.Textbox(label="reviewed 文件路径")
            with gr.Row():
                passed = gr.Textbox(label="质检是否通过")
                risk_level = gr.Textbox(label="风险等级")
            review_detail = gr.Markdown(label="质检详情")
            generate_btn.click(
                generate_one,
                inputs=[idea_id_input, single_dry_run],
                outputs=[single_status, draft_path, reviewed_path, passed, risk_level, review_detail],
            )

        with gr.Tab("批量生成"):
            with gr.Row():
                limit_input = gr.Number(label="生成数量 limit", value=3, precision=0)
                batch_dry_run = gr.Checkbox(label="dry-run（不调用真实 API）", value=True)
            batch_btn = gr.Button("开始批量生成", variant="primary")
            batch_status = gr.HTML()
            batch_table = gr.Dataframe(
                headers=["idea_id", "标题", "状态", "draft 路径", "reviewed 路径", "风险等级", "失败原因"],
                datatype=["str", "str", "str", "str", "str", "str", "str"],
                row_count=(0, "dynamic"),
                column_count=(7, "fixed"),
                interactive=False,
            )
            batch_btn.click(batch_generate, inputs=[limit_input, batch_dry_run], outputs=[batch_status, batch_table])

        with gr.Tab("发布包"):
            gr.Markdown(
                "<div class='app-note'>从 `content/reviewed/` 选择内容，查看 `content/packages/` 中的人工发布包。这里不会自动发布、评论或私信。</div>"
            )
            refresh_btn = gr.Button("刷新 reviewed 列表", variant="primary")
            reviewed_status = gr.HTML()

            reviewed_table = gr.Dataframe(
                headers=["文件名", "idea_id", "post_id", "创建时间", "状态"],
                datatype=["str", "str", "str", "str", "str"],
                row_count=(0, "dynamic"),
                column_count=(5, "fixed"),
                interactive=False,
            )

            with gr.Accordion("📝 内容预览", open=False):
                preview = gr.Markdown(label="Markdown 内容")
            with gr.Accordion("📦 发布包预览", open=True):
                package_preview = gr.Markdown(label="发布包")

            # Events
            refresh_btn.click(
                refresh_reviewed,
                outputs=[reviewed_status, reviewed_table, preview],
            )
            reviewed_table.select(
                fn=preview_reviewed,
                outputs=preview,
            )
            reviewed_table.select(
                fn=preview_package,
                outputs=package_preview,
            )

        with gr.Tab("模型配置"):
            gr.Markdown(
                """
这里配置的是当前 `web_app.py` 进程内的环境变量，不会保存到 `.env`、`config.yaml` 或其他磁盘文件。

关闭或重启 Web 工作台后，需要重新填写。真实调用时请取消对应页面里的 dry-run。
"""
            )
            config_info = gr.Textbox(label="当前配置状态", value=config_summary(), lines=6)
            refresh_config_btn = gr.Button("刷新配置状态")
            refresh_config_btn.click(config_summary, outputs=config_info)

            with gr.Row():
                llm_key_input = gr.Textbox(
                    label="LLM API key",
                    placeholder="粘贴你的模型 API key",
                    type="password",
                    scale=3,
                )
                apply_llm_btn = gr.Button("应用 LLM key", variant="primary", scale=1)
                clear_llm_btn = gr.Button("清除 LLM key", scale=1)
            llm_key_status = gr.HTML()
            apply_llm_btn.click(
                apply_llm_key,
                inputs=llm_key_input,
                outputs=[llm_key_status, llm_key_input, config_info],
            )
            clear_llm_btn.click(clear_llm_key, outputs=[llm_key_status, config_info])

            with gr.Row():
                feishu_secret_input = gr.Textbox(
                    label="飞书 app secret",
                    placeholder="粘贴飞书 app secret",
                    type="password",
                    scale=3,
                )
                apply_feishu_btn = gr.Button("应用飞书 secret", scale=1)
                clear_feishu_btn = gr.Button("清除飞书 secret", scale=1)
            feishu_secret_status = gr.HTML()
            apply_feishu_btn.click(
                apply_feishu_secret,
                inputs=feishu_secret_input,
                outputs=[feishu_secret_status, feishu_secret_input, config_info],
            )
            clear_feishu_btn.click(clear_feishu_secret, outputs=[feishu_secret_status, config_info])

        with gr.Tab("周复盘"):
            weekly_dry_run = gr.Checkbox(label="dry-run（不调用真实 API）", value=True)
            weekly_btn = gr.Button("生成周复盘", variant="primary")
            weekly_status = gr.HTML()
            weekly_path = gr.Textbox(label="报告路径")
            weekly_preview = gr.Markdown(label="报告预览")
            weekly_btn.click(make_weekly, inputs=weekly_dry_run, outputs=[weekly_status, weekly_path, weekly_preview])

        with gr.Tab("项目检查"):
            health_btn = gr.Button("运行健康检查", variant="primary")
            health_output = gr.Textbox(label="检查输出", lines=12)
            health_btn.click(health_check, outputs=health_output)

        with gr.Tab("API 测试"):
            gr.Markdown("飞书测试只读取 `idea_id=001`，不写入数据；大模型测试只发送简单 prompt，不调用飞书。")
            with gr.Row():
                feishu_btn = gr.Button("测试飞书连接")
                llm_btn = gr.Button("测试大模型连接")
            api_output = gr.Textbox(label="测试输出", lines=10)
            feishu_btn.click(test_feishu, outputs=api_output)
            llm_btn.click(test_llm, outputs=api_output)


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, css=CSS)
