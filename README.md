# ai-sdlc-platform

> 端到端 AI 研发流水线：需求评审 → 方案设计 → 开发 → 测试 → 上线，全流程由 AI agent 执行，人在门禁处把关。Build in public。

## 这是什么

一套**公司级、开源自托管**的 AI 软件研发流水线（AI-Native SDLC）。不是给某个 IDE 加插件，而是把整个软件交付流程重构为：

- **规格先行**（Spec-Driven）：需求/设计/任务全部是 git 里的 markdown 工件，工件链即审计链
- **agent 干活**：BA/架构/开发/QA/发布五种角色 agent 接力执行，人类不再逐行写代码
- **人守门禁**：需求评审、设计评审、MR 合并、上线审批四道人工门禁
- **搜索验证内置**：所有版本类事实强制带时间戳与来源，运行期每周新鲜度巡检——对抗 LLM 知识过时

## 架构

```
┌─ L5 治理层 ── 人工门禁(n8n表单+GitLab MR) + 质量门禁(GitLab CI) + Langfuse(trace/成本/审计)
├─ L4 平台层 ── GitLab CE(代码/MR审批/CI执行面/制品库) + n8n(编排控制面) + Langfuse
├─ L3 编排层 ── n8n 工作流:
│     ① SDLC 主流程(需求→设计→开发→测试→上线, 含 4 道审批 Wait 门禁)
│     ② 运维回环(监控告警→诊断 agent→incident.md→回流①)
│     ③ 辅助流(成本日报/changelog/夜间批量, 谷时窗口)
│     ④ 新鲜度巡检(每周核查组件版本/弃用公告/CVE→升级 intent)
├─ L2 Agent层 ─ OpenHands(Agent Canvas, 开发执行, Docker 沙箱)
│               + n8n AI Agent 节点(轻量角色: BA/架构/SM/QA/Release)
│               经 LiteLLM 网关: DeepSeek V4 家族(主力) / GLM(fallback 槽位)
└─ L1 方法论层 ─ Spec Kit + BMAD v6.x 模板 + docs-as-code 工件链
```

## 六阶段流程

```mermaid
flowchart LR
    A[表单提交想法] --> B[BA agent<br/>intent.md + PRD]
    B --> G1{{门禁A<br/>需求审批}}
    G1 --> C[Architect agent<br/>spec.md + ADR + OpenAPI]
    C --> G2{{门禁B<br/>设计审批}}
    G2 --> D[SM agent<br/>tasks.md]
    D --> E[OpenHands dev agent<br/>TDD 逐任务开发]
    E --> F[GitLab CI<br/>lint/单测/构建/扫描]
    F --> H[QA agent<br/>对抗性 review + E2E]
    H --> G3{{门禁C<br/>MR 合并审批}}
    G3 --> I[Release agent<br/>changelog/部署单/回滚预案]
    I --> G4{{门禁D<br/>上线审批}}
    G4 --> J[蓝绿部署]
    J --> K[监控/告警]
    K -. incident.md 回流 .-> A
```

## 组件选型

| 组件 | 角色 | 版本锁定 |
|---|---|---|
| DeepSeek V4 家族 | 主力模型（Pro 推理 / Flash 高吞吐） | 见 `versions.lock` |
| LiteLLM Proxy | 模型网关：路由/配额/成本/降级 | 见 `versions.lock` |
| n8n | 编排控制面（工作流①–④） | 见 `versions.lock` |
| GitLab CE | 代码/MR/CI 执行面/制品库 | 见 `versions.lock` |
| OpenHands (Agent Canvas) | 开发执行 agent | 见 `versions.lock` |
| Langfuse v3 | LLM 可观测 | 见 `versions.lock` |

**版本纪律**：部署配置只允许引用 [`versions.lock`](versions.lock) 中经活体验证的版本，禁止 `latest`。每个版本的验证日期与来源 URL 均记录在案。

## 目录结构

```
docs/                    平台自身文档(docs-as-code, 自食其果)
  decisions/             ADR 架构决策记录
  runbooks/              部署/运维手册
deploy/                  各组件部署配置(docker-compose + Helm values)
agents/                  五个角色 agent 提示词
templates/project-scaffold/  业务项目脚手架模板(docs-as-code 结构)
n8n-workflows/           工作流①–④ 可导入 JSON
pipelines/               GitLab CI 模板(lint/测试/扫描/部署)
scripts/                 模型探测/新鲜度巡检/部署脚本
versions.lock            组件版本锁定清单(含验证日期与来源)
```

## 里程碑

| # | 里程碑 | 状态 |
|---|---|---|
| M0 | 仓库 bootstrap | ✅ |
| M1 | LiteLLM 网关（DeepSeek 活体验证 + 冒烟） | ⏳ |
| M2 | 角色提示词（BA/架构/SM/QA/Release） | |
| M3 | 项目脚手架模板（docs-as-code） | |
| M4 | n8n 工作流① 主流程编排 | |
| M5 | GitLab CI 模板 + 蓝绿部署 | |
| M6 | 工作流②③④（回环/辅助/巡检） | |
| M7 | K8s Helm values + 部署 runbook | |

## 核心原则（写进 agent 宪法）

1. **工件链即审计链**：每阶段产物是 git 里的 markdown，不可跳过
2. **版本类事实必须带时间戳和来源**：引用超过 90 天未复核的版本信息视为缺陷
3. **技术选型必须活体验证**：查官方文档 + API 探测，不信任二手资料
4. **凭据最小化**：key 只经环境变量注入，永不落盘入库
5. **确定性优先于智能**：能 lint/测试/扫描判定的，不交给 LLM 判断

## License

MIT
