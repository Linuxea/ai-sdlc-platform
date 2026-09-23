#!/usr/bin/env bash
# GitLab 测试实例一键初始化(在 local 主机执行, 需 GitLab 已就绪)
# 步骤: 就绪等待 → root PAT(rails 生成) → group/project → 推送平台/试点仓库 → webhook → runner
# 产出: deploy/test-env/.env 追加 GITLAB_TOKEN=glpat-...
set -euo pipefail
export NO_PROXY="10.0.0.0/24,localhost,127.0.0.1,${NO_PROXY:-}"; export no_proxy="$NO_PROXY"
GL=http://10.0.0.5:8090
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
ENV_FILE="$HERE/.env"
GLAB_CONTAINER=$(docker ps --format '{{.Names}}' | grep -m1 gitlab)

echo "[1/7] 等待 GitLab 就绪(首次 3-5 分钟)..."
until curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$GL/users/sign_in" | grep -q 200; do sleep 10; done
echo "  就绪"

echo "[2/7] 生成 root PAT..."
TOKEN="glpat-$(openssl rand -hex 20)"
docker exec "$GLAB_CONTAINER" gitlab-rails runner "
  u = User.find_by_username('root')
  t = u.personal_access_tokens.new(name: 'platform-test', scopes: [:api], expires_at: nil)
  t.set_token('$TOKEN')
  t.save!
" >/dev/null 2>&1 || { echo "  rails 生成失败 — 手动在 UI 创建 PAT 后写入 $ENV_FILE"; exit 1; }
echo "GITLAB_TOKEN=$TOKEN" >> "$ENV_FILE"
echo "  PAT 已写入 .env"

api() { curl -sS -H "PRIVATE-TOKEN: $TOKEN" "$@"; }

echo "[3/7] 创建 group 与项目..."
api -X POST "$GL/api/v4/groups" -d name=platform -d path=platform | jq -r '.id // .message' | sed 's/^/  group: /'
api -X POST "$GL/api/v4/projects" -d name=ai-sdlc-platform -d namespace_id=platform -d visibility=internal | jq -r '.id // .message' | sed 's/^/  platform repo: /'
api -X POST "$GL/api/v4/projects" -d name=pilot-app -d namespace_id=platform -d visibility=internal | jq -r '.id // .message' | sed 's/^/  pilot repo: /'

echo "[4/7] 推送平台仓库与试点脚手架..."
git -C "$ROOT" remote remove gitlab-test 2>/dev/null || true
git -C "$ROOT" remote add gitlab-test "http://root:$TOKEN@10.0.0.5:8090/platform/ai-sdlc-platform.git"
git -C "$ROOT" push -q gitlab-test main
PILOT=$(mktemp -d); cp -r "$HERE/pilot-app/." "$PILOT/"
git -C "$PILOT" init -q -b main && git -C "$PILOT" add -A
git -C "$PILOT" -c user.name=platform -c user.email=platform@test commit -qm "chore: pilot scaffold from platform template"
git -C "$PILOT" remote add origin "http://root:$TOKEN@10.0.0.5:8090/platform/pilot-app.git"
git -C "$PILOT" push -q origin main
echo "  已推送"

echo "[5/7] 配置 webhook(n8n 回调)..."
for hook in "pipeline-events" "merge-request-events"; do
  api -X POST "$GL/api/v4/projects/platform%2Fpilot-app/hooks" \
    -d url="http://10.0.0.1:5678/webhook/gitlab-pipeline-done" \
    -d "enable_ssl_verification=false" -d "$hook=true" | jq -r '.id // .message' | sed "s/^/  $hook: /"
done
api -X POST "$GL/api/v4/projects/platform%2Fpilot-app/hooks" \
  -d url="http://10.0.0.1:5678/webhook/gitlab-mr-merged" \
  -d "enable_ssl_verification=false" -d "merge_request_events=true" | jq -r '.id // .message' | sed 's/^/  mr-merged: /'

echo "[6/7] 注册 gitlab-runner..."
RT=$(api "$GL/api/v4/projects/platform%2Fpilot-app" | jq -r '.runners_token // empty')
if [ -n "$RT" ]; then
  docker rm -f pilot-runner 2>/dev/null || true
  docker run -d --name pilot-runner --restart unless-stopped \
    -v pilot-runner-config:/etc/gitlab-runner -v /var/run/docker.sock:/var/run/docker.sock \
    gitlab/gitlab-runner:v19.4.0 >/dev/null
  docker exec pilot-runner gitlab-runner register --non-interactive \
    --url "$GL" --token "$RT" --executor docker \
    --docker-image python:3.12-slim --docker-pulls-disabled=false 2>&1 | tail -1
  echo "  runner 已注册"
else
  echo "  runners_token 不可读(API 行为变更?) — 手动注册: docker exec ... gitlab-runner register (token 见项目设置)"
fi

echo "[7/7] 完成 — .env 已含 GITLAB_TOKEN, 重启 n8n 使其生效:"
echo "  ssh tencent 'cd ~/ai-sdlc-test && echo GITLAB_TOKEN=$TOKEN >> .env && docker compose up -d n8n'"
