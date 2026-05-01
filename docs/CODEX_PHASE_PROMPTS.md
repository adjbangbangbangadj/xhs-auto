# Codex 分阶段执行 Prompt

本文件用于让 Codex 按阶段改造项目。不要一次性完成三阶段，每次只执行一个阶段。

执行顺序：

1. 阶段 0：读取路线图并生成迁移计划；
2. 阶段 1：本地工程化 Pipeline；
3. 阶段 2：GitHub Actions 内容 CI/CD；
4. 阶段 3：飞书驱动 / ChatOps 交互。

每个阶段完成后都必须运行测试，更新 README，并输出变更摘要。

---

# 阶段 0 Prompt：读取路线图并制定计划

请阅读以下文件：

- AGENTS.md
- README.md
- docs/THREE_STAGE_ROADMAP.md
- 当前项目目录结构
- scripts/
- prompts/
- rules/
- mock/
- config.example.yaml

请不要修改代码。

请输出：

1. 当前项目与三阶段路线图的差距；
2. 阶段 1 需要新增、移动、重构的文件；
3. 哪些现有代码可以复用；
4. 哪些脚本需要保留为兼容入口；
5. 阶段 1 的详细实施步骤；
6. 阶段 1 的测试计划；
7. 需要我确认的问题。

注意：

- 不要自动发布小红书；
- 不要引入 Web 后台；
- 不要引入数据库；
- 不要删除现有可用功能；
- 优先保持 dry-run 可用；
- 先给计划，不要直接改代码。

---

# 阶段 1 Prompt：本地工程化 Pipeline

请按照 docs/THREE_STAGE_ROADMAP.md 中“阶段 1：本地工程化 Pipeline”的要求改造项目。

目标：

将当前脚本型项目升级为 Python Pipeline 包。

请实现：

## 1. 新增 pipeline 包

创建：

```text
pipeline/
├── __init__.py
├── __main__.py
├── cli.py
├── runner.py
├── idea_loader.py
├── writer.py
├── reviewer.py
├── scorer.py
├── packager.py
└── weekly_review.py
```

## 2. 支持命令

必须支持：

```bash
python -m pipeline run --idea-id 001 --dry-run
python -m pipeline batch --limit 3 --dry-run
python -m pipeline weekly-review --dry-run
```

可选支持：

```bash
python -m pipeline generate --idea-id 001 --dry-run
python -m pipeline review --latest --dry-run
python -m pipeline package --latest
```

## 3. 复用现有 client_factory

保留并复用：

```text
scripts/clients/client_factory.py
scripts/clients/llm_client.py
scripts/clients/feishu_client.py
scripts/clients/mock_client.py
```

业务逻辑必须通过 client_factory 获取：

```text
llm
content_store
```

不得在 pipeline 中直接初始化 OpenAI client 或 Feishu client。

## 4. 增加内容评分阶段

新增：

```text
prompts/scorer.md
reports/score/
```

每篇内容必须输出 score JSON。

评分字段：

```json
{
  "favorite_score": 0,
  "comment_score": 0,
  "dm_conversion_score": 0,
  "specificity_score": 0,
  "personal_experience_score": 0,
  "ai_smell_risk": 0,
  "compliance_risk": "low",
  "publish_recommendation": "publish",
  "suggested_improvements": []
}
```

dry-run 时用 MockLLMClient 或规则生成模拟评分，不调用真实 LLM。

## 5. 增加发布包阶段

新增：

```text
content/packages/
```

每篇通过质检的内容生成：

```text
content/packages/YYYY-MM-DD_idea-id_publish_package.md
```

发布包包含：

- 标题；
- 封面文案；
- 正文；
- 标签；
- 评论区引导；
- 私信回复建议；
- 人工发布前检查清单。

## 6. 兼容旧脚本

原有脚本不要直接删除。可以改成调用 pipeline 包：

```text
scripts/generate_post.py
scripts/review_post.py
scripts/weekly_review.py
```

作为兼容入口保留。

## 7. 更新 README

README 中新增：

- AI Content Factory Pipeline 定位；
- pipeline 命令说明；
- 阶段 1 使用方式；
- dry-run 测试方式；
- 输出目录说明；
- 人工发布边界。

