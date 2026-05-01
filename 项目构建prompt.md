
你现在是我的项目搭建 Agent。请从零搭建一个“小红书计算机复试 AI 内容 Agent 工作台”。

项目目标是在“最佳实践”和“最快落地”之间取得平衡，不要过度工程化。请采用 Feishu-lite Agent Workspace 架构，并增加统一 API 管理层：

- 飞书多维表格作为主控面板；
- 本地 Markdown 保存正文内容；
- 本地 JSON 保存质检报告；
- Python 脚本负责生成、质检、同步和周复盘；
- OpenAI-compatible LLM client 负责统一模型调用；
- 飞书 API、大模型 API、mock 数据都通过统一 client factory 创建；
- Codex 负责项目搭建和后续迭代；
- 人工最终审核并手动发布小红书。

不要做自动登录小红书、自动发帖、自动评论、自动私信、浏览器自动化、爬虫、批量铺量。

---

# 一、我的背景

我是东南大学计算机专业本硕学生，做过：

- 研究生初试辅导；
- 研究生复试辅导；
- 本科生课程辅导；
- 小红书面试问题记录和求职经验整理。

我现在想围绕“小红书 + 计算机复试 + AI 提效”做一个内容工作台，用于持续生产小红书笔记，长期沉淀成：

- 计算机复试 AI 准备包；
- 计算机复试 1v1 诊断服务；
- 计算机项目介绍模板；
- 面试题复盘库；
- AI 提效问题库。

---

# 二、项目名称

项目名：

xhs-cs-ai-agent-workspace

如果当前目录是空目录，可以直接在当前目录创建项目文件；如果不是空目录，请先提示我确认，不要覆盖已有文件。

---

# 三、总体架构

请搭建以下架构：

飞书多维表格：
- 只存结构化数据；
- 作为我每天看的主控面板；
- 第一版只接 3 张表：
  1. 选题库
  2. 内容库
  3. 发布记录

本地 Markdown：
- 保存小红书草稿；
- 保存已质检版本；
- 保存已发布归档；
- 保存周复盘报告；
- 保存资料包草稿。

本地 JSON：
- 保存模型质检报告；
- 保存结构化审查结果。

Python 脚本：
- 从飞书或 mock 数据读取选题；
- 调用模型生成草稿；
- 调用模型质检；
- 写入 Markdown 和 JSON；
- 回写飞书状态；
- 读取发布记录并生成周复盘。

统一 API 管理层：
- 所有真实 API 和 mock 数据都通过 clients 目录封装；
- 业务脚本不能直接初始化 OpenAI client 或 Feishu client；
- 业务脚本统一通过 client_factory.py 获取 clients；
- dry-run 模式必须使用 MockLLMClient 和 MockContentStore；
- 非 dry-run 模式使用 OpenAICompatibleLLMClient 和 FeishuContentStore；
- 后续可以方便扩展 Notion、SQLite、Airtable 等存储方式。

dry-run 模式：
- 必须保留；
- 不调用真实飞书 API；
- 不调用真实 LLM API；
- 不读取任何真实 API key；
- 使用本地 mock 数据跑通完整流程。

---

# 四、请创建的目录结构

请创建如下目录：

xhs-cs-ai-agent-workspace/
├── AGENTS.md
├── README.md
├── config.example.yaml
├── config.yaml
├── requirements.txt
├── .gitignore
├── mock/
│   ├── ideas.json
│   ├── content_records.json
│   └── published_records.json
├── prompts/
│   ├── generate_post.md
│   ├── review_post.md
│   ├── rewrite_xhs_style.md
│   └── weekly_review.md
├── rules/
│   ├── positioning.md
│   ├── xhs_style.md
│   └── compliance.md
├── posts/
│   ├── draft/
│   ├── reviewed/
│   └── published/
├── reports/
│   ├── review/
│   └── weekly/
└── scripts/
    ├── __init__.py
    ├── generate_post.py
    ├── review_post.py
    ├── weekly_review.py
    ├── sync_to_feishu.py
    ├── utils.py
    └── clients/
        ├── __init__.py
        ├── base.py
        ├── client_factory.py
        ├── llm_client.py
        ├── feishu_client.py
        └── mock_client.py

不要创建数据库。
不要创建 Web 后台。
不要创建浏览器自动化脚本。

---

# 五、AGENTS.md 要求

请创建 AGENTS.md，并写入项目级规则。AGENTS.md 必须包含：

