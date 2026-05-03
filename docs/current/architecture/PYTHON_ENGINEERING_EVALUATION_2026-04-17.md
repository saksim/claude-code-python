# Claude Code Python Python 工程评估报告（2026-04-17）

- 项目：`claude-code-python`
- 评估日期：`2026-04-17`
- 评估视角：`top-python-dev` + Python 工程质量 / 可维护性 / 扩展性 / 发布完整性
- 关联基线文档：
  - `docs/current/architecture/ARCHITECTURE_EVALUATION_2026-04-16.md`
  - `docs/current/middleware/MIDDLEWARE_EVOLUTION_ASSESSMENT_2026-04-16.md`
  - `docs/current/performance/PERFORMANCE_ONE_PAGER.md`
  - `docs/current/performance/BASELINE_V1.md`

---

## 1. 执行摘要

### 1.1 总体结论

当前仓库已经具备“核心 CLI 主链路可运行、测试可回归、任务中间件开始收敛”的基础能力，但从全球顶级 Python 工程标准看，**仍然明显停留在“工程可用基线”而非“可稳定演进平台”阶段**。

更具体地说：

1. **主链路健康度不错**：语法检查通过，全量测试 `90 passed`，旧文档中已经闭环的 Query / permission / runtime 基线大体保持稳定。
2. **发布与扩展面明显落后**：`pyproject.toml` 无法解析、`setup.py` 安装元数据有硬错误、MCP 客户端主链路并未真正打通、插件本地加载器只能读元数据不能加载执行实例。
3. **配置契约与运行时契约不一致**：文档、`main.py`、`config.py`、命令层和 provider 层对“支持哪些 provider、model 如何生效、配置从哪里读取”给出了彼此冲突的答案。
4. **迭代风险仍偏高**：代码体量已经接近 `4.8 万 LOC`，存在 `133` 处宽泛异常、`34` 处占位函数、多个 `700+ LOC` 的核心文件，说明后续任何跨模块改动都需要更强的契约测试和模块收敛。

### 1.2 结论评分

- 核心 CLI 主链路：`8.2 / 10`
- Python 工程完整度：`7.1 / 10`
- 发布/扩展面成熟度：`5.8 / 10`

### 1.3 当前最值得优先处理的四条线

1. 修复**打包发布链路**，否则项目无法形成可靠分发闭环。
2. 修复**MCP / 插件扩展面**，否则“支持 MCP/插件”目前更像文档承诺而不是可用能力。
3. 收敛**配置 -> 命令 -> runtime -> provider** 的单一事实来源。
4. 收敛**应用生命周期 / 调度 / 工作目录 / 子代理执行上下文** 的行为一致性。

---

## 2. 评估范围与验证方法

### 2.1 覆盖范围

本次评估覆盖：

1. `claude_code/` 主代码目录
2. `tests/` 当前测试体系
3. `README.md`、`pyproject.toml`、`setup.py`、`requirements.txt`
4. `docs/current/` 下当前架构 / 中间件 / 性能文档

### 2.2 已执行验证

1. 语法检查：
   - 命令：`D:\code_environment\anaconda_all_css\py311\python.exe scripts/check_syntax.py --root claude_code`
   - 结果：`208` 个文件，`0` 个语法错误
2. 全量测试：
   - 命令：`D:\code_environment\anaconda_all_css\py311\python.exe -m pytest -q -c pytest.ini`
   - 结果：`90 passed, 3 warnings`
3. 补充事实验证：
   - `pyproject.toml` 用 `tomllib` 解析，结果 `TOMLDecodeError`
   - `Config(api_provider="ollama")` / `vllm` / `deepseek` 直接触发 `ValidationError`
   - `packaging.requirements.Requirement("boto3>=1.35.0  # AWS Bedrock")` 解析失败
   - `ClaudeMdLoader` 在父目录存在 `CLAUDE.md` 时，`find_claude_md_files()` 能找到文件，但 `load_content()` 返回 `None`

### 2.3 本次无法完成的检查

1. `ruff` 与 `mypy` 在给定解释器环境中不可用：
   - `No module named ruff`
   - `No module named mypy`
