# Claude Code Python

一个面向代码工作的 AI CLI / REPL / MCP 项目，提供 Claude Code 风格的交互、工具调用、任务运行时、Agent、多 Provider 接入，以及一套持续演进中的工程化基础设施。

本 README 是当前仓库的统一入口。大体量专题文档继续保留在 `docs/`，这里只保留必要摘要、明确导航和后续维护约定，避免文档再次失控。

## 项目定位

- 语言与运行时：Python 3.10+、`asyncio`
- 主入口：`python -m claude_code.main` 或 `python run.py`
- 交互模式：交互式 REPL、单次 query、管道模式、MCP 服务器模式
- 模型接入：`anthropic`、`openai`、`ollama`、`vllm`、`deepseek`、`bedrock`、`vertex`
- 关键子系统：`QueryEngine`、`ToolRegistry`、权限系统、任务运行时、Agent、MCP、技能系统、服务层

当前代码中 `azure` 路径有显式 fail-fast 提示，因此这里不把它作为当前推荐运行路径。

## 当前整理结论

截至 `2026-04-17`，本仓库的 Markdown 文档可以收敛为以下结构：

1. `README.md` 只负责统一入口，不再堆砌超长教程和实现枚举。
2. “当前状态”优先看带日期的评估/执行文档，而不是更早的评审草稿。
3. `docs/current/reference/AGENT.MD` 与 `docs/current/reference/MCP.md` 体量较大，保留独立文档，不再重复搬进 README。
4. 架构、性能、中间件三条线分别保留“当前结论”与“历史细节”两层，不再并列堆叠多个同级入口。

本次额外核对结果：

- 测试复核：`pytest -q -c pytest.ini` 通过，结果为 `90 passed`
- 架构最新快照：`2026-04-16` 的评测结论为“工程可用基线可推进”，评分 `8.4 / 10`
- 中间件演进快照：`Phase 0` 已完成，`Phase 1` 持续推进
- 性能快照：`Baseline V1` 记录启动耗时约 `1109.38 ms`

## 快速开始

### 1. 安装依赖

```bash
python -m pip install -r requirements.txt
```

如果你只是从源码运行，本仓库当前建议以 `requirements.txt` 和 `pytest.ini` 为准。

### 2. 选择 Provider

#### Anthropic

```bash
export CLAUDE_API_PROVIDER=anthropic
export ANTHROPIC_API_KEY=your-key
export CLAUDE_MODEL=claude-sonnet-4-20250514
```

#### Ollama / 本地 OpenAI 兼容模型

```bash
export CLAUDE_API_PROVIDER=ollama
export OPENAI_BASE_URL=http://localhost:11434/v1
export CLAUDE_MODEL=qwen2.5:14b
```

说明：

- `openai` / `deepseek` 需要 `OPENAI_API_KEY`
- `ollama` / `vllm` 允许本地模型路径，不强制真实 API Key
- PowerShell 请将 `export` 改为 `$env:变量名="值"`

### Windows 推荐启动（避免 WindowsApps stub）

Windows 上不要依赖 `C:\Users\<you>\AppData\Local\Microsoft\WindowsApps\python.exe` 这类 Store alias stub。

建议优先使用：

```powershell
py -3 -m claude_code.main --doctor
py -3 -m claude_code.main
```

或显式使用虚拟环境解释器：

```powershell
.\.venv\Scripts\python.exe -m claude_code.main --doctor
.\.venv\Scripts\python.exe -m claude_code.main
```

`--doctor` 会输出解释器来源与风险提示；若命中 WindowsApps stub，会给出明确警告与替代启动命令。

### 3. 常用启动方式

```bash
# 查看帮助
python -m claude_code.main --help

# 版本
python -m claude_code.main --version

# 健康检查
python -m claude_code.main --doctor

# 交互式 REPL
python -m claude_code.main

# 单次提问
python -m claude_code.main "解释当前目录下的项目结构"

# 管道模式
echo "帮我总结这段代码" | python -m claude_code.main --pipe

# 作为 MCP 服务器启动
python -m claude_code.main --mcp-serve

# 启动本地 daemon / API 控制面（P1-01）
python -m claude_code.main --daemon-serve --daemon-host 127.0.0.1 --daemon-port 8787

# CLI 以 thin-client 走 daemon（P1-06）
python -m claude_code.main --daemon-client "explain current repo status"
echo "summarize changed files" | python -m claude_code.main --pipe --daemon-client
```

## 核心能力概览

- 交互层：REPL、单轮 query、管道模式、命令系统
- 工具层：文件读写、搜索、Shell/PowerShell、工作流、任务控制、技能、浏览器、LSP、MCP、Worktree、Cron、Team
- 运行时：`QueryEngine` 编排模型对话、工具调用、权限判定和上下文构建
- 任务体系：`TaskManager`、`TaskRepository`、`TaskQueue` 支撑后台任务和任务存储演进
- 服务层：缓存、速率限制、遥测、历史管理、记忆、加密、hooks、shutdown、token estimation
- 扩展能力：MCP server/client、Agent、技能目录、项目级 `.claude/` 运行数据

