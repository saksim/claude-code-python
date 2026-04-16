# claude-code-python 修复方案汇总

> 以下每个方案都包含：问题描述、修复代码、可行性评估、风险点。请逐条讨论。

---

## P0-01: TaskManager 类被空壳覆盖

**问题**: `tasks/manager.py` 第 34 行定义完整 `TaskManager` 类（含 `create_agent_task` 等），第 297 行又定义同名空壳类，后者覆盖前者。所有方法丢失。

**修复**: 删除空壳类，将单例模式合并到完整类。

```python
# 删除 managers.py 第 293-318 行的空壳类和无用全局变量
# 将单例模式合并到完整类中

class TaskManager:
    """Manages task execution and tracking."""
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
    
    # ... 保留原有全部方法（create_bash_task, create_agent_task, start_task 等）
    #     一行不改，只是移到这个类里面

# 保留模块级便捷函数，但指向合并后的类
def get_task_manager() -> TaskManager:
    return TaskManager.get_instance()

def set_task_manager(manager: TaskManager) -> None:
    TaskManager._instance = manager
```

**可行性**: ✅ 纯删除+微调，无依赖变化  
**风险**: 低。空壳类从未被正常使用（因为 `TaskManager()` 会得到无方法实例，任何调用即刻崩溃）

---

## P0-02: AgentTool 导入路径错误

**问题**: `tools/agent/__init__.py` 第 236-237, 270 行使用 `.claude_code.engine.query` 相对导入，该路径不存在。

```python
# 当前（错误）
from .claude_code.engine.query import QueryEngine          # 行 236
from .claude_code.api.client import APIClient, APIClientConfig  # 行 237
from .claude_code.engine.query import Message, ToolUse, ToolCallResult  # 行 270
```

**修复**: 改为绝对导入。

```python
# 修复后
from claude_code.engine.query import QueryEngine, Message, ToolUse, ToolCallResult
from claude_code.api.client import APIClient, APIClientConfig
```

同时，`Message`, `ToolUse`, `ToolCallResult` 这些类在 `engine/query.py` 中都定义了（行 51-99），需确认它们在 `__all__` 或可直接导入。检查 `engine/query.py` 的导出：

```python
# engine/query.py 中确认这些类公开可导出
# 行 51-99 已经定义了 Message, ToolUse, ToolCallResult
# 只需确保 engine/__init__.py 重新导出即可
```

**可行性**: ✅ 一行改动  
**风险**: 极低。只需要确认 `claude_code.engine.query` 模块中确实导出了这些类名。

**额外修复**: 行 270 的 `ToolCallResult` 在 `engine/query.py` 中可能不存在（需确认），如果不存在，应删除该导入并调整事件处理逻辑。

---

## P0-03: create_default_registry() 导入歧义

**问题**: 4 个文件 `from claude_code.tools.registry import create_default_registry` 获得的是抛 `NotImplementedError` 的桩函数，而非 `tools/__init__.py` 中的真实实现。

Python 模块解析让 `claude_code.tools.registry` 指向 `tools/registry.py` 文件，而不是 `tools/` 包。

**修复方案 A** (推荐): 将真实实现移入 `registry.py`，删除 `__init__.py` 中的重复定义。

```python
# tools/registry.py — 用 tools/__init__.py 中的实现替换桩函数

def create_default_registry() -> ToolRegistry:
    """Create the default tool registry with all built-in tools."""
    registry = ToolRegistry(lazy=True)
    # 从 tools/__init__.py 的实现原样搬过来
    registry.register_lazy("bash", lambda: BashTool(), ["shell", "sh"])
    registry.register_lazy("read", lambda: ReadTool(), ["file_read", "read_file"])
    # ... 全部注册行 ...
    return registry
```

然后 `tools/__init__.py` 改为从 `registry.py` 重新导出：

```python
# tools/__init__.py — 删除 create_default_registry 的本地定义，改为重新导出
from claude_code.tools.registry import ToolRegistry, create_default_registry
```

**修复方案 B**: 修改所有导入路径为 `from claude_code.tools import create_default_registry`。

需要改动 4 个文件：
- `claude_code/__init__.py:9`
- `claude_code/main.py:31`
- `claude_code/engine/query.py:28`
- `claude_code/tools/search/__init__.py:101`