## 8. 测试要求

必须运行：

```bash
python -m pipeline run --idea-id 001 --dry-run
python -m pipeline batch --limit 3 --dry-run
python -m pipeline weekly-review --dry-run
```

如果项目已有：

```bash
python scripts/run_smoke_tests.py
```

也必须运行并修复直到通过。

## 9. 完成后输出

请输出：

1. 新增文件列表；
2. 修改文件列表；
3. 三个 pipeline 命令的测试结果；
4. 生成的 draft/review/score/package 文件路径；
5. 是否存在未完成事项；
6. 下一阶段建议。

---

# 阶段 2 Prompt：GitHub Actions 内容 CI/CD

请按照 docs/THREE_STAGE_ROADMAP.md 中“阶段 2：GitHub Actions 内容 CI/CD”的要求改造项目。

目标：

让内容生成、质检、评分、打包可以通过 GitHub Actions 手动或定时执行。

请实现：

## 1. 新增 workflows

创建：

```text
.github/workflows/
├── smoke-test.yml
├── generate-content.yml
└── weekly-review.yml
```

## 2. smoke-test.yml

触发：

```yaml
on:
  push:
  pull_request:
  workflow_dispatch:
```

运行：

```bash
pip install -r requirements.txt
python -m pipeline run --idea-id 001 --dry-run
python -m pipeline weekly-review --dry-run
```

## 3. generate-content.yml

触发：

```yaml
on:
  workflow_dispatch:
    inputs:
      idea_id:
        description: "Optional idea_id for single content generation"
        required: false
      limit:
        description: "Number of ideas to generate in batch mode"
        required: false
        default: "3"
      dry_run:
        description: "Run without real APIs"
        required: true
        default: "true"
        type: choice
        options:
          - "true"
          - "false"
```

逻辑：

- 如果 idea_id 不为空，运行单篇；
- 如果 idea_id 为空，运行 batch；
- 上传 artifacts。

Artifact 包含：

```text
content/reviewed/
content/packages/
reports/review/
reports/score/
```

## 4. weekly-review.yml

触发：

```yaml
on:
  workflow_dispatch:
  schedule:
    - cron: "0 12 * * 0"
```

注意 GitHub Actions cron 使用 UTC。README 中说明这一点。

运行：

```bash
python -m pipeline weekly-review
```

上传：

```text
reports/weekly/
```

## 5. Secrets

README 中说明需要配置：

```text
LLM_API_KEY
FEISHU_APP_SECRET
```

并说明：

- dry_run=true 不需要 secrets；
- dry_run=false 需要正确配置 config.yaml 或环境变量；
- 不要提交 config.yaml、.env、真实密钥。

## 6. 更新 .gitignore

确保忽略：

```text
.env
config.yaml
```

保留：

```text
config.example.yaml
```

## 7. 更新 README

新增：

- GitHub Actions 使用方式；
- 如何手动 Run workflow；
- generate-content 输入参数说明；
- weekly-review 定时说明；
- artifact 下载说明；
- GitHub Secrets 配置说明；
- 不自动发布小红书的边界说明。

## 8. 测试要求

本地至少运行：

```bash
python -m pipeline run --idea-id 001 --dry-run
python -m pipeline batch --limit 3 --dry-run
python -m pipeline weekly-review --dry-run
```

并检查 workflow YAML 语法结构。

## 9. 完成后输出

请输出：

1. 新增 workflow 文件；
2. 每个 workflow 的作用；
3. 如何手动触发；
4. artifacts 包含什么；
5. README 更新摘要；
6. 当前不能在本地完全验证的 GitHub Actions 行为；
7. 下一阶段建议。

---

# 阶段 3 Prompt：飞书驱动 / ChatOps 交互

请按照 docs/THREE_STAGE_ROADMAP.md 中“阶段 3：飞书驱动 / ChatOps 交互”的要求制定并实现最小版本。

目标：

让飞书成为主要交互入口，但仍不做自动发布小红书。

请先实现轻量版本，不要过度复杂。

## 1. 新增 integrations 目录

创建：

