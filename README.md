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