**可行性**: ✅ 方案 A 更干净（单点修改），方案 B 更保守  
**风险**: 方案 A 需要小心移动大块代码；方案 B 需要改动 4 处导入，遗漏即崩。

**我推荐方案 A**，因为从根本上消除了歧义——`registry.py` 成为单一职责模块。

---

## P0-04: frozen SessionMetadata 被就地修改

**问题**: `engine/session.py` 第 24 行 `SessionMetadata` 定义为 `@dataclass(frozen=True, slots=True)`，但第 330-331 行直接修改其字段：

```python
self._metadata.message_count += 1   # FrozenInstanceError!
self._metadata.last_active = time.time()  # FrozenInstanceError!
```

**修复方案 A** (最小改动): 移除 `frozen=True`。

```python
@dataclass(slots=True)  # 移除 frozen=True
class SessionMetadata:
    id: str
    created_at: float
    # ... 其余不变
```

**修复方案 B** (更健壮): 保留 frozen，使用 `object.__setattr__` 绕过。

```python
def add_message(self, role: str, content: str, **kwargs) -> MessageRecord:
    msg = MessageRecord(...)
    self._messages.append(msg)
    object.__setattr__(self._metadata, 'message_count', self._metadata.message_count + 1)
    object.__setattr__(self._metadata, 'last_active', time.time())
    # ...
```

**可行性**: ✅ 方案 A 最简单；方案 B 保留 frozen 的不可变语义  
**风险**: 方案 A 丧失 frozen 保护（metadata 可被意外修改）；方案 B 对 `slots=True` 的 dataclass 有效但不够 Pythonic。

**我推荐方案 A**：`SessionMetadata` 在内部被频繁修改计数器，本身就不应该 frozen。frozen 更适合纯值对象。

---

## P0-05: TaskListTool 命名冲突

**问题**: `tools/workflow/__init__.py` 导出的 `TaskListTool` 和 `tools/control/__init__.py` 导出的 `TaskListTool` 同名，后者覆盖前者。注册表中 `task_list` 只存在一个，workflow 版本被静默丢弃。

**修复**: 将 `tools/control/` 中的版本重命名为 `ControlTaskListTool`，区分两个不同功能的工具。

```python
# tools/control/__init__.py — 重命名
class ControlTaskListTool(Tool):  # 原 TaskListTool
    @property
    def name(self) -> str:
        return "control_task_list"  # 原 "task_list"

# tools/__init__.py — 更新导入和注册
from claude_code.tools.control import (
    TaskStopTool,
    TaskOutputTool,
    ControlTaskListTool,  # 原 TaskListTool
)

# ...
registry.register_lazy("control_task_list", lambda: ControlTaskListTool())
```

或者在 workflow 包中重命名：

```python
# tools/workflow/__init__.py — 重命名
class WorkflowTaskListTool(Tool):
    @property
    def name(self) -> str:
        return "workflow_task_list"

# tools/__init__.py
registry.register_lazy("workflow_task_list", lambda: WorkflowTaskListTool())
```

**可行性**: ✅ 简单重命名  
**风险**: 如果有代码通过 `TaskListTool` 类名引用，需要全局替换。搜索确认只有 `tools/__init__.py` 和各自的 `__init__.py` 引用。

---

## P1-06: Agent 系统两套定义断联

**问题**: `agents/builtin.py`（294行, 10个Agent）无人导入，与 `tools/agent/__init__.py`（4个Agent）完全独立。

**修复**: 统一为单一 `AgentDefinition`，让 `AgentTool` 引用 `agents/builtin.py`。

步骤：
1. 在 `agents/builtin.py` 中统一字段名，使其兼容 `tools/agent/__init__.py` 的 `AgentDefinition`
2. 让 `AgentTool` 加载 `agents/builtin.py` 的 Agent 列表

```python
# agents/builtin.py — 将 name/system_prompt 映射为 agent_type/prompt
# 保留原有 BuiltinAgent(dataclass)，但增加转换方法

@dataclass
class AgentDefinition:
    """Unified agent definition."""
    agent_type: str       # 原 name 字段
    description: str
    prompt: str           # 原 system_prompt 字段
    model: str = "sonnet"
    background: bool = False
    isolation: Optional[str] = None
    permission_mode: str = "acceptEdits"
    tools: list[str] = field(default_factory=lambda: ["*"])
    disallowed_tools: list[str] = field(default_factory=list)
    color: Optional[str] = None
    max_turns: Optional[int] = None
    memory: Optional[str] = None
```

