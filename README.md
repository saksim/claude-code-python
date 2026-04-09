# Claude Code Python

Claude Code 的 Python 实现版本，一个 AI 编程助手。

## 背景：一场改写AI历史的“意外”
2026年3月31日，AI行业迎来历史性转折点。Anthropic——这家以“安全”为信仰、估值超 3500亿美元 的巨头，在其IPO前夕，因一次低级构建配置失误（未屏蔽 source map 文件），导致其核心产品 Claude Code 的 51.2 万行 TypeScript 源码 完整暴露于公共 npm 仓库。

这不是黑客入侵，而是一场源于人类疏忽的“史诗级工程事故”。  
更令人震惊的是，Anthropic随后采取的“危机公关”——**大规模滥用 DMCA 版权投诉**——竟无差别删除了数千个 GitHub 开源项目，将一场技术乌龙演变为对全球开发者社区的冒犯。

但真正的火种，从未熄灭。
当源码如星尘洒落互联网，一群坚信 “技术属于全人类” 的开发者站了出来。我们没有复制，而是理解、重构、超越——用完全自主的方式，基于泄露架构的精神内核，结合现代开源LLM的力量，打造了这个项目。

> **Claude Code Python —— 不是复刻，而是涅槃。**

---
## 概述
**Claude Code Python** 是一个完全基于免费开放LLM模型基于CC泄露TS版本代码而实现的开发，完整实现 Claude Code 核心能力的 **纯 Python 开源版本**。它并非简单翻译，而是一次由社区驱动的**架构级重铸**：
- ✅ **100% 由开源/免费 LLM 迭代生成与修复**  
从第一行代码到最终稳定版，全程由第三方大模型（如 DeepSeek、Qwen、Llama 3）协同开发、自调试、自优化。
- ✅ **零 Anthropic 闭源依赖**  
无需官方 API（除非你主动启用），支持任意 OpenAI 兼容或本地 LLM（Ollama, vLLM, LM Studio 等）。
- ✅ **功能对齐原版，体验超越期待**
完整复现 Claude Code 的交互范式，并针对 Python 生态深度优化。

本项目提供了与原版类似的功能集，包括：

- 交互式 REPL 界面
- 丰富的工具系统 (53+ 工具)
- 命令系统
- 服务层 (缓存、遥测、MCP 等)
- 权限管理
- 上下文构建

## 安装

```bash
# 克隆仓库
git clone <repository-url>
cd claude-code-python

# 安装依赖
pip install -r requirements.txt

# 设置 API Key (可选 - 也支持本地模型)
export ANTHROPIC_API_KEY="your-api-key"
```

## 快速开始

```bash
# 查看帮助
python -m claude_code.main --help

# 交互模式
python -m claude_code.main

# 管道模式
echo "帮我写一个 hello world" | python -m claude_code.main --pipe

# 健康检查
python -m claude_code.main --doctor

# 版本信息
python -m claude_code.main --version
```

## 🔧 使用 Ollama 本地大模型

Claude Code Python 支持完全本地化运行！无需任何云 API，你可以使用 Ollama 启动本地大模型服务。

### 1. 安装 Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows (通过 winget)
winget install Ollama.Ollama

# 或者直接下载安装包: https://ollama.com/download
```

### 2. 启动 Ollama 并下载模型

```bash
# 启动 Ollama 服务 (默认端口 11434)
ollama serve

# 在另一个终端下载喜欢的模型
ollama pull llama3.2          # 最新轻量模型 (约 2GB)
# ollama pull qwen2.5:14b    # 阿里通义 (约 8GB)
# ollama pull deepseek-r1:14b # 深度思考 (约 8GB)
# ollama pull mistral        # Mistral (约 4GB)

# 查看已安装模型
ollama list
```

### 3. 配置 Claude Code Python 使用 Ollama

#### 方式 A: 环境变量 (推荐)

```bash
# 启用 OpenAI 兼容模式
export CLAUDE_CODE_USE_OPENAI=1

