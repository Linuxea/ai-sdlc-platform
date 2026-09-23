# 测试报告模板 — REPORT-<date>.md

> 每轮完整测试后复制本模板填写，归档于 docs/test/。结果矩阵是验收唯一依据。

- 测试日期: YYYY-MM-DD
- 环境: tencent@10.0.0.1 + local@10.0.0.5（见 docs/runbooks/test-env.md）
- versions.lock 快照: <commit-hash>

## L0 静态测试

| 项 | 结果 | 备注 |
|---|---|---|
| 工作流拓扑(4 wf) | ⏳ | tests/test_workflows.py |
| 版本锁定契约 | ⏳ | tests/test_versions_lock.py |
| 环境变量契约 | ⏳ | tests/test_env_contract.py |

## L1 环境就绪

| 项 | 结果 | 备注 |
|---|---|---|
| 六向连通矩阵 | ⏳ | |
| 网关三路由冒烟 | ⏳ | scripts/probe_gateway.sh |
| 双栈 compose 健康 | ⏳ | |

## L2 组件测试

| 组件 | 用例 | 结果 |
|---|---|---|
| LiteLLM | 三路由 + pro-max reasoning | ⏳ |
| n8n | 4 工作流导入 + 激活 | ⏳ |
| GitLab | group/project/webhook/runner 就绪 | ⏳ |
| Runner | 示例 pipeline 全绿 | ⏳ |
| OpenHands | 真实小任务（经网关调 pro） | ⏳ |
| Harbor | trivy 扫描测试镜像 | ⏳ |

## L3 E2E 主流程（wf1 真跑）

| 轮次 | 场景 | 结果 | 工件链 | 耗时 | 费用 |
|---|---|---|---|---|---|
| 1 | 全绿通过（auto-approve） | ⏳ | n/10 | | |
| 2 | 门禁A 拒绝→打回→恢复 | ⏳ | | | |

断言明细: `python3 scripts/e2e_check.py --project platform/pilot-app --slug <slug> --mr-merged`

## L4 异常注入

| 场景 | 预期 | 结果 |
|---|---|---|
| CI 失败（注入 lint 错） | 失败分支通知，不进 QA | ⏳ |
| 门禁拒绝×3 | 升级人工，不再打回 | ⏳ |
| LiteLLM pro 断流 | fallback→flash，流程不中断 | ⏳ |
| webhook 丢失 | n8n retry/可重放 | ⏳ |

## L5 安全测试

| 项 | 结果 |
|---|---|
| E2E 全产物 gitleaks | ⏳ |
| 网关虚拟 key 配额/越权 | ⏳ |
| OpenHands 沙箱边界冒烟 | ⏳ |
| n8n 执行日志无凭据 | ⏳ |

## L6 成本/性能

| 指标 | 值 |
|---|---|
| 单轮 E2E tokens（ LiteLLM spend） | |
| 单轮 E2E 费用 | |
| 表单→上线 总耗时 / 各门禁耗时分解 | |

## L7 升级回归（wf4）

| 场景 | 结果 |
|---|---|
| lock 注入旧版本 → UPGRADE INTENT 产出 | ⏳ |

## 缺陷与遗留

| # | 描述 | 严重级 | 状态 |
|---|---|---|---|

## 结论

- [ ] L0-L2 全绿
- [ ] L3 ≥1 轮全绿 + 1 轮拒绝恢复
- [ ] L4/L5 全过
- [ ] 成本记录在案
- 总体判定: PASS / CONDITIONAL / FAIL