```python
# tools/agent/__init__.py — 引用 agents/builtin.py

from claude_code.agents.builtin import create_builtin_agents

# 构建完整 Agent 字典
def _build_agent_registry() -> dict[str, AgentDefinition]:
    """Build agent registry from builtin agents."""
    from claude_code.agents.builtin import create_builtin_agents
    builtin = create_builtin_agents()
    return {
        name: AgentDefinition(
            agent_type=agent.name,
            description=agent.description,
            prompt=agent.system_prompt,
            model=agent.model,
            background=agent.background,
            permission_mode=agent.permission_mode,
        )
        for name, agent in builtin.items()
    }

# 替换硬编码的 BUILTIN_AGENTS
ALL_AGENTS: dict[str, AgentDefinition] = _build_agent_registry()
```

**可行性**: ✅ 需要统一两个 `AgentDefinition` 的字段名  
**风险**: 中等。需要确保字段映射正确，特别是 `name → agent_type` 和 `system_prompt → prompt`。

---

## P1-07: 异步 Agent 从未执行

**问题**: `_run_async_agent()` 调用 `TaskManager().create_agent_task()`，但：
1. 由于 P0-01，拿到的是空壳 `TaskManager`
2. 即使修复 P0-01，`create_agent_task()` 只创建 Task 对象，不调用 `start_task()`

**修复**: 重写 `_run_async_agent()` 方法，实现真正的异步执行。

```python
async def _run_async_agent(
    self,
    agent_name: str,
    description: str,
    prompt: str,
    agent_def: AgentDefinition,
    model: str,
    isolation: Optional[str],
    cwd: str,
    context: ToolContext,
    on_progress: Optional[ToolCallback],
) -> ToolResult:
    """Run agent asynchronously in background."""
    from claude_code.tasks.manager import TaskManager
    from claude_code.engine.query import QueryEngine
    from claude_code.api.client import APIClient, APIClientConfig
    
    task_manager = TaskManager.get_instance()  # 用单例而非新实例
    task = await task_manager.create_agent_task(
        prompt=prompt,
        model=model,
        background=True,
    )
    
    async def _execute_agent(task: Task) -> TaskResult:
        api_config = APIClientConfig()
        api_client = APIClient(api_config)
        engine = QueryEngine(api_client=api_client)
        engine.config.system_prompt = agent_def.prompt
        if model:
            engine.config.model = f"claude-{model}-4-20250514"
        
        result_parts = []
        async for event in engine.query(prompt):
            if hasattr(event, 'content') and hasattr(event, 'role') and event.role == "assistant":
                content = event.content
                if isinstance(content, str):
                    result_parts.append(content)
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            result_parts.append(block.get("text", ""))
        
        return TaskResult(
            code=0,
            stdout="\n".join(result_parts) if result_parts else "Agent completed with no output",
        )
    
    await task_manager.start_task(task.id, executor=_execute_agent)
    
    return ToolResult(
        content=f"Started background agent: {agent_name}\n"
                f"Task ID: {task.id}\n"
                f"Description: {description}\n\n"
                f"Use /tasks to monitor progress."
    )
```

同时删除无用的导入（行 304-305 导入了 `TaskType` 和 `BashTask` 但未使用）。

**可行性**: ✅ 核心逻辑已存在，只需串联  
**风险**: 中等。`_execute_agent` 内部创建新 `QueryEngine` 实例，需确保它能正确运行（依赖 P0-02 的修复）。另外，API 客户端配置需要从主对话继承而非硬编码。

---

## P1-08: Config 从未传递到 Tool 层

**问题**: `Config` 有 `permission_mode`、`always_allow`、`always_deny` 等关键字段，但 `ToolContext` 只有 `working_directory`、`environment`、`abort_signal`。权限检查形同虚设。

**修复**: 扩展 `ToolContext` 以携带配置，并在 `QueryEngine` 构造时传递。

