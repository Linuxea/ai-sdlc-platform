"""工作流拓扑校验 — n8n JSON 的静态完整性

不启动 n8n, 只验证: JSON 合法 / 连接引用存在 / agent 挂载模型 / webhook 路径不冲突
"""
import re
from pathlib import Path

AGENT_TYPE_SUFFIX = ".agent"
SUB_NODE_INPUTS = {"ai_languageModel", "ai_tool"}


def test_workflows_load(workflows):
    for name, wf in workflows.items():
        assert wf.get("nodes"), f"{name}: nodes 为空"
        assert wf.get("connections") is not None, f"{name}: 缺 connections"


def test_connection_refs_exist(workflows):
    for name, wf in workflows.items():
        names = {n["name"] for n in wf["nodes"]}
        for src, conns in wf["connections"].items():
            assert src in names, f"{name}: 连接源不存在 {src}"
            for ctype, groups in conns.items():
                assert ctype in {"main", *SUB_NODE_INPUTS}, f"{name}: 未知连接类型 {ctype}"
                for group in groups:
                    for conn in group:
                        assert conn["node"] in names, f"{name}: 连接目标不存在 {src}->{conn['node']}"


def test_agents_have_language_model(workflows):
    for name, wf in workflows.items():
        wired = {
            c["node"]
            for conns in wf["connections"].values()
            for group in conns.get("ai_languageModel", [])
            for c in group
        }
        for node in wf["nodes"]:
            if node["type"].endswith(AGENT_TYPE_SUFFIX):
                assert node["name"] in wired, f"{name}: agent 未挂载模型子节点: {node['name']}"


def test_model_routes_match_gateway(workflows):
    """模型子节点只允许使用 LiteLLM 网关存在的路由(deploy/litellm/config.yaml)"""
    cfg = Path(__file__).resolve().parent.parent / "deploy/litellm/config.yaml"
    routes = set(re.findall(r"model_name:\s*(\S+)", cfg.read_text(encoding="utf-8")))
    assert {"deepseek-flash", "deepseek-v4-pro", "deepseek-v4-pro-max"} <= routes
    for name, wf in workflows.items():
        for node in wf["nodes"]:
            if node["type"].endswith("lmChatOpenAi"):
                model = node["parameters"].get("model")
                assert model in routes, f"{name}: 模型 {model} 不在网关路由中"


def test_webhook_paths_unique(workflows):
    seen = {}
    for name, wf in workflows.items():
        for node in wf["nodes"]:
            if node["type"].endswith(".webhook"):
                path = node["parameters"]["path"]
                assert path not in seen, f"webhook 路径冲突: {path} ({seen[path]} 与 {name})"
                seen[path] = name


def test_gate_wait_nodes_present(workflows):
    """wf1 必须含 4 道门禁(3 个 Wait + 1 个 MR webhook)与打回循环"""
    wf = workflows.get("wf1-sdlc-main.json")
    if not wf:
        pytest.skip("wf1 不在本次测试范围")
    waits = [n for n in wf["nodes"] if n["type"].endswith(".wait")]
    assert len(waits) >= 3, "wf1 门禁 Wait 节点不足 3 个(A/B/D)"
    assert any("门禁C" in n["name"] for n in wf["nodes"]), "wf1 缺门禁C(MR 合并回调)"
    assert any("打回" in n["name"] for n in wf["nodes"]), "wf1 缺打回循环节点"