如果你要看完整工具清单，不再从 README 查找，直接看 `docs/current/reference/MCP.md`。

## 仓库结构

```text
claude-code-python/
├── claude_code/          # 主代码
│   ├── main.py           # CLI 入口
│   ├── engine/           # QueryEngine / context / session / permissions
│   ├── tools/            # 工具系统
│   ├── commands/         # 命令系统
│   ├── tasks/            # 任务运行时、仓储、队列
│   ├── services/         # 缓存、遥测、历史、hooks、shutdown 等
│   ├── mcp/              # MCP 服务端实现
│   ├── agents/           # 内置 Agent 定义
│   ├── skills/           # 技能系统
│   └── state/            # 状态模型
├── docs/                 # 专题文档
├── examples/             # 示例脚本
├── scripts/              # 辅助脚本与性能脚本
├── tests/                # 测试
├── run.py                # 源码运行入口
├── requirements.txt      # 依赖清单
└── pytest.ini            # pytest 配置
```

## 文档地图

下面是整理后的推荐阅读顺序。

| 文档 | 角色 | 什么时候看 | 当前定位 |
|---|---|---|---|
| `README.md` | 总入口 | 第一次进入仓库 | 唯一导航入口 |
| `docs/current/architecture/ARCHITECTURE_EVALUATION_2026-04-16.md` | 架构现状快照 | 想知道项目现在整体状态 | 架构主入口 |
| `docs/current/architecture/CLAUDE_CODE_SUPERSEDE_STRATEGY_2026-04-29.md` | 产品战略与超车路线图 | 想知道项目如何从“可用底盘”走到“超越 Claude Code” | 战略主入口 |
| `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` | 执行计划与任务卡单 | 想直接开工并明确每张卡的研发范围、完成标准、测试深度 | 执行主入口 |
| `docs/current/middleware/MIDDLEWARE_EVOLUTION_EXECUTION_2026-04-16.md` | 任务/中间件落地记录 | 想知道任务系统已改到哪一步 | 中间件现状主入口 |
| `docs/current/performance/PERFORMANCE_ONE_PAGER.md` | 性能一页纸 | 想快速看性能状态 | 性能主入口 |
| `docs/current/reference/MCP.md` | MCP 使用手册 | 想把仓库作为 MCP server 接入 | MCP 主入口 |
| `docs/current/reference/AGENT.MD` | Agent 全量手册 | 想理解 Agent、异步子任务、多智能体 | Agent 主入口 |
| `docs/history/architecture/ARCHITECTURE_REVIEW.md` | 首轮问题盘点 | 想追溯最初发现了哪些问题 | 架构历史文档 |
| `docs/history/architecture/FIX_PROPOSALS.md` | 修复方案库 | 想看历史修复设计与备选方案 | 架构历史文档 |
| `docs/current/middleware/MIDDLEWARE_EVOLUTION_ASSESSMENT_2026-04-16.md` | 中间件演进评估 | 想评估 Redis/MySQL/平台化是否有必要 | 中间件决策文档 |
| `docs/history/performance/PERFORMANCE_TOP_TIER_EVALUATION_PLAN.md` | 性能路线图 | 想看阶段目标和执行计划 | 性能路线图 |
| `docs/history/performance/PERFORMANCE_OPTIMIZATION_REPORT.md` | 性能优化明细 | 想追踪具体改了哪些热路径 | 性能细节文档 |
| `docs/history/performance/OPTIMIZATION_PROGRESS.md` | 性能进度记录 | 想看阶段性进展 | 性能历史文档 |
| `docs/current/performance/BASELINE_V1.md` | 性能基线摘要 | 想看基线结论 | 性能数据摘要 |
| `docs/current/performance/baseline_v1.json` | 原始基线数据 | 想做对比或自动化处理 | 性能原始数据 |

## 各主题的权威入口

为避免“同一主题多个入口同时有效”，后续统一按下面的主入口理解：

