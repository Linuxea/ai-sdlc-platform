# 试点项目宪章 (platform/pilot-app)

> 所有 AI agent 每次任务开始前必须完整读取。与平台仓库条款冲突时以本文件为准。

## 1. 事实与新鲜度铁律

1.1 版本类事实必须附来源 URL + 验证日期；超 90 天未复核标 `[待复核]`
1.2 依赖版本以 `pyproject.toml` 锁定为准；升级走需求流程
1.3 第三方库行为存疑时查官方文档，不凭记忆断言

## 2. 技术栈约束(测试试点专用)

| 层 | 允许 | 禁止 |
|---|---|---|
| 语言 | Python 3.12+ | 其他语言 |
| 框架 | FastAPI + uvicorn | Flask/Django/新框架 |
| 测试 | pytest(含 junitxml 输出) | 其他 runner |
| Lint | ruff | 其他 linter |
| 依赖 | pyproject.toml 声明 + pypi 清华镜像 | requirements 手写散置 |
| 数据 | 内存存储(测试试点) | 任何外部数据库 |

## 3. 安全铁律

3.1 凭据只经环境变量；硬编码 = QA BLOCKER
3.2 无敏感数据场景(试点)仍禁止引入真实凭据/PII 样例

## 4. 质量门禁

4.1 先测后实现(TDD)；验收标准逐条对应测试
4.2 ruff + pytest 全绿是 MR 进入 QA 审查的前置
4.3 API 变更必须同步 `docs/api/openapi.yaml`

## 5. 提交约定

5.1 Conventional Commits；agent 提交带 `Agent: <角色>` trailer
5.2 分支: `intent/` `spec/` `task/` `release/` 前缀
