# 平台架构

## 分层总览

```
L5 治理层   人工门禁 + 质量门禁 + 可观测(Langfuse)
L4 平台层   GitLab CE | n8n | Langfuse
L3 编排层   n8n 工作流①②③④
L2 Agent层  OpenHands(开发) + n8n AI 节点(轻量角色) → LiteLLM → DeepSeek V4 / GLM
L1 方法论层 Spec Kit + BMAD v6.x 模板 + docs-as-code 工件链
```

## 控制面与执行面分离

| 面 | 组件 | 职责 |
|---|---|---|
| 控制面（大脑） | n8n | 阶段流转、审批等待（Wait + webhook 回调）、agent 调度、事件回环 |
| 执行面（手脚） | GitLab CI | 构建测试扫描部署等确定性 job；OpenHands 沙箱跑 agent 代码任务 |

**为什么不用 n8n 跑构建**：n8n 擅长编排与集成，不适合跑重编译/测试负载；GitLab CI 天然有 stage/manual approval/缓存/审计语义。
**为什么不用 GitLab CI 做总编排**：跨系统状态机（表单→agent→审批→回调）在 CI YAML 里表达晦涩，n8n 可视化+Wait 节点+失败重试更合适。

## 模型路由（v1.3 基准，以 versions.lock 冻结值为准）

| 用途 | 路由 | 理由 |
|---|---|---|
| OpenHands 开发 agent | DeepSeek Pro (+reasoning effort) | 长程编码质量 |
| 架构设计 / QA 对抗审查 | DeepSeek Pro + `max` effort | 深度推理 |
| BA / SM / Release / changelog | DeepSeek Flash | 便宜 3 倍、2500 并发 |
| fallback | GLM（槽位预留） | DeepSeek 故障降级 |

成本要点：constitution 等固定内容放 prompt 前缀吃 cache-hit 折扣（约 50 倍）；批量任务调度谷时窗口（北京白天=峰时）。

## 工件链（业务项目仓库内）

```
docs/intent/*.md → docs/spec/*.md → docs/design/ADR-*.md → docs/tasks/*.md
→ 代码+测试(MR) → 部署单 → incident.md(回流 intent)
```

每阶段产物是 git commit，PR/MR 记录审批人——审计链天然成立。

## 安全基线

- agent 全部沙箱执行（OpenHands Docker 沙箱 / n8n 容器）
- 生产凭据不进 agent 环境；DeepSeek key 只经 LiteLLM 网关暴露
- 一切代码变更经 MR + 门禁 C 人工合并
- LiteLLM 虚拟 key 按组件发放，单 key 配额