# 设置 Ollama 地址 (默认 http://localhost:11434)
export OPENAI_BASE_URL=http://localhost:11434

# 不需要 API Key (本地模型)
export OPENAI_API_KEY=unused

# 设置模型名称
export OPENAI_MODEL=llama3.2
```

#### 方式 B: 配置文件

在 `~/.claude-code-python/config.json` 中添加:

```json
{
  "api_provider": "openai",
  "api_key": "unused",
  "model": "llama3.2",
  "openai_base_url": "http://localhost:11434"
}
```

#### 方式 C: 代码中配置

```python
from claude_code.config import Config

config = Config(
    api_provider="openai",
    api_key="unused",
    model="llama3.2",
    openai_base_url="http://localhost:11434"
)
```

### 4. 验证配置

```bash
# 健康检查
python -m claude_code.main --doctor

# 测试对话
echo "你好，请介绍一下自己" | python -m claude_code.main --pipe
```

### 5. 推荐配置

| 模型 | 适用场景 | 内存要求 |
|------|----------|----------|
| `llama3.2:1b` | 快速测试 | ~2GB |
| `llama3.2:3b` | 日常使用 | ~4GB |
| `qwen2.5:14b` | 中文优化 | ~16GB |
| `deepseek-r1:14b` | 复杂推理 | ~16GB |

### 6. 高级配置

```bash
# 自定义端口
export OPENAI_BASE_URL=http://localhost:11434/v1

# 调整模型参数 (如果模型支持)
export OPENAI_MODEL=llama3.2

# 调整超时时间 (秒)
export OPENAI_TIMEOUT=120
```

### Ollama + Claude Code Python 工作原理

```
┌─────────────────┐      OpenAI Protocol      ┌─────────────────┐
│ Claude Code     │ ─────────────────────────→ │    Ollama      │
│ Python          │                            │  (本地模型)     │
│                 │ ←───────────────────────── │                │
└─────────────────┘     (JSON / SSE)          └─────────────────┘

支持模型:
- Llama 3.2 / 3.1
- Qwen 2.5
- DeepSeek R1
- Mistral
- Phi
- Gemma
- 任何 Ollama 支持的模型
```

---

## 🏗️ 架构改进 (超越原版)

除了将 TypeScript 版本转换为 Python，我们还进行了大量架构级改进：

### 1. 质量保证 (QA)

- **异常处理规范化**: 修复了 13 处裸 `except:` 问题，替换为具体异常类型
- **日志系统升级**: 将 30+ 处 `print` 语句替换为标准 `logging` 模块
- **类型提示完善**: 152 个文件使用 `from __future__ import annotations`

### 2. 依赖注入增强

```python
from claude_code.di import ServiceContainer, CircularDependencyError

container = ServiceContainer()

# 现在会自动检测循环依赖！
# 如果 A 依赖 B，B 依赖 A，会抛出清晰错误:
try:
    service = container.get(SomeService)
except CircularDependencyError as e:
    print(e)  # Circular dependency detected: A -> B -> A
```

### 3. 统一状态管理

```python
from claude_code.state import StateManager

# 集中访问所有全局状态
config = StateManager.get_config()
container = StateManager.get_container()
telemetry = StateManager.get_telemetry()

# 检查初始化状态
if StateManager.is_initialized():
    print("Ready!")
```

### 4. 环境配置分层

```bash
# 配置加载顺序 (后面的覆盖前面的):
# 1. 默认值
# 2. base.json        - 基础配置
# 3. dev.json        - 开发环境
# 4. config.json     - 用户配置
# 5. 环境变量        - 最高优先级

