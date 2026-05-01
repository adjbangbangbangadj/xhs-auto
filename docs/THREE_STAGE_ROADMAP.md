# AI Content Factory Pipeline 三阶段路线图

## 项目定位

本项目不是“小红书自动发帖工具”，而是一个面向计算机复试、面试、AI 提效内容的 AI Content Factory Pipeline。

核心目标：

1. 自动生成内容草稿；
2. 自动质检；
3. 自动评分；
4. 自动生成发布包；
5. 人工最终审核并发布；
6. 发布后回填数据；
7. 用数据反推下一轮选题。

长期服务于：

- 计算机复试 AI 准备包；
- 计算机复试 1v1 诊断；
- 计算机项目介绍模板；
- 面试题复盘库；
- AI 提效问题库。

## 核心边界

严格不做：

- 自动登录小红书；
- 自动发布小红书；
- 自动评论；
- 自动私信；
- 浏览器自动化模拟操作；
- 爬取小红书数据；
- 批量铺量；
- 代写、代考、代做毕设、伪造项目；
- “保过”“押题必中”“内部资料”等夸大承诺。

人工必须负责：

- 最终内容审核；
- 最终发布；
- 评论和私信的关键回复；
- 发布数据回填；
- 商业化判断。

---

# 阶段 1：本地工程化 Pipeline

## 阶段目标

把当前脚本型项目整理成一个清晰、可测试、可复用的 Python Pipeline。

从：

```text
scripts/generate_post.py
scripts/review_post.py
scripts/weekly_review.py
```

升级为：

```bash
python -m pipeline run --idea-id 001 --dry-run
python -m pipeline batch --limit 3 --dry-run
python -m pipeline weekly-review --dry-run
```

## 阶段 1 交互方式

主要靠本地 CLI：

```bash
python -m pipeline run --idea-id 001 --dry-run
python -m pipeline batch --limit 3 --dry-run
python -m pipeline weekly-review --dry-run
```

你本人参与：

1. 在 mock 或飞书中维护选题；
2. 本地运行 pipeline；
3. 查看生成的 reviewed 内容；
4. 人工判断是否可发。

## 阶段 1 技术范围

保留：

- Feishu-lite 架构；
- client_factory；
- MockLLMClient；
- MockContentStore；
- FeishuContentStore；
- OpenAICompatibleLLMClient；
- Markdown 内容存储；
- JSON 质检报告；
- dry-run 模式。

新增：

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

新增输出目录：

```text
content/drafts/
content/reviewed/
content/packages/
reports/review/
reports/score/
reports/weekly/
```

## 阶段 1 必须实现的能力

### 1. 单篇完整流水线

命令：

```bash
python -m pipeline run --idea-id 001 --dry-run
```

流程：

```text
读取选题
→ 生成 draft Markdown
→ 生成 review JSON
→ 生成 score JSON
→ 如果通过，生成 reviewed Markdown
→ 生成 publish package Markdown
```

### 2. 批量生成

命令：

```bash
python -m pipeline batch --limit 3 --dry-run
```

流程：

```text
读取待生成选题
→ 按优先级排序
→ 最多处理 limit 条
→ 每条执行 run 流程
→ 单条失败不影响下一条
→ 最后输出成功/失败摘要
```

### 3. 周复盘

命令：

```bash
python -m pipeline weekly-review --dry-run
```

流程：

```text
读取 mock 或飞书发布记录
→ 计算收藏率、评论率、私信率、转粉率
→ 生成周复盘 Markdown
→ 输出下周 10 个选题建议
```

### 4. 内容评分

新增评分维度：

```text
favorite_score：收藏潜力，0-10
comment_score：评论潜力，0-10
dm_conversion_score：私信转化潜力，0-10
specificity_score：复试场景具体度，0-10
personal_experience_score：个人经验浓度，0-10
ai_smell_risk：AI 味风险，0-10
compliance_risk：low / medium / high
publish_recommendation：publish / revise / reject
```

输出：

```text
reports/score/YYYY-MM-DD_idea-id_score.json
```

### 5. 发布包

每篇通过审核的内容生成发布包：

```text
content/packages/YYYY-MM-DD_idea-id_publish_package.md
```

发布包包含：

- 最终标题；
- 封面文案；
- 正文；
- 标签；
- 评论区引导；
- 私信回复建议；
- 人工发布前检查清单。

## 阶段 1 验收标准

必须通过：

```bash
python -m pipeline run --idea-id 001 --dry-run
python -m pipeline batch --limit 3 --dry-run
python -m pipeline weekly-review --dry-run
```

如果项目已有测试脚本，也必须通过：

```bash
python scripts/run_smoke_tests.py
```

阶段 1 完成时，应满足：

