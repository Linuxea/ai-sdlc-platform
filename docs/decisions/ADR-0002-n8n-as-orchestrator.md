# ADR-0002: n8n 为编排控制面, GitLab CI 为执行面

- 状态: 已接受 (2026-09-24)
- 决策: 不自研 LangGraph 编排、不用 Jenkins。n8n(2.x, 自托管) 负责 SDLC 状态机、审批 Wait、agent 调度与事件回环；GitLab CE 负责代码托管/MR 审批/CI 确定性执行/制品库。
- 理由: "现成工具组合"路线 2-4 周出 MVP；n8n AI Agent 节点 + MCP 双向支持 + Wait/webhook 审批模式成熟；GitLab CI 天然具备 stage/manual approval/审计语义。
- 已知代价: n8n 为 fair-code 许可（Sustainable Use），内部使用无碍、不可转售托管；自托管需自行打补丁（历史 Ni8mare CVE）→ 由工作流④巡检覆盖。
- 演进: 若后续出现 n8n 表达不了的场景，自研编排服务替换控制面，执行面不动。