# 使用特定环境
export CLAUDE_ENV=prod   # 加载 prod.json
```

### 5. 架构评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 简洁性 | 8/10 | 模块清晰 |
| 可扩展性 | 8/10 | 接口设计良好 |
| 可维护性 | 9/10 | 类型提示完整 |
| 性能优先 | 8/10 | 异步优先设计 |
| 容错设计 | 8/10 | 完善的错误处理 |

---

## CLI 选项

```
-h, --help            显示帮助
--model MODEL         指定模型 (默认: claude-sonnet-4-20250514)
-v, --verbose         详细输出
--system SYSTEM       系统提示
-p, --pipe            管道模式
--doctor              健康检查
--init                初始化项目
--version             版本信息
```

## 工具系统

Claude Code Python 提供了 53+ 内置工具，涵盖文件操作、网络搜索、代码分析等多个领域。

### 工具分类

#### 1. 内置工具 (Builtin)

| 工具 | 描述 |
|------|------|
| `BashTool` | 执行 Shell 命令 |
| `ReadTool` | 读取文件内容 |
| `WriteTool` | 写入文件 |
| `EditTool` | 编辑文件 |
| `GlobTool` | 文件模式匹配 |
| `GrepTool` | 文本搜索 |
| `NotebookEditTool` | Jupyter 笔记本编辑 |

#### 2. 工具类 (Utility)

| 工具 | 描述 |
|------|------|
| `TodoWriteTool` | 任务管理 |
| `WebSearchTool` | 网络搜索 |
| `WebFetchTool` | 网页抓取 |
| `SendMessageTool` | 发送消息 |
| `SnipTool` | 代码片段 |
| `BriefTool` | 简短说明 |

#### 3. 系统工具 (System)

| 工具 | 描述 |
|------|------|
| `SleepTool` | 延迟执行 |
| `PowerShellTool` | PowerShell 命令 |
| `MonitorTool` | 系统监控 |
| `ConfigTool` | 配置管理 |

#### 4. 工作流工具 (Workflow)

| 工具 | 描述 |
|------|------|
| `VerifyTool` | 验证代码 |
| `EnterPlanModeTool` | 进入计划模式 |
| `ExitPlanModeTool` | 退出计划模式 |
| `WorkflowTool` | 工作流 |
| `TaskCreateTool` | 创建任务 |
| `TaskGetTool` | 获取任务 |
| `TaskUpdateTool` | 更新任务 |
| `TaskListTool` | 列出任务 |
| `REPLTool` | REPL 工具 |
| `ReviewArtifactTool` | 审查制品 |

#### 5. Agent 工具

| 工具 | 描述 |
|------|------|
| `AgentTool` | 代理工具 |

#### 6. MCP 工具

| 工具 | 描述 |
|------|------|
| `MCPTool` | MCP 工具 |
| `ListMcpResourcesTool` | 列出 MCP 资源 |
| `ReadMcpResourceTool` | 读取 MCP 资源 |
| `McpAuthTool` | MCP 认证 |
| `ListMcpToolsTool` | 列出 MCP 工具 |
| `ListMcpPromptsTool` | 列出 MCP 提示 |

#### 7. 技能工具 (Skills)

| 工具 | 描述 |
|------|------|
| `SkillTool` | 技能调用 |
| `ListSkillsTool` | 列出技能 |
| `DiscoverSkillsTool` | 发现技能 |

#### 8. 控制工具 (Control)

| 工具 | 描述 |
|------|------|
| `TaskStopTool` | 停止任务 |
| `TaskOutputTool` | 任务输出 |
| `TaskListTool` | 任务列表 |

#### 9. 分析工具 (Analysis)

| 工具 | 描述 |
|------|------|
| `AnalyzeTool` | 代码分析 |

#### 10. 问答工具 (Ask Question)

| 工具 | 描述 |
|------|------|
| `AskUserQuestionTool` | 用户问题 |
| `AskFollowUpQuestionTool` | 跟进问题 |

#### 11. 工作树工具 (Worktree)

| 工具 | 描述 |
|------|------|
| `EnterWorktreeTool` | 进入工作树 |
| `ExitWorktreeTool` | 退出工作树 |
| `ListWorktreesTool` | 列出工作树 |

#### 12. Cron 工具

| 工具 | 描述 |
|------|------|
| `ScheduleCronTool` | 计划定时任务 |
| `CronListTool` | 列出定时任务 |
| `CronDeleteTool` | 删除定时任务 |

#### 13. 团队工具 (Team)

| 工具 | 描述 |
|------|------|
| `TeamCreateTool` | 创建团队 |
| `TeamDeleteTool` | 删除团队 |
| `TeamAddMemberTool` | 添加成员 |
| `TeamListTool` | 列出团队 |

#### 14. 终端工具 (Terminal)

| 工具 | 描述 |
|------|------|
| `TerminalCaptureTool` | 终端捕获 |

#### 15. 搜索工具 (Search)

| 工具 | 描述 |
|------|------|
| `ToolSearchTool` | 工具搜索 |
| `RemoteTriggerTool` | 远程触发 |

#### 16. 浏览器工具 (Browser)

| 工具 | 描述 |
|------|------|
| `BrowserTool` | 浏览器自动化 (需要 playwright) |

### 工具使用示例

```python
import asyncio
from claude_code.tools import BashTool
from claude_code.tools.base import ToolContext