- 架构现状：`docs/current/architecture/ARCHITECTURE_EVALUATION_2026-04-16.md`
- 产品战略 / 超越 Claude Code 路线图：`docs/current/architecture/CLAUDE_CODE_SUPERSEDE_STRATEGY_2026-04-29.md`
- 执行计划 / 任务卡单：`docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 架构历史问题与修复备选：`docs/history/architecture/ARCHITECTURE_REVIEW.md` + `docs/history/architecture/FIX_PROPOSALS.md`
- 任务/中间件当前落地状态：`docs/current/middleware/MIDDLEWARE_EVOLUTION_EXECUTION_2026-04-16.md`
- 任务/中间件演进决策依据：`docs/current/middleware/MIDDLEWARE_EVOLUTION_ASSESSMENT_2026-04-16.md`
- 性能当前状态：`docs/current/performance/PERFORMANCE_ONE_PAGER.md`
- 性能基线数据：`docs/current/performance/BASELINE_V1.md` + `docs/current/performance/baseline_v1.json`
- MCP 使用：`docs/current/reference/MCP.md`
- Agent 使用：`docs/current/reference/AGENT.MD`

## 架构、性能、中间件的摘要

### 架构

综合 `docs/current/architecture/ARCHITECTURE_EVALUATION_2026-04-16.md` 与历史评审文档，目前可以将架构结论收敛为：

- 方向上是合理的模块化单体
- 关键主链路曾出现过工具暴露、权限硬闸、Agent 异步、Provider 适配等断点
- 截至 `2026-04-16` 的评测文档，这些关键断点已完成一轮闭环修复，测试记录为 `68 passed`
- 更早的 `docs/history/architecture/ARCHITECTURE_REVIEW.md` 和 `docs/history/architecture/FIX_PROPOSALS.md` 主要用于追溯“为什么会这么改”，不再代表最新状态

### 中间件 / 任务系统

综合两份中间件文档，当前结论是：

- 仓库原始模型是“进程内队列 + 文件持久化”，不是数据库队列架构
- 对单机 CLI 合理，但对平台化、多实例、可恢复场景风险较高
- 当前落地重点已从“是否立刻上 Redis/MySQL”转为“先把任务模型、仓储、队列抽象收敛”
- 已完成的工作包括：`tasks.json` schema 统一、文件锁、安全写入、durable 语义修复、`TaskRepository` / `TaskQueue` 抽象接入

### 性能

综合性能文档，当前结论是：

- 已建立语法门禁、性能 smoke、基线脚本三件基础设施
- 当前基线主数据见 `docs/current/performance/baseline_v1.json`
- 单页摘要优先看 `docs/current/performance/PERFORMANCE_ONE_PAGER.md`
- 详细优化项优先看 `docs/history/performance/PERFORMANCE_OPTIMIZATION_REPORT.md`

## 开发与验证

```bash
# 运行测试
python -m pytest -q -c pytest.ini

# 运行 Phase 0 主链回归门禁（提交前/合并前）
python scripts/run_phase0_gate.py

# 运行 Phase 1 控制面回归门禁（P1-01）
python scripts/run_p1_control_plane_gate.py

# 运行 Phase 1 事件日志回归门禁（P1-02）
python scripts/run_p1_event_journal_gate.py

# 运行 Phase 1 SQLite 状态后端回归门禁（P1-03）
python scripts/run_p1_sqlite_state_backend_gate.py

# 运行 Phase 1 Active Memory 回归门禁（P1-04）
python scripts/run_p1_active_memory_gate.py

# 运行 Phase 1 Hook/Permission/Audit 收敛门禁（P1-05）
python scripts/run_p1_hook_permission_audit_gate.py

# 运行 Phase 1 CLI thin-client 迁移门禁（P1-06）
python scripts/run_p1_cli_thin_client_gate.py

# 运行 Phase 2 多 Agent Supervisor 门禁（P2-01）
python scripts/run_p2_multi_agent_supervisor_gate.py

# 运行 Phase 2 Artifact Bus 门禁（P2-02）
python scripts/run_p2_artifact_bus_gate.py

# 运行 Phase 2 IDE 集成门禁（P2-03）
python scripts/run_p2_ide_integration_gate.py

# 运行 Phase 2 GitHub/CI workflow 门禁（P2-04）
python scripts/run_p2_github_ci_workflow_gate.py

# 运行 Phase 2 组织策略与审计门禁（P2-05）
python scripts/run_p2_org_policy_audit_gate.py

# 运行 Phase 2 Agent 运行时一致性门禁（P2-07）
python scripts/run_p2_agent_runtime_parity_gate.py

# 运行 Phase 2 自定义 Agent 目录加载门禁（P2-08）
python scripts/run_p2_custom_agents_loader_gate.py

# 运行 Phase 2 JetBrains IDE 集成门禁（P2-10）
python scripts/run_p2_jetbrains_ide_integration_gate.py

# 运行 Phase 0-2 Linux 统一验尸门禁（P2-06）
python scripts/run_linux_unified_gate.py

# 运行 Phase 2 Linux 统一验尸执行门禁（P2-09，Linux 执行）
python scripts/run_p2_linux_unified_execution_gate.py --dry-run
python scripts/run_p2_linux_unified_execution_gate.py --continue-on-failure
# 分片并行示例（3 个 job 中的第 2 片）
python scripts/run_p2_linux_unified_execution_gate.py --shard-total 3 --shard-index 2 --continue-on-failure

# 聚合多分片 summary 并给出全局通过/失败判定（P2-12，Linux 回收阶段执行）
python scripts/run_p2_linux_shard_aggregation_gate.py --artifacts-dir .claude/reports
python scripts/run_p2_linux_shard_aggregation_gate.py --summary-glob ".claude/reports/**/summary.json"

# 从 merged summary 发布最终报告（P2-13，Linux 回收阶段执行）
python scripts/run_p2_linux_report_publish_gate.py --merged-summary .claude/reports/linux_unified_gate/merged_summary.json
python scripts/run_p2_linux_report_publish_gate.py --merged-summary .claude/reports/linux_unified_gate/merged_summary.json --output-json .claude/reports/linux_unified_gate/final_report.json --output-markdown .claude/reports/linux_unified_gate/final_report.md