2. 因此本次静态质量结论主要来自：
   - 手工代码审查
   - AST/文本扫描
   - 当前测试与定点复现

---

## 3. 量化快照

基于本地 AST / 文本扫描得到的当前快照如下：

| 指标 | 数值 |
|---|---:|
| Python 文件数 | `208` |
| 代码总行数（约） | `47,864` |
| 函数 / 方法总数 | `2,237` |
| `async def` 数量 | `461` |
| 类数量 | `550` |
| 宽泛异常（`except:` / `except Exception`） | `133` |
| 占位函数（`pass` / 空壳接口） | `34` |
| 缺失返回类型标注 | `29` |
| 缺失参数类型标注 | `41` |
| 含 `Any` 的函数源码片段 | `537` |

### 3.1 复杂度热点

文件体量 Top 6：

1. `claude_code/skills/builtin.py`：`1040` 行
2. `claude_code/services/mcp/client.py`：`887` 行
3. `claude_code/ui/rendering.py`：`784` 行
4. `claude_code/tasks/manager.py`：`777` 行
5. `claude_code/engine/query.py`：`744` 行
6. `claude_code/api/client.py`：`645` 行

长函数 Top 6：

1. `claude_code/agents/builtin.py:create_builtin_agents`：`209` 行
2. `claude_code/tools/registry.py:create_default_registry`：`170` 行
3. `claude_code/engine/query.py:query`：`142` 行
4. `claude_code/main.py:main`：`140` 行
5. `claude_code/tools/builtin/bash.py:execute`：`109` 行
6. `claude_code/hooks/registry.py:_execute_hook`：`102` 行

结论：**当前仓库最主要的工程风险已经不再是“能不能跑”，而是“局部复杂度过高 + 契约边界不清 + 扩展面未收敛”。**

---

## 4. 与旧文档的关系

### 4.1 旧文档中已关闭、且本次复核仍然成立的事项

以下事项本次未发现回滚：

1. Query 主链路基础可运行。
2. 权限系统已从“多套并行语义”收敛到可工作的 canonical 路径。
3. 任务仓储/队列抽象已具备雏形，`tasks.json` 也已有 schema 兼容层。
4. 全量测试已从旧文档的 `68 passed` 增长到 `90 passed`。

### 4.2 旧文档覆盖不足、但本次发现仍然重要的方向

旧文档较少覆盖以下内容，而这些内容会直接影响后续迭代开发：

1. Python 打包/发布完整性
2. MCP 客户端是否真的可用
3. 插件本地加载器是否真的能加载代码
4. 配置系统与命令系统是否驱动真实 runtime
5. 工作目录 / 子代理上下文是否真的被正确传播

---

## 5. 关键问题清单（按严重级别）

## P0：必须优先处理，否则会直接阻断后续迭代

### P0-1：打包发布链路当前不可作为可靠分发入口

证据：

1. `pyproject.toml:1-39` 不是 TOML，而是 JSON 风格对象；本地 `tomllib` 解析直接失败。
2. `pyproject.toml:9` 与 `pyproject.toml:14` 出现重复 `rich` 依赖。
3. `setup.py:7-11` 直接把 `requirements.txt` 每行 `line.strip()` 放进 `install_requires`，而 `requirements.txt:16-18` 包含内联注释，生成的 requirement 字符串不符合 PEP 508。
4. `setup.py:39-40` 注册了 `claude_code.gui:main`，但仓库中不存在 `claude_code/gui.py`。
5. `setup.py:17`、`setup.py:21` 仍是占位元数据（`example@example.com` / `your-repo`）。

影响：

1. 无法把仓库稳定发布为可安装 Python 包。
2. 本地开发“从源码运行”与“通过包安装运行”是两条完全不同的路径。
3. 后续若接 CI 发布、wheel 构建、editable install、插件分发，会被这条链路卡死。

建议：

1. 先在单个 PR 中收敛为**唯一打包事实源**，推荐标准 TOML。
2. `requirements.txt` 不要直接喂给 `install_requires`；可拆成 runtime / optional / dev 三层。
3. 删除或补齐 `claude_code.gui` 入口，不能再保留悬空 entry point。

