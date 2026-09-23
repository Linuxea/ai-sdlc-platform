#!/usr/bin/env bash
# 网关冒烟验证: 经 LiteLLM 调用各路由模型
# 用法: LITELLM_MASTER_KEY=sk-xxx ./probe_gateway.sh [URL]
# 退出码: 0=全部通过
set -euo pipefail
URL="${1:-http://127.0.0.1:4000}"
KEY="${LITELLM_MASTER_KEY:?环境变量 LITELLM_MASTER_KEY 未设置}"

fail=0
check() { # name model [max_tokens] [extra_json]
  local name="$1" model="$2" tokens="${3:-32}" extra="${4:-}"
  local body
  body=$(curl -sS --max-time 180 "$URL/v1/chat/completions" \
    -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"reply with the single word: pong\"}],\"max_tokens\":$tokens${extra:+\",$extra}}") || body='{"error":"curl failed"}'
  if printf '%s' "$body" | jq -e '.choices[0].message.content | select(. != "")' >/dev/null 2>&1; then
    echo "PASS  $name -> $(printf '%s' "$body" | jq -r '.choices[0].message.content' | head -c 40)"
  else
    echo "FAIL  $name -> $(printf '%s' "$body" | jq -c '.error // .' | head -c 200)"
    fail=1
  fi
}

echo "# 网关模型清单 $URL/v1/models"
curl -sS --max-time 30 "$URL/v1/models" -H "Authorization: Bearer $KEY" \
  | jq -r '.data[].id' | sed 's/^/  /' || { echo "FAIL: /v1/models 不可达"; exit 1; }

check "deepseek-flash(轻量路由)"      "deepseek-flash"
check "deepseek-v4-pro(开发主力)"     "deepseek-v4-pro"
check "deepseek-v4-pro-max(推理路由)" "deepseek-v4-pro-max" 1024  # 推理消耗预算, 需充足 max_tokens
exit $fail
