#!/usr/bin/env bash
# 一键部署 tencent 控制面栈(从本机执行)
# 用法: ./bootstrap-tencent.sh [up|down|probe]
# 密钥: DEEPSEEK_API_KEY 从本机环境取, 经 ssh 写入远端 .env(不回显)
set -euo pipefail
CMD="${1:-up}"
HOST=tencent
REMOTE_DIR=/home/ubuntu/ai-sdlc-test
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/../.."

[ -n "${DEEPSEEK_API_KEY:-}" ] || { echo "本机环境缺 DEEPSEEK_API_KEY"; exit 1; }

case "$CMD" in
up)
  ssh "$HOST" "mkdir -p $REMOTE_DIR/workflows"
  scp -q "$ROOT/deploy/litellm/config.yaml" "$HOST:$REMOTE_DIR/config.yaml"
  scp -q "$HERE/tencent-stack.yml" "$HOST:$REMOTE_DIR/docker-compose.yml"
  # 密钥类 .env: 幂等(已存在则保留, 首次生成); key 经 stdin 传输不落本机文件
  ssh "$HOST" "test -f $REMOTE_DIR/.env || cat > $REMOTE_DIR/.env" <<EOF
# 测试环境密钥(生成于 \$(date -I)); .gitignore 同名保护, 勿外传
DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY
LITELLM_MASTER_KEY=$(openssl rand -hex 24 | sed 's/^/sk-/')
N8N_ENCRYPTION_KEY=$(openssl rand -hex 24)
EOF
  # 同步工作流 JSON 供 n8n CLI 导入(T2)
  scp -q "$ROOT"/n8n-workflows/wf*.json "$HOST:$REMOTE_DIR/workflows/"
  ssh "$HOST" "cd $REMOTE_DIR && docker compose up -d --wait && docker compose ps --format '{{.Name}} {{.Status}}'"
  ;;
probe)
  MASTER=$(ssh "$HOST" "grep LITELLM_MASTER_KEY $REMOTE_DIR/.env" | cut -d= -f2)
  LITELLM_MASTER_KEY="$MASTER" "$ROOT/scripts/probe_gateway.sh" http://10.0.0.1:4000
  ;;
down)
  ssh "$HOST" "cd $REMOTE_DIR && docker compose down -v"
  ;;
*) echo "用法: $0 [up|down|probe]"; exit 1;;
esac