```python
# tools/base.py — 扩展 ToolContext

@dataclass
class ToolContext:
    """Context available during tool execution."""
    working_directory: str
    environment: dict[str, str] = field(default_factory=dict)
    read_file_cache: dict[str, str] = field(default_factory=dict)
    abort_signal: Optional[asyncio.Event] = None
    # ↓↓↓ 新增字段 ↓↓↓
    permission_mode: str = "default"
    always_allow: list[str] = field(default_factory=list)
    always_deny: list[str] = field(default_factory=list)
    model: Optional[str] = None
    session_id: Optional[str] = None
    
    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if a tool is allowed based on permission context."""
        if tool_name in self.always_deny:
            return False
        if tool_name in self.always_allow:
            return True
        # In default mode, all tools need confirmation
        if self.permission_mode == "default":
            return True  # but needs user confirmation
        if self.permission_mode == "yolo":
            return True  # bypass all checks
        if self.permission_mode == "plan":
            return tool_name in ("read", "glob", "grep", "web_search", "web_fetch")
        return True
```

```python
# engine/query.py — 在 _execute_tool 中传递配置

def _execute_tool(self, tool, tool_input, config=None):
    context = ToolContext(
        working_directory=self._working_directory,
        environment=dict(os.environ),
        abort_signal=self._abort_signal,
        permission_mode=config.permission_mode if config else "default",
        always_allow=config.always_allow if config else [],
        always_deny=config.always_deny if config else [],
        model=config.model if config else None,
    )
```

**可行性**: ✅ 扩展 dataclass 是向后兼容的（所有新字段有默认值）  
**风险**: 低。不影响现有调用方（它们不传新字段时使用默认值）。

---

## P1-09: PermissionMode 五处定义不一致

**问题**: 5 个文件各自定义 `PermissionMode` 枚举，值各不相同。

**修复**: 以 `claude_code/permissions.py`（根目录）为权威来源，统一定义。

```python
# claude_code/permissions.py — 替换现有内容

"""
Claude Code Python - Unified Permission System

This module is the single source of truth for permission types.
All other modules must import from here.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class PermissionMode(Enum):
    """Permission modes for tool execution.
    
    Single canonical definition — all modules import from here.
    """
    DEFAULT = "default"
    AUTO = "auto"
    PLAN = "plan"
    ACCEPT_EDITS = "acceptEdits"
    BYPASS = "bypass"
    YOLO = "yolo"


# PermissionMode 字符串值列表，方便校验
PERMISSION_MODES: list[str] = [m.value for m in PermissionMode]


@dataclass(frozen=True, slots=True)
class ToolPermissionContext:
    """Permission context for tool execution control."""
    # ... 保留原有 ToolPermissionContext 实现
```

然后在其他 4 个文件中删除本地定义，改为导入：

```python
# engine/context.py — 删除本地 PermissionMode 定义，改为：
from claude_code.permissions import PermissionMode, ToolPermissionContext

# engine/permissions.py — 同上
# services/permissions_manager.py — 同上
# state/app_state.py — 同上
# config.py — 同上
```

每个文件删除 `class PermissionMode(Enum):` 块及其枚举成员定义。

**可行性**: ✅ 标准重构  
**风险**: 中等。需要确保所有引用 `PermissionMode.XXX` 的代码都使用统一枚举值。需全局搜索替换。

---

## P1-10: protocols.py 引用不存在的模块

**问题**: `api/protocols.py` 引用 4 个不存在的模块（`openai_client`, `azure_client`, `bedrock_client`, `vertex_client`）。

**修复方案 A** (渐进式): 对缺失模块做 graceful 降级。

