# 工作流① — SDLC 主流程 (wf1-sdlc-main)

`wf1-sdlc-main.json` 为可导入 n8n 2.x 的骨架（拓扑完整、参数含表达式，凭据与实例地址导入后配置）。

## 阶段拓扑

```
表单 → 初始化 → [BA·flash] → GitLab MR → ⛔门禁A(表单回调)
  ↖ 打回(round≤3) ↙
→ [Architect·pro-max] → GitLab MR → ⛔门禁B(表单回调)
→ [SM·flash] → GitLab MR
→ OpenHands(创建任务) → webhook(完成回调) → GitLab Pipeline → webhook(CI结果)
   ├─ 失败 → 通知人工
   └─ 全绿 → [QA·pro-max] → MR 评论(QA报告) → ⛔门禁C(GitLab人工合并)
→ [Release·flash] → GitLab MR(部署单) → ⛔门禁D(表单回调)
→ GitLab 部署(blue-green) → 归档
```

## 节点-路由对照

| 阶段 | Agent 节点 | 模型子节点 | LiteLLM 路由 |
|---|---|---|---|
| 需求 | BA · 意图文档 | DeepSeek Flash 模型 | `deepseek-flash` |
| 设计 | Architect · 规格与ADR | DeepSeek Pro-Max 模型 | `deepseek-v4-pro-max` |
| 任务 | SM · 任务拆解 | DeepSeek Flash 模型(复用) | `deepseek-flash` |
| 测试 | QA · 对抗性审查 | DeepSeek Pro-Max 模型(复用) | `deepseek-v4-pro-max` |
| 发布 | Release · 发布材料 | DeepSeek Flash 模型(复用) | `deepseek-flash` |

## 导入后配置清单（画布内也有便签）

1. 凭据：两个模型子节点挂 OpenAI 类型 credential（key=`LITELLM_MASTER_KEY`；baseURL 已指向 `$env.LITELLM_BASE_URL`）
2. n8n 环境变量：`LITELLM_BASE_URL` `GITLAB_TOKEN` `OPENHANDS_URL` `OPENHANDS_TOKEN` `TARGET_REPO` `N8N_PUBLIC_URL`
3. 全局替换 `https://gitlab.example.com` 为实际 GitLab 实例
4. 修正两处已知占位：QA 评论节点的 MR IID 透传；OpenHands 请求体字段（以部署版本 API 文档为准）
5. 建议把各 agent systemMessage 替换为平台仓库 `agents/*.md` 全文，UI 调试通过后导出回本目录

## 门禁回调契约

A/B/D 门禁（Wait webhook 挂起，审批表单提交后 POST 回调）：

```json
{ "approved": true, "comment": "可选批注" }
```

- `approved=false` → 打回上游 agent 定点修订（`rejectNote` 带入），round≥3 升级人工
- 门禁 C 由 GitLab merge event webhook 驱动（人在 GitLab 页面审 diff 后点合并）
