#!/usr/bin/env bash
# ============================================================
# 蓝绿部署脚本骨架 — release agent 产出的部署单(回滚预案)必须与本脚本一致
# 前置: K8s 集群凭据(DEPLOY_KUBECONFIG 变量)、命名空间 DEPLOY_NAMESPACE
# 验收: 冒烟失败自动切回旧版本并退出非零(宪章5.4: 无有效回滚=禁止上线)
# ============================================================
set -euo pipefail

NS="${DEPLOY_NAMESPACE:?DEPLOY_NAMESPACE 未设置}"
SVC="${DEPLOY_SERVICE:?DEPLOY_SERVICE 未设置}"
NEW_COLOR="$(date +%s)"            # 新版本标识
OLD_COLOR="$(kubectl -n "$NS" get svc "$SVC" -o jsonpath='{.spec.selector.color}' || echo blue)"
[ "$OLD_COLOR" = "$NEW_COLOR" ] && OLD_COLOR=blue

log() { printf '[blue-green] %s\n' "$*"; }

# 1. 部署新版本 (green) — 不接流量
log "部署新版本 color=$NEW_COLOR (deployment/$SVC-$NEW_COLOR)"
kubectl -n "$NS" set image "deployment/$SVC-$NEW_COLOR" \
  "app=$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG" --record 2>/dev/null \
  || kubectl -n "$NS" create deployment "$SVC-$NEW_COLOR" --image="$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG"

# 2. 等待新版本就绪
if ! kubectl -n "$NS" rollout status "deployment/$SVC-$NEW_COLOR" --timeout="${ROLLOUT_TIMEOUT:-300}s"; then
  log "新版本未就绪, 保持旧版本 $OLD_COLOR 承接流量"; exit 1
fi

# 3. 切换流量
log "切换流量: $OLD_COLOR -> $NEW_COLOR"
kubectl -n "$NS" patch svc "$SVC" -p "{\"spec\":{\"selector\":{\"color\":\"$NEW_COLOR\"}}}"

# 4. 冒烟验证 (量化触发条件与部署单一致)
if ! curl -fsS --max-time 10 "${SMOKE_URL:?SMOKE_URL 未设置}/health" >/dev/null; then
  log "冒烟失败! 自动回滚流量 -> $OLD_COLOR"
  kubectl -n "$NS" patch svc "$SVC" -p "{\"spec\":{\"selector\":{\"color\":\"$OLD_COLOR\"}}}"
  exit 1
fi
log "上线成功: $NEW_COLOR (旧版本 $OLD_COLOR 保留 ${KEEP_OLD:-24}h 供观察窗口内回滚)"

# TODO(按项目落地): 观察窗口后清理旧 deployment; 数据库迁移按部署单顺序在切换前执行