### P0-2：`claude_code.services.mcp.client` 主链路未真正打通

证据：

1. `claude_code/services/mcp/client.py:407-427`
   - `MCPProtocol.send_request()` 只创建 `future` 和 `message`，**没有把消息发送到任何 transport**，最后直接 `return await future`。
2. `claude_code/services/mcp/client.py:565`、`590`、`609`、`634`、`649`
   - `MCPClient` 多处调用 `self.protocol.send_request(...)`，因此这些路径理论上都会悬挂。
3. `claude_code/services/mcp/client.py:136-140`
   - `MCPStdIOTransport.send()` 对 `stdin.write()` / `stdin.flush()` 使用 `await`，但这些接口不是 awaitable；这里是明显的 asyncio API 使用错误。
4. `claude_code/services/mcp/client.py:532-536`
   - HTTP/SSE transport 仍然是 `NotImplementedError`。
5. `claude_code/services/mcp/client.py:289-292`
   - `MCPWebSocketTransport.connect()` 创建 `aiohttp.ClientSession()` 后没有持久保存 session 句柄，也没有关闭。
6. `claude_code/services/mcp/client.py:322-341`
   - `_reader_loop()` 内部直接引用 `aiohttp.WSMsgType`，但该名字不在方法作用域中，运行时会 `NameError`。

影响：

1. MCP 客户端目前更像“接口草图”，不是可依赖能力。
2. 后续若围绕 MCP 接入生态扩展，这部分会持续制造误判。

建议：

1. 把 `MCPProtocol` 与 transport 真正绑定，先打通一个可工作的 `STDIO` 路径。
2. HTTP/SSE / WebSocket 不要提前宣称支持，未打通前应显式 feature-flag 或 fail-fast。
3. 为 `MCPClient.connect -> initialize -> list tools/resources -> call tool` 补一条契约测试主链路。

### P0-3：本地插件加载器只能读元数据，无法把插件变成可执行实例

证据：

1. `claude_code/plugins/__init__.py:252-273`
   - `LocalPluginLoader.load()` 只读取 `plugin.json` 并返回 `Plugin(...)`，没有导入插件模块，也没有设置 `_instance`。
2. `claude_code/plugins/__init__.py:186-209`
   - `get_all_tools()` / `get_all_commands()` / `get_all_hooks()` 都依赖 `plugin.instance` 实现 `ToolPlugin` / `CommandPlugin` / `HookPlugin`。

结果：

1. Builtin loader 能拿到 `module.get_plugin()` 实例（`claude_code/plugins/__init__.py:234-235`）。
2. Local loader 只能返回 metadata，导致本地插件处于“登记了，但不能提供功能”的状态。

影响：

1. 插件系统对本地开发者基本不可用。
2. 文档/架构上宣称的 plugin extensibility 与真实行为不一致。

建议：

1. 为 local plugin 明确入口约定，例如 `plugin.py:get_plugin()`。
2. 给 local / builtin / marketplace 三类插件做统一 loader 抽象，不要只在 builtin 路径加载实例。

### P0-4：Cron 体系出现双文件、双 schema、双实现的分裂

证据：

1. `claude_code/tools/cron/create.py:214`、`268`
   - `CronCreateTool` 使用 `.claude/scheduled_tasks.json`。
2. `claude_code/tools/cron/__init__.py:113`、`195`、`285`
   - `ScheduleCronTool` / `CronListTool` / `CronDeleteTool` 使用 `.claude/schedules.json`。
3. `claude_code/tools/cron/create.py:171`、`232`
   - `CronCreateTool` 还区分 `durable` 与 `session-only`。
4. `claude_code/tools/cron/__init__.py:117-129`、`200-201`、`298-299`
   - 老的 cron tools 直接 `open/json.load/json.dump`，没有复用新路径的原子写/会话语义。

影响：

1. `cron_create` 创建的内容，`cron_list` / `cron_delete` 不一定能看到。
2. 对调度系统做任何迭代时，都会先踩到数据分裂问题。

测试现状：

1. 当前只有 `tests/test_tasks_middleware_runtime.py` 覆盖了 `CronCreateTool` 的 `durable` 行为。
2. 没有看到针对 `ScheduleCronTool` / `CronListTool` / `CronDeleteTool` 与 `CronCreateTool` 一致性的回归测试。