## 1. 项目定位

这是一个“小红书计算机复试 AI 内容 Agent 工作台”。

目标不是自动发布小红书，而是自动生成、质检、整理待发布内容，最终由人工确认后手动发布。

## 2. 账号人设

账号定位：

- 东南大学计算机本硕学长；
- 分享计算机复试、项目介绍、面试准备、AI 提效方法；
- 目标用户是计算机考研/保研复试学生、本科生、求职学生；
- 语气真实、具体、克制，不像机构营销号。

## 3. 内容原则

每篇内容必须：

- 有具体场景；
- 有明确痛点；
- 有可执行方法；
- 最好包含一个可复制 AI Prompt；
- 适合用户收藏；
- 避免空泛鸡汤；
- 避免夸张营销。

## 4. 禁止事项

严格禁止：

- 自动登录小红书；
- 自动发帖；
- 自动评论；
- 自动私信；
- 浏览器自动化模拟发布；
- 爬取小红书数据；
- 批量铺量；
- 承诺“保过”“必中”“押题必中”“内部资料”“百分百上岸”；
- 鼓励代写论文、代做毕设、代写作业、伪造项目、作弊；
- 硬编码 API key；
- 泄露真实学生隐私；
- 使用未经授权的学校、导师、学生信息。

## 5. 技术规范

- Python 3.11+；
- 使用 pathlib；
- 使用 argparse；
- 使用清晰函数拆分；
- 使用 config.yaml 管理配置；
- 使用环境变量读取密钥；
- 使用 OpenAI-compatible 模型调用封装；
- 使用 clients/client_factory.py 统一创建 API client；
- 业务脚本不得直接初始化真实 API client；
- 所有 Prompt 放在 prompts/；
- 所有规则放在 rules/；
- 小红书正文用 Markdown 保存；
- 质检报告用 JSON 保存；
- dry-run 必须不依赖任何真实 API。

## 6. 完成标准

项目完成后必须满足：

- 可以运行 `python scripts/generate_post.py --idea-id 001 --dry-run` 生成模拟草稿；
- 可以运行 `python scripts/review_post.py --file posts/draft/某个文件.md --dry-run` 生成模拟质检报告；
- 可以运行 `python scripts/weekly_review.py --dry-run` 生成模拟周复盘；
- README 中的命令可以直接复制运行；
- 不包含任何自动发布小红书的代码；
- 不包含任何硬编码密钥；
- 业务脚本统一通过 client_factory 创建 API client；
- dry-run 不读取任何真实 API key。

---

# 六、飞书多维表格设计

第一版只支持 3 张表：

## 表 1：选题库

字段建议：

- idea_id：文本，例如 001
- 选题：文本
- 目标用户：单选，例如 复试学生 / 本科生 / 求职学生
- 痛点：长文本
- 内容类型：单选，例如 方法论 / 清单 / Prompt / 案例 / 模板
- 优先级：数字，1-5
- 状态：单选，例如 待生成 / 已生成 / 已质检 / 待发布 / 已发布 / 暂缓
- 来源：单选，例如 手动 / 评论 / 私信 / 1v1 / AI建议
- 备注：长文本

## 表 2：内容库

字段建议：

- post_id：文本，例如 p001
- idea_id：文本，关联选题
- 标题：文本
- 标题备选：长文本
- 封面文案：文本
- 正文文件路径：文本
- 质检报告路径：文本
- 风险等级：单选，例如 low / medium / high
- 质检状态：单选，例如 未质检 / 通过 / 需修改 / 不建议发布
- 状态：单选，例如 草稿 / 已质检 / 待发布 / 已发布
- 创建时间：日期
- 更新时间：日期

## 表 3：发布记录

字段建议：

- post_id：文本
- 发布时间：日期
- 发布平台：单选，例如 小红书
- 小红书链接：URL
- 阅读量：数字
- 点赞数：数字
- 收藏数：数字
- 评论数：数字
- 关注数：数字
- 私信数：数字
- 复盘备注：长文本

第一版不要自动创建飞书表结构。请在 README 中说明用户需要手动创建这 3 张表，并填写 table_id。

---

# 七、统一 API 管理层要求

请创建 `scripts/clients/` 目录，并实现统一 API 管理层。

## scripts/clients/base.py

定义协议或抽象接口。

建议包含：