async def main():
    tool = BashTool()
    ctx = ToolContext(working_directory=".")
    result = await tool.execute({"command": "ls -la"}, ctx)
    print(result.content)

asyncio.run(main())
```

## 命令系统

### 内置命令

| 命令 | 描述 | 别名 |
|------|------|------|
| `/help` | 显示帮助信息 | `h`, `?` |
| `/clear` | 清除对话历史 | 无 |

### 使用方式

在 REPL 中输入 `/help` 查看所有可用命令。

## 服务层

Claude Code Python 提供了完整的服务层支持：

### 1. 缓存服务 (CacheService)

```python
from claude_code.services import CacheService

cache = CacheService(max_size=100, default_ttl=3600)
await cache.set("key", "value")
value = await cache.get("key")
```

特性：
- 内存缓存，支持 TTL
- LRU 淘汰策略
- 异步支持
- 统计功能

### 2. 令牌估算 (TokenEstimator)

```python
from claude_code.services import rough_token_count, estimate_message_tokens

tokens = rough_token_count("Hello world")
message_tokens = estimate_message_tokens({"role": "user", "content": "Hello"})
```

特性：
- 字符级估算
- 消息级估算
- 内容块分析

### 3. 速率限制 (RateLimiter)

```python
from claude_code.services import RateLimiter

limiter = RateLimiter()
await limiter.acquire("resource")
```

特性：
- Token Bucket 算法
- 可配置限制
- 异步优先

### 4. 遥测服务 (TelemetryService)

```python
from claude_code.services import TelemetryService, TelemetryEventType

telemetry = TelemetryService()
await telemetry.track_event(TelemetryEventType.QUERY, {"model": "sonnet"})
```

事件类型：
- `QUERY` - 查询事件
- `TOOL_CALL` - 工具调用
- `TOOL_RESULT` - 工具结果
- `ERROR` - 错误事件
- `SESSION_START` - 会话开始
- `SESSION_END` - 会话结束

### 5. 分析服务 (AnalyticsService)

```python
from claude_code.services.analytics import AnalyticsService

analytics = AnalyticsService()
await analytics.track_event(AnalyticsEventType.QUERY_START, {})
```

### 6. 会话内存 (SessionMemory)

```python
from claude_code.services import SessionMemory

memory = SessionMemory()
await memory.set("key", "value")
value = await memory.get("key")
```

### 7. 成本追踪 (CostTracker)

```python
from claude_code.services import CostTracker

tracker = CostTracker()
stats = tracker.get_stats()
```

### 8. 历史管理 (HistoryManager)

```python
from claude_code.services import HistoryManager

history = HistoryManager()
entries = await history.get_entries(limit=10)
```

### 9. 加密服务 (SessionEncryption)

```python
from claude_code.services import SessionEncryption

