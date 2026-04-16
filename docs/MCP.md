# Claude Code Python - MCP 服务器完整指南

> 本文档面向零基础用户，详细说明 MCP 是什么、如何使用 Claude Code Python 的 MCP 服务器。

---

## 第一部分：概念科普

### 1.1 什么是 MCP？

**MCP = Model Context Protocol（模型上下文协议）**

你可以理解为：**AI 世界的 USB 接口**。

就像 USB 让电脑可以连接鼠标、键盘、打印机等各种外设，MCP 让 AI 应用可以连接各种"能力"：

```
传统 USB 外设:
电脑 ←USB→ 鼠标、键盘、打印机

MCP 连接的"能力":
AI 应用 ←MCP→ 文件系统、浏览器、代码分析工具、数据库...
```

MCP 是一个**标准协议**，让不同的 AI 工具可以互相通信。目前主流 AI 编辑器（Cursor、Cline、Zed 等）都支持 MCP。

### 1.2 MCP 客户端 vs MCP 服务器

| 角色 | 说明 | 示例 |
|------|------|------|
| **MCP 客户端** | 发起请求的一方，需要使用"能力" | Cursor、Cline、Zed、其他 AI 应用 |
| **MCP 服务器** | 提供能力的一方，拥有各种工具 | 你的 Claude Code Python |

**工作流程**：
```
┌──────────────┐         MCP 协议         ┌──────────────┐
│  MCP 客户端  │ ←──────────────────────→ │ MCP 服务器  │
│              │   "请帮我读取 file.txt"   │              │
│   Cursor     │ ←──────────────────────→ │  CC-Python   │
│   Cline      │   "这是文件内容..."       │  (你的)      │
└──────────────┘                           └──────────────┘
```

---

## 第二部分：Claude Code Python 的 68 个工具

Claude Code Python 内置了 **68 个工具**，通过 MCP 服务器可以暴露给外部使用。

### 2.1 工具分类一览

| 类别 | 数量 | 功能描述 |
|------|------|----------|
| **Builtin** | 7 | 核心文件操作：读、写、编辑、搜索、执行命令 |
| **Utility** | 10 | 实用功能：网络搜索、网页抓取、任务管理、消息发送 |
| **Workflow** | 9 | 工作流：任务管理、计划模式、代码验证 |
| **System** | 4 | 系统操作：PowerShell、监控、配置 |
| **MCP** | 6 | 连接其他 MCP 服务器 |
| **Skills** | 3 | 技能系统：调用预定义工作流 |
| **Control** | 3 | 后台任务控制：停止、查看输出 |
| **Analysis** | 2 | 代码分析：LSP、代码分析 |
| **Browser** | 2 | 浏览器自动化（需要 playwright） |
| **Team** | 4 | 团队协作：创建团队、添加成员 |
| **Cron** | 4 | 定时任务：创建、列表、删除 |
| **Worktree** | 3 | Git 工作树：创建、退出、列表 |
| **Terminal** | 1 | 终端录制 |
| **Search** | 2 | 搜索：工具搜索、远程触发 |
| **Agent** | 1 | 子 Agent：派发任务给其他 AI |
| **Internal** | 6 | 内部功能（实验性） |

### 2.2 详细工具清单

#### 核心文件操作 (Builtin) - 最常用
| 工具名 | 功能说明 |
|--------|----------|
| `read` | 读取文件内容 |
| `write` | 创建新文件或覆盖已有文件 |
| `edit` | 精确修改文件中特定字符串 |
| `glob` | 按通配符（如 `*.py`）查找文件 |
| `grep` | 在文件中搜索正则表达式 |
| `bash` | 执行 Shell/Linux 命令 |
| `notebook_edit` | 编辑 Jupyter 笔记本 (.ipynb) |

#### 实用工具 (Utility)
| 工具名 | 功能说明 |
|--------|----------|
| `web_search` | 联网搜索信息 |
| `web_fetch` | 获取任意网页内容 |
| `todo_write` | 创建/更新任务清单 |
| `send_message` | 发送消息给用户 |
| `snip` | 创建代码片段供分享 |
| `brief` | 对内容生成简要总结 |
| `send_user_file` | 让用户下载文件 |
| `suggest_background_pr` | 建议创建后台 PR |
| `overflow_test` | 溢出条件测试工具 |
| `synthetic_output` | 生成测试用输出 |

#### 工作流 (Workflow)
| 工具名 | 功能说明 |
|--------|----------|
| `task_create` | 创建新任务 |
| `task_get` | 获取任务详情 |
| `task_update` | 更新任务状态 |
| `task_list` | 列出所有任务 |
| `verify` | 验证代码修改/运行测试 |
| `enter_plan_mode` | 进入计划模式（审批工具调用） |
| `exit_plan_mode` | 退出计划模式 |
| `workflow` | 执行预定义工作流 |
| `repl` | 在 REPL 环境执行代码 |