```python
# api/protocols.py — 修改 LLMClientFactory.create()

@classmethod
def create(cls, provider: str, api_key=None, base_url=None, model=None, **kwargs):
    provider = provider.lower()
    
    if provider == "anthropic":
        from claude_code.api.client import APIClient, APIClientConfig, APIProvider
        config = APIClientConfig(api_key=api_key, provider=APIProvider.ANTHROPIC, base_url=base_url)
        return APIClient(config)
    
    elif provider in ("openai", "ollama", "vllm", "deepseek"):
        try:
            from claude_code.api.openai_client import OpenAIClient
            return OpenAIClient(api_key=api_key or "dummy", base_url=base_url, model=model)
        except ImportError:
            raise ValueError(
                f"OpenAI-compatible provider '{provider}' requires the openai package. "
                f"Install with: pip install openai"
            )
    
    elif provider == "azure":
        raise ValueError(
            "Azure OpenAI provider is not yet implemented. "
            "Use CLAUDE_API_PROVIDER=anthropic instead."
        )
    
    elif provider == "bedrock":
        raise ValueError(
            "AWS Bedrock provider is not yet implemented. "
            "Use CLAUDE_API_PROVIDER=anthropic instead."
        )
    
    elif provider == "vertex":
        raise ValueError(
            "Google Vertex AI provider is not yet implemented. "
            "Use CLAUDE_API_PROVIDER=anthropic instead."
        )
    
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

**修复方案 B** (完整式): 创建 4 个 provider 适配器。

这需要分别实现每个提供商的流式响应转换。工作量较大，建议先做方案 A，再逐步实现提供商。

**可行性**: 方案 A ✅ 立即可行；方案 B ⏳ 需要大量工作  
**风险**: 方案 A 零风险（原来也是崩溃，改为明确错误信息）

---

## P2-11: 删除死代码

**问题**: ~5,500 行从未被引用的代码。

**修复**: 逐步删除以下模块：

| 优先级 | 模块 | 行数 | 说明 |
|--------|------|------|------|
| 高 | `tools/registry_new.py` | 309 | 旧版注册表，`create_default_registry_old()` 从未调用 |
| 高 | `utils/features.py` | 223 | 与 `features.py` 重复 |
| 高 | `session.py` (根目录) | 402 | 与 `engine/session.py` 重复 |
| 高 | `repl/interface.py` | 9 | 空文件 |
| 中 | `graph.py` | 239 | 0 引用 |
| 中 | `remote.py` | 478 | 0 引用 |
| 中 | `plugins/__init__.py` | 354 | 0 引用 |
| 中 | `diagnostics/snapshots.py` | 275 | 0 引用 |
| 中 | `modes/` | 223 | 0 外部引用 |
| 低 | `hooks/` | ~1001 | 仅内部引用 |
| 低 | `context/` | ~1127 | 被 `commands/init` 引用（保留） |
| 低 | `porting/` | ~811 | 被 `commands/graph` 引用（graph 是死代码，但 porting 审计功能有价值） |

**删除策略**: 先标记为 `# DEPRECATED: 将在下一版本移除`，而非直接删除。给使用者一个过渡期。

```python
# 在每个要废弃的文件头部添加：
import warnings
warnings.warn(
    f"{__name__} is deprecated and will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)
```

**可行性**: ✅ 低风险，纯删除  
**风险**: 如果有外部代码导入这些模块（不太可能因为是内部项目），会报 ImportError。

---

## P2-12: 移除永远失败的工具注册

**问题**: 7 个 internal 工具注册后永远返回 "not available" 错误。

**修复**: 在 `create_default_registry()` 中用 feature flag 门控。

```python
# tools/__init__.py — 在注册部分添加

from claude_code.features import feature, Feature

# Internal/feature-gated tools — 仅在对应功能启用时注册
if feature(Feature.BUDDY):
    registry.register_lazy("tungsten", lambda: TungstenTool())

# 其他永远不可用的工具，直接不注册
# 或者保留注册但添加 clear 的描述说明不可用
```

对于确定永远不可用的工具（push_notification, subscribe_pr, ctx_inspect, list_peers, verify_plan_execution），直接移除注册：

```python
# tools/__init__.py — 删除以下行
# registry.register_lazy("push_notification", lambda: PushNotificationTool())
# registry.register_lazy("subscribe_pr", lambda: SubscribePRTool())
# registry.register_lazy("ctx_inspect", lambda: CtxInspectTool())
# registry.register_lazy("list_peers", lambda: ListPeersTool())
# registry.register_lazy("verify_plan_execution", lambda: VerifyPlanExecutionTool())
```

**可行性**: ✅ 简单删除注册行  
**风险**: 极低。这些工具永远返回错误，移除它们只会减少发送给 API 的 tool 列表长度（节省 token）。

---

## P2-13: 合并重复模块

| 重复组 | 保留 | 删除 | 行数节省 |
|--------|------|------|---------|
| Feature 系统 | `features.py` | `utils/features.py` | 223 |
| Session 定义 | `engine/session.py` | `session.py` (根目录) | 402 |
| PermissionMode | 统一到 `permissions.py` | 其他 4 处定义 | ~100 |
| Logging | `utils/logging.py` | `utils/logging_system.py` | 316 |
| ToolRegistry | `tools/registry.py` (合并后) | `tools/registry_new.py` | 309 |