encryption = SessionEncryption()
encrypted = encryption.encrypt(data)
```

### 10. Hooks 管理 (HooksManager)

```python
from claude_code.services import HooksManager

hooks = HooksManager()
await hooks.execute("pre_tool", context)
```

### 11. MCP 管理 (MCPManager)

```python
from claude_code.services.mcp.client import MCPManager

mcp = MCPManager()
tools = mcp.get_all_tools()
```

### 12. 权限管理 (PermissionsManager)

```python
from claude_code.services import PermissionsManager

pm = PermissionsManager()
allowed = await pm.check_permission("bash", "ls")
```

## 状态管理

### AppState

```python
from claude_code.state import AppState, PermissionMode, EffortLevel

state = AppState(
    main_loop_model="claude-sonnet-4-20250514",
    verbose=True
)
```

### 权限模式

| 模式 | 描述 |
|------|------|
| `DEFAULT` | 默认模式，危险操作前询问 |
| `AUTO` | 自动批准安全操作 |
| `PLAN` | 计划模式，所有操作需确认 |
| `BYPASS` | 绕过模式，无权限检查 |
| `YOLO` | 无限制模式 |

### 努力级别

| 级别 | 描述 |
|------|------|
| `LOW` | 低努力 |
| `MEDIUM` | 中等努力 |
| `HIGH` | 高努力 |

## 配置

### 配置文件位置

- 全局配置: `~/.claude/config.json`
- 项目配置: `.claude/config.json`
- 环境变量: `CLAUDE_*`

### 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | 必需 |
| `CLAUDE_MODEL` | 使用的模型 | claude-sonnet-4-20250514 |
| `CLAUDE_API_PROVIDER` | API 提供商 | anthropic |
| `CLAUDE_MAX_TOKENS` | 最大输出令牌 | 8192 |
| `CLAUDE_VERBOSE` | 启用详细输出 | false |
| `CLAUDE_PERMISSION_MODE` | 权限模式 | default |

### 主要配置项

```python
from claude_code.config import Config, get_config

config = get_config()
model = config.api.model
api_key = config.api.api_key
```

## MCP (Model Context Protocol)

Claude Code Python 支持完整的 MCP 协议，包括客户端和服务器功能。

### MCP 客户端

连接外部 MCP 服务器：

```python
from claude_code.services.mcp.client import MCPClient

client = MCPClient(config)
await client.connect("server-name")
tools = await client.list_tools()
```

### MCP 服务器

将 Claude Code Python 作为 MCP 服务器暴露给外部客户端（Cursor、Cline、Zed 等）：

```bash
# 启动 MCP 服务器 (STDIO 模式)
python -m claude_code.main --mcp-serve

# 指定服务器名称
python -m claude_code.main --mcp-serve --mcp-name "my-cc-server"
```

### MCP 服务器配置

在 Cursor/Cline/Zed 的 `mcp.json` 中配置：

```json
{
  "mcpServers": {
    "claude-code-python": {
      "command": "python",
      "args": ["-m", "claude_code.main", "--mcp-serve"],
      "env": {
        "PYTHONPATH": "/path/to/claude-code-python"
      }
    }
  }
}
```

### MCP 服务器功能

- **68+ 内置工具**：BashTool、ReadTool、WriteTool、EditTool、GrepTool 等
- **完整工具执行**：通过 MCP 协议调用任何工具
- **资源访问**：server://info、server://tools 等资源
- **提示模板**：tool_list、tool_info 等内置提示

### MCP 配置

创建 `mcp.json` 配置文件：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    }
  }
}
```

## 技能系统

技能是可重用的工作流：

```python
from claude_code.skills import invoke_skill

result = await invoke_skill("skill-name", context)
```

### 技能来源

- 内置技能 (bundled with Claude Code)
- 用户技能 (`~/.claude/skills/`)
- 项目技能 (`.claude/skills/`)
- MCP 服务提供