# 一键串联执行->汇总->发布全链门禁（P2-14，Linux 编排入口）
python scripts/run_p2_linux_unified_pipeline_gate.py --dry-run
python scripts/run_p2_linux_unified_pipeline_gate.py --continue-on-failure --fail-fast
# 仅做汇总+发布（跳过执行阶段）
python scripts/run_p2_linux_unified_pipeline_gate.py --skip-execution --summary-glob ".claude/reports/**/summary.json"

# 生成 Linux 分片执行计划（P2-15，供 CI fan-out job 直接消费）
python scripts/run_p2_linux_shard_plan_gate.py --shard-total 4 --dry-run --print-commands
python scripts/run_p2_linux_shard_plan_gate.py --shard-total 4 --output .claude/reports/linux_unified_gate/shard_plan.json --continue-on-failure -- -k runtime

# 生成 Linux CI matrix 产物（P2-16，供 CI matrix 直接消费）
python scripts/run_p2_linux_ci_matrix_gate.py --shard-plan .claude/reports/linux_unified_gate/shard_plan.json --dry-run --print-matrix
python scripts/run_p2_linux_ci_matrix_gate.py --shard-plan .claude/reports/linux_unified_gate/shard_plan.json --output .claude/reports/linux_unified_gate/ci_matrix.json --skip-empty-shards

# 生成 Linux CI workflow 计划产物（P2-17，供 fan-out/fan-in job 直接消费）
python scripts/run_p2_linux_ci_workflow_plan_gate.py --ci-matrix .claude/reports/linux_unified_gate/ci_matrix.json --dry-run --print-plan
python scripts/run_p2_linux_ci_workflow_plan_gate.py --ci-matrix .claude/reports/linux_unified_gate/ci_matrix.json --output .claude/reports/linux_unified_gate/ci_workflow_plan.json

# 将 workflow 计划渲染为 GitHub Actions YAML（P2-18，供 CI 直接执行）
python scripts/run_p2_linux_ci_workflow_yaml_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --dry-run --print-yaml
python scripts/run_p2_linux_ci_workflow_yaml_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --output-workflow .github/workflows/linux_unified_gate.yml --output-metadata .claude/reports/linux_unified_gate/ci_workflow_render.json

# 校验/同步 workflow 渲染产物漂移（P2-19，防止 plan->yaml 漂移）
python scripts/run_p2_linux_ci_workflow_sync_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --workflow-path .github/workflows/linux_unified_gate.yml --metadata-path .claude/reports/linux_unified_gate/ci_workflow_render.json --print-diff
python scripts/run_p2_linux_ci_workflow_sync_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --workflow-path .github/workflows/linux_unified_gate.yml --metadata-path .claude/reports/linux_unified_gate/ci_workflow_render.json --write

# 校验/规范化 workflow 计划中的命令契约（P2-20，防止 command/parts/路径 漂移）
python scripts/run_p2_linux_ci_workflow_command_guard_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_command_guard_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --write --output .claude/reports/linux_unified_gate/ci_workflow_command_guard.json

# 汇总 workflow 漂移 + 命令 + 元数据血缘治理（P2-21，生成单一治理结论）
python scripts/run_p2_linux_ci_workflow_governance_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --workflow-path .github/workflows/linux_unified_gate.yml --metadata-path .claude/reports/linux_unified_gate/ci_workflow_render.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_governance_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --workflow-path .github/workflows/linux_unified_gate.yml --metadata-path .claude/reports/linux_unified_gate/ci_workflow_render.json --output .claude/reports/linux_unified_gate/ci_workflow_governance.json

# 发布治理结论为 CI 可消费决策（P2-22，生成 should_execute_workflow 与发布报告）
python scripts/run_p2_linux_ci_workflow_governance_publish_gate.py --governance-report .claude/reports/linux_unified_gate/ci_workflow_governance.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_governance_publish_gate.py --governance-report .claude/reports/linux_unified_gate/ci_workflow_governance.json --output-json .claude/reports/linux_unified_gate/ci_workflow_governance_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_governance_publish.md

# 将治理发布结果收敛为执行决策闸门（P2-23，统一 execute/blocked 判定与退出策略）
python scripts/run_p2_linux_ci_workflow_decision_gate.py --governance-publish .claude/reports/linux_unified_gate/ci_workflow_governance_publish.json --workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --workflow-path .github/workflows/linux_unified_gate.yml --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_decision_gate.py --governance-publish .claude/reports/linux_unified_gate/ci_workflow_governance_publish.json --workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --workflow-path .github/workflows/linux_unified_gate.yml --on-block skip --output-json .claude/reports/linux_unified_gate/ci_workflow_execution_decision.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_execution_decision.md

# 将执行决策收敛为可调度命令契约（P2-24，统一 dispatch-ready/blocked 与 gh workflow run 命令）
python scripts/run_p2_linux_ci_workflow_dispatch_gate.py --execution-decision .claude/reports/linux_unified_gate/ci_workflow_execution_decision.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_dispatch_gate.py --execution-decision .claude/reports/linux_unified_gate/ci_workflow_execution_decision.json --workflow-ref main --output-json .claude/reports/linux_unified_gate/ci_workflow_dispatch.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_dispatch.md

