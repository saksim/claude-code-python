# claude-code-python 架构评审报告

> 审查日期: 2026-04-09 | 代码总量: ~46,800 行 / 114 个 Python 文件

---

## 一、严重级别定义

| 级别 | 含义 | 处理时限 |
|------|------|---------|
| **P0** | 运行时必定崩溃，阻塞核心功能 | 立即修复 |
| **P1** | 功能逻辑错误，数据不一致 | 本迭代修复 |
| **P2** | 死代码/冗余/技术债 | 规划清理 |
| **P3** | 优化建议/改善方向 | 可选 |

---

## 二、P0 — 运行时崩溃

### BUG-01: TaskManager 类被同一文件中的空壳类覆盖

**文件**: `claude_code/tasks/manager.py`

```
第一次定义 (行 34-289): 完整的 TaskManager 类，包含 create_agent_task()、start_task() 等全量方法
第二次定义 (行 297-308): 空壳 TaskManager 类，仅有 get_instance() 单例方法
```

Python 执行模块级代码时，第二次定义覆盖了第一次。结果：
- `TaskManager()` 实例化得到的是空壳类
- `create_agent_task()`、`start_task()`、`cancel_task()` 等方法全部丢失
- `get_task_manager()` 返回的也是空壳实例
- **所有异步 Agent 执行路径断路**

**修复**:
```python
# 删除行 297-318 的空壳类，将单例模式合并到完整类中
class TaskManager:
    _instance: Optional['TaskManager'] = None
    
    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._background_tasks: set[str] = set()
        self._task_handlers: dict[str, Callable] = {}
        self._event_handlers: list[Callable[[TaskEvent], None]] = []
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'TaskManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    # ... 保留 create_agent_task(), start_task() 等全部方法
```

---

### BUG-02: AgentTool._run_sync_agent() 使用错误的相对导入路径

**文件**: `claude_code/tools/agent/__init__.py` 行 236-237, 270

```python
# 错误 — .claude_code 会解析为 claude_code.tools.agent.claude_code
from .claude_code.engine.query import QueryEngine
from .claude_code.api.client import APIClient, APIClientConfig
from .claude_code.engine.query import Message, ToolUse, ToolCallResult
```

这三个 import 语句在运行时必定抛出 `ModuleNotFoundError`，因为：
- `.claude_code` 在 `tools/agent/` 包内会解析为 `claude_code.tools.agent.claude_code`
- 正确路径应为绝对导入

**修复**:
```python
from claude_code.engine.query import QueryEngine, Message, ToolUse, ToolCallResult
from claude_code.api.client import APIClient, APIClientConfig
```

---

### BUG-03: create_default_registry() 导入路径歧义导致 NotImplementedError

**现象**: 4 个文件导入了错误的 `create_default_registry`:

| 文件 | 导入语句 | 实际获取 |
|------|---------|---------|
| `claude_code/__init__.py:9` | `from claude_code.tools.registry import create_default_registry` | **NotImplementedError** 版本 |
| `claude_code/main.py:31` | `from claude_code.tools.registry import create_default_registry` | **NotImplementedError** 版本 |
| `claude_code/engine/query.py:28` | `from claude_code.tools.registry import create_default_registry` | **NotImplementedError** 版本 |
| `claude_code/tools/search/__init__.py:101` | `from claude_code.tools.registry import create_default_registry` | **NotImplementedError** 版本 |

`claude_code/tools/registry.py:146-148` 中:
```python
def create_default_registry() -> ToolRegistry:
    raise NotImplementedError("Use create_default_registry from claude_code.tools")
```

正确实现在 `claude_code/tools/__init__.py:164-289`，但 Python 的模块解析让 `from claude_code.tools.registry import create_default_registry` 直接指向 `registry.py` 文件中的桩函数。

**修复**: 统一导入路径。在所有需要处使用:
```python
from claude_code.tools import create_default_registry  # 从 __init__.py
```
或删除 `registry.py` 中的桩函数，将实际实现移入 `registry.py`。

---

### BUG-04: frozen=True 的 SessionMetadata 被就地修改

**文件**: `claude_code/engine/session.py` 行 330-331

```python
@dataclass(frozen=True)
class SessionMetadata:
    # ...

def add_message(self, ...):
    self._metadata.message_count += 1  # FrozenInstanceError!
```