- dry-run 不读取任何真实 API key；
- dry-run 不调用飞书；
- dry-run 不调用真实 LLM；
- 所有输出文件路径清晰；
- README 已更新；
- 业务逻辑不再散落在多个脚本里；
- 原 scripts 命令可以保留为兼容入口，但核心逻辑应进入 pipeline 包。

---

# 阶段 2：GitHub Actions 内容 CI/CD

## 阶段目标

让内容生产从本地命令升级为 GitHub Actions 自动流水线。

你和系统的交互变成：

```text
飞书写选题
→ GitHub Actions 手动或定时运行
→ 生成 artifact 或 PR
→ 你审核发布包
→ 人工发布小红书
→ 回填数据
```

## 阶段 2 技术范围

新增：

```text
.github/workflows/
├── smoke-test.yml
├── generate-content.yml
└── weekly-review.yml
```

## smoke-test.yml

触发方式：

```text
push
pull_request
workflow_dispatch
```

运行：

```bash
pip install -r requirements.txt
python -m pipeline run --idea-id 001 --dry-run
python -m pipeline weekly-review --dry-run
```

## generate-content.yml

触发方式：

```text
workflow_dispatch
```

输入参数：

```text
idea_id：可选，指定单篇内容
limit：生成几篇，默认 3
dry_run：是否 dry-run，默认 true
```

运行逻辑：

```text
如果 idea_id 不为空，运行单篇生成；
如果 idea_id 为空，运行 batch；
生成 reviewed 内容、review 报告、score 报告、发布包；
上传 artifact。
```

Artifact 包含：

```text
content/reviewed/
content/packages/
reports/review/
reports/score/
```

## weekly-review.yml

触发方式：

```text
workflow_dispatch
schedule
```

运行：

```bash
python -m pipeline weekly-review
```

输出 artifact：

```text
reports/weekly/
```

## 阶段 2 安全要求

GitHub Secrets 中保存：

```text
LLM_API_KEY
FEISHU_APP_SECRET
```

不能提交：

```text
.env
config.yaml
真实 app_secret
真实 LLM key
Cookie
小红书登录态
```

## 阶段 2 验收标准

必须满足：

- push 时 smoke-test 成功；
- Actions 页面可以手动触发 generate-content；
- workflow 支持输入 limit；
- 内容结果以 artifact 形式输出；
- weekly-review 可以手动触发；
- 可选 schedule 不影响手动触发；
- 项目仍然不包含自动发布小红书能力；
- README 写清楚如何配置 GitHub Secrets。

---

# 阶段 3：飞书驱动 / ChatOps 交互

## 阶段目标

把交互进一步产品化，让你主要在飞书中操作，而不是频繁进入 GitHub。

目标交互：

```text
飞书新增选题或修改状态
→ 触发 GitHub Actions / 后端 webhook
→ 自动生成内容
→ 回写飞书内容库
→ 你在飞书查看状态和发布包链接
```

## 阶段 3 交互方式

优先级从低复杂度到高复杂度：

### 方案 A：飞书手动维护 + GitHub Actions 手动触发

这是阶段 2 的延续，最稳。

### 方案 B：飞书按钮 / 状态触发

你在飞书把状态改成：

```text
待生成
```

然后通过飞书自动化或 webhook 触发 GitHub Actions。

### 方案 C：飞书 ChatOps

在飞书群里发送：

```text
/generate 复试项目介绍
/review p001
/weekly-review
```

机器人返回生成结果链接。

## 阶段 3 技术范围

可选新增：

```text
integrations/
├── __init__.py
├── github_dispatch.py
├── feishu_webhook.py
└── chatops_bot.py
```

新增能力：

- 调用 GitHub workflow_dispatch API；
- 飞书回写生成状态；
- 飞书回写 artifact / PR 链接；
- 可选飞书机器人命令。

## 阶段 3 风险控制

阶段 3 不允许：

- 通过飞书触发自动发布小红书；
- 通过机器人自动回复小红书评论；
- 通过机器人自动私信；
- 通过第三方 MCP 批量发帖。

所有外部触发都只能生成内容和发布包，不得直接发布。

## 阶段 3 验收标准

必须满足：

- 飞书中可以看到内容状态；
- 飞书中可以看到生成结果链接；
- 触发行为有日志；
- 失败有清晰错误提示；
- 所有触发都只生成内容，不发布小红书；
- README 写清楚 webhook 和 token 配置方式。

---

# 三阶段最终交互形态

## 阶段 1

```text
你 → CLI → 本地生成内容
```

## 阶段 2

```text
你 → GitHub Actions → Artifact / PR → 人工发布
```

## 阶段 3

```text
你 → 飞书 / ChatOps → GitHub Actions → 飞书回写 → 人工发布
```

## 长期不变的原则

```text
内容生成可以自动化
内容质检可以自动化
内容评分可以自动化
发布包可以自动化
最终发布必须人工确认
评论和私信必须人工把关
```