# 执行调度契约并输出最终执行回执（P2-25，统一 dispatched/blocked/fail 的执行结果）
python scripts/run_p2_linux_ci_workflow_dispatch_execution_gate.py --dispatch-report .claude/reports/linux_unified_gate/ci_workflow_dispatch.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_dispatch_execution_gate.py --dispatch-report .claude/reports/linux_unified_gate/ci_workflow_dispatch.json --project-root . --output-json .claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.md

# 将 dispatch 执行结果收敛为 run trace 契约（P2-27，统一 run_id/url/poll 命令与状态）
python scripts/run_p2_linux_ci_workflow_dispatch_trace_gate.py --dispatch-execution-report .claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_dispatch_trace_gate.py --dispatch-execution-report .claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.json --poll-now --project-root . --output-json .claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.md

# 等待 dispatch run 收敛为最终完成判定（P2-28，统一 completed/in_progress/timeout/failure 语义）
python scripts/run_p2_linux_ci_workflow_dispatch_completion_gate.py --dispatch-trace-report .claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_dispatch_completion_gate.py --dispatch-trace-report .claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.json --project-root . --poll-interval-seconds 20 --max-polls 15 --output-json .claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.md

# 发布 dispatch completion 的终局结论（P2-29，统一 promote/hold 发布语义）
python scripts/run_p2_linux_ci_workflow_terminal_publish_gate.py --dispatch-completion-report .claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_terminal_publish_gate.py --dispatch-completion-report .claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.json --output-json .claude/reports/linux_unified_gate/ci_workflow_terminal_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_terminal_publish.md

# 将 terminal publish 收敛为 release handoff 契约（P2-30，统一 release job 触发语义）
python scripts/run_p2_linux_ci_workflow_release_handoff_gate.py --terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_terminal_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_handoff_gate.py --terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_terminal_publish.json --target-environment production --release-channel stable --output-json .claude/reports/linux_unified_gate/ci_workflow_release_handoff.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_handoff.md

# 执行 release 最终触发门禁（P2-31，统一 release dispatch 执行语义）
python scripts/run_p2_linux_ci_workflow_release_trigger_gate.py --release-handoff-report .claude/reports/linux_unified_gate/ci_workflow_release_handoff.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_trigger_gate.py --release-handoff-report .claude/reports/linux_unified_gate/ci_workflow_release_handoff.json --release-workflow-path .github/workflows/release.yml --release-workflow-ref main --output-json .claude/reports/linux_unified_gate/ci_workflow_release_trigger.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_trigger.md

# 追踪 release trigger 执行后的 run 语义（P2-32，统一 release run trace/poll 状态）
python scripts/run_p2_linux_ci_workflow_release_trace_gate.py --release-trigger-report .claude/reports/linux_unified_gate/ci_workflow_release_trigger.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_trace_gate.py --release-trigger-report .claude/reports/linux_unified_gate/ci_workflow_release_trigger.json --poll-now --project-root . --output-json .claude/reports/linux_unified_gate/ci_workflow_release_trace.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_trace.md

# 等待 release run 收敛为最终完成判定（P2-33，统一 release 完成态语义）
python scripts/run_p2_linux_ci_workflow_release_completion_gate.py --release-trace-report .claude/reports/linux_unified_gate/ci_workflow_release_trace.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_completion_gate.py --release-trace-report .claude/reports/linux_unified_gate/ci_workflow_release_trace.json --project-root . --poll-interval-seconds 20 --max-polls 15 --output-json .claude/reports/linux_unified_gate/ci_workflow_release_completion.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_completion.md

# 发布 release completion 的终局结论（P2-34，统一 release finalize/hold 语义）
python scripts/run_p2_linux_ci_workflow_release_terminal_publish_gate.py --release-completion-report .claude/reports/linux_unified_gate/ci_workflow_release_completion.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_terminal_publish_gate.py --release-completion-report .claude/reports/linux_unified_gate/ci_workflow_release_completion.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.md

# 将 release terminal publish 收敛为最终 finalization 决策（P2-35，统一 finalize/hold/abort 语义）
python scripts/run_p2_linux_ci_workflow_release_finalization_gate.py --release-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_finalization_gate.py --release-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.json --on-hold pass --output-json .claude/reports/linux_unified_gate/ci_workflow_release_finalization.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_finalization.md

# 将 release finalization 收敛为最终 closure 发布契约（P2-36，统一 close/notify/rollback 语义）
python scripts/run_p2_linux_ci_workflow_release_closure_gate.py --release-finalization-report .claude/reports/linux_unified_gate/ci_workflow_release_finalization.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_closure_gate.py --release-finalization-report .claude/reports/linux_unified_gate/ci_workflow_release_finalization.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_closure.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_closure.md