`frozen=True` 的 dataclass 不允许字段赋值，运行时抛 `dataclasses.FrozenInstanceError`。

**修复**: 移除 `frozen=True`，或使用 `object.__setattr__` 绕过:
```python
object.__setattr__(self._metadata, 'message_count', self._metadata.message_count + 1)
```

---

### BUG-05: ToolListTool 重复注册导致工具丢失

**文件**: `claude_code/tools/__init__.py`

两个不同的 `TaskListTool` 类被导入:
- 行 91: 来自 `claude_code.tools.workflow` 的 `TaskListTool`
- 行 120: 来自 `claude_code.tools.control` 的 `TaskListTool`

由于 Python 的命名空间规则，**后者覆盖前者**，使用 `from X import TaskListTool` 不会报错，但在 `__init__.py` 的全局命名空间中只保留一个 `TaskListTool`。注册表 `create_default_registry()` 中 `task_list` 只注册一次，实际注册的是 **control 版本**（后导入的）。

workflow 版本的 `TaskListTool` 被静默丢弃。

**修复**: 重命其中一个为 `WorkflowTaskListTool` 或 `ControlTaskListTool`，或合并为一个。

---

## 三、P1 — 功能逻辑错误

### BUG-06: Agent 系统完全断联

`claude_code/agents/builtin.py` (294 行) 和 `claude_code/tools/agent/__init__.py` (360 行) 是两套**完全独立**的系统:

| 维度 | `agents/builtin.py` | `tools/agent/__init__.py` |
|------|-------------------|--------------------------|
| AgentDefinition 字段 | `name`, `system_prompt`, `capabilities` | `agent_type`, `prompt` |
| Agent 数量 | 10 (含 debugger, tester, architect 等) | 4 (general-purpose, editor, reviewer, researcher) |
| 注册机制 | 全局 `AGENTS` 字典 + `register_agent()` | `BUILTIN_AGENTS` 字典（硬编码） |
| 被谁引用 | **无人引用** — 0 处 import | `AgentTool.execute()` |

`agents/builtin.py` 是一座**孤岛** — 没有任何文件 import 它。`setup_builtin_agents()` 从未被调用。10 个精心定义的 Agent 永远不会被使用。

**修复**: 在 `AgentTool.__init__()` 中加载 `agents/builtin.py` 的注册表，合并到 `BUILTIN_AGENTS`:

```python
# tools/agent/__init__.py
from claude_code.agents.builtin import AGENTS as _EXTENDED_AGENTS, AgentDefinition as _ExtAgentDef

class AgentTool(Tool):
    def __init__(self):
        super().__init__()
        self._agents = dict(BUILTIN_AGENTS)  # 复制内置4个
        # 合并扩展的 Agent
        for name, agent in _EXTENDED_AGENTS.items():
            if name not in self._agents:
                self._agents[name] = AgentDefinition(
                    agent_type=agent.name,
                    description=agent.description,
                    prompt=agent.system_prompt,
                    model=agent.model,
                    background=agent.background,
                    permission_mode=agent.permission_mode,
                )
```

---

### BUG-07: 异步 Agent 从未实际执行

`AgentTool._run_async_agent()` 调用 `TaskManager().create_agent_task()`，但:

1. 由于 BUG-01，`TaskManager()` 实例化的是空壳类，没有 `create_agent_task()` 方法 → `AttributeError`
2. 即使修复 BUG-01 使方法存在，`create_agent_task()` 只是创建 `AgentTask` 对象并存入 `_tasks` 字典，**从不调用 `start_task()`**
3. `start_task()` 需要传入 `executor` (Callable)，但 `_run_async_agent()` 没有传

**影响**: 所有 `run_in_background=true` 的 Agent 调用都会创建一个永远停留在 PENDING 状态的任务。

**修复**: 在 `_run_async_agent()` 中实现完整的 Agent 执行逻辑:

