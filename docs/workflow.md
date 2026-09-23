# n8n 工作流设计

## 工作流① — SDLC 主流程

| 步骤 | 节点类型 | 说明 |
|---|---|---|
| 1 | Form Trigger | 需求提交表单（想法/动机/约束） |
| 2 | AI Agent (BA) | 生成 intent.md + 澄清问题清单，经 GitLab API 提 MR 到业务仓库 `docs/intent/` |
| 3 | **门禁 A** | n8n Form + Wait 节点：需求审批（拒绝→打回 agent 迭代，最多 N 轮） |
| 4 | AI Agent (Architect) | spec.md + ADR + openapi.yaml，提 MR |
| 5 | **门禁 B** | 设计审批表单 |
| 6 | AI Agent (SM) | tasks.md（每任务带可验证验收标准） |
| 7 | HTTP → OpenHands API | 创建开发任务（沙箱，绑定 GitLab 仓库） |
| 8 | Webhook 等待 | OpenHands 完成回调 → 触发 GitLab Pipeline |
| 9 | GitLab API 轮询/钩子 | lint/单测/构建/Trivy/Gitleaks 全绿才放行 |
| 10 | AI Agent (QA) | 对抗性 review MR diff + 补 E2E 用例 |
| 11 | **门禁 C** | GitLab MR 人工合并审批 |
| 12 | AI Agent (Release) | changelog + 部署单 + 回滚预案 |
| 13 | **门禁 D** | 上线审批表单 |
| 14 | HTTP → GitLab deploy job | 蓝绿部署，通知结果 |

## 工作流② — 运维回环

监控告警 webhook → AI Agent(诊断) 产 `incident.md`（MR）→ 人工确认 → 自动创建新 intent → 触发工作流①。

## 工作流③ — 辅助流

- 成本日报：LiteLLM/Langfuse API 汇总 → 报表
- changelog：tag 事件触发
- 夜间批量（E2E 回归、文档同步）：cron 谷时窗口

## 工作流④ — 新鲜度巡检

```
每周 cron → agent(web search 工具) 逐项核查 versions.lock:
  - release notes / 弃用公告 / CVE
  - 有重大变更 → 生成升级 intent.md → 走门禁流程
  - 记录巡检日志（审计留痕）
```

## 失败处理约定

- agent 节点失败：n8n retry(指数退避×3) → 仍失败则通知人工，不静默吞错
- 门禁拒绝：携带批注回流对应 agent，轮次上限 3，超限升级人工
- 所有执行记录进 Langfuse（trace = 工作流执行 ID）