# 将 release closure 收敛为最终证据归档契约（P2-37，统一 archive/publish/block 语义）
python scripts/run_p2_linux_ci_workflow_release_archive_gate.py --release-closure-report .claude/reports/linux_unified_gate/ci_workflow_release_closure.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_archive_gate.py --release-closure-report .claude/reports/linux_unified_gate/ci_workflow_release_closure.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_archive.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_archive.md

# 将 release archive 收敛为最终发布判词契约（P2-38，统一 ship/hold/block 语义）
python scripts/run_p2_linux_ci_workflow_release_verdict_gate.py --release-archive-report .claude/reports/linux_unified_gate/ci_workflow_release_archive.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_verdict_gate.py --release-archive-report .claude/reports/linux_unified_gate/ci_workflow_release_archive.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_verdict.md

# 将 release verdict 收敛为 incident dispatch 执行契约（P2-39，统一告警触发语义）
python scripts/run_p2_linux_ci_workflow_release_incident_gate.py --release-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_verdict.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_incident_gate.py --release-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_verdict.json --incident-repo acme/demo --incident-label release-incident --output-json .claude/reports/linux_unified_gate/ci_workflow_release_incident.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_incident.md

# 将 release incident 收敛为终局 terminal verdict 契约（P2-40，统一 ship/hold/escalate/block 语义）
python scripts/run_p2_linux_ci_workflow_release_terminal_verdict_gate.py --release-incident-report .claude/reports/linux_unified_gate/ci_workflow_release_incident.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_terminal_verdict_gate.py --release-incident-report .claude/reports/linux_unified_gate/ci_workflow_release_incident.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.md

# 将 release terminal verdict 收敛为最终 delivery 契约（P2-41，统一 deliver/hold/escalate/block 语义）
python scripts/run_p2_linux_ci_workflow_release_delivery_gate.py --release-terminal-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_delivery_gate.py --release-terminal-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_delivery.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_delivery.md

# P2-42: converge release delivery to terminal publish contract (announce_release/announce_hold/announce_blocker/abort_publish).
python scripts/run_p2_linux_ci_workflow_release_delivery_terminal_publish_gate.py --release-delivery-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_delivery_terminal_publish_gate.py --release-delivery-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.md

# P2-43: converge release delivery terminal publish to final verdict contract (close_release/open_follow_up/escalate_blocker/abort_close).
python scripts/run_p2_linux_ci_workflow_release_delivery_final_verdict_gate.py --release-delivery-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_delivery_final_verdict_gate.py --release-delivery-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.md


# P2-44: converge release delivery final verdict to follow-up dispatch contract (no_action/dispatch_follow_up/dispatch_escalation/abort_dispatch).
python scripts/run_p2_linux_ci_workflow_release_follow_up_dispatch_gate.py --release-delivery-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_follow_up_dispatch_gate.py --release-delivery-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.md

# P2-45: converge release follow-up dispatch to follow-up closure contract (no_action/queue_follow_up/queue_escalation/abort_queue).
python scripts/run_p2_linux_ci_workflow_release_follow_up_closure_gate.py --release-follow-up-dispatch-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_follow_up_closure_gate.py --release-follow-up-dispatch-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.json --follow-up-repo acme/demo --follow-up-label release-follow-up --output-json .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.md

# P2-46: converge release follow-up closure to terminal publish contract (announce_closed/announce_queued/announce_pending_queue/announce_queue_failure/abort_publish).
python scripts/run_p2_linux_ci_workflow_release_follow_up_terminal_publish_gate.py --release-follow-up-closure-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_follow_up_terminal_publish_gate.py --release-follow-up-closure-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.md

# P2-47: converge release follow-up terminal publish to final verdict contract (close_follow_up/keep_follow_up_open/escalate_queue_failure/abort_close).
python scripts/run_p2_linux_ci_workflow_release_follow_up_final_verdict_gate.py --release-follow-up-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_follow_up_final_verdict_gate.py --release-follow-up-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.md

# P2-48: converge delivery/follow-up final verdicts to one release final outcome contract (ship_and_close/ship_with_follow_up_open/escalate_blocker/abort_outcome).
python scripts/run_p2_linux_ci_workflow_release_final_outcome_gate.py --release-delivery-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json --release-follow-up-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_outcome_gate.py --release-delivery-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json --release-follow-up-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.md

# P2-49: converge release final outcome to terminal publish contract (announce_release_closure/announce_release_with_follow_up/announce_blocker/abort_publish).
python scripts/run_p2_linux_ci_workflow_release_final_terminal_publish_gate.py --release-final-outcome-report .claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_terminal_publish_gate.py --release-final-outcome-report .claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.md

# P2-50: converge release final terminal publish to final handoff contract (handoff_release_closure/handoff_release_with_follow_up/handoff_blocker/abort_handoff).
python scripts/run_p2_linux_ci_workflow_release_final_handoff_gate.py --release-final-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_handoff_gate.py --release-final-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.md

# P2-51: converge release final handoff to final closure contract (close_release/close_with_follow_up/close_blocker/abort_close).
python scripts/run_p2_linux_ci_workflow_release_final_closure_gate.py --release-final-handoff-report .claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_closure_gate.py --release-final-handoff-report .claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_closure.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_closure.md

