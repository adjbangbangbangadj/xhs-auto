# xhs-cs-ai-agent-workspace

这是一个面向计算机复试、面试、AI 提效内容的 AI Content Factory Pipeline。

它负责自动生成内容草稿、自动质检、自动评分、生成发布包和生成周复盘。最终内容审核、发布小红书、评论回复、私信回复和数据回填都必须由人工完成。

本项目明确不做自动登录小红书、自动发帖、自动评论、自动私信、浏览器自动化或小红书爬虫。

## 阶段 1：本地工程化 Pipeline

阶段 1 的主入口是：

```bash
python -m pipeline run --idea-id 001 --dry-run
python -m pipeline batch --limit 3 --dry-run
python -m pipeline weekly-review --dry-run
```

推荐日常流程：

1. 在 `mock/ideas.json` 或飞书选题库维护选题；
2. 本地运行 pipeline；
3. 查看 `content/reviewed/` 和 `content/packages/`；
4. 人工审核发布包；
5. 人工发布小红书；
6. 人工回填发布数据；
7. 周末运行周复盘。

## 输出目录

阶段 1 新 pipeline 默认使用：

```text
content/drafts/      # draft Markdown
content/reviewed/    # 通过质检后的 reviewed Markdown
content/packages/    # 人工发布包 Markdown
reports/review/      # 质检 JSON
reports/score/       # 内容评分 JSON
reports/weekly/      # 周复盘 Markdown
```

旧的 `posts/` 目录保留为历史兼容目录，但不再作为新 pipeline 的默认输出目录。

## 安装

```bash
pip install -r requirements.txt
```

建议使用 Python 3.11+。

## 配置

`config.example.yaml` 是模板，`config.yaml` 是本地配置文件。仓库会忽略 `config.yaml` 和 `.env`，不要提交真实密钥。

环境变量示例：

```bash
export LLM_API_KEY="your_key"
export FEISHU_APP_SECRET="your_feishu_app_secret"
```

Windows PowerShell 示例：

```powershell
$env:LLM_API_KEY="your_key"
$env:FEISHU_APP_SECRET="your_feishu_app_secret"
```

## dry-run 边界

`--dry-run` 会使用 `MockLLMClient` 和 `MockContentStore`：

- 不读取 `LLM_API_KEY`；
- 不读取 `FEISHU_APP_SECRET`；
- 不调用飞书；
- 不调用真实大模型；
- 评分阶段使用规则 + 默认值生成 `score JSON`；
- 只在本地写入 Markdown / JSON 报告。

## Pipeline 命令

单篇完整流水线：

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

批量生成：

```bash
python -m pipeline batch --limit 3 --dry-run
```

周复盘：

```bash
python -m pipeline weekly-review --dry-run
```

## 评分 JSON

每篇内容都会生成：

```text
reports/score/YYYY-MM-DD_idea-id_score.json
```

字段包含：

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

## 发布包

每篇通过质检的内容都会生成：

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

发布包只是给人工复制、检查和发布使用，不会触发小红书自动发布。

## 兼容旧脚本

旧脚本保留为兼容入口：

```bash
python scripts/generate_post.py --idea-id 001 --dry-run
python scripts/review_post.py --file content/drafts/某个文件.md --dry-run
python scripts/weekly_review.py --dry-run
```

核心业务逻辑已经收束到 `pipeline/` 包，旧脚本只作为调用入口保留。

## 交互式工作台

仍可启动命令行工作台：

```bash
python app.py
```

它用于生成、质检、批量处理、查看发布包、周复盘和健康检查。它不会自动发布小红书，不会自动评论，不会自动私信，也不会做浏览器自动化。

## 可视化工作台

仍可启动本地 Gradio 可视化工作台：

```bash
python web_app.py
```

然后打开：

```text
http://127.0.0.1:7860/
```

页面只保留内容生成、批量生成、发布包查看、模型配置、周复盘和项目检查等本地工作台能力。发布包页只展示 `content/reviewed/` 和 `content/packages/`，不会自动发布小红书。

模型配置页不会把密钥保存到 `.env`、`config.yaml` 或其他磁盘文件。它只会写入当前运行中的 `web_app.py` 进程环境变量；关闭或重启后需要重新填写。

## 测试方法

阶段 1 dry-run 测试：

```bash
python -m pipeline run --idea-id 001 --dry-run
python -m pipeline batch --limit 3 --dry-run
python -m pipeline weekly-review --dry-run
python scripts/run_smoke_tests.py
```

全部通过时，冒烟测试会输出：

```text
SMOKE TEST PASSED
```

## 真实 API 使用

真实模式需要配置飞书和大模型：

1. 在 `llm` 中填写 OpenAI-compatible `base_url`、`model`、`api_key_env`；
2. 在 `feishu` 中设置 `enabled: true`，填写 `app_id`、`app_token`、三张表的 `table_id`；
3. 设置 `LLM_API_KEY` 和 `FEISHU_APP_SECRET`；
4. 运行不带 `--dry-run` 的 pipeline 命令。

真实模式示例：

```bash
python -m pipeline run --idea-id 001
```

## 飞书表结构

第一版不会自动创建飞书表结构。请在飞书多维表格中手动创建：

1. 选题库：`idea_id`、`选题`、`目标用户`、`痛点`、`内容类型`、`优先级`、`状态`、`来源`、`备注`
2. 内容库：`post_id`、`idea_id`、`标题`、`标题备选`、`封面文案`、`正文文件路径`、`质检报告路径`、`风险等级`、`质检状态`、`状态`、`创建时间`、`更新时间`
3. 发布记录：`post_id`、`发布时间`、`发布平台`、`小红书链接`、`阅读量`、`点赞数`、`收藏数`、`评论数`、`关注数`、`私信数`、`复盘备注`

## MCP 发布模块状态

`mcp_xhs_publish/` 目前保留为 disabled / experimental 代码，不属于阶段 1 主流程。

阶段 1 中：

- `pipeline/` 不 import、不调用、不依赖 `mcp_xhs_publish/`；
- `app.py` 不提供自动发布入口；
- `web_app.py` 不提供自动发布入口；
- `.claude/.mcp.json` 默认不注册小红书发布 MCP server；
- 发布动作必须由人工完成。

## 常见错误排查

- `feishu.enabled=false`：当前是非 dry-run 模式，请启用飞书或添加 `--dry-run`；
- `缺少大模型 API key`：请设置 `LLM_API_KEY`，或检查 `llm.api_key_env`；
- `找不到 idea_id=xxx`：dry-run 下请检查 `mock/ideas.json`，真实模式下请检查飞书选题库；
- `找不到文本文件`：检查传入的 Markdown 路径是否存在；
- 依赖安装失败：先确认网络和 Python 版本，再重试 `pip install -r requirements.txt`。

## 为什么不做自动发布

本项目定位是内容工厂和人工发布辅助工具，不是小红书自动化工具。自动登录、自动发帖、自动评论、自动私信、浏览器模拟发布和爬取数据都不在项目范围内。

长期原则：

```text
内容生成可以自动化
内容质检可以自动化
内容评分可以自动化
发布包可以自动化
最终发布必须人工确认
评论和私信必须人工把关
```
