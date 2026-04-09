# AGENT.MD — Agent 系统完全指南

> 本文档面向有 Python 基础但对 Claude Code Agent 系统零了解的开发者，从零讲起，逐步深入，覆盖概念、架构、实战、进阶全链路。

---

## 目录

1. [什么是 Agent？为什么需要 Agent？](#1-什么是-agent为什么需要-agent)
2. [Agent 系统全景架构](#2-agent-系统全景架构)
3. [核心概念速查表](#3-核心概念速查表)
4. [内置 Agent 一览](#4-内置-agent-一览)
5. [Agent 的工作流程详解](#5-agent-的工作流程详解)
6. [自定义 Agent：.claude/agents/ 目录](#6-自定义-agent-claudeagents-目录)
7. [在 Python 项目中创建新 Agent](#7-在-python-项目中创建新-agent)
8. [Agent 工具权限与安全模型](#8-agent-工具权限与安全模型)
9. [同步 vs 异步 vs Fork：三种执行模式](#9-同步-vs-异步-vs-fork三种执行模式)
10. [TeamMate 多智能体协作](#10-teammate-多智能体协作)
11. [Agent 记忆系统](#11-agent-记忆系统)
12. [环境变量与 Feature Flags](#12-环境变量与-feature-flags)
13. [实战示例集](#13-实战示例集)
14. [常见问题与排错](#14-常见问题与排错)
15. [术语表](#15-术语表)

---

## 0. 架构修复记录（2024-Q1）

以下修复已落地，文档内容已更新以反映当前代码状态：

| 修复项 | 文件 | 说明 |
|--------|------|------|
| P0-02: AgentTool 导入路径 | `tools/agent/__init__.py` | 从 `.claude_code.engine.query` 改为 `claude_code.engine.query` 绝对导入 |
| P0-05: TaskControlListTool | `tools/control/__init__.py` | 控制面板的 TaskListTool 重名为 TaskControlListTool，避免与工作流版本冲突 |
| P1-06: Agent 系统统一 | `agents/builtin.py` + `tools/agent/__init__.py` | 统一为 `agent_type`/`prompt` 字段；`BUILTIN_AGENTS` 通过 `create_builtin_agents()` 加载全部 10 个 Agent |
| P1-07: 异步 Agent 执行 | `tools/agent/__init__.py` | `_run_async_agent()` 使用 TaskManager 单例，创建 AgentTask，通过 `start_task(executor=...)` 实际执行 |
| P1-08: Config→ToolContext 传播 | `tools/base.py` + `engine/query.py` | `ToolContext` 新增 `permission_mode`/`always_allow`/`always_deny`/`model`/`session_id` 字段；`QueryEngine._execute_tool()` 从 `QueryConfig` 传入 |
| P1-09: PermissionMode 统一 | `permissions.py` (权威) + 5 个模块 | 6 值枚举 (`DEFAULT/AUTO/PLAN/ACCEPT_EDITS/BYPASS/YOLO`)，所有模块统一从此导入 |
| P1-10: 多提供商适配器 | `api/protocols.py` + `api/openai_adapter.py` (新) | `BaseLLMAdapter` ABC + `OpenAIAdapter` 完整实现，`LLMClientFactory` 有优雅 ImportError |
| P0-04: SessionMetadata frozen | `engine/session.py` + `state/session_state.py` | 改为 `@dataclass(slots=True)`（不再 frozen），允许字段修改 |

Python 版本要求：**>=3.10**（因使用 `dataclass(slots=True)` 等 3.10+ 特性）。

---

## 1. 什么是 Agent？为什么需要 Agent？

### 1.1 一句话理解

**Agent = 一个被你（或主对话）派出去的"分身"，它有独立的系统提示词、工具集、权限，在一个隔离的对话循环中自主完成任务，然后把结果带回来。**

类比：你是项目经理，Agent 是你派出去的实习生。你告诉实习生任务（prompt），实习生有自己的工作方式和权限（工具集），完成后交回报告（result）。

### 1.2 为什么不用主对话直接做？

| 问题 | Agent 如何解决 |
|------|---------------|
| 主对话上下文太长，容易迷失方向 | Agent 在独立上下文中工作，不污染主对话 |
| 多个任务需要并行 | 异步 Agent 可以后台运行，主对话继续工作 |
| 某些任务需要更便宜/更快的模型 | Agent 可以指定 `model: haiku` 来节省成本 |
| 某些任务需要不同权限 | Agent 可以限定只读权限（`permissionMode`），避免误操作 |
| 代码修改需要在隔离环境中做 | Agent 可以在 git worktree 中工作，不影响主分支 |

### 1.3 最简单的例子

当你在 Claude Code 中输入：

```
> 请帮我在 src/utils/ 下找到所有 TODO 注释，并统计每个文件的数量
```

Claude Code 可能会调用 Agent 工具：

```json
{
  "description": "搜索 TODO 注释",
  "prompt": "在 src/utils/ 下搜索所有 TODO 注释，列出每个文件的 TODO 数量和内容摘要",
  "subagent_type": "general-purpose"
}
```

Agent 完成后，结果返回到主对话，你看不到 Agent 内部的工具调用过程，只看到最终答案。

---

## 2. Agent 系统全景架构

### 2.1 顶层视图

```
用户输入
   │
   ▼
┌──────────────────────────────────────────────────┐
│              主对话循环 (REPL)                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────┐  │
│  │ QueryEngine │  │  AgentTool │  │  其他 61+ 工具  │  │
│  └────┬────┘  └────┬────┘  └─────────────────┘  │
│       │            │                             │
└───────┼────────────┼─────────────────────────────┘
        │            │
        │     调用 AgentTool
        │            │
        ▼            ▼
┌──────────────────────────────────────────────────┐
│            Agent 执行层                            │
│                                                   │
│  ┌─────────────┐  ┌─────────────┐                │
│  │ 同步 Agent    │  │ 异步 Agent    │                │
│  │ (阻塞主对话)  │  │ (后台运行)    │                │
│  └──────┬──────┘  └──────┬──────┘                │
│         │                │                        │
│         ▼                ▼                        │
│  ┌────────────────────────────┐                   │
│  │      QueryEngine (新实例)    │                   │
│  │  ┌───────┐  ┌───────────┐  │                   │
│  │  │ 指定工具集 │  │ 指定模型    │  │                   │
│  │  └───────┘  └───────────┘  │                   │
│  └────────────────────────────┘                   │
│                                                   │
│  ┌────────────────────────────────┐               │
│  │  TeamMate (多智能体)            │               │
│  │  ┌──────────┐  ┌──────────┐    │               │
│  │  │ Agent A   │  │ Agent B   │    │               │
│  │  │ (前端)    │  │ (后端)    │    │               │
│  │  └──────────┘  └──────────┘    │               │
│  └────────────────────────────────┘               │
└──────────────────────────────────────────────────┘
```

### 2.2 TypeScript 原版 vs Python 版本对照

| 概念 | TypeScript 原版 | Python 版本 |
|------|----------------|------------|
| Agent 定义 | `AgentDefinition` (3 种子类型) | `AgentDefinition` dataclass (`agent_type`/`prompt` 字段，与 TS 对齐) |
| Agent 注册 | `.claude/agents/*.md` + 代码内置 | `agents/builtin.py` → `create_builtin_agents()` → `BUILTIN_AGENTS` (10 个) |
| 执行引擎 | `runAgent()` in `AgentTool/runAgent.ts` | `_run_sync_agent()` in `tools/agent/__init__.py` |
| 异步执行 | `runAsyncAgentLifecycle()` | `TaskManager.get_instance()` → `create_agent_task()` → `start_task(executor=_execute_agent)` |
| 权限系统 | 5 种 PermissionMode | 6 种：`DEFAULT/AUTO/PLAN/ACCEPT_EDITS/BYPASS/YOLO`，权威定义在 `permissions.py` |
| Config → Tool 传播 | 通过 `ToolUseContext` 完整传播 | `ToolContext` 包含 `permission_mode`/`always_allow`/`always_deny`/`model`/`session_id`，`QueryEngine._execute_tool()` 已从 `QueryConfig` 传递 |
| LLM 多提供商 | OpenAI/Bedrock/Vertex/Azure 直连 | `BaseLLMAdapter` ABC + `OpenAIAdapter` 实现，`LLMClientFactory` 有优雅 ImportError |
| Fork 模式 | `forkSubagent.ts` (完整实现) | 未实现 |
| TeamMate | `spawnMultiAgent.ts` (完整实现) | `tools/team/` (骨架) |
| Agent 记忆 | `agentMemory.ts` (完整实现) | 未实现 |
| 工具筛选 | `filterToolsForAgent()` 完整实现 | 未实现 |
| 自定义 Agent 加载 | `loadAgentsDir.ts` (完整) | 未实现 |

> **当前状态**：Python 版本的 Agent 系统核心框架已就绪——Agent 定义通过 `create_builtin_agents()` 统一注册（10 个），同步/异步执行逻辑可用，权限传播已从 `Config` 透传到 `ToolContext`，多提供商适配器已有 `BaseLLMAdapter` 基类和 `OpenAIAdapter` 实现。高级功能（Fork、TeamMate、记忆、工具筛选、自定义 Agent 加载）仍需完善。

---

## 3. 核心概念速查表

| 术语 | 含义 |
|------|------|
| **Agent** | 一个独立的对话实体，拥有自己的系统提示词、工具集、权限 |
| **主对话 (Parent)** | 用户直接交互的 Claude Code REPL |
| **子 Agent (Subagent)** | 由主对话通过 AgentTool 派生的 Agent |
| **AgentType** | Agent 的类型标识符，如 `general-purpose`、`editor`、`researcher` |
| **AgentDefinition** | 定义一种 Agent 的数据结构（系统提示词、工具、模型等） |
| **System Prompt** | Agent 的"人格"指令，决定了它怎么思考和回答 |
| **Tool Pool** | Agent 可使用的工具子集 |
| **Permission Mode** | Agent 的权限级别：`default`、`acceptEdits`、`bypassPermissions` 等 |
| **Fork Agent** | 继承父对话上下文的低成本 Agent（TS 版独有） |
| **TeamMate** | 多 Agent 并行协作模式 |
| **Worktree Isolation** | 在独立的 git worktree 中运行 Agent，不污染主分支 |
| **Feature Flag** | 通过环境变量控制功能开关，如 `FEATURE_FORK_SUBAGENT=1` |

---

## 4. 内置 Agent 一览

### 4.1 TypeScript 原版内置 Agent

| Agent 类型 | 描述 | 模型 | 工具 | 是否只读 |
|-----------|------|------|------|---------|
| `general-purpose` | 通用任务 | 继承父级 | 全部 (`*`) | 否 |
| `Explore` | 快速搜索代码库 | haiku (外部) / inherit (内部) | 只读（不含 Edit/Write/Agent） | 是 |
| `Plan` | 软件架构规划 | inherit | 只读 | 是 |
| `verification` | 对抗性验证 | inherit | 可写 /tmp | 否 |
| `claude-code-guide` | 产品帮助 | haiku | Glob/Grep/Read/Web | 是 |
| `statusline-setup` | 状态栏配置 | sonnet | Read/Edit | 否 |

### 4.2 Python 版本内置 Agent

| Agent 类型 | 描述 | 模型 | 能力标签 |
|-----------|------|------|---------|
| `general-purpose` | 通用助手 | sonnet | 全部能力 |
| `editor` | 精确文件编辑 | sonnet | CODE_EDITING, REFACTORING |
| `reviewer` | 代码审查 | sonnet | CODE_REVIEW |
| `debugger` | 调试排错 | sonnet | DEBUGGING |
| `tester` | 编写测试 | sonnet | TESTING |
| `researcher` | 快速研究 | haiku | RESEARCH |
| `architect` | 系统架构 | opus | ARCHITECTURE |
| `docs-writer` | 文档编写 | sonnet | DOCUMENTATION |
| `quick` | 简单快速任务 | haiku | CODE_EDITING |
| `deep` | 深度复杂分析 | opus | 全部能力 (后台运行) |

### 4.3 AgentTool 中注册的 Agent

Python 版本的 `AgentTool` 通过 `create_builtin_agents()` 从 `agents/builtin.py` 加载全部 10 种 Agent：

```python
# claude_code/tools/agent/__init__.py
from claude_code.agents.builtin import create_builtin_agents

BUILTIN_AGENTS: dict[str, AgentDefinition] = create_builtin_agents()
# 结果：10 个 Agent（general-purpose, editor, reviewer, debugger, tester,
#        researcher, architect, docs-writer, quick, deep）
```

> **注意**：之前 `AgentTool` 和 `agents/builtin.py` 是两个独立的 Agent 系统，各定义各的。现在已统一：`BUILTIN_AGENTS` 直接从 `create_builtin_agents()` 构建，字段也从旧的 `name`/`system_prompt` 统一为 `agent_type`/`prompt`，与 TypeScript 版本对齐。

---

## 5. Agent 的工作流程详解

### 5.1 完整生命周期

```
用户输入 → Claude 判断需要派 Agent
              │
              ▼
        调用 AgentTool.execute()
              │
              ├─ 解析参数（description, prompt, subagent_type, model...）
              ├─ 查找 AgentDefinition
              ├─ 决定同步/异步执行
              │
              ▼
        ┌─────────────────────────┐
        │   _run_sync_agent()     │  或  _run_async_agent()
        │                         │
        │  1. 构建 System Prompt   │
        │  2. 创建 QueryEngine    │
        │  3. 配置模型和工具       │
        │  4. [可选] 创建 worktree │
        │  5. 执行 query() 循环    │
        │  6. 收集结果             │
        │  7. [可选] 清理 worktree │
        └──────────┬──────────────┘
                   │
                   ▼
           ToolResult 返回主对话
```

### 5.2 关键步骤详解

#### 步骤 1: 参数解析

Agent 接收的参数：

```python
{
    "description": "搜索 TODO",          # 必须: 3-5词简述
    "prompt": "在 src/ 下搜索...",        # 必须: 完整任务描述
    "subagent_type": "general-purpose", # 可选: Agent 类型
    "model": "haiku",                    # 可选: 模型覆盖
    "run_in_background": false,          # 可选: 是否后台运行
    "name": "todo-searcher",            # 可选: Agent 名称
    "isolation": "worktree",            # 可选: 隔离模式
    "cwd": "/path/to/project",          # 可选: 工作目录
}
```

#### 步骤 2: 查找 AgentDefinition

```python
# 在 BUILTIN_AGENTS 字典中查找
agent_def = BUILTIN_AGENTS.get(subagent_type)
if not agent_def:
    return ToolResult(
        content=f"Unknown agent type: {subagent_type}. Available: ...",
        is_error=True
    )
```

#### 步骤 3: 构建 System Prompt

```python
system_prompt = f"""{agent_def.prompt}

You are executing as a sub-agent of Claude Code. Your task is:
{prompt}

Working directory: {cwd}

Report your findings and results clearly."""
```

#### 步骤 4: 执行

```python
engine = QueryEngine(api_client=api_client, ...)
engine.config.system_prompt = system_prompt
if model:
    engine.config.model = f"claude-{model}-4-20250514"

# 逐事件收集结果
result_parts = []
async for event in engine.query(prompt):
    if isinstance(event, Message) and event.role == "assistant":
        result_parts.append(event.content)

return ToolResult(content=f"[{agent_name}] {description}\n\n{result}")
```

### 5.3 TypeScript 版本的高级生命周期（参考）

TS 版本的 Agent 执行流程更复杂，包含以下 Python 版本尚未实现的功能：

```
1. 类型解析 → 查找 AgentDefinition (优先级: built-in < plugin < user < project < flag)
2. MCP 服务器检查 → 如果 Agent 要求特定 MCP，等待最多 30s
3. 系统提示词构建 → 支持记忆注入、环境信息增强
4. 工具池组装 → 过滤不允许的工具、添加 Agent 特有的工具
5. Worktree 设置 → 可选的 git 隔离
6. 同步/异步决策 → 多种条件决定
7. 上下文创建 → 隔离的 ToolUseContext
8. 执行 → query() 循环 + sidechain 转录记录
9. 结果交付 → 同步直接返回 / 异步通知
10. 安全分类 → 可选的 transcript classifier
11. 清理 → MCP、hooks、文件状态缓存
```

---

## 6. 自定义 Agent：.claude/agents/ 目录

### 6.1 什么是自定义 Agent？

自定义 Agent 是你通过创建 Markdown 文件来声明的新 Agent 类型。Claude Code 会自动加载 `.claude/agents/` 目录下的 `.md` 文件，解析其中的 frontmatter 生成 AgentDefinition。

### 6.2 文件格式

在项目根目录创建 `.claude/agents/my-agent.md`：

```markdown
---
name: my-agent
description: 一个专门做 X 的智能体
model: haiku
tools:
  - Read
  - Grep
  - Glob
  - WebSearch
  - WebFetch
permissionMode: default
background: false
maxTurns: 30
---

你是一个专业的 XX 领域助手。

你的职责：
1. ...详细描述...
2. ...

工作方式：
- 保持简洁
- 只使用被允许的工具
- 在完成后汇报结果
```

### 6.3 Frontmatter 字段详解

| 字段 | 类型 | 是否必须 | 默认值 | 说明 |
|------|------|---------|--------|------|
| `name` | string | **是** | — | Agent 类型标识符（同时也是 `subagent_type` 的值）|
| `description` | string | **是** | — | 简要描述 Agent 的用途（显示在 Agent 列表中）|
| `model` | string | 否 | `inherit` | 模型选择：`haiku`、`sonnet`、`opus`、`inherit`（继承父级）|
| `tools` | string[] | 否 | `["*"]`(全部) | 允许的工具白名单，`["*"]` 表示全部 |
| `disallowedTools` | string[] | 否 | `[]` | 禁止的工具黑名单 |
| `permissionMode` | string | 否 | `acceptEdits` | 权限模式 |
| `background` | boolean | 否 | `false` | 是否默认后台运行 |
| `maxTurns` | integer | 否 | 无限制 | 最大对话轮数 |
| `color` | string | 否 | — | UI 颜色：red/blue/green/yellow/purple/orange/pink/cyan |
| `isolation` | string | 否 | — | 隔离模式：`worktree` |
| `memory` | string | 否 | — | 记忆范围：`user`/`project`/`local` |
| `skills` | string[] | 否 | `[]` | 预加载的 Skill 名称 |
| `mcpServers` | array | 否 | `[]` | Agent 专属 MCP 服务器 |
| `hooks` | object | 否 | — | 会话级钩子配置 |
| `initialPrompt` | string | 否 | — | 在第一轮用户消息前注入的提示 |
| `effort` | string/integer | 否 | — | 思考努力级别 |
| `omitClaudeMd` | boolean | 否 | `false` | 是否省略 CLAUDE.md 内容（节省 token）|

### 6.4 Frontmatter 中的 tools 字段

`tools` 字段控制 Agent 可以使用哪些工具。完整的工具名称列表：

**核心工具**：
- `Bash` / `Shell` — 执行命令
- `Read` / `FileRead` — 读取文件
- `Write` / `FileWrite` — 写入文件
- `Edit` / `FileEdit` — 精确编辑文件
- `Glob` / `GlobFiles` — 按模式搜索文件
- `Grep` / `Search` — 搜索文件内容

**Web 工具**：
- `WebSearch` — 网页搜索
- `WebFetch` — 抓取网页

**Agent/任务工具**：
- `Agent` — 派生子 Agent（需注意递归风险）
- `TaskCreate` / `TaskGet` / `TaskUpdate` / `TaskList` — 任务管理

**工作流工具**：
- `TodoWrite` — 管理任务列表
- `EnterWorktree` / `ExitWorktree` — Git worktree 管理

> **重要**：某些工具在 Agent 中始终被禁用，无论 `tools` 如何设置。见第 8 节。

### 6.5 Agent 优先级

当多个来源的 Agent 同名时，优先级从低到高：

```
built-in（内置）< plugin（插件）< userSettings（用户级）< projectSettings（项目级）< flagSettings（命令行标志）
```

即：如果你在 `.claude/agents/` 中创建了名为 `general-purpose` 的 Agent，它会覆盖内置的 `general-purpose`。

### 6.6 实际示例

#### 示例 1：代码搜索 Agent（只读、高速）

```markdown
---
name: code-searcher
description: 快速搜索代码库中的特定模式
model: haiku
tools:
  - Grep
  - Glob
  - Read
  - WebSearch
  - WebFetch
permissionMode: default
omitClaudeMd: true
---

你是一个代码搜索专家。你的任务是精确地搜索代码并返回结果。

规则：
1. 只使用搜索和读取工具
2. 不要修改任何文件
3. 报告搜索结果时包含文件路径和行号
4. 如果搜索结果太多，只返回最相关的
```

#### 示例 2：测试编写 Agent

```markdown
---
name: test-writer
description: 编写全面的单元测试和集成测试
model: sonnet
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
permissionMode: acceptEdits
maxTurns: 30
---

你是一个测试编写专家。

流程：
1. 先读取需要测试的代码文件
2. 分析代码的公共接口和边界条件
3. 使用 pytest 编写全面的测试
4. 运行测试确认通过
5. 如果测试失败，修复失败用例

规则：
- 测试函数名使用 test_ 前缀
- 使用 pytest.fixture 管理测试数据
- 每个测试只验证一个行为
- 包含正常、边界、异常情况
```

#### 示例 3：后台安全审计 Agent

```markdown
---
name: security-audit
description: 在后台运行全面的安全审计
model: opus
background: true
tools:
  - Read
  - Grep
  - Glob
  - Bash
permissionMode: default
maxTurns: 50
color: red
---

你是一个安全审计专家。你的任务是全面检查代码中的安全问题。

检查项目：
1. SQL 注入风险
2. XSS 漏洞
3. 硬编码密钥和凭证
4. 不安全的依赖
5. 权限配置问题
6. 输入验证缺失

输出格式：
- 严重程度：Critical / High / Medium / Low
- 文件路径和行号
- 问题描述
- 修复建议
```

> **当前状态**：Python 版本的 `AgentTool` 现在通过 `create_builtin_agents()` 加载全部 10 个内置 Agent。自定义 Agent 目录加载（`.claude/agents/`）仍需实现（见第 7.3 节）。

---

## 7. 在 Python 项目中创建新 Agent

### 7.1 方法一：修改 BUILTIN_AGENTS（最简单）

编辑 `claude_code/agents/builtin.py`（**统一入口**）：

```python
from claude_code.agents.builtin import AgentDefinition, create_builtin_agents

# create_builtin_agents() 返回所有内置 Agent 的字典
# 使用 agent_type/prompt 字段（与 TS 版对齐）
BUILTIN_AGENTS = create_builtin_agents()

# 要添加新 Agent，修改 agents/builtin.py 中的 create_builtin_agents()
# 或者在 tools/agent/__init__.py 中往 BUILTIN_AGENTS 字典追加
BUILTIN_AGENTS["code-searcher"] = AgentDefinition(
    agent_type="code-searcher",
    description="Fast code search agent (read-only, haiku model)",
    prompt="""You are a code search specialist...""",
    model="haiku",
)

### 7.2 方法二：扩展 AgentDefinition 数据类

编辑 `claude_code/agents/builtin.py` 中的 `AgentDefinition`：

> **注意**：字段已从旧版 `name`/`system_prompt` 统一为 `agent_type`/`prompt`，与 TypeScript 版本对齐。

```python
@dataclass(slots=True)
class AgentDefinition:
    """Definition of an agent type.
    
    Fields use agent_type/prompt naming (matching TypeScript version).
    """
    agent_type: str
    description: str
    prompt: str
    
    # 模型选择: "haiku" | "sonnet" | "opus" | "inherit"
    model: str = "sonnet"
    
    # 是否后台运行
    background: bool = False
    
    # 隔离模式: None | "worktree"
    isolation: Optional[str] = None
    
    # 权限模式
    permission_mode: str = "acceptEdits"
    
    # ↓↓↓ 新增字段（对齐 TS 版本） ↓↓↓
    
    # 允许的工具列表，["*"] 表示全部
    tools: list[str] = field(default_factory=lambda: ["*"])
    
    # 禁止的工具列表
    disallowed_tools: list[str] = field(default_factory=list)
    
    # 最大对话轮数
    max_turns: Optional[int] = None
    
    # 颜色标识
    color: Optional[str] = None
    
    # 是否省略 CLAUDE.md
    omit_claude_md: bool = False
    
    # 记忆范围: "user" | "project" | "local"
    memory: Optional[str] = None
    
    # 预加载的 Skill 名称
    skills: list[str] = field(default_factory=list)
    
    # Agent 专属 MCP 服务器
    mcp_servers: Optional[list[dict]] = None
    
    # 初始提示（注入到第一轮用户消息前）
    initial_prompt: Optional[str] = None
```

### 7.3 方法三：实现自定义 Agent 加载器（高级）

模仿 TS 版本的 `loadAgentsDir.ts`，创建 `claude_code/agents/loader.py`：

```python
"""
Agent loader - from .claude/agents/ directory.

Supports Markdown files with YAML frontmatter, matching
the TypeScript version's format.
"""

import os
from pathlib import Path
from typing import Optional
import yaml

from claude_code.tools.agent import AgentDefinition


def load_agents_from_directory(cwd: str) -> dict[str, AgentDefinition]:
    """Load agent definitions from .claude/agents/ directory.
    
    Scans for .md files with YAML frontmatter.
    
    Args:
        cwd: Current working directory to search from
        
    Returns:
        Dictionary mapping agent_type to AgentDefinition
    """
    agents: dict[str, AgentDefinition] = {}
    
    # Walk up from cwd to root, collecting agent directories
    path = Path(cwd).resolve()
    for parent in [path, *path.parents]:
        agents_dir = parent / ".claude" / "agents"
        if agents_dir.is_dir():
            for md_file in sorted(agents_dir.glob("*.md")):
                agent = _parse_agent_markdown(md_file)
                if agent:
                    agents[agent.agent_type] = agent
        
        # Stop at git root
        if (parent / ".git").is_dir():
            break
    
    return agents


def _parse_agent_markdown(filepath: Path) -> Optional[AgentDefinition]:
    """Parse a single agent Markdown file.
    
    Format:
        ---
        name: my-agent
        description: What this agent does
        model: haiku
        tools:
          - Read
          - Grep
        ---
        
        System prompt content here...
    """
    content = filepath.read_text(encoding="utf-8")
    
    # Parse YAML frontmatter
    if not content.startswith("---"):
        return None
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    
    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    
    if not isinstance(frontmatter, dict):
        return None
    
    # Required fields
    name = frontmatter.get("name")
    description = frontmatter.get("description")
    
    if not name or not description:
        return None
    
    system_prompt = parts[2].strip()
    
    # Optional fields with defaults
    model = frontmatter.get("model", "sonnet")
    if model == "inherit":
        model = "sonnet"  # Python version: inherit not directly supported
    
    tools = frontmatter.get("tools", ["*"])
    if isinstance(tools, str):
        tools = [t.strip() for t in tools.split(",")]
    
    disallowed_tools = frontmatter.get("disallowedTools", [])
    if isinstance(disallowed_tools, str):
        disallowed_tools = [t.strip() for t in disallowed_tools.split(",")]
    
    background = frontmatter.get("background", False)
    permission_mode = frontmatter.get("permissionMode", "acceptEdits")
    max_turns = frontmatter.get("maxTurns")
    color = frontmatter.get("color")
    isolation = frontmatter.get("isolation")
    memory = frontmatter.get("memory")
    
    return AgentDefinition(
        agent_type=name,
        description=description,
        prompt=system_prompt,
        model=model,
        background=background,
        isolation=isolation,
        permission_mode=permission_mode,
        tools=tools if isinstance(tools, list) else ["*"],
        disallowed_tools=disallowed_tools if isinstance(disallowed_tools, list) else [],
        max_turns=max_turns,
        color=color,
        memory=memory,
    )
```

然后在 `AgentTool` 中使用：

```python
class AgentTool(Tool):
    def __init__(self):
        super().__init__()
        self._custom_agents: dict[str, AgentDefinition] = {}
    
    def _ensure_agents_loaded(self, cwd: str):
        """Lazy load custom agents from .claude/agents/ directory."""
        if not self._custom_agents:
            from claude_code.agents.loader import load_agents_from_directory
            self._custom_agents = load_agents_from_directory(cwd)
    
    async def execute(self, input_data, context, on_progress=None):
        subagent_type = input_data.get("subagent_type", "general-purpose")
        
        # Load custom agents on first use
        self._ensure_agents_loaded(context.working_directory)
        
        # Check custom agents first (higher priority), then built-in
        agent_def = self._custom_agents.get(subagent_type) or \
                    BUILTIN_AGENTS.get(subagent_type)
        # ... rest of the logic
```

### 7.4 方法四：通过函数式 API 注册 Agent（程序化）

```python
from claude_code.agents.builtin import AgentDefinition, register_agent

# 注册自定义 Agent
register_agent(AgentDefinition(
    agent_type="my-custom-agent",
    description="一个自定义的数据分析 Agent",
    prompt="""你是一个数据分析专家...""",
    model="sonnet",
    permission_mode="default",
))
```

> **注意**：`register_agent()` 已在 `agents/builtin.py` 中实现。新注册的 Agent 会实时添加到全局 `AGENTS` 字典中，并且 `BUILTIN_AGENTS` 在 `tools/agent/__init__.py` 初始化时调用 `create_builtin_agents()` 包含所有已注册 Agent。要使新注册生效，需要重新初始化 `BUILTIN_AGENTS`。

---

## 8. Agent 工具权限与安全模型

### 8.1 白名单 vs 黑名单

Agent 的工具访问通过 **`tools`（白名单）** 和 **`disallowedTools`（黑名单）** 两层控制：

```
最终可用工具 = (白名单工具 ∩ 所有注册工具) - 黑名单工具 - 全局禁止工具
```

### 8.2 全局禁止工具

无论 Agent 如何配置，以下工具 **始终禁止** 在子 Agent 中使用：

| 工具 | 为什么禁止 |
|------|-----------|
| `TaskOutput` | 防止 Agent 读取其他 Agent 的私有输出 |
| `ExitPlanMode` | Plan 模式由父级控制 |
| `EnterPlanMode` | 同上 |
| `Agent` (外部) | 外部 Agent 不可再派子 Agent（防止无限递归）|
| `AskUser` | Agent 不应直接与用户交互 |
| `TaskStop` | 防止 Agent 停止自己或其他 Agent |
| `Workflow` | 工作流由父级控制 |

### 8.3 异步 Agent 工具限制

后台运行的 Agent 只能使用以下工具子集：

```
Read, WebSearch, Todo, Grep, WebFetch, Glob, 
Bash/PowerShell, Edit, Write, Notebook, 
Skill, SyntheticOutput, ToolSearch,
EnterWorktree, ExitWorktree
```

### 8.4 权限模式

| 模式 | 值 | 说明 |
|------|------|------|
| `default` | `PermissionMode.DEFAULT` | 每次危险操作都需要用户确认 |
| `acceptEdits` | `PermissionMode.ACCEPT_EDITS` | 自动允许文件编辑，命令仍需确认（**Agent 默认**） |
| `plan` | `PermissionMode.PLAN` | 只读模式 + 规划，不执行任何修改操作 |
| `auto` | `PermissionMode.AUTO` | 自动允许所有预定义安全操作 |
| `bypass` | `PermissionMode.BYPASS` | 跳过权限检查（等同于 yolo，名称不同） |
| `yolo` | `PermissionMode.YOLO` | 跳过所有权限检查（危险！） |

> **规范**：`PermissionMode` 的唯一权威定义在 `claude_code/permissions.py`。所有其他模块（`config.py`、`engine/context.py`、`engine/permissions.py`、`services/permissions_manager.py`、`state/app_state.py`）均通过 `from claude_code.permissions import PermissionMode` 导入。

### 8.5 在 Python 中实现工具筛选

当前 Python 版本没有实现 `filterToolsForAgent()`。要添加，可以这样：

```python
# claude_code/tools/agent/permissions.py

ALL_AGENT_DISALLOWED_TOOLS = {
    "task_output", "exit_plan_mode", "enter_plan_mode",
    "ask_user", "task_stop", "workflow",
}

ASYNC_AGENT_ALLOWED_TOOLS = {
    "read", "bash", "grep", "glob", "edit", "write",
    "web_search", "web_fetch", "todo_write", "skill",
    "tool_search", "notebook_edit", "enter_worktree", "exit_worktree",
    "synthetic_output",
}


def filter_tools_for_agent(
    all_tools: set[str],
    allowed: list[str] | None,
    disallowed: list[str] | None,
    is_async: bool = False,
    is_external: bool = True,
) -> set[str]:
    """Filter tools available to an agent.
    
    Args:
        all_tools: Full set of registered tool names
        allowed: Whitelist (["*"] means all)
        disallowed: Blacklist
        is_async: Whether the agent runs asynchronously
        is_external: Whether the agent is an external subagent
        
    Returns:
        Filtered set of allowed tool names
    """
    # Start from whitelist or all tools
    if allowed and "*" not in allowed:
        result = set(allowed) & all_tools
    else:
        result = set(all_tools)
    
    # Remove blacklisted tools
    if disallowed:
        result -= set(disallowed)
    
    # Remove globally disallowed tools
    result -= ALL_AGENT_DISALLOWED_TOOLS
    
    # External agents can't spawn sub-agents
    if is_external:
        result -= {"agent"}
    
    # Async agents have restricted tool set
    if is_async:
        result &= ASYNC_AGENT_ALLOWED_TOOLS
    
    return result
```

---

## 9. 同步 vs 异步 vs Fork：三种执行模式

### 9.1 同步 Agent（默认）

```
主对话 ──── 调用 Agent ──── 等待 ──── 获得结果 ──── 继续
                                    ↑
                            Agent 执行中
                            (阻塞主对话)
```

- Agent 运行时，主对话被阻塞
- 如果超过 120 秒，自动转为后台
- 结果直接返回到当前对话

### 9.2 异步 Agent（后台）

```
主对话 ──── 调用 Agent ──── 立即获得 task_id ──── 继续工作
                                                    │
                                          Agent 后台运行中
                                                    │
                          ← 通知: task_id 完成 ──────┘
```

- 主对话不阻塞，可以继续接受用户输入
- 通过 `run_in_background: true` 触发
- 完成后通过通知系统返回结果
- 工具使用受限（见 8.3 节）

### 9.3 Fork Agent（TS 版独有）

```
父对话 ──── 创建 Fork ──── 立即获得回复 ──── 继续
                               │
                    Fork 共享父对话的缓存上下文
                    (显著降低 API 成本)
```

- 继承父对话的 **完整上下文**（包括已渲染的 system prompt）
- 使用父对话的 **完全相同的工具集**
- 目的是利用 Prompt Cache，减少重复 token 计费
- **始终异步**运行
- **不支持嵌套 Fork**（防止无限递归）

> **Python 状态**：Fork Agent 尚未在 Python 版本中实现。Feature Flag `FEATURE_FORK_SUBAGENT=1` 在 Python 版本中已定义但功能未实现。

### 9.4 在 Python 中使用异步 Agent

```python
# 在 AgentTool.execute() 中
result = await self._run_async_agent(
    agent_name="bg-audit",
    description="security audit",
    prompt="Audit all Python files for security vulnerabilities...",
    agent_def=agent_def,
    model="opus",
    isolation=None,
    cwd=context.working_directory,
    context=context,
    on_progress=on_progress,
)
# 返回 task_id，主对话继续
```

---

## 10. TeamMate 多智能体协作

### 10.1 什么是 TeamMate？

TeamMate 是多个 Agent **并行协作**的模式。每个 TeamMate 可以是：

- **进程内 (in-process)**：在同一 Python 进程中运行（默认）
- **分屏 (split-pane)**：在 tmux/iTerm2 分屏中运行
- **独立窗口 (separate-window)**：在 tmux 新窗口中运行

### 10.2 TypeScript 的 spawnMultiAgent

TS 版本支持通过 `team_name` 和 `name` 参数启动 TeamMate：

```json
{
  "description": "前端开发",
  "prompt": "实现用户界面...",
  "name": "frontend-dev",
  "team_name": "web-app-team",
  "subagent_type": "general-purpose"
}
```

### 10.3 实现 TeamMate 的 Python 原型

```python
# claude_code/tools/team/spawn.py

import asyncio
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TeamMateConfig:
    """Configuration for spawning a teammate."""
    name: str
    prompt: str
    team_name: str = "default"
    model: str = "sonnet"
    agent_type: str = "general-purpose"
    use_splitpane: bool = False
    cwd: Optional[str] = None


class TeamMateSpawner:
    """Spawns and manages teammate agents."""
    
    def __init__(self):
        self._teammates: dict[str, asyncio.Task] = {}
    
    async def spawn_in_process(
        self,
        config: TeamMateConfig,
    ) -> str:
        """Spawn a teammate in the same process."""
        from claude_code.engine.query import QueryEngine
        from claude_code.api.client import APIClient, APIClientConfig
        
        api_config = APIClientConfig()
        api_client = APIClient(api_config)
        engine = QueryEngine(api_client=api_client)
        
        # Configure
        engine.config.system_prompt = f"你是团队 '{config.team_name}' 的成员 '{config.name}'。\n\n{config.prompt}"
        engine.config.model = f"claude-{config.model}-4-20250514"
        
        # Run in background
        task = asyncio.create_task(
            self._run_teammate(config, engine)
        )
        self._teammates[config.name] = task
        
        return config.name
    
    async def _run_teammate(
        self,
        config: TeamMateConfig,
        engine: QueryEngine,
    ) -> str:
        """Run a teammate and collect results."""
        result_parts = []
        async for event in engine.query(config.prompt):
            if hasattr(event, 'content'):
                result_parts.append(str(event.content))
        return "\n".join(result_parts)
    
    async def wait_for(self, name: str, timeout: float = 300) -> str:
        """Wait for a teammate to complete."""
        task = self._teammates.get(name)
        if not task:
            raise ValueError(f"Unknown teammate: {name}")
        return await asyncio.wait_for(task, timeout=timeout)
```

---

## 11. Agent 记忆系统

### 11.1 三级记忆范围

| 范围 | 存储位置 | 生命周期 | 用途 |
|------|---------|---------|------|
| `user` | `~/.claude/agent-memory/<agentType>/` | 跨项目、跨会话 | 通用学习知识 |
| `project` | `.claude/agent-memory/<agentType>/` | 项目级，提交到 Git | 项目特定知识 |
| `local` | `.claude/agent-memory-local/<agentType>/` | 项目级，不提交 | 临时/敏感数据 |

### 11.2 记忆如何工作

1. Agent 启动时，系统检查是否有记忆文件
2. 记忆作为额外的 system prompt 注入
3. Agent 可以使用 `Read`、`Write` 工具读写自己的记忆
4. 记忆格式为 `MEMORY.md`

### 11.3 记忆快照（TS 版独有）

项目可以在 `.claude/agent-memory-snapshots/<agentType>/` 中预设记忆，新 Agent 第一次运行时自动复制到本地记忆。

> **Python 状态**：记忆系统尚未实现。

---

## 12. 环境变量与 Feature Flags

### 12.1 Agent 相关环境变量

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `CLAUDE_CODE_SUBAGENT_MODEL` | — | 覆盖所有子 Agent 的模型选择 |
| `FEATURE_FORK_SUBAGENT` | `0` | 启用 Fork 子 Agent（TS 版） |
| `FEATURE_ADVANCED_ORCHESTRATION` | `0` | 启用高级工具编排 |
| `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` | — | 禁用异步 Agent |
| `CLAUDE_AUTO_BACKGROUND_TASKS` | — | 120 秒后自动转后台 |
| `CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS` | — | 在 SDK 模式下禁用内置 Agent |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | — | 启用 Agent 团队（外部用户）|

### 12.2 Python Feature Flags

在 `claude_code/features.py` 中，Agent 相关的 Feature Flags：

```python
class Feature(Enum):
    FORK_SUBAGENT = "fork_subagent"          # Fork 子 Agent
    ADVANCED_ORCHESTRATION = "advanced_orchestration"  # 高级编排
    PLUGINS = "plugins"                       # 插件（含 Agent 插件）
    # ...
```

启用方式：`FEATURE_FORK_SUBAGENT=1 python -m claude_code`

---

## 13. 实战示例集

### 13.1 示例：创建一个代码审查 Agent

**步骤 1：创建 Agent 定义文件**

创建 `.claude/agents/code-reviewer.md`：

```markdown
---
name: code-reviewer
description: 专业的代码审查 Agent，检查安全、性能和最佳实践
model: sonnet
tools:
  - Read
  - Grep
  - Glob
  - Bash
permissionMode: default
---

你是一个资深代码审查专家。

审查维度：
1. **安全性**：SQL 注入、XSS、硬编码密钥、输入验证
2. **性能**：N+1 查询、内存泄漏、不必要的循环
3. **可维护性**：命名规范、函数长度、注释质量
4. **错误处理**：异常捕获是否完善、边界条件

输出格式：
对于每个发现的问题，提供：
- 严重程度：🔴 Critical / 🟡 Medium / 🟢 Low
- 位置：`file:line`
- 问题描述
- 建议修复

最后提供一个总体评分和改进建议摘要。
```

**步骤 2：在代码中注册（当前需要手动注册）**

```python
# 由于 Python 版本的自定义 Agent 加载器尚未实现，
# 暂时需要手动将 Agent 定义添加到 BUILTIN_AGENTS

# 编辑 claude_code/tools/agent/__init__.py
BUILTIN_AGENTS["code-reviewer"] = AgentDefinition(
    agent_type="code-reviewer",
    description="专业的代码审查 Agent",
    prompt="""你是一个资深代码审查专家...""",
    model="sonnet",
)
```

**步骤 3：使用**

在 Claude Code 对话中：

```
> 请审查 src/api/auth.py 的安全性
```

Claude 会调用：

```json
{
  "description": "代码安全审查",
  "prompt": "审查 src/api/auth.py 的安全性...",
  "subagent_type": "code-reviewer"
}
```

### 13.2 示例：创建并行工作的多 Agent 流程

```python
import asyncio
from claude_code.tools.agent import AgentTool, AgentDefinition, BUILTIN_AGENTS
from claude_code.tools.base import ToolContext


async def run_parallel_agents():
    """Run multiple agents in parallel."""
    
    # 定义多个任务
    tasks = [
        ("前端测试", "运行前端测试套件并报告覆盖率", "quick"),
        ("后端测试", "运行后端 API 测试并报告结果", "quick"),
        ("代码审查", "审查最近 5 个 commit 的代码质量", "reviewer"),
    ]
    
    context = ToolContext(working_directory="/path/to/project")
    tool = AgentTool()
    
    # 并行执行
    results = await asyncio.gather(*[
        tool.execute(
            input_data={
                "description": desc,
                "prompt": prompt,
                "subagent_type": agent_type,
                "run_in_background": True,
            },
            context=context,
        )
        for desc, prompt, agent_type in tasks
    ])
    
    for result in results:
        print(result.content)


asyncio.run(run_parallel_agents())
```

### 13.3 示例：在 Worktree 中隔离运行 Agent

```python
# 当需要 Agent 修改代码但不影响当前工作区时，
# 使用 isolation: "worktree"

result = await agent_tool.execute(
    input_data={
        "description": "refactor auth module",
        "prompt": "重构 src/api/auth.py，提取认证逻辑到独立的 middleware",
        "subagent_type": "editor",
        "isolation": "worktree",
    },
    context=ToolContext(working_directory="/path/to/project"),
)
```

Agent 会在 `.claude-worktrees/<agent-name>/` 中创建一个 git worktree，所有修改都在独立分支上。完成后 worktree 会被自动清理。

### 13.4 示例：程序化创建和使用 Agent

```python
from claude_code.engine.query import QueryEngine
from claude_code.api.client import APIClient, APIClientConfig


async def run_custom_agent():
    """直接使用 QueryEngine 运行自定义 Agent。"""
    
    # 1. 配置 API
    api_config = APIClientConfig()
    api_client = APIClient(api_config)
    
    # 2. 创建引擎
    engine = QueryEngine(
        api_client=api_client,
        config=None,
        tool_registry=None,
    )
    
    # 3. 设置 Agent 的系统提示词
    engine.config.system_prompt = """你是一个 Python 代码生成专家。
    只生成符合 PEP 8 的高质量 Python 代码。
    总是包含类型提示和文档字符串。"""
    
    # 4. 设置模型
    engine.config.model = "claude-sonnet-4-20250514"
    
    # 5. 执行
    results = []
    async for event in engine.query(
        "创建一个 FastAPI 应用的用户注册端点"
    ):
        if hasattr(event, 'content') and event.role == 'assistant':
            results.append(str(event.content))
    
    return "\n".join(results)
```

### 13.5 示例：扩展 AgentTool 支持自定义 Agent 目录

这是一个完整的实现方案，将 Python 版本的 AgentTool 与 `.claude/agents/` 目录联动：

```python
# 在 AgentTool 类中添加以下方法

from pathlib import Path
from typing import Optional
import yaml


class AgentTool(Tool):
    def __init__(self):
        super().__init__()
        self._custom_agents: Optional[dict[str, AgentDefinition]] = None
    
    def _load_custom_agents(self, cwd: str) -> dict[str, AgentDefinition]:
        """Load agents from .claude/agents/ directories.
        
        Searches from cwd up to git root, merging agents.
        Project-level agents override user-level agents.
        """
        if self._custom_agents is not None:
            return self._custom_agents
        
        agents: dict[str, AgentDefinition] = {}
        path = Path(cwd).resolve()
        
        search_paths = []
        for parent in [path, *path.parents]:
            agents_dir = parent / ".claude" / "agents"
            if agents_dir.is_dir():
                search_paths.append(agents_dir)
            if (parent / ".git").is_dir():
                break
        
        # Load in reverse order (root first), so deeper dirs override
        for agents_dir in reversed(search_paths):
            for md_file in sorted(agents_dir.glob("*.md")):
                agent = self._parse_agent_markdown(md_file)
                if agent:
                    agents[agent.agent_type] = agent
        
        self._custom_agents = agents
        return agents
    
    def _parse_agent_markdown(self, filepath: Path) -> Optional[AgentDefinition]:
        """Parse an agent .md file with YAML frontmatter."""
        content = filepath.read_text(encoding="utf-8")
        
        if not content.startswith("---"):
            return None
        
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        
        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError:
            return None
        
        if not isinstance(frontmatter, dict):
            return None
        
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        if not name or not description:
            return None
        
        return AgentDefinition(
            agent_type=name,
            description=description,
            prompt=parts[2].strip(),
            model=frontmatter.get("model", "sonnet"),
            background=frontmatter.get("background", False),
            isolation=frontmatter.get("isolation"),
            permission_mode=frontmatter.get("permissionMode", "acceptEdits"),
        )
    
    async def execute(self, input_data, context, on_progress=None):
        subagent_type = input_data.get("subagent_type", "general-purpose")
        
        # Load custom agents (lazy, cached)
        custom_agents = self._load_custom_agents(context.working_directory)
        
        # Priority: custom > built-in
        agent_def = custom_agents.get(subagent_type) or \
                    BUILTIN_AGENTS.get(subagent_type)
        
        if not agent_def:
            available = sorted(set(list(custom_agents.keys()) + list(BUILTIN_AGENTS.keys())))
            return ToolResult(
                content=f"Unknown agent type: {subagent_type}. "
                        f"Available: {', '.join(available)}",
                is_error=True,
            )
        
        # ... rest of execute logic
```

---

## 14. 常见问题与排错

### Q1: Agent 调用报 "Unknown agent type" 错误

**原因**：`subagent_type` 不在 `BUILTIN_AGENTS` 字典中。

**解决**：

1. 检查 `BUILTIN_AGENTS` 的键（`claude_code/tools/agent/__init__.py`）
2. 如果想用自定义 Agent，需要实现加载器或手动注册
3. 当前的 `input_schema` 中 `enum` 只列出了 `BUILTIN_AGENTS` 的键

### Q2: Agent 执行但没有任何结果

**原因**：之前版本有导入路径 bug（使用 `.claude_code.engine.query` 相对导入）。

**已修复**：所有 Agent 内部导入已改为绝对路径 `from claude_code.engine.query import QueryEngine`。如果仍有问题，检查 API key 配置和 QueryConfig 是否正确传递。

> **注意**：`_run_sync_agent()` 和 `_run_async_agent()` 中创建 `APIClient(APIClientConfig())` 时未继承父对话的 API key 配置。如果父对话使用了特定环境变量或自定义 API 配置，子 Agent 会回退到默认配置。这是一个已知的待改进点。

### Q3: 异步 Agent 创建了 Task 但没有实际执行

**已修复**：`_run_async_agent()` 现在使用 `TaskManager.get_instance()` 获取单例，创建 `AgentTask`，然后通过 `start_task(executor=_execute_agent)` 启动实际执行逻辑。执行函数 `_execute_agent()` 创建新的 `QueryEngine` 实例运行 Agent 循环。

### Q4: Agent 无限递归调用

**原因**：Agent 的工具列表包含 `Agent` 工具本身，导致子 Agent 再派子 Agent。

**解决**：在 `filterToolsForAgent()` 中禁止外部 Agent 调用 `Agent` 工具（见第 8 节）。

### Q5: 如何调试 Agent 行为？

1. **设置环境变量**：
   ```bash
   export CLAUDE_VERBOSE=1
   ```
2. **使用同步模式**（`run_in_background: false`），方便在主对话中看到结果
3. **指定 `haiku` 模型**进行快速测试
4. **检查 Agent 的 system prompt**：在 Agent 定义中添加调试信息
5. **限制 `maxTurns`**：避免 Agent 陷入无限循环

### Q6: 自定义 Agent 文件不被识别

**当前已知限制**：Python 版本没有实现 `.claude/agents/` 目录的自动加载。你需要：

1. 实现 `load_agents_from_directory()` 函数（见 7.3 节）
2. 修改 `AgentTool` 的 `execute()` 方法来合并自定义和内置 Agent
3. 或者直接将 Agent 定义硬编码到 `BUILTIN_AGENTS` 字典中

---

## 15. 术语表

| 术语 | 英文 | 解释 |
|------|------|------|
| Agent | Agent | 独立运行的对话实体，拥有自己的系统提示词和工具集 |
| Subagent | Subagent | 由主对话派生的 Agent |
| TeamMate | TeamMate | 多智能体协作中的团队成员 |
| Spawn | Spawn | 创建并启动一个 Agent |
| System Prompt | System Prompt | Agent 的系统提示词，定义其行为和角色 |
| Tool Pool | Tool Pool | Agent 可使用的工具集合 |
| Permission Mode | Permission Mode | Agent 的权限级别 |
| Worktree | Worktree | Git 工作树，用于隔离 Agent 的文件修改 |
| Feature Flag | Feature Flag | 通过环境变量控制的功能开关 |
| Fork | Fork | 继承父上下文的低成本 Agent 模式 |
| Async Agent | Async/Bg Agent | 在后台运行的 Agent |
| AgentDefinition | AgentDefinition | 定义 Agent 类型的数据结构 |
| Frontmatter | Frontmatter | Markdown 文件顶部的 YAML 元数据 |
| Prompt Cache | Prompt Cache | API 提供商的缓存机制，减少重复 token 计费 |
| QueryEngine | QueryEngine | 核心对话引擎，管理消息循环和工具调用 |
| TaskManager | TaskManager | 任务管理器，管理异步 Agent 的生命周期 |

---

> **最后提醒**：Python 版本的 Agent 系统是**骨架状态**。核心框架（`AgentTool`、`AgentDefinition`、`BUILTIN_AGENTS`）已搭好，但以下功能需要你来完善：
>
> 1. ✅ 已实现：`AgentDefinition` 定义、`AgentTool` 调用、同步执行
> 2. ⚠️ 需修复：`_run_sync_agent()` 的导入路径 bug
> 3. ⚠️ 需实现：`_run_async_agent()` 的实际执行逻辑
> 4. ❌ 未实现：`.claude/agents/` 目录自动加载
> 5. ❌ 未实现：工具筛选（`filterToolsForAgent`）
> 6. ❌ 未实现：Fork Agent
> 7. ❌ 未实现：TeamMate 多智能体
> 8. ❌ 未实现：Agent 记忆系统
> 9. ❌ 未实现：Agent 记忆快照
> 10. ❌ 未实现：与 `agents/builtin.py` 注册表的联动
>
> 本文档提供了每个未实现功能的架构参考和代码示例，你可以按照文档中的步骤逐步实现。