# P2-52: publish release final closure contract (announce_release_closed/announce_release_closed_with_follow_up/announce_release_blocker/abort_publish).
python scripts/run_p2_linux_ci_workflow_release_final_closure_publish_gate.py --release-final-closure-report .claude/reports/linux_unified_gate/ci_workflow_release_final_closure.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_closure_publish_gate.py --release-final-closure-report .claude/reports/linux_unified_gate/ci_workflow_release_final_closure.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_closure_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_closure_publish.md

# P2-53: archive release final closure publish contract (archive_release_closed/archive_release_closed_with_follow_up/archive_release_blocker/abort_archive).
python scripts/run_p2_linux_ci_workflow_release_final_archive_gate.py --release-final-closure-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_final_closure_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_archive_gate.py --release-final-closure-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_final_closure_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_archive.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_archive.md

# P2-54: converge release final archive to final verdict contract (ship_release/ship_release_with_follow_up/escalate_release_blocker/abort_verdict).
python scripts/run_p2_linux_ci_workflow_release_final_verdict_gate.py --release-final-archive-report .claude/reports/linux_unified_gate/ci_workflow_release_final_archive.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_verdict_gate.py --release-final-archive-report .claude/reports/linux_unified_gate/ci_workflow_release_final_archive.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.md

# P2-55: publish release final verdict contract (announce_release_shipped/announce_release_shipped_with_follow_up/announce_release_blocker/abort_publish).
python scripts/run_p2_linux_ci_workflow_release_final_verdict_publish_gate.py --release-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_verdict_publish_gate.py --release-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.md

# P2-56: archive release final verdict publish contract (archive_release_shipped/archive_release_shipped_with_follow_up/archive_release_blocker/abort_archive).
python scripts/run_p2_linux_ci_workflow_release_final_publish_archive_gate.py --release-final-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_publish_archive_gate.py --release-final-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.md

# P2-57: close gate-script/runtime-test/manifest drift contract.
python scripts/run_p2_linux_gate_manifest_drift_gate.py --dry-run --print-report
python scripts/run_p2_linux_gate_manifest_drift_gate.py --output-json .claude/reports/linux_unified_gate/linux_gate_manifest_drift.json --output-markdown .claude/reports/linux_unified_gate/linux_gate_manifest_drift.md

# P2-59: converge P2-56+P2-57 to one Linux terminal verdict contract.
python scripts/run_p2_linux_ci_workflow_terminal_verdict_gate.py --release-final-publish-archive-report .claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.json --gate-manifest-drift-report .claude/reports/linux_unified_gate/linux_gate_manifest_drift.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_terminal_verdict_gate.py --release-final-publish-archive-report .claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.json --gate-manifest-drift-report .claude/reports/linux_unified_gate/linux_gate_manifest_drift.json --output-json .claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.md

# P2-60: dispatch Linux validation command from P2-59 terminal verdict contract.
python scripts/run_p2_linux_ci_workflow_linux_validation_dispatch_gate.py --terminal-verdict-report .claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_linux_validation_dispatch_gate.py --terminal-verdict-report .claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.json --linux-validation-timeout-seconds 7200 --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.md

# P2-61: converge Linux validation dispatch into one final Linux validation verdict contract.
python scripts/run_p2_linux_ci_workflow_linux_validation_verdict_gate.py --linux-validation-dispatch-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_linux_validation_verdict_gate.py --linux-validation-dispatch-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict.md

# 一键串联 P2-17 -> P2-61 CI workflow 全链门禁（P2-26，Linux CI 总入口）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --dry-run
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --fail-fast --sync-write --command-guard-write --dispatch-trace-poll-now --completion-poll-interval-seconds 20 --completion-max-polls 15 --target-environment production --release-channel stable --release-workflow-path .github/workflows/release.yml --release-workflow-ref main --release-trace-poll-now --release-completion-poll-interval-seconds 20 --release-completion-max-polls 15 --on-release-hold pass --follow-up-repo acme/demo --follow-up-label release-follow-up
# 仅执行后半链（从治理发布开始）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance
# 仅执行 P2-29 终局发布（复用已产出的 completion 报告）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion
# 仅执行 P2-30 release handoff（复用已产出的 terminal publish 报告）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --target-environment staging --release-channel canary --skip-release-trigger --skip-release-trace --skip-release-completion
# 仅执行 P2-31 release trigger（复用已产出的 release handoff 报告）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --release-workflow-path .github/workflows/release.yml --release-workflow-ref main --skip-release-trace --skip-release-completion
# 仅执行 P2-32 release trace（复用已产出的 release trigger 报告）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --release-trace-poll-now --skip-release-completion
# 仅执行 P2-33 release completion（复用已产出的 release trace 报告）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --release-completion-poll-interval-seconds 20 --release-completion-max-polls 15 --skip-release-terminal-publish
# 仅执行 P2-34 release terminal publish（复用已产出的 release completion 报告）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-finalization --skip-release-closure --skip-release-archive
# 仅执行 P2-35 release finalization（复用已产出的 release terminal publish 报告）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --on-release-hold fail --skip-release-closure --skip-release-archive
# 仅执行 P2-36 release closure（复用已产出的 release finalization 报告）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-archive
# 仅执行 P2-37 release archive（复用已产出的 release closure 报告）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-verdict --skip-release-incident
# 仅执行 P2-38 release verdict（复用已产出的 release archive 报告）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-incident
# 仅执行 P2-39 release incident（复用已产出的 release verdict 报告）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-terminal-verdict --incident-repo acme/demo --incident-label release-incident
# 仅执行 P2-40 release terminal verdict（复用已产出的 release incident 报告）
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch
# P2-42 only: run release delivery terminal publish (reuse release delivery report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch
# P2-43 only: run release delivery final verdict (reuse release delivery terminal publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-follow-up-dispatch
# P2-44 only: run release follow-up dispatch (reuse release delivery final verdict report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict
# P2-45 only: run release follow-up closure (reuse release follow-up dispatch report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --follow-up-repo acme/demo --follow-up-label release-follow-up