```text
integrations/
├── __init__.py
├── github_dispatch.py
├── feishu_webhook.py
└── README.md
```

## 2. github_dispatch.py

实现：

- 读取 GitHub repo、workflow name、branch；
- 使用 GitHub token 触发 workflow_dispatch；
- 支持传入：
  - idea_id
  - limit
  - dry_run
- 不在日志中打印 token。

环境变量：

```text
GITHUB_TOKEN
GITHUB_REPOSITORY
GITHUB_WORKFLOW_ID
GITHUB_REF
```

## 3. feishu_webhook.py

第一版可以实现为简单 CLI 模拟，不要强制部署复杂服务。

优先实现：

```bash
python integrations/feishu_webhook.py --idea-id 001 --dry-run true
```

功能：

- 接收 idea_id、limit、dry_run；
- 调用 github_dispatch.py；
- 返回触发结果；
- dry-run 时不真实触发 GitHub workflow。

## 4. 飞书回写策略

第一版不强制实现自动回写。

README 中设计清楚：

- 阶段 3A：飞书手动维护 + GitHub Actions 手动触发；
- 阶段 3B：飞书 webhook 触发 GitHub Actions；
- 阶段 3C：飞书机器人 ChatOps。

## 5. 禁止事项

不得实现：

- 自动发布小红书；
- 自动评论；
- 自动私信；
- 小红书 Cookie 管理；
- 浏览器自动化。

## 6. README 更新

新增：

- 飞书驱动交互说明；
- GitHub workflow_dispatch token 配置；
- 如何从飞书触发内容生成；
- 为什么阶段 3 不等于自动发布；
- 阶段 3A/3B/3C 的差异。

## 7. 测试要求

至少支持本地模拟：

```bash
python integrations/github_dispatch.py --dry-run true --idea-id 001
python integrations/feishu_webhook.py --dry-run true --idea-id 001
```

dry-run 时不得真实触发 GitHub workflow。

## 8. 完成后输出

请输出：

1. 新增 integrations 文件；
2. 本地模拟命令；
3. 真实触发需要的环境变量；
4. 飞书侧需要配置什么；
5. 当前仍需人工完成的动作；
6. 风险边界说明。

---

# 依次复制给 Codex 的执行口令

## 第一次：只让 Codex 做计划

```text
请阅读 docs/THREE_STAGE_ROADMAP.md 和 docs/CODEX_PHASE_PROMPTS.md。

现在只执行“阶段 0 Prompt：读取路线图并制定计划”。

不要修改代码。
不要创建新文件。
先输出当前项目与三阶段路线图的差距、阶段 1 实施计划和测试计划。
```

## 第二次：执行阶段 1

```text
请执行 docs/CODEX_PHASE_PROMPTS.md 中的“阶段 1 Prompt：本地工程化 Pipeline”。

要求：
1. 按文档实现阶段 1；
2. 保留现有功能；
3. 不做自动发布小红书；
4. 完成后运行阶段 1 要求的 dry-run 测试；
5. 如果失败，请修复并重跑；
6. 最后输出测试结果和变更摘要。
```

## 第三次：执行阶段 2

```text
请执行 docs/CODEX_PHASE_PROMPTS.md 中的“阶段 2 Prompt：GitHub Actions 内容 CI/CD”。

要求：
1. 新增 GitHub Actions workflows；
2. 不改变阶段 1 的本地 pipeline 能力；
3. workflow 默认支持 dry-run；
4. 上传 reviewed 内容、发布包、review 报告、score 报告作为 artifact；
5. 更新 README；
6. 完成后运行本地 dry-run 测试；
7. 最后输出变更摘要和 GitHub Actions 使用说明。
```

## 第四次：执行阶段 3

```text
请执行 docs/CODEX_PHASE_PROMPTS.md 中的“阶段 3 Prompt：飞书驱动 / ChatOps 交互”。

要求：
1. 先实现最小可用版本；
2. 只做 GitHub workflow_dispatch 触发；
3. 支持本地 dry-run 模拟；
4. 不引入复杂 Web 服务；
5. 不做小红书自动发布；
6. 更新 README；
7. 输出真实接入飞书前需要配置的事项。
```