```python
from typing import Protocol, Any


class LLMClientProtocol(Protocol):
    def chat(self, messages: list[dict[str, str]]) -> str:
        ...


class ContentStoreProtocol(Protocol):
    def get_idea_by_id(self, idea_id: str) -> dict[str, Any]:
        ...

    def create_content_record(self, record: dict[str, Any]) -> dict[str, Any]:
        ...

    def update_idea_status(self, idea_id: str, status: str) -> None:
        ...

    def update_content_review(self, post_id: str, review: dict[str, Any]) -> None:
        ...

    def get_published_records(self) -> list[dict[str, Any]]:
        ...
````

如果 Protocol 增加复杂度，可以使用普通类，但接口方法必须保持一致。

## scripts/clients/llm_client.py

实现 OpenAICompatibleLLMClient。

要求：

* 使用 openai SDK；
* 使用 OpenAI-compatible 调用方式；
* 从 config.yaml 读取 base_url、model、temperature、max_tokens、api_key_env；
* API key 从环境变量读取；
* 不允许硬编码 API key；
* 缺少 API key 时给出清晰错误；
* 实现 `chat(messages)` 方法；
* 不负责 prompt 拼接，只负责调用模型。

## scripts/clients/feishu_client.py

实现 FeishuContentStore。

第一版只实现：

* get_idea_by_id(idea_id)
* create_content_record(record)
* update_idea_status(idea_id, status)
* update_content_review(post_id, review)
* get_published_records()

要求：

* 从 config.yaml 读取 app_id、app_secret_env、app_token、table_ids；
* app_secret 从环境变量读取；
* 封装 token 获取逻辑；
* token 可以简单缓存到进程内，不需要持久化；
* 出错时给出清晰提示；
* 如果 feishu.enabled=false，非 dry-run 模式应报错并提示启用飞书或使用 dry-run；
* 第一版不要自动创建飞书表和字段；
* 不要在业务脚本中暴露飞书 API URL 拼接细节。

## scripts/clients/mock_client.py

实现：

* MockLLMClient
* MockContentStore

要求：

MockLLMClient：

* 实现 `chat(messages)`；
* 不调用真实 API；
* 返回可用的模拟小红书内容或模拟质检 JSON；
* dry-run 下所有模型输出都由它产生。

MockContentStore：

* 从 mock/ideas.json 读取选题；
* 从 mock/published_records.json 读取发布记录；
* create_content_record 可以写入 mock/content_records.json 或仅返回模拟记录；
* update_idea_status 可以打印模拟更新信息；
* update_content_review 可以打印模拟更新信息；
* 不读取任何真实 API key；
* 不调用飞书。

## scripts/clients/client_factory.py

实现统一创建入口。

建议包含：

* AppClients 数据结构，包含：

  * llm
  * content_store

实现函数：

```python
def create_clients(config: dict, dry_run: bool) -> AppClients:
    ...
```

逻辑要求：

* 如果 dry_run=true：

  * 返回 MockLLMClient；
  * 返回 MockContentStore；
  * 不检查真实 API key；
  * 不调用飞书。
* 如果 dry_run=false：

  * 创建 OpenAICompatibleLLMClient；
  * 如果 config.feishu.enabled=true，创建 FeishuContentStore；
  * 如果 config.feishu.enabled=false，报错并提示使用 dry-run 或启用飞书；
  * 缺少必要环境变量时给出清晰错误。
* generate_post.py、review_post.py、weekly_review.py 必须通过 create_clients(config, dry_run) 获取 client。

---

# 八、config.yaml 要求

请创建 config.example.yaml 和 config.yaml。

config.example.yaml 示例内容：

```yaml
app:
  mode: "feishu-lite"
  dry_run_default: true

llm:
  provider: "openai-compatible"
  base_url: "https://api.openai.com/v1"
  api_key_env: "LLM_API_KEY"
  model: "gpt-4.1-mini"
  temperature: 0.7
  max_tokens: 3000

content_store:
  provider: "feishu"

feishu:
  enabled: false
  app_id: "your_feishu_app_id"
  app_secret_env: "FEISHU_APP_SECRET"
  app_token: "your_bitable_app_token"
  table_ids:
    ideas: "your_ideas_table_id"
    contents: "your_contents_table_id"
    publishing: "your_publishing_table_id"

content:
  niche: "计算机复试 AI 准备"
  target_audience: "计算机考研/保研复试学生"
  output_language: "zh-CN"

