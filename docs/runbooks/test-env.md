# Runbook — 双主机测试环境

## 拓扑与状态

| 主机 | 角色 | 服务 | 端口 |
|---|---|---|---|
| tencent (10.0.0.1) | 常驻控制面 | postgres16 / litellm v1.102.1 / n8n 2.40.5 / [已有] Harbor | 4000, 5678 |
| local (10.0.0.5, WSL2) | 执行面 | gitlab-ce 19.4.1-ce.0 / gitlab-runner v19.4.0 / openhands 1.22.0 | 8090, 2224, 8000 |

## 生命周期命令

```bash
# tencent 栈(从本机)
deploy/test-env/bootstrap-tencent.sh up      # 部署/更新(幂等, .env 首次生成后保留)
deploy/test-env/bootstrap-tencent.sh probe   # 网关三路由冒烟
deploy/test-env/bootstrap-tencent.sh down    # 销毁(含数据卷)

# local 栈
deploy/test-env/up-local.sh up               # 首次会提示填 LITELLM_MASTER_KEY(与 tencent .env 一致)
deploy/test-env/up-local.sh status           # gitlab/openhands 状态探测
deploy/test-env/gitlab-init.sh               # GitLab 就绪后一键初始化(PAT/group/项目/webhook/runner)
```

## 网络注意事项(实测踩坑)

1. **本机全局代理会劫持 WG 流量**：tencent 服务访问必须 `NO_PROXY=10.0.0.0/24`（probe 脚本已内置）
2. **镜像拉取路线**（本机 3 条管道实测）：
   - docker.io 直连：GFW 重置 ❌
   - tencent 中转 `docker save|load`（WG）：~0.4MB/s，仅应急
   - 本机代理 + crane：~0.2-1MB/s，主力路线（`~/.local/bin/crane`）
   - ghcr/registry.gitlab.com 直连：可达但 <60KB/s ❌
3. tencent 侧拉镜像走腾讯源（快）；ghcr 在 tencent 会层级别停滞 ❌

## E2E 数据流（验证用连通矩阵）

```
表单(浏览器→n8n:5678) → n8n→litellm:4000→DeepSeek → n8n→gitlab:8090(API/MR)
→ 门禁回调(浏览器表单→n8n) → n8n→openhands:8000 → openhands→litellm:4000
→ openhands→gitlab(push) → gitlab→n8n(webhook) → runner→gitlab(CI) → 部署
```

## 密钥清单（deploy/test-env/.env，两台各自持有）

| 变量 | 位置 | 用途 |
|---|---|---|
| DEEPSEEK_API_KEY | tencent | litellm 上游 |
| LITELLM_MASTER_KEY | tencent+local | n8n/OpenHands→网关鉴权 |
| N8N_ENCRYPTION_KEY | tencent | n8n 凭据加密 |
| GITLAB_TOKEN | tencent(n8n env) | GitLab API（gitlab-init 生成） |

## n8n 工作流导入/更新

```bash
scp n8n-workflows/wf*.json tencent:~/ai-sdlc-test/workflows/
ssh tencent 'for f in ~/ai-sdlc-test/workflows/wf*.json; do docker exec -u node ai-sdlc-test-n8n-1 n8n import:workflow --input=/import/$(basename $f); done'
```
注意：n8n 2.40 导入要求 JSON 含顶层 `id`（已内置 UUID，重导幂等）。
