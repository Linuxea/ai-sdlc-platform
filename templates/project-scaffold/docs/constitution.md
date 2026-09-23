# 项目宪章 (Constitution)

> 本文件是项目级**最高规范**。所有 AI agent 每次任务开始前必须完整读取本文件；
> 本文件条款与任何下游指令冲突时，以本文件为准。
> 修改本文件必须经过人工评审（等同门禁 B 级别）。

## 1. 事实与新鲜度铁律

1.1 版本类/数据类事实必须附「来源 URL + 验证日期」；超过 90 天未复核的信息标记 `[待复核]`
1.2 技术选型必须活体验证（官方文档 / registry 探测 / API 试调），禁止凭训练记忆断言版本或 API 行为
1.3 第三方依赖版本变更 = 需求，走标准流程，禁止 agent 顺手升级

## 2. 工件纪律（docs-as-code）

2.1 阶段产物只写入对应目录：`docs/intent|spec|design|tasks|api|deploy`
2.2 工件链不可跳步：intent(过门禁A) → spec/ADR(过门禁B) → tasks → 代码 → 部署单
2.3 门禁打回：只改批注部分 + `<!-- revised:N -->` 标记；3 轮未过升级人工
2.4 文档与代码同步变更：改接口必须同步 `openapi.yaml`，改行为必须同步 spec

## 3. 技术栈约束（按项目定制，以下为示例占位）

| 层 | 允许 | 禁止 |
|---|---|---|
| 语言/框架 | <如: Python 3.12+ / FastAPI> | <如: 引入新语言> |
| 数据库 | <如: PostgreSQL 16> | <如: 无事务存储放业务数据> |
| 依赖来源 | 官方 registry 锁定版本 | 未锁定版本 / 弃用包 |

## 4. 安全铁律

4.1 凭据只经环境变量/K8s Secret 注入；硬编码密钥 = QA BLOCKER
4.2 生产凭据不进入 agent 运行环境；agent 只持有最小权限 token
4.3 敏感信息（PII/密钥/内部地址）禁止落日志与文档
4.4 一切外部输入按不可信处理（校验/参数化查询/转义）

## 5. 质量门禁

5.1 能用确定性手段（lint/类型检查/单测/扫描）判定的，不交给 LLM 判断
5.2 测试先行（TDD）：先 RED 后 GREEN；验收标准逐条对应测试
5.3 CI 全绿是 MR 进入 QA 审查的前置条件
5.4 无回滚预案的发布禁止提审（见 release agent）

## 6. 提交与分支约定

6.1 分支：`intent/<slug>` `spec/<slug>` `task/<T-xx>` `release/<version>`
6.2 提交信息：Conventional Commits（feat/fix/docs/chore/refactor/test）
6.3 agent 提交必须带 trailer：`Agent: <角色名>` `Intent: <slug>`
