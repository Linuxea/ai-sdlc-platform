#!/usr/bin/env python3
"""DeepSeek 模型活体探测 — 新鲜度检查的标准工具。

用途:
  1. M1 冻结 versions.lock 前的验证
  2. n8n 工作流④(新鲜度巡检)每周复跑, 对比模型 ID 是否变动

用法:
  python3 probe_deepseek.py            # 列出线上模型
  python3 probe_deepseek.py --chat     # 额外发一条最小完成度请求验证可用性

退出码: 0=成功, 1=失败。密钥只从环境变量 DEEPSEEK_API_KEY 读取。
"""
import json
import os
import sys
import urllib.request
from datetime import date

API_BASE = "https://api.deepseek.com"


def http_json(url: str, payload: dict | None = None) -> dict:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        print("FAIL: 环境变量 DEEPSEEK_API_KEY 未设置", file=sys.stderr)
        sys.exit(1)
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main() -> None:
    print(f"# DeepSeek 活体探测 @ {date.today().isoformat()} | source: {API_BASE}/models")
    result = http_json(f"{API_BASE}/models")
    models = result.get("data", [])
    if not models:
        print("FAIL: /models 返回为空 — 模型清单可能已变更, 人工介入", file=sys.stderr)
        sys.exit(1)
    for m in models:
        effort = ",".join(m.get("effort", {}).get("supported_levels", [])) or "-"
        print(f"  {m['id']:<22} | {m.get('name',''):<24} | ctx={m.get('context_window',0)} | effort={effort}")

    if "--chat" in sys.argv:
        model_id = models[0]["id"]
        print(f"# 最小完成度验证: {model_id}")
        out = http_json(f"{API_BASE}/chat/completions", {
            "model": model_id,
            "messages": [{"role": "user", "content": "ping, reply with pong only"}],
            "max_tokens": 16,
            "stream": False,
        })
        content = out["choices"][0]["message"].get("content", "")
        print(f"  -> {content!r}")
    print("OK")


if __name__ == "__main__":
    main()
