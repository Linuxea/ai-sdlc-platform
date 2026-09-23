#!/usr/bin/env python3
"""E2E 驱动器 — 等待工件出现 + 门禁自动回调

用法:
  # 等某工件文件在 GitLab 出现(轮询)
  python3 auto_approver.py wait-file --project platform/pilot-app --path docs/intent/INTENT-<slug>.md --ref intent/<slug>
  # 门禁审批(A/B/D 为 Wait webhook 回调)
  python3 auto_approver.py approve --slug <slug> --gate A [--comment "..."]
  python3 auto_approver.py reject  --slug <slug> --gate A --comment "验收标准不可验证"

环境: GITLAB_API(默认 http://10.0.0.5:8090) GITLAB_TOKEN N8N_PUBLIC_URL(默认 http://10.0.0.1:5678)
注意: NO_PROXY 需含 10.0.0.0/24(本机代理会劫持 WG 流量)
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from urllib.parse import quote

GITLAB_API = os.environ.get("GITLAB_API", "http://10.0.0.5:8090")
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN", "")
N8N = os.environ.get("N8N_PUBLIC_URL", "http://10.0.0.1:5678")


def http(method: str, url: str, payload: dict | None = None, token: str = "") -> tuple[int, str]:
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps(payload).encode() if payload else None)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("PRIVATE-TOKEN", token)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def cmd_wait_file(args):
    pid = quote(args.project, safe="")
    url = f"{GITLAB_API}/api/v4/projects/{pid}/repository/files/{quote(args.path, safe='')}/raw?ref={quote(args.ref, safe='')}"
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        code, body = http("GET", url, token=GITLAB_TOKEN)
        if code == 200:
            print(f"OK file ready: {args.path}@{args.ref} ({len(body)} bytes)")
            return 0
        time.sleep(args.interval)
    print(f"FAIL: {args.timeout}s 内未出现 {args.path}@{args.ref}", file=sys.stderr)
    return 1


def _gate(args, approved: bool) -> int:
    gate = args.gate.upper()
    suffix = f"gate-{gate.lower()}-{args.slug}"
    url = f"{N8N}/webhook/{suffix}"
    payload = {"approved": approved, "comment": args.comment or ""}
    code, body = http("POST", url, payload)
    ok = code in (200, 201, 202)
    print(f"{'PASS' if ok else 'FAIL'} gate-{gate} {'approve' if approved else 'reject'} -> [{code}] {body[:200]}")
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    wf = sub.add_parser("wait-file")
    wf.add_argument("--project", required=True)
    wf.add_argument("--path", required=True)
    wf.add_argument("--ref", default="main")
    wf.add_argument("--timeout", type=int, default=1800)
    wf.add_argument("--interval", type=int, default=15)
    wf.set_defaults(fn=cmd_wait_file)

    ap = sub.add_parser("approve")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--gate", required=True, choices=["A", "B", "D", "a", "b", "d"])
    ap.add_argument("--comment", default="")
    ap.set_defaults(fn=lambda a: _gate(a, True))

    rj = sub.add_parser("reject")
    rj.add_argument("--slug", required=True)
    rj.add_argument("--gate", required=True, choices=["A", "B", "D", "a", "b", "d"])
    rj.add_argument("--comment", required=True)
    rj.set_defaults(fn=lambda a: _gate(a, False))

    args = p.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
