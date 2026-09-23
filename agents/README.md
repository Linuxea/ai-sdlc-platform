# agents/

五个角色 agent 提示词，由 n8n AI Agent 节点作为 system message 加载（OpenHands 开发 agent 另行在 M7 配置）。

## 角色与路由

| 文件 | 角色 | 阶段 | model_route（LiteLLM） | 产出工件 |
|---|---|---|---|---|
| [ba.md](ba.md) | 业务分析师 | 需求 | `deepseek-flash` | `docs/intent/INTENT-*.md` |
| [architect.md](architect.md) | 软件架构师 | 设计 | `deepseek-v4-pro-max` | `docs/spec/` + ADR + openapi.yaml |
| [sm.md](sm.md) | 任务拆解 | 任务 | `deepseek-flash` | `docs/tasks/TASKS-*.md` |
| [qa.md](qa.md) | 质量工程师(对抗) | 测试 | `deepseek-v4-pro-max` | QA 报告 + 补充 E2E |
| [release.md](release.md) | 发布工程师 | 发布 | `deepseek-flash` | CHANGELOG + 部署单 |

## 设计要点

- **单一职责接力**：每个角色只读上游工件、只写自己的工件，context 按角色裁剪
- **工件模板内嵌**：产出格式固定，下游（人工门禁/下一个 agent）可预期
- **打回协议**：门禁拒绝时只改批注部分 + `<!-- revised:N -->` 标记，最多 3 轮升级人工
- **新鲜度铁律**：所有角色继承「版本类事实带来源+日期、90 天未复核标 `[待复核]`」

## 参考来源（方法论借鉴，非复制）

- BMAD-METHOD v6.12.0（2026-09-23 活跃，github.com/bmad-code-org/BMAD-METHOD）— 角色接力/工件驱动
- GitHub Spec Kit v0.8.x — constitution/四阶段
- Anthropic AI-Native SDLC Playbook (2026-08) — 工件链即审计链
- EARS 需求语法 — 可验证验收标准