**可行性**: ✅ 纯重构  
**风险**: 需要全局搜索所有 import 路径并更新。建议 IDE 辅助重构。

---

## P2-14: 7 个未调用的公共函数

| 函数 | 文件 | 处理 |
|------|------|------|
| `setup_builtin_agents()` | `agents/builtin.py:278` | 被修复 P1-06 后会使用 |
| `register_agent()` | `agents/builtin.py:50` | 被修复 P1-06 后会使用 |
| `get_agent()` | `agents/builtin.py:55` | 同上 |
| `list_agents()` | `agents/builtin.py:60` | 同上 |
| `create_default_registry_old()` | `registry_new.py:299` | 删除 |
| `get_default_skills_tools()` | `tools/skills/__init__.py:324` | 保留或删除（看 skills 是否实现） |
| `create_mcp_tool()` | `tools/mcp/__init__.py:369` | 保留或删除（看 mcp 是否实现） |

前 4 个在 P1-06 修复后会自然成为活代码。后 3 个需评估。

---

## 未实现功能修复优先级

| # | 功能 | 修复策略 | 工作量 | 优先级 |
|---|------|---------|--------|--------|
| 1 | 自定义 Agent 加载器 | AGENT.MD §7.3 的 `loader.py` | 4h | P1 |
| 2 | Agent 工具筛选 | AGENT.MD §8 的 `filterToolsForAgent()` | 3h | P1 |
| 3 | 异步 Agent 执行通知 | 在 `_run_async_agent` 完成后通过事件系统通知 | 4h | P1 |
| 4 | 模型解析 | `model/agent.py` — 将 `claude-{model}-4-20250514` 替换为查表 | 2h | P1 |
| 5 | OpenAI 兼容层 | P1-10 方案 A（降级错误）+ 方案 B（逐步实现） | 8h+ | P1→P2 |
| 6 | Config 传递 | P1-08 修复后，后续功能逐步添加 | 2h | P1 |
| 7 | Fork Subagent | 参照 TS 版 `forkSubagent.ts` 实现 | 16h | P2 |
| 8 | TeamMate 多智能体 | 参照 TS 版 `spawnMultiAgent.ts` 实现 | 20h | P2 |
| 9 | Agent 记忆系统 | 参照 TS 版 `agentMemory.ts` 实现 | 8h | P2 |
| 10 | Agent 记忆快照 | 依赖 #9 | 4h | P3 |
| 11 | 25 个 CLI 子命令 | 从 `main.py` 逐步扩展 | 40h+ | P2 |
| 12 | Hook 系统集成 | 将 `hooks/` 模块接入 QueryEngine | 8h | P2 |
| 13 | Daemon 模式 | TS 版功能，Python 暂不实现 | — | P3 |
| 14 | Compaction | `engine/compact.py` 集成到 QueryEngine | 4h | P2 |

---

## 讨论要点

请对以下决策点讨论：

1. **P0-03 方案选择**: 方案 A（移动实现到 `registry.py`）vs 方案 B（修改 4 处导入路径）？我倾向 A。

2. **P0-04 方案选择**: 方案 A（移除 `frozen=True`）vs 方案 B（`object.__setattr__` 绕过）？我倾向 A，因为 `message_count` 和 `last_active` 本就是可变状态。

3. **P1-06 统一 Agent 定义**: 应该以 `agents/builtin.py` 的字段名（`name`/`system_prompt`/`capabilities`）为准，还是以 `tools/agent/__init__.py` 的字段名（`agent_type`/`prompt`）为准？我倾向 `agent_type`/`prompt`，因为与 TS 版一致。

4. **P1-10 OpenAI 兼容层**: 先做降级错误（方案 A），还是直接实现 OpenAI 适配器（方案 B）？

5. **P2-11 死代码处理**: 直接删除还是先加 deprecation warning？

6. **修复顺序**: P0 修复后再做 P1，还是交叉进行？我建议 P0 全部修完后再动 P1。

7. **AGENT.MD 在 P1-06 中的角色**: 之前写的 AGENT.MD 中的代码示例是否需要随着 P1-06 的修复同步更新？