```python
async def _run_async_agent(self, agent_name, description, prompt,
                           agent_def, model, isolation, cwd, context, on_progress):
    from claude_code.tasks.manager import TaskManager
    
    task_manager = TaskManager.get_instance()
    task = await task_manager.create_agent_task(
        prompt=prompt, model=model, background=True
    )
    
    async def _execute():
        from claude_code.engine.query import QueryEngine
        from claude_code.api.client import APIClient, APIClientConfig
        
        api_config = APIClientConfig()
        api_client = APIClient(api_config)
        engine = QueryEngine(api_client=api_client)
        engine.config.system_prompt = agent_def.prompt
        if model:
            engine.config.model = f"claude-{model}-4-20250514"
        
        result_parts = []
        async for event in engine.query(prompt):
            if hasattr(event, 'content'):
                result_parts.append(str(event.content))
        return "\n".join(result_parts)
    
    await task_manager.start_task(task.id, executor=_execute)
    return ToolResult(content=f"Started background agent: {agent_name}\nTask ID: {task.id}")
```

---

### BUG-08: Config 从未抵达 Tool 执行层

`claude_code/config.py` 定义了丰富的 `Config` 类（584 行），包含 `permission_mode`、`always_allow`、`always_deny` 等关键字段。但:

1. `main.py` 的 `create_engine()` 直接从 CLI 参数构造 `QueryConfig`，**不使用 Config 对象**
2. `QueryEngine._execute_tool()` 构造 `ToolContext` 时只传入 `working_directory`、`environment`、`abort_signal`
3. **权限检查系统完全失效** — `permissions.py`(247行)、`engine/permissions.py`(602行)、`services/permissions_manager.py`(342行) 三套权限系统全部形同虚设

**影响**: 所有工具调用都**跳过权限检查**，用户无法控制哪些工具需要确认。

---

### BUG-09: PermissionMode 定义 5 次，互相不一致

| 位置 | 枚举值 | 含特殊值 |
|------|--------|---------|
| `config.py:37` | default, auto, plan, bypass, yolo | 有 `YOLO` |
| `engine/context.py:426` | default, plan, auto, accept_edits | 无 `bypass`, 无 `YOLO` |
| `engine/permissions.py:57` | default, plan, auto, accept_edits | 同上 |
| `services/permissions_manager.py:21` | default, auto, plan, bypass | 无 `accept_edits`, 无 `YOLO` |
| `state/app_state.py:18` | default, auto, plan, bypass, yolo | 有 `YOLO` |

`config.py` 和 `state/app_state.py` 包含 `YOLO` 模式；`engine/` 下两个文件包含 `accept_edits` 模式。如果代码中用 `PermissionMode.YOLO` 但引用的是 `engine/context.py` 版本，**运行时抛 ValueError**。

**修复**: 定义单一的 `PermissionMode` 枚举，所有模块从同一位置导入:

```python
# claude_code/permissions.py (统一入口)
from enum import Enum

class PermissionMode(Enum):
    DEFAULT = "default"
    AUTO = "auto"
    PLAN = "plan"
    ACCEPT_EDITS = "acceptEdits"
    BYPASS = "bypass"
    YOLO = "yolo"
```

删除其他 4 处定义，统一 `from claude_code.permissions import PermissionMode`。

---

### BUG-10: api/protocols.py 引用 4 个不存在的模块

**文件**: `claude_code/api/protocols.py` 行 138-141, 179

```python
PROVIDERS = {
    "openai": ("claude_code.api.openai_client", "OpenAIClient"),
    "azure": ("claude_code.api.azure_client", "AzureClient"),
    "bedrock": ("claude_code.api.bedrock_client", "BedrockClient"),
    "vertex": ("claude_code.api.vertex_client", "VertexClient"),
}
```

这 4 个模块 (`openai_client.py`, `azure_client.py`, `bedrock_client.py`, `vertex_client.py`) **不存在**。只有 `claude_code/api/client.py` 包含 Anthropic 提供商的实现。

**影响**: 任何尝试使用 `CLAUDE_API_PROVIDER=openai`（或 azure/bedrock/vertex）将触发 `ImportError`。

**修复**: 实现 4 个提供商客户端，或在 `LLMClientFactory` 中对缺失模块做 graceful fallback:

```python
def get_client(self, provider: str) -> APIClientProtocol:
    if provider == "anthropic":
        from claude_code.api.client import APIClient
        return APIClient(self._config)
    # Provider not yet implemented
    raise ValueError(f"Provider '{provider}' not yet implemented. "
                     f"Currently only 'anthropic' is supported.")
```

---

