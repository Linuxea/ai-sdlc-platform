# ADR-0003: 文档 docs-as-code, 工件链驱动全流程

- 状态: 已接受 (2026-09-24)
- 决策: 业务项目文档统一为仓库内 markdown（`docs/{intent,spec,design,tasks,api}` + `constitution.md`），agent 经 git 读写；MkDocs Material 渲染门户随 CI 发布。弃用独立文档系统作为 source of truth；现有 ShowDoc 至多作单向只读镜像（复用已有 MCP）。
- 理由: 工件即契约、版本化、可审计、agent 可直接读写；独立文档系统会制造第二事实源与同步漂移。
- 原则: 平台仓库自身同样 docs-as-code（本目录），自食其果。
