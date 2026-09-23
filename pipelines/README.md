# pipelines/

GitLab CI 统一模板（业务项目经 `include` 引用），版本锁定见根目录 `versions.lock`。

## 文件

| 文件 | 用途 |
|---|---|
| [templates/main.yml](templates/main.yml) | 统一 CI 入口: lint/test/build/scan(gitleaks+trivy)/pages/deploy |
| [scripts/blue-green-deploy.sh](scripts/blue-green-deploy.sh) | 蓝绿部署脚本骨架: 就绪检测→切流→冒烟失败自动回滚 |

## 门禁语义（与工作流①对应）

- `gitleaks`/`trivy` = 确定性安全门禁（宪章 5.1：能确定性判定的不交给 LLM）
- `unit-test` 覆盖率 + junit 报告 → QA agent 审查的输入之一
- `deploy-production` 双保险：`when: manual`（GitLab 页面可点）+ wf1 门禁 D 通过后经 API 触发
- 扫描镜像版本已锁定: gitleaks v8.30.1 / trivy v0.74.0（2026-09-24 验证）

## 项目接入

```yaml
include:
  - project: platform/ai-sdlc-platform
    ref: main
    file: pipelines/templates/main.yml
variables:
  LINT_CMD: "ruff check ."
  TEST_CMD: "pytest --junitxml=junit.xml"
  ENABLE_UNIT_TEST: "true"
  ENABLE_TRIVY: "true"
```