paths:
  draft_dir: "posts/draft"
  reviewed_dir: "posts/reviewed"
  published_dir: "posts/published"
  review_report_dir: "reports/review"
  weekly_report_dir: "reports/weekly"
  mock_ideas: "mock/ideas.json"
  mock_content_records: "mock/content_records.json"
  mock_published_records: "mock/published_records.json"
```

要求：

* config.yaml 可以由 config.example.yaml 复制而来；
* 不要在 config.yaml 中写真实密钥；
* .gitignore 中应忽略 .env；
* .gitignore 中应忽略 config.yaml；
* 保留 config.example.yaml；
* README 要说明如何配置环境变量。

---

# 九、mock 数据要求

请创建 mock/ideas.json，至少包含 15 个“计算机复试 AI 准备”方向选题：

1. 计算机复试自我介绍怎么写？
2. 复试项目介绍怎么准备？
3. 老师追问项目细节怎么办？
4. 英文自我介绍不会写怎么办？
5. 专业课忘了怎么办？
6. 简历项目太普通怎么讲出亮点？
7. 跨考计算机复试怎么补短板？
8. 复试被问为什么选择我们学校怎么答？
9. 如何用 AI 模拟复试导师追问？
10. 复试前 7 天怎么冲刺？
11. 复试项目中如何讲清楚个人贡献？
12. 复试老师问毕设细节怎么准备？
13. 没有科研经历复试怎么表达？
14. 如何用 AI 整理专业课问答？
15. 如何准备计算机复试英文问答？

每条 mock idea 包含：

* idea_id
* theme
* audience
* pain_point
* content_type
* priority
* status
* source
* notes

请创建 mock/published_records.json，至少包含 5 条模拟发布数据，用于 weekly_review dry-run。

请创建 mock/content_records.json，初始可以为空数组。

---

# 十、Prompt 文件要求

## prompts/generate_post.md

用于生成小红书笔记。

输入变量包括：

* idea_id
* theme
* audience
* pain_point
* content_type
* positioning
* xhs_style
* compliance

要求模型输出 Markdown，必须包含：

* 标题备选 3 个
* 封面文案
* 正文
* 标签
* 评论区引导
* 私信回复建议
* 可复制 AI Prompt
* 适合沉淀到资料包的片段
* 适合 1v1 诊断服务的转化点

风格要求：

* 像真实学长经验；
* 具体；
* 有场景；
* 有方法；
* 不要空泛；
* 不要营销号语气；
* 不要制造过度焦虑；
* 每篇必须能让用户收藏；
* 不承诺保过；
* 不伪造内部信息；
* 不直接放外部联系方式、二维码或诱导导流话术。

## prompts/review_post.md

用于质检内容。

要求模型只输出 JSON，不要输出多余解释。

JSON 字段必须包括：

* passed：boolean
* risk_level：low / medium / high
* issues：数组
* suggested_fixes：数组
* final_comment：字符串
* needs_human_review：boolean

质检维度包括：

1. 是否有“保过”“必中”“押题必中”“内部资料”“百分百上岸”等夸大表达；
2. 是否涉及代写论文、代做毕设、代写作业、伪造项目、作弊；
3. 是否存在过度焦虑营销；
4. 是否存在过度导流；
5. 是否像明显 AI 生成；
6. 是否内容空泛；
7. 是否对计算机复试学生有实际帮助；
8. 是否包含可执行的方法；
9. 是否适合小红书收藏；
10. 是否需要人工重点复核。

## prompts/rewrite_xhs_style.md

用于把普通内容改写成小红书风格，但必须保持真实、克制、具体。

## prompts/weekly_review.md

用于根据发布记录做周复盘。

要求输出 Markdown 报告，包括：

* 本周数据概览；
* 表现最好的内容；
* 收藏率分析；
* 评论率分析；
* 私信率分析；
* 转粉率分析；
* 下周建议继续写的方向；
* 下周建议减少的方向；
* 下周 10 个新选题建议。

---

# 十一、rules 文件要求

## rules/positioning.md

写清楚账号定位、目标用户、长期产品方向。

必须包含：

* 账号人设；
* 目标用户；
* 用户痛点；
* 内容主线；
* 长期产品方向；
* 不做什么。

## rules/xhs_style.md

写清楚小红书内容风格。

必须包含：

* 标题具体；
* 开头直接点出痛点；
* 正文结构清晰；
* 每篇给一个方法、模板或 Prompt；
* 少用鸡汤；
* 少用夸张词；
* 不伪装成机构；
* 不装作有内部资源；
* 不制造过度焦虑；
* 语气像真实学长。

## rules/compliance.md

写清楚内容合规边界。

必须包含：

* 不代写；
* 不代考；
* 不作弊；
* 不伪造项目；
* 不夸大结果；
* 不泄露隐私；
* 不使用真实学生案例，除非已匿名化；
* 不使用未授权学校、导师、学生信息；
* 不直接放外部联系方式、二维码或诱导导流话术；
* 不自动发布小红书。

---

# 十二、Python 脚本要求

## scripts/utils.py

实现工具函数：

* load_config(path)
* ensure_dir(path)
* read_text(path)
* write_text(path, content)
* write_json(path, data)
* read_json(path)
* slugify(text, max_length=40)
* current_date_str()
* render_template(template, variables)
* extract_title_from_markdown(markdown)
* extract_front_matter(markdown)
* make_post_id(idea_id)

要求：

* 使用 pathlib；
* 错误提示清晰；
* 兼容中文文件名；
* slugify 对中文可以保留简短拼音不强求，如果实现困难，可使用 idea_id + 简短英文 fallback。

## scripts/generate_post.py

功能：

* 支持 `--idea-id`
* 支持 `--dry-run`
* 支持可选 `--config config.yaml`
* 通过 `create_clients(config, dry_run)` 获取 llm 和 content_store；
* dry-run 时从 MockContentStore 读取选题；
* 非 dry-run 时从 FeishuContentStore 读取选题；
* 读取 rules/positioning.md、rules/xhs_style.md、rules/compliance.md；
* 读取 prompts/generate_post.md；
* 调用 clients.llm.chat(...) 生成小红书草稿；
* dry-run 时不调用真实 LLM；
* 将草稿保存到 posts/draft/；
* Markdown 文件名格式：YYYY-MM-DD_idea-id_slug.md；
* Markdown 开头加入 YAML front matter：

---

idea_id: "001"
post_id: "p001"
status: "draft"
content_type: "方法论"
target_audience: "考研复试学生"
created_at: "YYYY-MM-DD"
reviewed_at: ""
published_at: ""
----------------

* 非 dry-run 时，通过 content_store.create_content_record(...) 在飞书“内容库”新增内容记录；
* 非 dry-run 时，通过 content_store.update_idea_status(...) 将选题状态更新为“已生成”；
* dry-run 时使用 MockContentStore 模拟上述更新；
* 最后打印生成文件路径和下一步命令。

## scripts/review_post.py

功能：

* 支持 `--file`
* 支持 `--dry-run`
* 支持可选 `--config config.yaml`
* 通过 `create_clients(config, dry_run)` 获取 llm 和 content_store；
* 读取 Markdown 草稿；
* 读取 prompts/review_post.md；
* 读取 rules/compliance.md；
* 调用 clients.llm.chat(...) 进行质检；
* dry-run 时不调用真实 LLM；
* 输出 JSON 到 reports/review/；
* 如果 passed=true，则将 Markdown 复制或改写到 posts/reviewed/；
* 如果 passed=false，则仍保存报告，但不复制到 reviewed；
* 如果能从 front matter 识别 post_id，则通过 content_store.update_content_review(...) 回写质检状态；
* dry-run 时使用 MockContentStore 模拟回写；
* 最后打印质检结果和 reviewed 文件路径。

## scripts/weekly_review.py

功能：

* 支持 `--dry-run`
* 支持可选 `--config config.yaml`
* 通过 `create_clients(config, dry_run)` 获取 llm 和 content_store；
* dry-run 时从 MockContentStore 读取 mock/published_records.json；
* 非 dry-run 时从 FeishuContentStore 读取飞书“发布记录”；
* 计算：

  * 收藏率 = favorites / views
  * 评论率 = comments / views
  * 私信率 = dm_count / views
  * 转粉率 = follows / views
* 处理 views=0 的情况，不要报错；
* 输出 Markdown 周复盘报告到 reports/weekly/；
* 报告包含：

  * 数据总览；
  * 表现最好的内容；
  * 表现较弱的内容；
  * 下周内容建议；
  * 下周 10 个新选题建议；
* dry-run 不调用真实 LLM，可以用规则生成报告；
* 如果非 dry-run 且配置了 LLM，可以用 LLM 辅助生成更自然的复盘建议。

## scripts/sync_to_feishu.py

第一版只做预留，可以实现简单占位：

* 打印当前项目支持的飞书同步方向；
* 提示第一版主要由 generate_post.py、review_post.py、weekly_review.py 内部完成同步；
* 不需要复杂实现。

---

# 十三、requirements.txt

至少包含：

openai
pyyaml
python-dotenv
requests

如果需要其他轻量依赖可以添加，但不要引入复杂框架。

---

# 十四、.gitignore 要求

至少忽略：

.env
config.yaml
**pycache**/
*.pyc
.DS_Store
reports/**/*.tmp
outputs/
.venv/
venv/

注意：保留 config.example.yaml。

---

# 十五、README.md 要求

README 必须写清楚：

1. 项目简介；
2. 为什么采用 Feishu-lite 架构；
3. 为什么飞书只存状态和索引，正文仍保存在 Markdown；
4. 为什么增加统一 API 管理层；
5. clients 目录各文件职责；
6. 目录结构；
7. 安装方法；
8. 环境变量配置；
9. config.yaml 配置方法；
10. 如何手动创建飞书三张表；
11. 如何填写 app_id、app_secret、app_token、table_id；
12. dry-run 使用方法；
13. 真实飞书 API 使用方法；
14. 真实 LLM API 使用方法；
15. 如何添加选题；
16. 如何生成草稿；
17. 如何进行质检；
18. 如何人工发布；
19. 如何回填发布数据；
20. 如何做周复盘；
21. 为什么不做自动发布；
22. 后续扩展方向。

README 必须给出以下示例命令：

pip install -r requirements.txt

python scripts/generate_post.py --idea-id 001 --dry-run

python scripts/review_post.py --file posts/draft/某个文件.md --dry-run

python scripts/weekly_review.py --dry-run

真实 API 示例：

export LLM_API_KEY="your_key"
export FEISHU_APP_SECRET="your_feishu_app_secret"

python scripts/generate_post.py --idea-id 001

---

# 十六、代码质量要求

1. Python 3.11+；
2. 使用 argparse；
3. 使用 pathlib；
4. 函数拆分清晰；
5. 出错时给出清晰提示；
6. 输出目录不存在时自动创建；
7. 找不到 idea_id 时明确报错；
8. dry-run 不需要任何 API key；
9. 业务脚本不直接初始化 OpenAI client；
10. 业务脚本不直接初始化 Feishu client；
11. 业务脚本统一通过 client_factory 获取 clients；
12. 不要创建数据库；
13. 不要创建 Web 服务；
14. 不要创建浏览器自动化脚本；
15. 不要自动发布小红书；
16. 不要自动评论和私信；
17. 不要硬编码 API key；
18. 代码要简单、清晰、便于后续继续迭代。

---

# 十七、请按以下步骤执行

请严格按顺序执行：

1. 先阅读并理解本 prompt；
2. 先输出简短实现计划；
3. 创建项目目录和文件；
4. 编写代码；
5. 编写 README；
6. 运行 dry-run 自测；
7. 如果发现问题，直接修复；
8. 最后输出总结。

---

# 十八、dry-run 自测要求

请至少运行并验证：

1. `python scripts/generate_post.py --idea-id 001 --dry-run`

预期：

* 生成 posts/draft/ 下的 Markdown 草稿；
* 不需要任何 API key；
* 不调用飞书；
* 不调用真实大模型；
* 终端输出生成文件路径。

2. `python scripts/review_post.py --file posts/draft/生成的文件.md --dry-run`

预期：

* 生成 reports/review/ 下的 JSON 质检报告；
* 如果 passed=true，生成 posts/reviewed/ 下的 Markdown 文件；
* 不需要任何 API key；
* 不调用飞书；
* 不调用真实大模型。

3. `python scripts/weekly_review.py --dry-run`

预期：

* 读取 mock/published_records.json；
* 生成 reports/weekly/ 下的 Markdown 周复盘报告；
* 不需要任何 API key；
* 不调用飞书；
* 不调用真实大模型。

如果测试失败，请直接修复后再次测试。

---

# 十九、完成后请输出

完成后请输出：

1. 创建了哪些文件；
2. 统一 API 管理层如何工作；
3. 核心功能如何运行；
4. dry-run 测试结果；
5. 是否存在未完成事项；
6. 下一步我应该如何接入飞书；
7. 下一步我应该如何接入真实 LLM API；
8. 明确说明项目没有实现自动发布小红书、自动评论、自动私信、浏览器自动化。