建议：

1. 只保留一套 cron 数据模型。
2. 统一文件名、schema、会话语义、原子写策略。
3. 旧路径若保留，必须降级为兼容层，不能继续并行演进。

---

## P1：高优先级问题，会持续侵蚀后续开发效率

### P1-1：配置系统、命令系统、运行时对 provider/model 的定义并不一致

证据：

1. `claude_code/config.py:40`
   - `VALID_PROVIDERS` 只允许 `anthropic/openai/bedrock/vertex/azure`。
2. `claude_code/main.py:56-69`、`77-88`
   - `main.py` 明确支持 `ollama/vllm/deepseek`。
3. `README.md:12`、`56-64`
   - README 也明确把 `ollama/vllm/deepseek` 作为当前能力对外暴露。
4. 本地复现：
   - `Config(api_provider="ollama")` / `vllm` / `deepseek` 均直接 `ValidationError`。
5. `claude_code/config.py:337-342`
   - `update_from_env()` 只识别 `CLAUDE_API_PROVIDER` 属于 `VALID_PROVIDERS` 的情况，因此本地 provider 无法通过 config 正常进入配置对象。

额外不一致：

1. `azure` 在 `config.py` 中是合法 provider，但 `main.py` 与 `api/client.py` 当前都 fail-fast 禁用。
2. 这意味着配置层允许的 provider，不等于 runtime 真正能启动的 provider。

建议：

1. 定义一份**单一 provider 能力矩阵**。
2. `config.py`、`README`、`main.py`、`api/client.py` 必须共享同一个 truth source。
3. 对“已声明支持但尚未可靠”的 provider，统一改成 feature-flag + fail-fast 描述。

### P1-2：`/model` 与持久化配置不会真实驱动 runtime

证据：

1. `claude_code/commands/model/__init__.py:51-53`
   - `/model` 会把 `config.model` 写入配置并 `save_config()`。
2. `claude_code/main.py:177-182`
   - `create_engine()` 的 model 来源是参数或 `CLAUDE_MODEL` 环境变量，然后只把 `get_config()` 用于 permission 传播。
3. `claude_code/main.py:69-116`
   - `setup_api_client()` 也直接从环境变量读取 provider/api key，而不是使用 `Config`。

影响：

1. 用户通过 `/model` 或配置文件改的值，不一定影响真正执行的 engine。
2. 项目看起来有“完整配置系统”，实际上主链路仍是“环境变量优先且近乎唯一生效”。

建议：

1. 明确配置优先级：CLI args > local config > user config > env vars > defaults。
2. 让 `create_engine()` / `setup_api_client()` 统一从 `Config` 读取，而不是各自重新拼装。

### P1-3：`working_dir` 只影响 system prompt，不影响工具真实执行目录

证据：

1. `claude_code/main.py:162-188`
   - `create_engine(working_dir=...)` 只把 `working_dir` 传给 `build_system_prompt()`。
2. `claude_code/engine/query.py:567-576`
   - 工具执行时的 `ToolContext.working_directory` 直接写死为 `os.getcwd()`。

影响：

1. 上下文显示的工作目录与工具实际操作目录可能不同。
2. 后续若做 worktree、多仓、多根目录、远程执行，这会变成严重的一致性问题。

建议：

1. `QueryConfig` 或 `QueryEngine` 应持有 canonical working directory。
2. 所有 tool / task / agent / context builder 都从该统一字段取值。

### P1-4：`AgentTool` 的后台路径忽略了调用方上下文

证据：

1. `claude_code/tools/agent/__init__.py:184-199`
   - `effective_cwd` 被计算并传入 `_run_async_agent()`。
2. `claude_code/tools/agent/__init__.py:296-313`
   - 后台路径里重新构造 `APIClient(APIClientConfig())` 与 `QueryEngine(api_client=api_client)`，没有把 `cwd`、`tool_registry`、permission、provider 传进去。
3. `claude_code/tools/agent/__init__.py:308-311`
   - background agent 的 `engine.config.system_prompt` 只用 `agent_def.prompt`，不带父上下文拼接后的 cwd 信息。