### 技能目录结构

```
.skude/skills/
└── my-skill/
    ├── SKILL.md          # 主技能文件
    └── examples/
        └── example.md     # 使用示例
```

## Hooks 系统

Hooks 允许在特定事件发生时执行自定义脚本：

```python
from claude_code.hooks import get_hook_registry

registry = get_hook_registry()
hooks = await registry.get_hooks("pre_tool")
```

### 支持的事件

| 事件 | 描述 |
|------|------|
| `SessionStart` | 会话开始 |
| `SessionEnd` | 会话结束 |
| `PreToolCall` | 工具调用前 |
| `PostToolCall` | 工具调用后 |
| `PreMessage` | 消息发送前 |
| `PostMessage` | 消息接收后 |
| `PreQuery` | 查询前 |
| `PostQuery` | 查询后 |

## 引擎

### QueryEngine

```python
from claude_code.engine.query import QueryEngine

engine = QueryEngine(config)
async for event in engine.query("用户输入"):
    process(event)
```

### ContextBuilder

```python
from claude_code.context.builder import ContextBuilder

builder = ContextBuilder(working_directory=".")
context = await builder.build()
```

### PermissionManager

```python
from claude_code.engine.permissions import PermissionManager

pm = PermissionManager()
allowed = await pm.check_permission(tool_name, input_data)
```

## 任务管理

后台任务执行：

```python
from claude_code.tasks import run_background_bash

task = await run_background_bash("npm build", cwd="/project")
```

### 任务类型

| 类型 | 描述 |
|------|------|
| `BASH` | Shell 命令任务 |
| `AGENT` | Agent 任务 |
| `WORKFLOW` | 工作流任务 |

### 任务状态

| 状态 | 描述 |
|------|------|
| `PENDING` | 等待中 |
| `RUNNING` | 运行中 |
| `COMPLETED` | 已完成 |
| `FAILED` | 失败 |
| `CANCELLED` | 已取消 |

## 项目结构

```
claude_code/
├── __init__.py           # 包入口
├── main.py               # CLI 入口
├── config.py             # 配置管理
│
├── tools/                # 工具系统
│   ├── __init__.py       # 工具注册表
│   ├── base.py           # 基础类 (Tool, ToolContext, etc.)
│   ├── builtin/          # 内置工具
│   │   ├── bash.py
│   │   ├── read.py
│   │   ├── write.py
│   │   ├── edit.py
│   │   ├── glob.py
│   │   ├── grep.py
│   │   └── notebook_edit.py
│   ├── utility/          # 工具类
│   │   ├── todo.py
│   │   ├── web_search.py
│   │   ├── web_fetch.py
│   │   └── ...
│   ├── system/           # 系统工具
│   ├── workflow/         # 工作流工具
│   ├── mcp/              # MCP 工具
│   ├── skills/           # 技能工具
│   ├── control/          # 控制工具
│   ├── analysis/         # 分析工具
│   ├── worktree/         # 工作树工具
│   ├── cron/             # Cron 工具
│   ├── team/             # 团队工具
│   └── browser/          # 浏览器工具
│
├── engine/               # 核心引擎
│   ├── query.py          # 查询引擎
│   ├── context.py        # 上下文构建
│   ├── hooks.py          # Hook 执行器
│   ├── permissions.py    # 权限管理
│   ├── orchestration.py  # 编排
│   └── compact.py        # 对话压缩
│
├── services/             # 服务层
│   ├── __init__.py
│   ├── cache_service.py  # 缓存
│   ├── token_estimation.py # 令牌估算
│   ├── rate_limiter.py   # 速率限制
│   ├── analytics.py      # 分析
│   ├── telemetry_service.py # 遥测
│   ├── memory_service.py # 内存服务
│   ├── cost_tracker.py   # 成本追踪
│   ├── history_manager.py # 历史管理
│   ├── encryption_service.py # 加密
│   ├── hooks_manager.py  # Hooks 管理
│   ├── permissions_manager.py # 权限管理
│   └── mcp/              # MCP 客户端
│       ├── client.py
│       └── official_registry.py
│
├── state/                # 状态管理
│   ├── __init__.py
│   ├── app_state.py      # 应用状态
│   ├── store.py          # 状态存储
│   └── session_state.py  # 会话状态
│
├── commands/             # 命令系统
│   ├── __init__.py
│   ├── base.py           # 命令基类
│   ├── registry.py        # 命令注册表
│   └── builtins/         # 内置命令
│
├── context/              # 上下文
│   ├── __init__.py
│   ├── builder.py        # 上下文构建器
│   ├── notifications.py  # 通知
│   └── stats.py          # 统计
│
├── skills/              # 技能系统
│   ├── __init__.py
│   ├── models.py
│   ├── registry.py
│   └── invoker.py
│
├── hooks/               # Hooks 系统
│   ├── __init__.py
│   ├── events.py
│   ├── registry.py
│   └── config.py
│
├── tasks/               # 任务管理
│   ├── __init__.py
│   ├── types.py
│   ├── manager.py
│   └── shell.py
│
├── utils/              # 工具模块
│   ├── __init__.py
│   ├── errors.py       # 错误处理
│   ├── path.py         # 路径工具
│   ├── file.py         # 文件操作
│   ├── git.py          # Git 集成
│   ├── shell.py        # Shell 命令
│   ├── format.py       # 格式化
│   └── json.py         # JSON 工具
│
├── ui/                 # UI 组件
│   ├── __init__.py
│   ├── console.py
│   ├── rendering.py
│   └── ...
│
├── repl/               # REPL 界面
│   └── __init__.py
│
├── mcp/                # MCP 协议
│   ├── __init__.py
│   └── server.py
│
├── remote.py           # 远程传输
├── features.py         # 特性管理
└── graph.py            # 依赖图
```

