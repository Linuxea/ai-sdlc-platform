# Runbook — K8s 部署（M7 配置 → 集群落地）

> 前提：K8s 集群就绪（≥1.28 建议）、StorageClass、Envoy Gateway（Gateway API）、cert-manager、专用节点池（GitLab ≥4C8G）。
> 版本纪律：一切以 `versions.lock` 为准；部署当天先跑 `scripts/probe_deepseek.py` 与各组件 release 复核（wf4 上线后由其接管）。

## 部署顺序（依赖驱动）

```
0. 命名空间 ai-sdlc + 共享存储层: PostgreSQL 16 / Redis 7 / ClickHouse / MinIO
1. LiteLLM        deploy/litellm/      (config.yaml→ConfigMap; 验证 probe_gateway.sh)
2. n8n            deploy/n8n/          (导入 wf1-4 JSON; 按便签接凭据; N8N_ENCRYPTION_KEY 备份!)
3. GitLab CE      deploy/gitlab/       (chart 10.4.1; 外置 PG/Redis/MinIO; 开 Registry+Runner)
4. OpenHands      deploy/openhands/    (manifest; 沙箱方案按当时官方文档)
5. Langfuse       deploy/langfuse/     (v4 架构核对; LiteLLM 开 success_callback)
```

## Secret 清单（全部 `kubectl create secret` 预建，禁止入库）

| Secret | 用途 |
|---|---|
| litellm-secrets / litellm-db | 网关 masterKey、DB URL |
| litellm-virtual-key-openhands | OpenHands 专用网关虚拟 key（最小权限+配额） |
| n8n-encryption | n8n 凭据加密 key（**丢失=凭据全失效**，离线备份） |
| gitlab-platform-token / gitlab-pg / redis-shared | n8n 调 GitLab API 的 PAT、DB 口令 |
| openhands-token | wf1 调 OpenHands API |
| langfuse-nextauth/-pg/-clickhouse/-redis/-s3 | Langfuse 各依赖连接 |

DeepSeek key 只进 LiteLLM（`kubectl create secret` 或 env 注入），任何组件不直连厂商。

## 各组件验证

| 组件 | 验证命令 |
|---|---|
| LiteLLM | `scripts/probe_gateway.sh https://litellm.example.com`（三路由全 PASS） |
| n8n | 手动执行 wf1 到门禁 A 挂起即通 |
| GitLab | 建 platform group + scaffold 项目，push 后 pages/gitleaks job 出现 |
| OpenHands | 经 wf1 步骤 13 创建一次真实任务 |
| Langfuse | wf1 跑一轮后 trace 出现、成本可查 |

## 升级与回滚

- 升级：wf4 巡检 → UPGRADE INTENT → 门禁 A 评审 → 按 chart/镜像 lock 更新 values → `helm upgrade`
- 回滚：`helm rollback <release>`；n8n workflow 随库 JSON 重导入；GitLab 升级前 `kubectl get gitlab` 备份 CR + DB 快照
- 凡 versions.lock 变更：commit 必须含来源 URL 与验证日期（审计链）

## 已知风险备注

- GitLab 19.x Gateway API 迁移中：若集群无 Envoy，可临时 `nginx-ingress.enabled: true`（20.0 移除，届时必须迁移）
- n8n 高频迭代：每次 minor 升级前在测试命名空间导入 wf1-4 验证（ executions 兼容性）
- OpenHands 沙箱：镜像 tag 之外，runtime 隔离方案必须按部署当日文档确认（安全基线，不可省）
