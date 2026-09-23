#!/usr/bin/env python3
"""E2E 工件链断言器 — 核对一次完整运行留下的全部工件(L3 验收)

用法:
  python3 e2e_check.py --project platform/pilot-app --slug <slug> [--mr-merged]

断言(L3 通过线):
  1. docs/intent/INTENT-<slug>.md 存在且含澄清问题/成功判据章节
  2. docs/spec/SPEC-<slug>.md 存在
  3. docs/design/ 下存在至少 1 个 ADR-*.md
  4. docs/tasks/TASKS-<slug>.md 存在且含任务复选框
  5. docs/deploy/RELEASE-*.md 存在且含回滚预案章节
  6. [--mr-merged] 任务分支 MR 已合并到 main
  7. 提交信息含 Agent: trailer(审计链)
退出码 0=工件链完整
"""
import argparse
import json
import os
import re
import sys
from urllib.parse import quote

GITLAB_API = os.environ.get("GITLAB_API", "http://10.0.0.5:8090")
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN", "")


def api(path: str) -> tuple[int, object]:
    import urllib.request
    req = urllib.request.Request(f"{GITLAB_API}{path}")
    if GITLAB_TOKEN:
        req.add_header("PRIVATE-TOKEN", GITLAB_TOKEN)
    try:
        import urllib.error
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, None


def raw(project: str, path: str, ref: str = "main") -> str | None:
    pid = quote(project, safe="")
    code, _ = api(f"/api/v4/projects/{pid}/repository/files/{quote(path, safe='')}/raw?ref={quote(ref, safe='')}")
    return None if code != 200 else _raw_text(project, path, ref)


def _raw_text(project, path, ref):
    import urllib.request
    from urllib.parse import quote as q
    req = urllib.request.Request(
        f"{GITLAB_API}/api/v4/projects/{q(project, safe='')}/repository/files/{q(path, safe='')}/raw?ref={q(ref, safe='')}")
    if GITLAB_TOKEN:
        req.add_header("PRIVATE-TOKEN", GITLAB_TOKEN)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--mr-merged", action="store_true")
    p.add_argument("--task-ref", default=None, help="任务分支名(默认从 task/<slug> 找合并记录)")
    args = p.parse_args()

    checks, failed = [], []

    def ck(name: str, ok: bool, detail: str = ""):
        checks.append((name, ok, detail))
        if not ok:
            failed.append(name)
        print(f"{'PASS' if ok else 'FAIL'}  {name} {detail}")

    intent = raw(args.project, f"docs/intent/INTENT-{args.slug}.md")
    ck("intent.md 存在", intent is not None)
    ck("intent 含成功判据", bool(intent and re.search(r"成功判据|验收", intent)))

    spec = raw(args.project, f"docs/spec/SPEC-{args.slug}.md")
    ck("spec.md 存在", spec is not None)

    code, tree = api(f"/api/v4/projects/{quote(args.project, safe='')}/repository/tree?path=docs/design&ref=main")
    adrs = [t["name"] for t in (tree or []) if t.get("name", "").startswith("ADR-")] if code == 200 else []
    ck("ADR ≥1 个", len(adrs) > 0, str(adrs))

    tasks = raw(args.project, f"docs/tasks/TASKS-{args.slug}.md")
    ck("tasks.md 存在", tasks is not None)
    ck("tasks 含复选框", bool(tasks and "- [ ]" in tasks))

    code, tree = api(f"/api/v4/projects/{quote(args.project, safe='')}/repository/tree?path=docs/deploy&ref=main")
    releases = [t["name"] for t in (tree or []) if t.get("name", "").startswith("RELEASE-")] if code == 200 else []
    ck("RELEASE 部署单存在", len(releases) > 0, str(releases))
    rel = raw(args.project, f"docs/deploy/{releases[0]}") if releases else None
    ck("部署单含回滚预案", bool(rel and "回滚" in rel))

    code, commits = api(f"/api/v4/projects/{quote(args.project, safe='')}/repository/commits?ref=main&per_page=50")
    msgs = [c["message"] for c in (commits or [])] if code == 200 else []
    ck("提交含 Agent: 审计 trailer", any("Agent:" in m for m in msgs), f"最近{len(msgs)}条")

    if args.mr_merged:
        ref = args.task_ref or f"task/{args.slug}"
        ck("任务分支已并入 main", any(ref in m for m in msgs) or _branch_merged(args.project, ref))

    print(f"\n工件链: {len(checks) - len(failed)}/{len(checks)} 通过")
    sys.exit(1 if failed else 0)


def _branch_merged(project: str, ref: str) -> bool:
    code, mrs = api(f"/api/v4/projects/{quote(project, safe='')}/merge_requests?state=merged&per_page=20")
    return code == 200 and any(m.get("source_branch") == ref for m in (mrs or []))


if __name__ == "__main__":
    main()