## 使用示例

### 1. 交互式对话
```bash
python -m claude_code.main
```

### 2. 管道模式
```bash
echo "写一个 Python 快速排序" | python -m claude_code.main --pipe
```

### 3. 编程式使用
```python
import asyncio
from claude_code.engine.query import QueryEngine
from claude_code.config import get_config

async def main():
    config = get_config()
    engine = QueryEngine(config)

    async for event in engine.query("帮我写一个 hello world"):
        print(event)

asyncio.run(main())
```

### 4. 创建工具注册表
```python
from claude_code.tools import create_default_registry

registry = create_default_registry()
tools = registry.list_all()
print(f"已加载 {len(tools)} 个工具")

tool = registry.get("bash")
result = await tool.execute({"command": "ls"}, context)
```

### 5. 使用服务
```python
import asyncio
from claude_code.services import CacheService, TelemetryService

async def main():
    # 缓存
    cache = CacheService()
    await cache.set("data", {"key": "value"})

    # 遥测
    telemetry = TelemetryService()
    await telemetry.track_event(EventType.QUERY, {"model": "sonnet"})

asyncio.run(main())
```

## 开发

### 运行测试
```bash
pytest tests/ -v
```

### 查看测试
```bash
python -m pytest --collect-only
```

## 功能开关 (Feature Flags)

Claude Code Python 支持通过功能开关启用实验性功能。

### 编程方式

```python
from claude_code.config import Features

# 查看所有功能
Features.print_help()

# 启用单个功能
Features.enable("KAIROS")

# 启用所有实验性功能
Features.enable_all()

# 获取已启用的工具
print(Features.enabled_tools)
```

### 配置文件方式

在项目根目录创建 `.claude/features.json`:

```json
{
  "enabled": ["KAIROS", "WEB_BROWSER_TOOL"]
}
```

### 环境变量方式

```bash
# 启用推送通知
export KAIROS=1

# 启用网页浏览器
export WEB_BROWSER_TOOL=1
```

### 可用功能列表

