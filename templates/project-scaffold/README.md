# project-scaffold

业务项目初始化模板——新项目由平台（n8n 工作流或管理员）以此目录为模板创建仓库。

## 结构

```
docs/
  constitution.md   项目宪章(所有 agent 必读的最高规范, 含新鲜度/安全/质量铁律)
  intent/           阶段1: 需求意图(ba agent 产出)
  spec/             阶段2: 技术规格(architect agent 产出)
  design/           阶段2: 架构决策记录 ADR
  tasks/            阶段3: 任务拆解(sm agent 产出)
  api/              OpenAPI 契约(单一事实源)
  deploy/           发布部署单(release agent 产出)
mkdocs.yml          文档门户配置(CI 自动发布)
.gitlab-ci.yml      引用平台 pipelines 模板的 CI 入口
```

## 初始化步骤

1. 复制本目录到新仓库（排除 `.gitkeep` 与本 README）
2. 定制 `docs/constitution.md` 第 3 节技术栈约束（必做，占位符不删无法过门禁 B）
3. 填写 `mkdocs.yml` 的站点名与描述
4. 按需覆盖 `.gitlab-ci.yml` 变量开关

## 约定

- 平台 agent 提示词（`agents/`）与本模板的工件目录强耦合，改名需同步平台仓库
- MkDocs Material 版本锁定见平台 `versions.lock`（当前 9.7.7, 2026-07-17 验证）
