"""静态测试套件 — L0 层(零成本, 本地跑)

运行: .venv/bin/pytest tests/ -v
覆盖: 工作流拓扑 / 版本锁定契约 / 环境变量契约
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WF_DIR = ROOT / "n8n-workflows"
WF_FILES = sorted(WF_DIR.glob("wf*.json"))
LOCK = ROOT / "versions.lock"


@pytest.fixture(scope="module")
def lock_images():
    """versions.lock 中登记的全部版本(组件名+版本片段)"""
    text = LOCK.read_text(encoding="utf-8")
    rows = []
    for line in text.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if m and not m.group(1).startswith(("component", "-", ":")):
            rows.append((m.group(1).strip(), m.group(2).strip()))
    assert rows, "versions.lock 解析为空"
    return rows


@pytest.fixture(scope="module")
def workflows():
    assert WF_FILES, "未找到工作流 JSON"
    return {f.name: json.loads(f.read_text(encoding="utf-8")) for f in WF_FILES}
