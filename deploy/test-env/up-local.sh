#!/usr/bin/env bash
# 启动 local 执行面栈(本机 WSL2)
# 用法: ./up-local.sh [up|down|status]
# 密钥: LITELLM_MASTER_KEY 与 tencent .env 保持一致(n8n/OpenHands 经网关鉴权)
set -euo pipefail
CMD="${1:-up}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$HERE/.env"

case "$CMD" in
up)
  if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<EOF
# 测试环境密钥(生成于 $(date -I)); 勿入库
LITELLM_MASTER_KEY=sk-PASTE_FROM_TENCENT_ENV
EOF
    echo "已生成 $ENV_FILE —— 请把 tencent 端 .env 的 LITELLM_MASTER_KEY 填入后重跑"
    exit 1
  fi
  grep -q PASTE_FROM_TENCENT "$ENV_FILE" && { echo "$ENV_FILE 的 LITELLM_MASTER_KEY 还是占位符"; exit 1; }
  docker compose -f "$HERE/local-stack.yml" --env-file "$ENV_FILE" up -d
  echo "GitLab 首次启动需 3-5 分钟: http://10.0.0.5:8090 (root 密码: docker exec <gitlab容器> cat /etc/gitlab/initial_root_password)"
  ;;
down)
  docker compose -f "$HERE/local-stack.yml" down
  ;;
status)
  docker compose -f "$HERE/local-stack.yml" ps
  curl -s -o /dev/null -w "gitlab  :8090 -> %{http_code}\n" --max-time 5 http://10.0.0.5:8090/users/sign_in || true
  curl -s -o /dev/null -w "openhands :8000 -> %{http_code}\n" --max-time 5 http://10.0.0.5:8000 || true
  ;;
*) echo "用法: $0 [up|down|status]"; exit 1;;
esac