## 四、P2 — 死代码 / 冗余 / 技术债

### DEAD-01: 孤岛模块（从未被任何文件 import）

| 文件 | 行数 | 说明 |
|------|------|------|
| `claude_code/graph.py` | 239 | 依赖图分析，0 引用 |
| `claude_code/remote.py` | 478 | WebSocket/SSE 远程传输，0 引用 |
| `claude_code/session.py` | 402 | 与 `engine/session.py` 重复的 Session 定义 |
| `claude_code/permissions.py` | 247 | 与 4 处 PermissionMode 重复，0 引用 |
| `claude_code/plugins/__init__.py` | 354 | 插件系统，0 外部引用 |
| `claude_code/diagnostics/snapshots.py` | 275 | 诊断快照，0 引用 |
| `claude_code/modes/` (2 文件) | 223 | 直连模式，0 外部引用 |
| `claude_code/hooks/` (4 文件) | ~1001 | Hook 系统，仅内部自引用 |
| `claude_code/context/` (5 文件) | ~1127 | 仅被 `commands/init/` 引用 |
| `claude_code/porting/` (5 文件) | ~811 | 仅被 `commands/graph.py`(死代码) 引用 |
| `claude_code/bootstrap/` (4 文件) | ~416 | 仅 `setup.py` 内部引用 |
| `claude_code/features.py` | 142 | 仅被 `remote.py`(死代码) 引用 |
| `claude_code/repl/interface.py` | 9 | 空模块 |
| `claude_code/tools/registry_new.py` | 309 | 旧版注册表，0 引用 |
| `claude_code/utils/features.py` | 223 | 与 `features.py` 重复，仅自引用 |
| `claude_code/utils/logging_system.py` | 316 | 与 `utils/logging.py` 重复 |

**合计**: 约 **5,500+ 行死代码**

---

### DEAD-02: 注册但永远失败的工具

| 工具名 | 返回内容 |
|--------|---------|
| `tungsten` | "not available in open source" |
| `web_browser` | "feature not available" |
| `push_notification` | "feature not available" |
| `subscribe_pr` | "feature not available" |
| `ctx_inspect` | "feature not available" |
| `list_peers` | "feature not available" |
| `verify_plan_execution` | "feature not available" |

这 7 个工具在 `create_default_registry()` 中注册，但在 `execute()` 中永远返回错误。它们只会:
1. 增加 API 发送给模型的 tool 列表长度（浪费 token）
2. 误导模型尝试调用然后失败

**修复**: 不注册这些工具，或用 feature flag 门控。

---

### DEAD-03: 从未调用的函数/注册表

| 符号 | 文件 | 说明 |
|------|------|------|
| `setup_builtin_agents()` | `agents/builtin.py:278` | 0 调用 |
| `register_agent()`, `get_agent()`, `list_agents()` | `agents/builtin.py:50-62` | 0 调用 |
| `create_default_registry_old()` | `tools/registry_new.py:299` | 0 调用 |
| `LazyToolRegistry` | `tools/registry_new.py:131` | 0 调用 |
| `get_plugin_manager()` | `plugins/__init__.py:334` | 0 调用 |
| `create_mcp_tool()` | `tools/mcp/__init__.py:369` | 0 调用 |
| `create_browser_tool()` | `tools/browser/__init__.py:261` | 0 调用 |
| `get_default_skills_tools()` | `tools/skills/__init__.py:324` | 0 调用 |

---

### DUPE-01: 两套 Feature Flag 系统

| 位置 | 机制 |
|------|------|
| `claude_code/features.py` | `Feature` 枚举 + `FeatureRegistry` + `feature()` 函数 |
| `claude_code/utils/features_config.py` | `_FeaturesProxy` + config 集成 |

`config.py` 使用 `_FeaturesProxy` 懒加载 `features_config.py`；`features.py` 是完全独立的系统。两者功能重叠但不互通。

**修复**: 合并为单一系统，删除 `features.py`。

---

### DUPE-02: 双重日志系统

| 文件 | 行数 |
|------|------|
| `claude_code/utils/logging.py` | 298 |
| `claude_code/utils/logging_system.py` | 316 |

两个日志模块功能重叠。

---

### DUPE-03: 双重 Session 模块