结果：

1. 后台子代理不能稳定继承父 agent 的 provider / model / working directory / 权限上下文。
2. `run_in_background=True` 与同步执行路径的行为语义已经分叉。

建议：

1. 把子代理构造收敛到统一 builder。
2. 同步 / 后台 / worktree 三条路径共享同一份上下文构建逻辑。

### P1-5：`ClaudeMdLoader` 会静默丢失父目录中的 `CLAUDE.md`

证据：

1. `claude_code/engine/context.py:244-283`
   - `find_claude_md_files()` 会向上查找父目录 `CLAUDE.md`。
2. `claude_code/engine/context.py:283`
   - `filepath.relative_to(self._working_dir)` 对父目录文件会抛 `ValueError`。
3. 由于外围 `except Exception: continue`，最终内容会被静默跳过。

本地复现结果：

1. `find_claude_md_files()` 返回父目录文件。
2. `load_content()` 最终返回 `None`。

影响：

1. 这是一个真实的上下文丢失 bug，不是代码风格问题。
2. 上游目录里的团队规范无法稳定注入 prompt。

建议：

1. 用相对于共同祖先目录或绝对路径展示文件名。
2. 不要用宽泛异常把这类路径错误静默吞掉。

### P1-6：应用生命周期实现存在隐藏的副作用和一致性问题

证据：

1. `claude_code/app.py:200-204`
   - `Application._setup()` 里先创建并启动 `ShutdownManager`，然后又调用自己的 `_register_signal_handlers()`。
2. `claude_code/services/shutdown.py:31`、`67`
   - `force_after` 与 `_force_task` 已定义，但未真正实现强制关闭逻辑。
3. `claude_code/app.py:220-225`
   - `_teardown()` 会对 `cleanup=None` 的服务执行 `cleanup()`，只能靠 `try/except` 吞掉错误。
4. `claude_code/app.py:289-291`
   - `register_factory()` 为了推断类型直接执行 `factory()`，会提前触发副作用。

影响：

1. 生命周期行为难以预测。
2. 注册阶段与运行阶段边界不清。
3. 后续接入真实资源（DB 连接、网络客户端、线程池）时会放大问题。

建议：

1. 只保留一套 signal ownership。
2. `register_factory()` 明确传入 service type，禁止为推断类型执行 factory。
3. `_services` 不要再把 cleanup 和 service 元数据混放。

### P1-7：工具注册表的“lazy”只做到了延迟实例化，没有做到延迟导入

证据：

1. `claude_code/tools/registry.py:154-188`
   - `create_default_registry()` 内部会一次性 import 大量工具模块。
2. `claude_code/tools/registry.py:157-158`
   - 注释宣称“显著提升启动时间”，但真实行为只是延迟对象创建，不是延迟模块导入。

影响：

1. 冷启动成本仍然偏高。
2. 模块导入副作用依旧会在注册阶段触发。

补充问题：

1. `claude_code/tools/registry.py:139-142`
   - `get_definitions()` 只返回已经实例化的工具定义，不是全部注册工具。
2. `claude_code/tools/registry.py:151`
   - `get_names()` 把 `_tools.keys()` 与 `_lazy_factories.keys()` 直接拼接，存在重复项。

建议：

1. 把“模块发现”和“实例化”都做成真正的 lazy。
2. 对 registry API 建立清晰契约：`get_names()`、`get_definitions()`、`list_all()` 各自保证什么。

### P1-8：Provider 支持矩阵被高估，Vertex 路径大概率仍不完整

证据：

1. `claude_code/api/client.py:249-259`
   - `_setup_vertex()` 会调用 `google.auth.default()` 获取凭证，但后续只是构造 `AsyncAnthropic(base_url=...)`。
2. 代码中没有看到把 Google credentials 注入 bearer token / transport / request signing 的过程。

判断：

1. 这是**基于代码的推断**，不是执行后的黑盒结论。
2. 但从当前实现看，Vertex 路径极可能仍处于“看起来支持，实际并未真正接好认证”的状态。

建议：

