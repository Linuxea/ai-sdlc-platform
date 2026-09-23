# ADR-0001: 主力模型选择 DeepSeek V4 家族

- 状态: 已接受 (2026-09-24)
- 背景与决策: 见会话调研。DeepSeek V4 家族（Pro 1.6T/49B 激活、Flash 284B/13B 激活，均 1M 上下文）以极低成本提供旗舰级编码/推理能力；`deepseek-chat`/`deepseek-reasoner` 旧 ID 已于 2026-07-24 退役，思考模式变为请求级参数（reasoning effort: low/high/max）。
- 路由: 开发 agent=Pro；架构/QA=Pro+max effort；轻量角色=Flash。
- 后果: 模型 ID 处于活跃变动期（2026-09 Flash 已迭代 V4.1），**必须**在 M1 以 `/v1/models` 活体探测为准冻结进 versions.lock，此后由工作流④巡检跟进。
- 备选: GLM-5.x 作为 fallback 槽位；DeepSeek 另提供 Anthropic 兼容端点，可作网关故障旁路。