| 文件 | 行数 |
|------|------|
| `claude_code/session.py` | 402 |
| `claude_code/engine/session.py` | 548 |

`engine/session.py` 是主要使用的版本；根目录的 `session.py` 是孤岛。

---

## 五、未实现功能清单

以下对照 TypeScript 原版，列出 Python 版本未实现的核心功能:

| # | 功能 | TS 版文件 | Python 状态 | 优先级 |
|---|------|----------|-----------|--------|
| 1 | Fork Subagent | `forkSubagent.ts` (210行) | 未实现。`Feature.FORK_SUBAGENT` 已定义但无代码 | P1 |
| 2 | TeamMate 多智能体 | `spawnMultiAgent.ts` (1093行) | 骨架。`tools/team/` 有 4 个空壳工具 | P2 |
| 3 | 自定义 Agent 加载 | `loadAgentsDir.ts` (755行) | 未实现。`.claude/agents/*.md` 不会被读取 | P1 |
| 4 | Agent 工具筛选 | `agentToolUtils.ts` (687行) | 未实现。所有 Agent 获得全部工具 | P1 |
| 5 | Agent 记忆系统 | `agentMemory.ts` | 未实现 | P2 |
| 6 | Agent 记忆快照 | `agentMemorySnapshot.ts` | 未实现 | P3 |
| 7 | Agent 颜色系统 | `agentColorManager.ts` | 未实现 | P3 |
| 8 | Agent 模型解析 | `model/agent.ts` | 未实现。硬编码 `claude-{model}-4-20250514` | P1 |
| 9 | 异步 Agent 通知 | `agentToolUtils.ts` | 未实现。bg Agent 创建后无通知机制 | P1 |
| 10 | Agent 恢复 | `resumeAgent.ts` (265行) | 未实现 | P2 |
| 11 | 异步 Agent 执行 | `agentToolUtils.ts` | BUG: 只创建 Task 不启动执行 | P0 |
| 12 | OpenAI 兼容层 | `services/api/openai/` | 未实现。`protocols.py` 引用 4 个不存在的模块 | P1 |
| 13 | Gemini 兼容层 | `services/api/gemini/` | 未实现 | P2 |
| 14 | 权限系统 | `engine/permissions.ts` | 5 个互相矛盾的 PermissionMode 定义 | P0 |
| 15 | 权限传递到 Tool | `ToolUseContext` | Config 字段从不传递给 ToolContext | P1 |
| 16 | Compaction (上下文压缩) | `compact.ts` | `engine/compact.py` 有骨架但很可能未集成 | P2 |
| 17 | Hook 系统 | `hooks/` (4文件) | 仅自引用，未集成到 QueryEngine | P2 |
| 18 | Plugin 系统 | `plugins/` | 空壳，`get_plugin_manager()` 未调用 | P3 |
| 19 | Diagnostics 快照 | `diagnostics/` | 未集成 | P3 |
| 20 | Remote (WebSocket/SSE) | `remote.ts` | 孤岛模块，0 引用 | P3 |
| 21 | Daemon 模式 | `daemon/` | 未实现 | P3 |
| 22 | BG Sessions | `bgSessions.ts` | 未实现 | P3 |
| 23 | CLI Subcommands (mcp, server, ssh, auth, etc.) | `main.tsx` (4680行) | `main.py` (406行) 只有基础 REPL/pipe | P2 |
| 24 | Transcript Classifier | `transcriptClassifier.ts` | 未实现 | P3 |
| 25 | Worktree 工具 | `EnterWorktree/ExitWorktree` | 骨架存在，但 `AgentTool._create_worktree()` 用 subprocess 而非 Git worktree API | P2 |

---

## 六、架构层面问题

### ARCH-01: 包导入拓扑混乱

```
main.py → tools.registry → registry.py (NotImplementedError)  ❌
main.py → 应该 → tools/__init__.py → create_default_registry()  ✅

__init__.py → tools.registry → registry.py (NotImplementedError)  ❌
__init__.py → 应该 → tools → create_default_registry()  ✅
```

Python 的模块解析机制让 `from claude_code.tools.registry import X` 直接指向 `tools/registry.py` 文件，绕过 `tools/__init__.py` 中重新定义的 `create_default_registry()`。

**根因**: `registry.py:146-148` 的桩函数本意是"指引开发者使用正确路径"，但它会运行时崩溃。