1. provider 文档必须区分“已实测可用”和“仅接口占位”。
2. 给 Vertex / Bedrock / OpenAI-compatible 每条路径都补最小契约测试。

---

## P2：中优先级问题，会持续拉低可维护性

### P2-1：测试是绿色的，但测试盲区依然明显

已知现状：

1. 当前测试覆盖 Query / permissions / runtime tasks / middleware backend contract 基础路径，这一点是好的。
2. 但没有看到以下方向的有效回归保护：
   - Python 打包安装链路
   - `pyproject.toml` / `setup.py` 合法性
   - `PluginManager` / `LocalPluginLoader`
   - `MCPClient` / `MCPManager`
   - `Application.register_factory()` / 生命周期副作用
   - `ScheduleCronTool` / `CronListTool` / `CronDeleteTool` 与 `CronCreateTool` 的一致性
   - provider config chain（`Config` / `/model` / `main.py` / `APIClient`）

结论：

`90 passed` 很有价值，但当前更准确的表达应是：**核心回归保护不错，扩展面与分发面几乎没有得到同等级别验证。**

### P2-2：宽泛异常过多，错误被静默吞掉的概率偏高

量化结果：

1. 全仓库共有 `133` 处宽泛异常。
2. 热点文件包括：
   - `claude_code/engine/context.py`
   - `claude_code/api/client.py`
   - `claude_code/tasks/manager.py`
   - `claude_code/tools/mcp/__init__.py`
   - `claude_code/app.py`

风险：

1. 这会让“功能降级”与“功能损坏”在表面上都表现为“静默继续运行”。
2. 在多 provider、多工具、多 transport 场景下，排障成本会非常高。

建议：

1. 只在明确容错点使用宽泛异常。
2. 对 fallback、degrade、skip 的位置补结构化日志。

### P2-3：类型系统债务已经开始影响可读性和重构安全

量化结果：

1. 缺失返回类型标注：`29`
2. 缺失参数类型标注：`41`
3. 含 `Any` 的函数源码片段：`537`

热点文件：

1. `claude_code/remote.py`
2. `claude_code/plugins/__init__.py`
3. `claude_code/config.py`
4. `claude_code/services/cache_service.py`
5. `claude_code/services/token_estimation.py`
6. `claude_code/tasks/repository.py`

建议：

1. 优先收敛核心边界对象：
   - provider response
   - plugin instance
   - MCP transport / message
   - task repository record
2. 先减少公共接口层的 `Any`，再向实现层推进。

### P2-4：核心文件体量已经超过舒适维护阈值

高风险大文件：

1. `claude_code/services/mcp/client.py`
2. `claude_code/tasks/manager.py`
3. `claude_code/engine/query.py`
4. `claude_code/api/client.py`
5. `claude_code/config.py`

高风险长函数：

1. `create_default_registry`
2. `QueryEngine.query`
3. `main`
4. `BashTool.execute`

建议：

1. 先按“稳定边界”拆，不要按“代码行数平均分”拆。
2. 最优先拆分方向：
   - `MCP transport / protocol / auth / manager`
   - `QueryEngine loop / tool execution / response normalization`
   - `config loading / env overlay / provider config`

### P2-5：警告预算并未清零

本次测试警告：

1. `claude_code/utils/__init__.py:129`
   - 仍从 deprecated 的 `claude_code.utils.features` 导入。
2. `claude_code/app.py:58`
   - 仍导入 deprecated 的 `claude_code.utils.logging_system`。

这不是阻塞问题，但说明“弃用中的旧路径”仍然在主代码中存活，会持续增加认知成本。

### P2-6：`QueryEngine` 仍有未完工公共接口和细节一致性问题

证据：

1. `claude_code/engine/query.py:676`
   - `load_skill()` 仍是占位。
2. `claude_code/engine/query.py:741`
   - `resume_session()` 仍是占位。
3. `claude_code/engine/query.py:605`
   - 参数校验失败时 `duration_ms` 返回的是秒，不是毫秒。

结论：

这部分说明 `QueryEngine` 既承担主链路，又继续暴露未落地 API，后续需要尽快清理边界。

---

## P3：低优先级，但建议纳入后续治理

