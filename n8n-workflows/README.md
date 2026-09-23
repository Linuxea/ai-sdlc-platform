# n8n-workflows/

n8n 2.x 可导入的工作流 JSON（骨架完整：拓扑+参数+表达式；凭据导入后配置，见各 .md 配置清单）。

| 文件 | 工作流 | 状态 |
|---|---|---|
| [wf1-sdlc-main.json](wf1-sdlc-main.json) | ① SDLC 主流程（需求→设计→任务→开发→测试→发布，4 道门禁） | M4 ✅ 骨架 |
| wf2-ops-loop.json | ② 运维回环（告警→诊断→incident.md→回流①） | M6 |
| wf3-helpers.json | ③ 辅助流（成本日报/changelog/谷时批量） | M6 |
| wf4-freshness.json | ④ 新鲜度巡检（周检 versions.lock→升级 intent） | M6 |

## 版本化约定

- n8n 版本锁定见根目录 `versions.lock`
- UI 微调后：n8n 导出 → 覆盖本目录对应 JSON → commit（diff 即工作流变更审计）
- 门禁回调契约与环境变量清单见各工作流同名 `.md`