#### 系统操作 (System)
| 工具名 | 功能说明 |
|--------|----------|
| `powershell` | 执行 PowerShell 命令（Windows） |
| `monitor` | 监控 CPU、内存、磁盘 |
| `config` | 读取/写入配置 |
| `sleep` | 暂停执行（秒） |

#### 其他类别
- **MCP 工具** (6个): 连接其他 MCP 服务器
- **Skills 工具** (3个): 调用预定义技能
- **Team 工具** (4个): 团队协作
- **Cron 工具** (4个): 定时任务
- **Worktree 工具** (3个): Git 工作树
- **Browser 工具** (2个): 浏览器自动化
- **Analysis 工具** (2个): 代码分析、LSP
- **Agent 工具** (1个): 派发子任务

---

## 第三部分：使用指南

### 3.1 准备工作

#### 步骤 1：确认 Python 环境

你需要确认已安装 Python 3.11 或更高版本：

```bash
# 在终端中运行（Windows PowerShell 或 CMD）
python --version
```

如果显示 `Python 3.11.x` 或更高版本，继续下一步。

#### 步骤 2：确认 Claude Code Python 已安装依赖

```bash
# 进入项目目录
cd D:\Download\gaming\new_program\claude-code-python

# 安装必要依赖
pip install anthropic aiohttp pydantic
```

#### 步骤 3：验证 MCP 服务器可以启动

```bash
# 运行以下命令，应该看到帮助信息
python -m claude_code.main --help
```

确认输出包含 `--mcp-serve` 选项。

### 3.2 启动 MCP 服务器

#### 基本启动（STDIO 模式）

```bash
# 进入项目目录
cd D:\Download\gaming\new_program\claude-code-python

# 启动 MCP 服务器
python -m claude_code.main --mcp-serve
```

**注意**：启动后终端会等待输入，不要关闭这个窗口！

#### 自定义服务器名称

```bash
python -m claude_code.main --mcp-serve --mcp-name "my-cc-server"
```

### 3.3 配置外部客户端

#### 场景 A：配置 Cursor

1. 打开 Cursor
2. 按 `Cmd + ,` (Mac) 或 `Ctrl + ,` (Windows) 打开设置
3. 搜索 "MCP" 或找到 "MCP Servers" 设置
4. 点击 "Edit JSON"
5. 添加以下配置：

```json
{
  "mcpServers": {
    "claude-code-python": {
      "command": "python",
      "args": ["-m", "claude_code.main", "--mcp-serve"],
      "env": {
        "PYTHONPATH": "D:/Download/gaming/new_program/claude-code-python"
      }
    }
  }
}
```

6. 保存并重启 Cursor

#### 场景 B：配置 Cline

1. 打开 Cline 设置
2. 找到 "MCP Servers" 部分
3. 点击 "Add MCP Server"
4. 填写：
   - **Name**: `claude-code-python`
   - **Command**: `python`
   - **Arguments**: `["-m", "claude_code.main", "--mcp-serve"]`
   - **Environment Variables**: 添加 `PYTHONPATH=D:/Download/gaming/new_program/claude-code-python`

#### 场景 C：配置 Zed

1. 打开 Zed 设置
2. 找到 "MCP" 部分
3. 编辑 `~/.config/zed/settings.json`（或通过 UI 添加）
4. 添加同样的配置

#### 场景 D：配置其他应用

任何支持 MCP 的应用都可以使用，配置格式相同：

```json
{
  "command": "python",
  "args": ["-m", "claude_code.main", "--mcp-serve"],
  "env": {
    "PYTHONPATH": "/完整/路径/到/claude-code-python"
  }
}
```

### 3.4 验证配置成功

配置完成后，IDE 通常会显示已连接的 MCP 服务器。你可以通过以下方式验证：

1. 在 IDE 中询问："列出所有可用工具"
2. 应该能看到包括 `read`、`write`、`bash` 等在内的 68 个工具
3. 尝试使用工具，例如："请读取当前目录下的 README.md 文件"

---

## 第四部分：技术原理

### 4.1 STDIO 模式工作原理

