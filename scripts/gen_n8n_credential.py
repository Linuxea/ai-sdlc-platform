#!/usr/bin/env python3
"""生成 n8n 凭据导入文件(LiteLLM OpenAI 兼容凭据)。

用法: LITELLM_MASTER_KEY=sk-xxx python3 gen_n8n_credential.py > /tmp/litellm-cred.json
导入(tencent): scp /tmp/litellm-cred.json tencent:~/ai-sdlc-test/
  ssh tencent 'docker exec -i -u node ai-sdlc-test-n8n-1 n8n import:credentials --input=/import/litellm-cred.json'
说明: 凭据 id 固定为 litellm-gw, 便于工作流 JSON 以 id 引用(见 n8n-workflows/*.md 配置清单)。
"""
import json
import os
import sys

key = os.environ.get("LITELLM_MASTER_KEY", "")
base = os.environ.get("LITELLM_BASE_URL", "http://10.0.0.1:4000/v1")
if not key or "PASTE" in key:
    print("缺 LITELLM_MASTER_KEY", file=sys.stderr)
    sys.exit(1)

cred = {
    "id": "litellm-gw",
    "name": "LiteLLM Gateway",
    "type": "n8n-nodes-base.openAiApi",
    "data": {"apiKey": key, "baseUrl": base},
}
print(json.dumps([cred], ensure_ascii=False))