# P2-46 only: run release follow-up terminal publish (reuse release follow-up closure report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-final-verdict --follow-up-repo acme/demo --follow-up-label release-follow-up

# P2-47 only: run release follow-up final verdict (reuse release follow-up terminal publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --follow-up-repo acme/demo --follow-up-label release-follow-up
# P2-48 only: run release final outcome (reuse P2-43 + P2-47 final verdict reports).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict
# P2-49 only: run release final terminal publish (reuse P2-48 final outcome report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish
# P2-50 only: run release final handoff (reuse P2-49 final terminal publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-closure --skip-release-final-closure-publish
# P2-51 only: run release final closure (reuse P2-50 final handoff report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure-publish
# P2-52 only: run release final closure publish (reuse P2-51 final closure report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-archive

# P2-53 only: run release final archive (reuse P2-52 final closure publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish
# P2-54 only: run release final verdict (reuse P2-53 final archive report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive
# P2-55 only: run release final verdict publish (reuse P2-54 final verdict report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict
# P2-56 only: run release final publish archive (reuse P2-55 final verdict publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish
# P2-57 only: run gate manifest drift closure (independent closure check over scripts/tests/manifest).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive
# P2-59 only: run terminal verdict closure (reuse P2-56 + P2-57 reports).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift
# P2-60 only: run Linux validation dispatch (reuse P2-59 terminal verdict report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --linux-validation-timeout-seconds 7200
# P2-61 only: run Linux validation verdict (reuse P2-60 Linux validation dispatch report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch
# 语法检查
python scripts/check_syntax.py --root claude_code

# 运行性能 smoke
python -m pytest -q -c pytest.ini tests/perf/test_perf_smoke.py

# 生成性能基线
python scripts/perf/run_baseline.py --project-root . --iterations 20 --output docs/current/performance/baseline_v1.json
```

本次整理时实际复核过：

```bash
python -m pytest -q -c pytest.ini
```

结果为 `90 passed`。

## 配置与运行时文件

当前代码里常见的配置与运行时文件分布如下：

| 位置 | 用途 |
|---|---|
| `~/.claude-code-python/base.json` | 全局基础配置 |
| `~/.claude-code-python/{env}.json` | 按环境分层配置 |
| `~/.claude-code-python/config.json` | 用户手工覆盖配置 |
| `.claude-code-python.json` | 项目本地设置 |
| `.claude/` | 项目运行数据目录，常见内容包括任务、计划、技能、hooks、todo、team、scheduled tasks |
| `.mcp.json` | MCP 相关配置 |
| `CLAUDE.md` / `CLAUDE.local.md` | 项目指导信息，由 `/init` 初始化 |

如果你要排查任务系统，优先关注：

- `.claude/tasks.json`
- `.claude/runtime_tasks.json`
- `.claude/scheduled_tasks.json`

## 示例与入口文件

- `examples/basic_usage.py`：基础调用示例
- `examples/configuration.py`：配置示例
- `examples/custom_tools.py`：自定义工具示例
- `examples/mcp_integration.py`：MCP 集成示例
- `examples/session_management.py`：会话管理示例

## 后续文档维护规则

为了避免文档再次膨胀，后续建议遵守以下规则：

1. README 只做入口、摘要和导航，不再追加大型专题说明。
2. 同一主题最多保留一个“当前主文档”和一个“历史补充文档”。
3. 新的评估/总结文档必须带日期，并明确自己是否取代旧文档。
4. 超过一页的专题内容直接放到 `docs/`，README 只写摘要和链接。
5. 如果某个专题已经有主文档，后续补充优先更新原文档，而不是新建平行文档。

## 结论

这次整理后，`README.md` 不再承担“所有知识都写在一处”的职责，而是成为仓库的稳定入口：

- 想运行项目，先看“快速开始”
- 想看当前架构/性能/中间件状态，直接看对应主文档
- 想深入 Agent 或 MCP，再进入大文档
- 想追溯历史问题和修复方案，再看历史文档

这就是当前仓库文档的推荐阅读顺序和维护边界。




