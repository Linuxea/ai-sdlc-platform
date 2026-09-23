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

echo "[2/7] 生成 root PAT(90 天有效, 与新鲜度纪律对齐)..."
TOKEN="glpat-$(openssl rand -hex 20)"
docker exec "$GLAB_CONTAINER" gitlab-rails runner "
  u = User.find_by_username('root')
  t = u.personal_access_tokens.new(name: 'platform-test', scopes: [:api], expires_at: 90.days.from_now)
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

echo "[5/7] 放行内网 webhook 并配置..."
# GitLab 19 默认禁止 webhook 打内网地址(Outbound 安全), 测试环境需显式放行
api -X PUT "$GL/api/v4/application/settings?allow_local_requests_from_web_hooks_and_services=true" \
  | jq -r 'if .message then .message else "  local webhook 已放行" end'
# 注意: 事件字段是 merge_requests_events(复数); 用 JSON body 避免 form 编码歧义
api -X POST "$GL/api/v4/projects/platform%2Fpilot-app/hooks" -H "Content-Type: application/json" \
  -d '{"url":"http://10.0.0.1:5678/webhook/gitlab-pipeline-done","pipeline_events":true,"push_events":false,"enable_ssl_verification":false}' \
  | jq -r '"  pipeline-hook: " + (.id // .error // .message | tostring)'
api -X POST "$GL/api/v4/projects/platform%2Fpilot-app/hooks" -H "Content-Type: application/json" \
  -d '{"url":"http://10.0.0.1:5678/webhook/gitlab-mr-merged","merge_requests_events":true,"push_events":false,"enable_ssl_verification":false}' \
  | jq -r '"  mr-merged-hook: " + (.id // .error // .message | tostring)'

echo "[6/7] 注册 gitlab-runner(新 API 流程: 先建 runner 拿 token)..."
RUNNER_TOKEN=$(api -X POST "$GL/api/v4/user/runners" -H "Content-Type: application/json" \
  -d '{"runner_type":"project_type","project_id":2,"description":"pilot-runner","run_untagged":true}' \
  | jq -r '.token // empty')
if [ -n "$RUNNER_TOKEN" ]; then
  docker rm -f pilot-runner 2>/dev/null || true
  docker run -d --name pilot-runner --restart unless-stopped \
    -v pilot-runner-config:/etc/gitlab-runner -v /var/run/docker.sock:/var/run/docker.sock \
    gitlab/gitlab-runner:v19.4.0 >/dev/null
  docker exec pilot-runner gitlab-runner register --non-interactive \
    --url "$GL" --token "$RUNNER_TOKEN" --executor docker \
    --docker-image python:3.12-slim 2>&1 | tail -1
  echo "  runner 已注册"
else
  echo "  runner API 创建失败 — 手动注册(项目设置→Runners→new project runner)"
fi

echo "[7/7] 完成 — .env 已含 GITLAB_TOKEN, 重启 n8n 使其生效:"
echo "  ssh tencent 'cd ~/ai-sdlc-test && echo GITLAB_TOKEN=$TOKEN >> .env && docker compose up -d n8n'"
