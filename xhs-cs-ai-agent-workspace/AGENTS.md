# AGENTS.md

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