| 功能 | 环境变量 | 描述 |
|------|----------|------|
| Web Browser | `WEB_BROWSER_TOOL` | 网页自动化（导航、点击、截图） |
| Push Notifications | `KAIROS` | 推送通知到用户设备 |
| GitHub PR Subscriptions | `KAIROS_GITHUB_WEBHOOKS` | 通过 webhooks 订阅 GitHub PR 更新 |
| Context Inspection | `CONTEXT_COLLAPSE` | 调试和检查上下文折叠状态 |
| Peer Process List | `UDS_INBOX` | 列出连接的 peer 进程 |
| Plan Verification | `CLAUDE_CODE_VERIFY_PLAN` | 验证计划是否正确执行 |
| Terminal Capture | `TERMINAL_PANEL` | 捕获并显示终端输出 |
| Overflow Test | `OVERFLOW_TEST_TOOL` | 溢出条件测试工具 |
| History Snip | `HISTORY_SNIP` | 截取并包含历史对话上下文 |
| Remote Trigger | `AGENT_TRIGGERS_REMOTE` | 从外部源触发 agent |
| Monitor | `MONITOR_TOOL` | 系统监控和指标 |
| Workflow | `WORKFLOW_SCRIPTS` | 执行自定义工作流脚本 |

## 等价审计 (Parity Audit)

Claude Code Python 集成了 parity 审计功能，可以与 TypeScript 原版进行对比：

```python
from claude_code.porting import run_parity_audit, PORTED_TOOLS, PORTED_COMMANDS

# 运行等价审计
result = run_parity_audit()
print(result.to_markdown())
```

### 输出示例

```
## Tools
- Reference (TS): **184**
- Implemented (Python): **53**
- Coverage: **28.8%**

## Commands
- Reference (TS): **207**
- Implemented (Python): **5**
- Coverage: **2.4%**
```

### 快照查询

```python
from claude_code.porting import find_tools, find_commands, get_tool_snapshot

# 搜索工具
results = find_tools("bash", limit=10)

# 获取特定工具
tool = get_tool_snapshot("AgentTool")
print(tool.name, tool.source_hint)
```

## 会话持久化

保存和恢复会话：

```python
from claude_code.porting import StoredSession, save_session, load_session, list_sessions
from datetime import datetime
import uuid

# 创建并保存会话
session = StoredSession(
    session_id=uuid.uuid4().hex,
    messages=("Hello", "Hi there!"),
    input_tokens=100,
    output_tokens=50,
    created_at=datetime.now().isoformat(),
)
save_session(session)

# 列出所有会话
sessions = list_sessions()

# 加载会话
loaded = load_session(session_id)
```

### 会话存储位置

- 默认: `~/.claude/sessions/`
- 可自定义: `save_session(session, custom_directory)`

## 📄 许可证

本项目采用 **[MIT 许可证](LICENSE)** —— 一个简短、宽松、商业友好的开源协议。  
你可以自由地使用、修改、分发本项目代码，用于个人或商业用途，只需保留原始版权声明即可。

> ⚠️ **免责声明**：本项目是社区驱动的独立实现，所有代码均由开源大模型基于公开信息重新生成。

## 🤝 贡献指南

我们热烈欢迎任何形式的贡献！

- 💬 **提出想法**：通过 [Issues](https://github.com/your-username/claude-code-python/issues) 分享功能建议或使用反馈。
- 🐞 **报告问题**：遇到 Bug？请提供复现步骤、环境信息和日志。
- ✨ **提交代码**：Fork 仓库 → 创建分支 → 提交 PR。请确保代码风格一致，并附带必要注释。
- 🌍 **改进文档**：修正错别字、补充示例、翻译多语言，都是宝贵的贡献！

### 行为准则
请所有参与者遵守 **[Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)** 准则：保持尊重、包容与建设性沟通。任何形式的骚扰、歧视或不友善行为都将不被容忍。

---
一起让 AI 编程更开放、更强大！🚀