**建议**: 将 `tools/__init__.py` 中 `create_default_registry()` 的实现移入 `registry.py`，删除 `__init__.py` 中的重新定义。统一所有导入路径为 `from claude_code.tools.registry import create_default_registry`。

---

### ARCH-02: DI 容器未被使用

`claude_code/di/container.py` (405行) 实现了完整的依赖注入容器，包括循环依赖检测、生命周期管理等。但:

- `app.py` 有自己的 `AppConfig` / `App` 类，直接 `__init__` 硬编码依赖
- `QueryEngine` 在 `main.py` 中手动构造
- `APIClient` 在每次使用时直接 `APIClient(APIClientConfig())` 实例化
- `TaskManager` 使用模块级单例 (`get_task_manager()`)
- `ToolRegistry` 使用工厂函数 (`create_default_registry()`)

5 种不同的依赖获取模式并存，DI 容器是第 6 种但从未启用。

**建议**: 选定一种模式（推荐 DI 容器或简单模块级单例），移除其余模式。

---

### ARCH-03: 5 套 PermissionMode 碎片化

5 处独立定义 `PermissionMode` 枚举，字段各不相同:

```
config.py            → default, auto, plan, bypass, yolo
engine/context.py    → default, plan, auto, accept_edits
engine/permissions.py → default, plan, auto, accept_edits
services/perm_mgr.py → default, auto, plan, bypass
state/app_state.py   → default, auto, plan, bypass, yolo
```

**建议**: 保留 `claude_code/permissions.py`（根目录已存在但未被使用），将完整枚举定义在此，所有模块统一导入。

---

### ARCH-04: Agent 系统两套定义不兼容

| 维度 | `tools/agent/__init__.py` | `agents/builtin.py` |
|------|--------------------------|---------------------|
| 主键字段 | `agent_type` | `name` |
| 提示词字段 | `prompt` | `system_prompt` |
| 能力字段 | 无 | `capabilities: list[AgentCapability]` |
| 注册机制 | `BUILTIN_AGENTS` dict | `AGENTS` 全局 dict + `register_agent()` |
| 数据类 | `@dataclass(frozen=True, slots=True)` | `@dataclass` (可变) |
| 基类 | 无 | `AgentDefinition` → `BuiltinAgent` |
| 子类化 | 不支持 | `BuiltinAgent(AgentDefinition)` |

两个 `AgentDefinition` 是**不兼容的类型**，无法互相替代。

**建议**: 统一为单一 `AgentDefinition`，保留更完整的 `agents/builtin.py` 版本，让 `AgentTool` 引用它。

---

### ARCH-05: Config 层级断裂

```
config.py (Config, 584行) ──── 被 app.py 完全忽略
    ↓ (断裂)
app.py (AppConfig, 469行) ──── 自己的配置系统
    ↓ (断裂)
main.py (QueryConfig, inline) ── 直接从 CLI args 造配置
    ↓ (断裂)
engine/query.py (QueryEngine) ── 接收 QueryConfig 但看不到 Config
    ↓ (断裂)
tools/base.py (ToolContext) ── 只有 working_directory + env + abort_signal
```

Config 中的 `permission_mode`、`always_allow`、`always_deny`、`model_overrides` 等关键配置**从未到达**工具执行层。

---

## 七、修复优先级路线图

### Phase 1: 修复 P0 崩溃 (估算 1-2 天)

| 修复项 | 工作量 |
|--------|--------|
| BUG-01: 修复 TaskManager 重复类定义 | 0.5h |
| BUG-02: 修复 AgentTool 导入路径 | 0.5h |
| BUG-03: 统一 create_default_registry 导入 | 1h |
| BUG-04: 修复 SessionMetadata frozen 修改 | 0.5h |
| BUG-05: 修复 TaskListTool 命名冲突 | 0.5h |

### Phase 2: 修复 P1 功能中断 (估算 3-5 天)

| 修复项 | 工作量 |
|--------|--------|
| BUG-06: 统一 Agent 系统定义 | 2h |
| BUG-07: 修复异步 Agent 执行 | 3h |
| BUG-08: Config 传递到 ToolContext | 4h |
| BUG-09: 统一 PermissionMode | 2h |
| BUG-10: 修复 protocols.py 缺失模块 | 2h |