### P3-1：README、配置、代码对“支持的能力”描述不完全同步

表现包括：

1. provider 列表不一致
2. Azure 有的地方允许、有的地方直接禁用
3. plugin / MCP / cron 的对外心智模型比真实实现更完整

建议：

1. 建立“文档只写已实测可用能力”的约束。
2. 对实验性能力单独加 `experimental` 标记。

### P3-2：部分 API 仍然带有“演示性质”的元数据或注释

例如：

1. `setup.py` 中的 placeholder email / repo URL
2. 部分模块注释宣称“top standards”，但实现中仍保留 placeholder / deprecated / TODO 风格接口

这不会直接造成运行错误，但会削弱代码库的可信度。

---

## 6. 迭代建议（按收益排序）

### Iteration 1：先修“外部承诺层”

目标：让仓库的对外接口与实际能力一致。

1. 修复 `pyproject.toml` / `setup.py` / `requirements` 三件套。
2. 清理悬空 entry point。
3. 收敛 provider 支持矩阵。
4. 明确 README 中哪些能力是 stable，哪些是 experimental。

### Iteration 2：修复扩展面真实可用性

目标：让 MCP / plugin / cron 至少有一条稳定路径。

1. 打通一个最小可工作的 `MCP STDIO` 主链路。
2. 修复 `LocalPluginLoader`，支持真正加载本地插件实例。
3. 把 cron 收敛成单文件、单 schema、单工具集。

### Iteration 3：收敛配置与上下文传播

目标：让运行行为真正由统一配置驱动。

1. `Config` 成为 provider / model / permission / working_dir 的唯一事实源。
2. `/model`、`main.py`、`APIClient`、`QueryEngine` 统一走同一条配置解析链。
3. 修复 `working_dir`、`CLAUDE.md`、sub-agent cwd 的传播。

### Iteration 4：降低重构风险

目标：为中期持续演进打基础。

1. 收缩 `except Exception`
2. 提升公共接口的类型标注
3. 拆分 `services/mcp/client.py`、`engine/query.py`、`api/client.py`、`config.py`
4. 补齐扩展面契约测试

---

## 7. 推荐的下一轮任务拆分

建议把下一轮开发拆成以下 6 个独立工作包：

1. `packaging-hardening`
   - 修 `pyproject.toml`
   - 修 `setup.py`
   - 建安装/构建 smoke test
2. `provider-contract-unification`
   - 收敛 provider 列表
   - 统一 config -> runtime 映射
3. `mcp-minimal-viable-client`
   - 只打通 STDIO
   - 先不承诺 HTTP/SSE/WebSocket
4. `plugin-loader-fix`
   - 本地插件入口约定
   - loader / manager / tests
5. `cron-consolidation`
   - 合并 `scheduled_tasks.json` 与 `schedules.json`
6. `execution-context-hardening`
   - working_dir
   - CLAUDE.md 祖先加载
   - agent 上下文继承

---

## 8. 最终判断

如果把本仓库定位为“单机 CLI 的持续演进版原型”，当前状态是可接受的；如果把它定位为“可稳定扩展、可可靠分发、可承载多 provider / MCP / plugin / task platform 的 Python 工程”，那么当前最主要的问题已经不是功能缺失，而是：

1. **契约不一致**
2. **扩展面未闭环**
3. **发布面未达标**
4. **复杂度开始累积**

因此，下一阶段最合理的策略不是继续横向堆新功能，而是先把：

- 打包发布
- MCP / plugin / cron
- 配置到运行时映射
- 工作目录与上下文传播

这四条线收敛干净。否则后续每加一个新能力，都会把“局部可跑”继续放大成“整体难以维护”。

---

## 9. 附：本次评估的关键事实

1. 语法检查：通过（`208` 文件，`0` 错误）
2. 全量测试：通过（`90 passed, 3 warnings`）
3. `pyproject.toml`：当前不可被 `tomllib` 解析
4. `Config(api_provider="ollama")`：当前直接失败
5. `setup.py` + `requirements.txt`：当前不满足稳定打包要求
6. `ClaudeMdLoader` 父目录 `CLAUDE.md`：当前已复现丢失

