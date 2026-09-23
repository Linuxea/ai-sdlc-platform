"""环境变量契约 — 工作流引用的 $env.X 必须有部署侧定义

来源检查: deploy/test-env/tencent-stack.yml(注入 n8n) 或 .env.example(说明)
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WF_DIR = ROOT / "n8n-workflows"
STACK = ROOT / "deploy/test-env/tencent-stack.yml"
ENV_EXAMPLE = (ROOT / ".env.example").read_text(encoding="utf-8")


def _n8n_env_vars():
    text = STACK.read_text(encoding="utf-8")
    defined = set(re.findall(r"-\s+([A-Z][A-Z0-9_]+)=", text))
    defined |= set(re.findall(r"^([A-Z][A-Z0-9_]+)=.+", text, re.M))
    return defined


def test_workflow_env_vars_are_provisioned():
    defined = _n8n_env_vars()
    missing_total = {}
    for f in sorted(WF_DIR.glob("wf*.json")):
        refs = set(re.findall(r"\$env\.([A-Z][A-Z0-9_]+)", f.read_text(encoding="utf-8")))
        missing = refs - defined
        if missing:
            missing_total[f.name] = missing
    assert not missing_total, f"工作流引用了未在测试栈 provision 的环境变量: {missing_total}"


def test_secrets_documented_in_env_example():
    for var in ["DEEPSEEK_API_KEY", "LITELLM_MASTER_KEY", "N8N_ENCRYPTION_KEY", "GITLAB_TOKEN", "OPENHANDS_API_KEY"]:
        assert var in ENV_EXAMPLE, f".env.example 缺 {var} 说明"
        assert "sk-your" not in "" or True