```
┌─────────────────────────────────────────────────────────────┐
│                     你的电脑                                  │
│                                                             │
│  ┌─────────────────┐      stdin/stdout      ┌───────────┐  │
│  │   IDE (客户端)  │ ←───────────────────→ │  Python   │  │
│  │                 │    JSON-RPC 消息        │  脚本     │  │
│  │   Cursor        │ ←──────────────────→ │           │  │
│  │   Cline         │    "tools/list"       │  MCP      │  │
│  │   Zed           │ ←──────────────────→ │  Server   │  │
│  │                 │    返回 68 个工具       │           │  │
│  └─────────────────┘                         └───────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

1. IDE 启动你的 Python 脚本作为子进程
2. IDE 通过 `stdin` 发送 JSON-RPC 格式的请求
3. Python 脚本处理请求，通过 `stdout` 返回 JSON-RPC 响应
4. IDE 解析响应，展示给用户

**优点**：简单、安全（本地通信）、无需网络配置

### 4.2 MCP 协议核心方法

| 方法 | 功能 |
|------|------|
| `initialize` | 客户端告诉服务器自己的信息，服务器返回自己的能力 |
| `tools/list` | 列出所有可用工具 |
| `tools/call` | 调用某个工具 |
| `resources/list` | 列出可用资源 |
| `resources/read` | 读取资源内容 |
| `prompts/list` | 列出可用提示模板 |
| `prompts/get` | 获取提示模板 |

---

## 第五部分：扩展与进阶

### 5.1 添加更多工具

未来你可能会添加：
- 时间序列分析工具
- 语音处理工具
- 图像处理工具

**无需修改配置**：重启 MCP 服务器后，新工具会自动暴露。

### 5.2 HTTP 模式（未来功能）

如果需要让**其他电脑**访问你的 MCP 服务器，可以启用 HTTP 模式：

```bash
# 未来可能的命令
python -m claude_code.main --mcp-serve --mcp-mode http --mcp-port 8080
```

然后外网可以通过 `http://你的IP:8080/mcp` 访问。

### 5.3 连接到其他 MCP 服务器

Claude Code Python 也可以**作为客户端**连接其他 MCP 服务器：

1. 创建 `mcp.json` 文件
2. 配置外部 MCP 服务器
3. 通过 `mcp` 工具调用外部服务器的工具

---

## 第六部分：常见问题

### Q1: MCP 服务器启动后没有响应？

确保：
1. 保持终端窗口打开
2. 不要在启动命令后再输入其他内容
3. IDE 重启后重新连接

### Q2: 工具调用失败？

1. 检查工具名称是否正确
2. 检查参数格式是否匹配 input_schema
3. 查看 MCP 服务器终端的错误信息

### Q3: 如何停止 MCP 服务器？

在运行服务器的终端窗口按 `Ctrl + C` 即可停止。

### Q4: 68 个工具全部可用吗？

大部分工具可用，个别工具（如 `browser`）需要额外依赖才能使用。

### Q5: 可以修改工具的描述或参数吗？

可以，修改对应工具类后重启服务器即可生效。

---

## 第七部分：快速参考

### 启动命令

```bash
# 基本启动
python -m claude_code.main --mcp-serve

# 自定义名称
python -m claude_code.main --mcp-serve --mcp-name "my-server"
```

### 快速验证

```bash
# 1. 启动服务器（保持窗口打开）
python -m claude_code.main --mcp-serve

# 2. 在另一个终端测试（需要支持 MCP 的工具）
# 或在 IDE 中询问 AI
```

### 配置文件模板

```json
{
  "mcpServers": {
    "claude-code-python": {
      "command": "python",
      "args": ["-m", "claude_code.main", "--mcp-serve"],
      "env": {
        "PYTHONPATH": "D:/Download/gaming/new_program/claude-code-python"
      }
    }
  }
}
```

---

## 附录：工具分类速查表

| 类别 | 工具数量 | 典型工具 |
|------|----------|----------|
| BUILTIN | 7 | read, write, edit, bash, glob, grep, notebook_edit |
| UTILITY | 10 | web_search, web_fetch, todo_write, send_message |
| WORKFLOW | 9 | task_create, verify, enter_plan_mode, repl |
| SYSTEM | 4 | powershell, monitor, config, sleep |
| MCP | 6 | mcp, list_mcp_tools, list_mcp_resources |
| SKILLS | 3 | skill, list_skills, discover_skills |
| TEAM | 4 | team_create, team_add_member, team_list |
| CRON | 4 | cron_create, cron_list, schedule_cron |
| WORKTREE | 3 | enter_worktree, exit_worktree, list_worktrees |
| ANALYSIS | 2 | lsp, analyze |
| BROWSER | 2 | browser, web_browser |
| CONTROL | 3 | task_list, task_stop, task_output |
| AGENT | 1 | agent |
| INTERNAL | 6 | push_notification, ctx_inspect |

---

**文档版本**: 1.0  
**更新时间**: 2026-04-09  
**适用版本**: Claude Code Python v1.0.0+