### Phase 3: 清理 P2 死代码 (估算 2-3 天)

| 清理项 | 工作量 |
|--------|--------|
| 删除 5,500 行死代码 | 4h |
| 移除 7 个永远失败的工具注册 | 1h |
| 合并重复的 feature/logging/session 模块 | 3h |
| 删除 registry_new.py | 0.5h |

### Phase 4: 实现核心缺失功能 (估算 1-2 周)

| 功能 | 基于 AGENT.MD 章节 | 优先级 |
|------|-------------------|--------|
| 自定义 Agent 加载器 | AGENT.MD §7.3 | 高 |
| Agent 工具筛选 | AGENT.MD §8 | 高 |
| 异步 Agent 执行 + 通知 | AGENT.MD §9.2 | 高 |
| 模型解析逻辑 | — | 高 |
| Fork Subagent | AGENT.MD §9.3 | 中 |

---

## 八、架构优化建议

### 1. 统一依赖注入模式

当前 6 种依赖获取模式并存:
- DI 容器 (`di/container.py`)
- 模块级单例 (`get_task_manager()`)
- 工厂函数 (`create_default_registry()`)
- 直接构造 (`APIClient(APIClientConfig())`)
- 全局变量 (`_task_manager`, `_global_registry`)
- AppConfig 硬编码 (`app.py`)

**建议**: 选定模块级单例模式（最 Pythonic），移除 DI 容器和全局变量模式。

### 2. 分层配置管道

```
CLI Args / Env Vars
       │
       ▼
   Config (统一对象)
       │
       ├─→ QueryEngine.config
       ├─→ ToolContext.config
       ├─→ APIClient.config
       └─→ PermissionChecker.config
```

每个下游组件从同一个 Config 对象获取其配置片段，而非各自读取 env vars。

### 3. Agent 系统重构方向

```
claude_code/agents/           ← 统一入口
    ├── __init__.py            ← 重导出
    ├── definition.py          ← 唯一的 AgentDefinition dataclass
    ├── registry.py             ← Agent 注册/查找，合并 BUILTIN_AGENTS + 自定义加载
    ├── loader.py               ← .claude/agents/*.md 解析器 (AGENT.MD §7.3)
    ├── executor.py             ← 同步/异步/Fork 执行逻辑
    └── builtin/                ← 内置 Agent 定义
        ├── general_purpose.py
        ├── editor.py
        ├── reviewer.py
        └── ...
    
claude_code/tools/agent/       ← AgentTool (薄层，委托给 agents/)
    └── __init__.py             ← 仅保留 AgentTool 类，引用 agents/
```

### 4. 工具注册表重构

- 删除 `registry.py` 中的 `NotImplementedError` 桩
- 将 `create_default_registry()` 实现移入 `registry.py`
- `__init__.py` 仅做重新导出
- 不注册永远失败的工具（7 个 internal tools）
- feature flag 门控有条件注册

---

## 九、风险矩阵

| 风险 | 影响 | 概率 | 缓解 |
|------|------|------|------|
| P0 BUG 导致主流程崩溃 | 阻塞全部 Agent 功能 | 100% | Phase 1 立即修复 |
| Permission 不一致导致运行时 ValueError | 特定权限模式崩溃 | 80% | 统一 PermissionMode |
| Config 断裂导致权限检查形同虚设 | 安全风险 | 100% | 打通 Config → ToolContext 管道 |
| 死代码增加维护成本和新人困惑 | 低效 | 100% | 删除明确无用的 ~5500 行 |
| 多 Provider 支持 merely 抛异常 | OpenAI/Gemini/Azure/Bedrock 全部不可用 | 100% | 实现 provider 或 graceful 降级 |
| 两套 Agent 系统互相矛盾 | 新人无法判断使用哪个 | 90% | 合并为单一系统 |

---

**结论**: 项目核心架构（QueryEngine 循环 + Tool 注册表 + REPL + 多 Provider API 客户端）方向正确，但在**集成层**有严重断裂。5 个 P0 级 BUG 阻塞了 Agent 系统的任何实际使用，P1 级的逻辑错误导致权限系统完全失效和多 Provider 支持形同虚设。建议按 Phase 1-4 路线图逐步修复，优先解决 P0 崩溃问题。