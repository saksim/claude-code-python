# Claude Code Python 执行计划与任务卡单（2026-04-29）

## 1. 文档定位

- 文档性质：执行计划 + 任务卡单
- 上游文档：[CLAUDE_CODE_SUPERSEDE_STRATEGY_2026-04-29.md](D:/Download/gaming/new_program/claude-code-python/docs/current/architecture/CLAUDE_CODE_SUPERSEDE_STRATEGY_2026-04-29.md)
- 使用方式：
  - 产品、架构、研发、测试都以本文件作为近期实施清单
  - 每张任务卡必须能独立建分支、独立开发、独立验证、独立合并
  - 若一张卡无法在一个明确边界内完成，则继续向下拆

## 2. 当前拆解原则

### 2.1 拆卡原则

每张卡必须同时回答 5 个问题：

1. 解决什么问题？
2. 要做什么研发功能？
3. 要做到什么程度才算完成？
4. 测试代码要补到什么程度？
5. 有什么前置依赖和明确非目标？

### 2.2 完成定义（Definition of Done）

每张卡默认完成标准：

- 代码主链可运行
- 新增或修改测试通过
- 对应文档同步更新
- 不引入新的未解释脏状态
- 至少完成一轮本地手工验收

### 2.3 测试分层标准

为避免“写了点测试”但没有验收价值，统一采用以下深度分层：

| 层级 | 名称 | 目的 | 最低要求 |
|---|---|---|---|
| T1 | Unit | 纯函数、状态机、输入输出边界 | 正向 + 负向 + 边界 |
| T2 | Component | 单模块编排、带 fake/mocks 的行为验证 | 至少覆盖 1 条主链 + 1 条异常链 |
| T3 | Integration | 跨模块联动，验证真实依赖边界 | 至少覆盖 1 条端到端业务链 |
| T4 | Regression | 复现历史缺陷，防止回归 | 每个已知 bug 至少 1 条回归用例 |
| T5 | Manual Smoke | 人工快速验收 | 命令级/入口级实际运行 |

### 2.4 测试产物要求

每张代码卡至少满足：

- 新增或修改 `T1/T2` 测试
- 若变更影响 CLI、session、task、MCP、hooks、agent 主链，则必须补 `T3`
- 若任务卡源于已知缺陷，则必须补 `T4`
- 输出 1 份最小手工验收命令清单

## 3. 实施阶段总览

## 3.1 Phase 0：止血与收敛

目标：

- 修掉“看起来有、实际没打通”的假闭环
- 建立唯一主运行时入口
- 建立稳定的本地开发/测试施工面

## 3.2 Phase 1：平台化

目标：

- 从单进程 CLI 演进为可复用的执行后端
- 补齐 event journal、state backend、active memory

## 3.3 Phase 2：超车

目标：

- 建立多 Agent 控制面、IDE 客户端、CI 工作流、组织级治理能力

## 4. 依赖顺序图

```text
P0-01 Runtime Backbone
  -> P0-02 Session Resume
  -> P0-03 Auth/Config
  -> P0-04 Feature Flags
  -> P0-05 Review Command
  -> P0-06 Session/History/Memory Boundaries
  -> P0-07 Hooks Runtime
  -> P0-08 Windows Bootstrap
  -> P0-09 Temp Artifact Hygiene
  -> P0-10 Phase0 Regression Gate

P1-01 Daemon/API Control Plane
  -> P1-02 Event Journal
  -> P1-03 SQLite State Backend
  -> P1-04 Active Memory Runtime
  -> P1-05 Hook Policy/Audit Convergence
  -> P1-06 CLI Thin Client Migration

P2-01 Agent Supervisor
  -> P2-02 Artifact Bus
  -> P2-03 IDE Integration
  -> P2-04 GitHub/CI Workflow
  -> P2-05 Org Policy & Audit
```

## 5. Phase 0 任务卡单

## P0-01 统一主运行时骨架

- 卡号：`P0-01`
- 优先级：`P0`
- 解决问题：
  - `main.py`、`app.py`、session/task/hooks/memory 初始化链条分散
  - 子系统存在但未形成唯一运行时闭环
- 研发功能：
  - 建立统一 runtime bootstrap
  - 明确 `main -> Application -> QueryEngine -> Session -> TaskManager -> Hooks -> Memory`
  - 消除重复初始化路径与隐式全局状态依赖
- 实施范围：
  - `claude_code/main.py`
  - `claude_code/app.py`
  - `claude_code/engine/query.py`
  - 视需要新增 `claude_code/runtime/` 或等价模块
- 完成程度：
  - REPL、single query、pipe、MCP serve 共用同一 bootstrap 流
  - runtime 关键对象有唯一构建路径
  - 后续卡单不再依赖“各自偷偷初始化”
- 测试代码要求：
  - `T1`：bootstrap 参数解析、runtime object 构建边界
  - `T2`：不同运行模式下 runtime 组件装配一致性
  - `T3`：REPL / pipe / single query 至少各有 1 条主链 smoke
  - `T4`：覆盖“某模式漏初始化某服务”的历史断点
- 建议测试文件：
  - 新增 `tests/test_runtime_bootstrap.py`
  - 扩展 `tests/test_main_runtime.py`
- 手工验收：
  - `python -m claude_code.main --help`
  - `python -m claude_code.main --doctor`
  - `echo hi | python -m claude_code.main --pipe`
- 非目标：
  - 本卡不引入 daemon/API
  - 本卡不处理组织级策略
- 前置依赖：无

## P0-02 /resume 真闭环

- 卡号：`P0-02`
- 优先级：`P0`
- 解决问题：
  - `QueryEngine.resume_session()` 已存在，但 `/resume` 命令没有真正调用恢复链路
  - session 恢复是“文案功能”，不是“运行时功能”
- 研发功能：
  - 将 `/resume [session_id]` 真正接入 `QueryEngine.resume_session()`
  - 无参数时列最近 session；有参数时恢复指定 session 并接续对话
  - 明确恢复后的 session id、message list、working directory 行为
- 实施范围：
  - `claude_code/commands/compact/__init__.py`
  - `claude_code/engine/query.py`
  - `claude_code/engine/session.py`
  - `claude_code/repl/__init__.py`
- 完成程度：
  - `/resume` 不再只返回说明文字
  - 恢复后下一轮 query 能接着历史消息运行
  - 恢复失败时有可诊断错误信息
- 测试代码要求：
  - `T1`：session list / load 边界
  - `T2`：command -> engine 恢复链路
  - `T3`：创建 session、持久化、恢复、继续问答的一条完整链
  - `T4`：无 session / session_id 不存在 / 会话文件损坏
- 建议测试文件：
  - 扩展 `tests/test_query_engine_runtime.py`
  - 扩展 `tests/test_main_runtime.py`
  - 新增 `tests/test_resume_runtime.py`
- 手工验收：
  - 启动一次会话并生成持久化
  - 新进程执行 `/resume`
  - 确认恢复后继续对话
- 非目标：
  - 不引入跨机器恢复
  - 不引入 session 搜索 UI
- 前置依赖：`P0-01`

## P0-03 auth/config 主链修复与统一

- 卡号：`P0-03`
- 优先级：`P0`
- 解决问题：
  - `logout` / `auth` 使用未导入的 `ConfigManager`
  - `Config` 与 `ConfigManager` 双轨并存，认证状态判定不稳定
- 研发功能：
  - 选定 canonical config 读写路径
  - 修复 `/login`、`/logout`、`/auth`
  - 统一 env/config/key masking 规则
- 实施范围：
  - `claude_code/commands/auth/__init__.py`
  - `claude_code/config.py`
  - `claude_code/utils/config_manager.py`
  - 视需要调整 `claude_code/main.py`
- 完成程度：
  - `auth` 链路无 `NameError`
  - 认证状态输出与实际 env/config 一致
  - logout 能清理 runtime 可见的 key 来源
- 测试代码要求：
  - `T1`：env > config > default 优先级
  - `T2`：auth commands 在不同 key 来源下的行为
  - `T3`：命令级状态变化验证
  - `T4`：无 key / config 缺失 / key mask 输出
- 建议测试文件：
  - 新增 `tests/test_commands_auth_runtime.py`
  - 扩展 `tests/test_main_runtime.py`
- 手工验收：
  - 设置 env key
  - 运行 `/auth`
  - 运行 `/logout`
  - 再次运行 `/auth`
- 非目标：
  - 不引入 OAuth 真登录流
  - 不接第三方 secrets manager
- 前置依赖：`P0-01`

## P0-04 feature flag 运行时修复

- 卡号：`P0-04`
- 优先级：`P0`
- 解决问题：
  - `FeatureConfig` 为 frozen dataclass，但 `enable()/disable()` 试图原地修改
  - 当前 flag 机制对未来大功能切换不可靠
- 研发功能：
  - 重构 feature registry 的内部状态表达
  - 保持 env fallback，同时允许程序内安全切换
  - 明确 feature 读取与写入语义
- 实施范围：
  - `claude_code/features.py`
- 完成程度：
  - `enable()` / `disable()` 不抛 `FrozenInstanceError`
  - registry 内外行为一致
  - flags 可作为后续大卡的 gated rollout 机制
- 测试代码要求：
  - `T1`：enable / disable / env override / unknown feature
  - `T2`：registry 实例在多次调用中的状态一致性
  - `T4`：复现当前 `FrozenInstanceError` 的回归用例
- 建议测试文件：
  - 新增 `tests/test_features_runtime.py`
- 手工验收：
  - 本地脚本切换 feature 并读取
- 非目标：
  - 不引入远程 flag service
- 前置依赖：无

## P0-05 review 命令产品化

- 卡号：`P0-05`
- 优先级：`P0`
- 解决问题：
  - `/review` 只是引导文案，不执行真实审查
  - 用户无法依赖该命令检查 diff / 文件风险
- 研发功能：
  - 支持 review 当前 git diff
  - 支持 review 指定文件
  - 统一 findings 输出格式：问题、位置、严重度、建议
  - 明确“无发现”输出
- 实施范围：
  - `claude_code/commands/review/__init__.py`
  - 视需要新增 `claude_code/services/review_service.py`
  - 可接入 `git diff` / read-only analyzer
- 完成程度：
  - `/review` 不再返回占位 prompt
  - 能对当前改动或输入文件给出结构化结果
  - 输出可作为后续 PR/CI review 的雏形
- 测试代码要求：
  - `T1`：参数解析、无输入默认行为
  - `T2`：service 对 fake diff 的 findings 生成
  - `T3`：临时 git repo 中的 review 主链
  - `T4`：无 diff / 文件不存在 / 空结果
- 建议测试文件：
  - 新增 `tests/test_review_command_runtime.py`
- 手工验收：
  - 修改一个文件后执行 `/review`
  - 指定文件执行 `/review path`
- 非目标：
  - 不做组织级 code review dashboard
  - 不强行接 GitHub API
- 前置依赖：`P0-01`

## P0-06 session/history/memory 职责收敛

- 卡号：`P0-06`
- 优先级：`P0`
- 解决问题：
  - `Session`、`HistoryManager`、`SessionMemory` 职责交叉
  - 短期对话、长期记忆、归档历史边界不清
- 研发功能：
  - 明确三层职责：
    - `Session`：当前会话事实
    - `History`：已结束/已保存的消息归档
    - `Memory`：长期结构化知识
  - 消除重复保存与不一致加载路径
  - 为 P1 active memory 铺底
- 实施范围：
  - `claude_code/engine/session.py`
  - `claude_code/services/history_manager.py`
  - `claude_code/services/memory_service.py`
  - `claude_code/context/builder.py`
- 完成程度：
  - 三者职责与调用边界写清
  - 当前主链只保留一个 message persistence source of truth
  - memory 不再隐式承担 session/history 角色
- 测试代码要求：
  - `T1`：save/load/export/search 边界
  - `T2`：session -> persisted session 行为
  - `T3`：context builder 读取 memory/session 的联动
  - `T4`：防止重复消息、重复持久化、错误恢复
- 建议测试文件：
  - 新增 `tests/test_session_history_memory_runtime.py`
  - 扩展 `tests/test_context_builder_runtime.py`
- 手工验收：
  - 生成会话
  - 重启加载
  - 验证 memory 不被误写为聊天历史
- 非目标：
  - 不做向量数据库
  - 不做长期检索增强
- 前置依赖：`P0-01`

## P0-07 hooks 接入主运行时

- 卡号：`P0-07`
- 优先级：`P0`
- 解决问题：
  - hooks command、hooks manager、tool/command 执行链没有真正联动
  - hooks 目前更像静态配置，而不是运行时能力
- 研发功能：
  - 在 tool execution 前后触发 hooks
  - 在 command 执行前后触发 hooks
  - 在错误路径触发 `on_error`
  - 约定 hook context payload
- 实施范围：
  - `claude_code/services/hooks_manager.py`
  - `claude_code/commands/hooks/__init__.py`
  - `claude_code/engine/query.py`
  - `claude_code/repl/__init__.py`
  - 视需要接入 command dispatch 层
- 完成程度：
  - hooks 配置能真实生效
  - disabled hook、超时 hook、失败 hook 行为清晰
  - 对主链失败不产生不可控副作用
- 测试代码要求：
  - `T1`：hook load/save/parse
  - `T2`：trigger before_tool / after_tool / on_error
  - `T3`：真实 tool 调用链触发 hook
  - `T4`：hook timeout / hook command failure / disabled hook
- 建议测试文件：
  - 新增 `tests/test_hooks_runtime.py`
- 手工验收：
  - 配置一个简单 echo hook
  - 执行 read / grep / bash
  - 确认 hook 被触发
- 非目标：
  - 不做 org-wide hook registry
- 前置依赖：`P0-01`

## P0-08 Windows 启动与解释器探测稳定化

- 卡号：`P0-08`
- 优先级：`P1`
- 解决问题：
  - 系统 `python` 指向 WindowsApps stub，用户容易跑到假解释器
  - Windows 用户启动链脆弱
- 研发功能：
  - 在 `--doctor` 中识别解释器来源
  - 对 WindowsApps stub 给出明确警告
  - 统一推荐启动器 / wrapper 行为
  - 文档同步明确 Windows 推荐运行法
- 实施范围：
  - `claude_code/main.py`
  - `README.md`
  - 可选新增 `scripts/` 下辅助启动脚本
- 完成程度：
  - doctor 输出能诊断解释器风险
  - Windows 用户不会误以为 stub 可用
  - 项目入口文档清楚标注推荐解释器
- 测试代码要求：
  - `T1`：解释器路径识别逻辑
  - `T2`：doctor 输出分支
  - `T4`：WindowsApps stub 回归用例
- 建议测试文件：
  - 新增 `tests/test_doctor_runtime.py`
- 手工验收：
  - 模拟 / 检查 doctor 输出
- 非目标：
  - 不做完整安装器
- 前置依赖：`P0-01`

## P0-09 测试临时产物清理与隔离

- 卡号：`P0-09`
- 优先级：`P1`
- 解决问题：
  - `tests/.tmp_plugins/` 存在残留目录
  - 测试隔离性与仓库整洁性不足
- 研发功能：
  - 修复 plugin 测试的清理逻辑
  - 增补 `.gitignore` 或测试 teardown
  - 确保 pytest 结束后不新增脏目录
- 实施范围：
  - `tests/test_plugins_runtime.py`
  - `.gitignore`
  - 视需要调整 plugin fixture
- 完成程度：
  - 本地完整 pytest 后不再残留新增 `.tmp_*` / `.tmp_plugins/*`
  - 测试互不污染
- 测试代码要求：
  - `T2`：fixture cleanup 断言
  - `T4`：重复运行 pytest 不累计残留
- 建议测试文件：
  - 扩展 `tests/test_plugins_runtime.py`
- 手工验收：
  - 连续跑两次 pytest
  - 检查工作区脏文件
- 非目标：
  - 不清理用户真实运行数据
- 前置依赖：无

## P0-10 Phase 0 回归门禁

- 卡号：`P0-10`
- 优先级：`P0`
- 解决问题：
  - 现有测试分布较散，没有围绕 Phase 0 主链建立明确门禁
- 研发功能：
  - 定义一组必须通过的 runtime regression tests
  - 增加按主链分组的 pytest marker 或脚本入口
  - 明确提交前必跑命令
- 实施范围：
  - `pytest.ini`
  - `scripts/` 下校验脚本（如需要）
  - 测试文件标记整理
- 完成程度：
  - 能一条命令执行 P0 主链回归
  - 团队知道“开工前/合并前必须跑什么”
- 测试代码要求：
  - 本卡本质上是测试组织卡
  - 需要补 1 个测试入口脚本或 marker 验证
- 建议测试文件：
  - 如需新增：`tests/test_phase0_regression_contract.py`
- 手工验收：
  - 执行一条 phase0 gate 命令并验证通过
- 非目标：
  - 不要求此时接 CI SaaS
- 前置依赖：
  - `P0-02` ~ `P0-09`

## 6. Phase 1 任务卡单

## P1-01 daemon / API 控制面

- 卡号：`P1-01`
- 优先级：`P1`
- 解决问题：
  - 当前 CLI 是厚客户端，IDE/desktop/web/CI 无法共用执行后端
- 研发功能：
  - 提供本地 daemon/API 层
  - 抽离 session、task、tool execution、artifact 访问接口
  - CLI 改为 daemon client 的上层入口
- 实施范围：
  - 新增 `claude_code/server/` 或等价控制面模块
  - 调整 `main.py`
  - 复用 `app.py`
- 完成程度：
  - 单机可启动 daemon
  - CLI 与 daemon 可共享一套执行核心
- 测试代码要求：
  - `T1`：API schema / request validation
  - `T2`：server service 层行为
  - `T3`：client -> server -> runtime 一条完整链
  - `T4`：daemon 未启动 / 超时 / 会话不存在
- 前置依赖：`P0-01`、`P0-10`

## P1-02 event journal 事件日志

- 卡号：`P1-02`
- 优先级：`P1`
- 解决问题：
  - prompt、tool、task、permission 决策不可回放，不可审计
- 研发功能：
  - 定义统一事件模型
  - 写入 prompt/message/tool/task/permission/artifact 事件
  - 提供查询与 replay 基础能力
- 实施范围：
  - 新增 `claude_code/services/event_journal.py` 或等价模块
  - 接入 `QueryEngine`、`TaskManager`
- 完成程度：
  - 所有关键主链动作可产生结构化事件
  - 支持按 session 查询事件流
- 测试代码要求：
  - `T1`：事件 schema、序列化、versioning
  - `T2`：writer/reader correctness
  - `T3`：query -> tool -> task 事件链
  - `T4`：部分写入失败、乱序恢复
- 前置依赖：`P1-01`

## P1-03 SQLite runtime state backend

- 卡号：`P1-03`
- 优先级：`P1`
- 解决问题：
  - file/memory backend 对恢复、检索、多实例前准备不足
- 研发功能：
  - 为 session/task/event 提供 SQLite backend
  - 保留 file backend 作为兼容层或 fallback
  - 明确 migration 与 schema version
- 实施范围：
  - `claude_code/tasks/factory.py`
  - `claude_code/tasks/repository.py`
  - session/event 相关存储模块
- 完成程度：
  - 至少可用 SQLite 持久化 task/session/event
  - 单机重启后可恢复核心运行态
- 测试代码要求：
  - `T1`：schema init / migration
  - `T2`：repository CRUD contract
  - `T3`：重启恢复
  - `T4`：数据库损坏、锁冲突、重复初始化
- 前置依赖：`P1-02`

## P1-04 active memory 接入运行时

- 卡号：`P1-04`
- 优先级：`P1`
- 解决问题：
  - `SessionMemory` 现在是孤立 KV，不影响主对话上下文
- 研发功能：
  - 让 memory 与 context builder/runtime 联动
  - 定义 memory scope：user/project/local
  - 支持显式写入、按需注入、命中统计
- 实施范围：
  - `claude_code/services/memory_service.py`
  - `claude_code/context/builder.py`
  - `claude_code/agents/builtin.py`
- 完成程度：
  - memory 成为运行时真实输入，而非旁路存储
  - agent / main query 可选择不同 memory scope
- 测试代码要求：
  - `T1`：namespace / key / search 行为
  - `T2`：context builder memory 注入
  - `T3`：query 执行时命中 memory
  - `T4`：空 memory / 损坏 memory / scope 隔离
- 前置依赖：`P0-06`、`P1-02`

## P1-05 hooks / permission / audit 收敛

- 卡号：`P1-05`
- 优先级：`P1`
- 解决问题：
  - hooks、permissions、event journal 仍是分立能力
- 研发功能：
  - 统一 hook 事件、permission decision、audit event
  - 形成一次执行的完整审计链
  - 为未来 org policy 铺底
- 实施范围：
  - `claude_code/permissions.py`
  - `claude_code/services/hooks_manager.py`
  - event journal 相关模块
- 完成程度：
  - 每次 tool call 至少具备 request -> decision -> hook -> result 的闭环记录
- 测试代码要求：
  - `T2`：permission + hook + event 联动
  - `T3`：真实 tool 执行审计链
  - `T4`：deny / timeout / partial failure
- 前置依赖：`P0-07`、`P1-02`

## P1-06 CLI thin client 迁移

- 卡号：`P1-06`
- 优先级：`P1`
- 解决问题：
  - CLI 与控制面耦合过深，不利于 IDE/CI 共用
- 研发功能：
  - CLI 发请求给本地 runtime server/daemon
  - 保留单进程 fallback 模式
  - 统一输出与错误语义
- 实施范围：
  - `claude_code/main.py`
  - CLI/REPL client adapter
- 完成程度：
  - CLI 作为 runtime 前端存在，而非执行内核本身
- 测试代码要求：
  - `T2`：client adapter 行为
  - `T3`：CLI -> daemon 完整主链
  - `T4`：daemon 不可用 fallback
- 前置依赖：`P1-01`

## 7. Phase 2 任务卡单

## P2-01 多 Agent supervisor

- 卡号：`P2-01`
- 优先级：`P2`
- 解决问题：
  - 当前 agent 更像“单次子任务执行器”，不是控制面
- 研发功能：
  - agent DAG
  - budget / timeout / retry / ownership
  - parent-child artifact passing
- 完成程度：
  - 至少支持并行 agent + 汇总收口
- 测试代码要求：
  - `T1`：graph / budget / timeout 状态机
  - `T2`：supervisor 调度
  - `T3`：并行 agent 执行
  - `T4`：子 agent 失败恢复
- 前置依赖：`P1-01`、`P1-02`

## P2-02 artifact bus 与冲突收敛

- 卡号：`P2-02`
- 优先级：`P2`
- 解决问题：
  - 多 agent 输出缺少结构化 artifact 交换层
- 研发功能：
  - 统一 artifact schema
  - patch / note / diff / report / finding 流转
  - 冲突检测与合并策略
- 测试代码要求：
  - `T1`：artifact schema
  - `T2`：producer/consumer
  - `T3`：多 agent artifact 汇流
  - `T4`：冲突合并失败
- 前置依赖：`P2-01`

## P2-03 IDE 集成（VS Code first）

- 卡号：`P2-03`
- 优先级：`P2`
- 解决问题：
  - 当前仓库缺少真正可用的 IDE workflow
- 研发功能：
  - VS Code client
  - daemon 连接
  - diff、task、session、findings 展示
- 测试代码要求：
  - `T2`：client protocol adapter
  - `T3`：IDE -> daemon 核心链
  - `T5`：人工交互验收为主
- 前置依赖：`P1-06`

## P2-04 GitHub / CI 工作流 agent

- 卡号：`P2-04`
- 优先级：`P2`
- 解决问题：
  - 当前能力主要停留在本地 CLI，无法进入团队协作闭环
- 研发功能：
  - issue -> plan -> code -> test -> review -> PR 工作流
  - CI 环境的 headless execution 模式
- 测试代码要求：
  - `T2`：workflow state machine
  - `T3`：fake repo / fake PR 主链
  - `T4`：权限不足 / repo 状态不干净 / 网络失败
- 前置依赖：`P1-01`、`P1-02`

## P2-05 组织级策略与审计面板

- 卡号：`P2-05`
- 优先级：`P2`
- 解决问题：
  - 团队场景下缺乏治理、审批、审计、安全边界
- 研发功能：
  - policy model
  - approval queue
  - secret redaction
  - audit query / reporting
- 测试代码要求：
  - `T1`：policy matcher / redaction rules
  - `T2`：approval state transitions
  - `T3`：执行审计链闭环
  - `T4`：策略冲突 / 未审批执行阻断
- 前置依赖：`P1-05`

## 8. 推荐迭代顺序

若只允许一轮一轮推进，建议顺序如下：

1. `P0-01`
2. `P0-02`
3. `P0-03`
4. `P0-04`
5. `P0-05`
6. `P0-06`
7. `P0-07`
8. `P0-09`
9. `P0-08`
10. `P0-10`

说明：

- `P0-08` 不阻塞主功能修复，因此放在 `P0-09` 后面亦可
- `P0-10` 作为收口卡，应放在 Phase 0 尾部

## 9. 每轮迭代的最小产出要求

每完成一张卡，至少同步以下产物：

1. 代码变更
2. 测试变更
3. 文档变更
4. 手工验收命令
5. 风险与剩余盲区

建议每张卡的交付说明统一采用：

```text
【任务卡】P0-XX
【解决】……
【完成】……
【测试】……
【风险】……
【下一卡】……
```

## 10. 当前最适合立即开工的卡单

若立刻让 Codex 下刀，推荐第一批开工卡：

1. `P0-01 统一主运行时骨架`
2. `P0-02 /resume 真闭环`
3. `P0-03 auth/config 主链修复与统一`
4. `P0-04 feature flag 运行时修复`
5. `P0-05 review 命令产品化`

理由：

- 这 5 张卡直接决定项目是否从“可跑代码”进入“可施工产品”
- 它们都属于高确定性、高收益、可本地验证的任务
- 其测试回报率最高，且能为后续平台化卡单扫清障碍

## 11. 文档维护规则

- 若某张任务卡进入开发，新增执行记录时优先更新本文件，而不是平行新建“同主题小文档”
- 若一张任务卡被继续拆分，使用子编号：
  - `P0-03A`
  - `P0-03B`
- 若策略变化影响任务边界，先更新上游战略文档，再回写本文件

## 12. 结论

本文档的目标不是“列待办事项”，而是建立一个研发可执行、测试可验收、管理可跟踪的施工面。

从现在开始，后续所有开工建议都应基于任务卡，而不是基于模糊意图。

换言之：

> 先按卡开工，再按卡验尸，再按卡推进，不再凭感觉做重构。

## 13. Execution Log (2026-04-29)

- Card: `P0-01 Runtime Backbone`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/main.py`
  - `claude_code/mcp/server.py`
- Test scripts landed:
  - `tests/test_main_runtime.py` (runtime bootstrap + mcp serve wiring coverage)
  - `tests/test_runtime_bootstrap.py` (entrypoint consistency + mcp registry injection)
- Not executed locally per release policy:
  - Unit/component/integration tests will be executed in Linux unified validation stage.

## 14. Execution Log (2026-04-29, P0-02)

- Card: `P0-02 /resume Runtime Closure`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/commands/compact/__init__.py`
  - `claude_code/engine/query.py`
  - `claude_code/repl/__init__.py`
- Test scripts landed:
  - `tests/test_resume_runtime.py`
- Not executed locally per release policy:
  - Resume-related unit/component/integration checks will run in Linux unified validation stage.

## 15. Execution Log (2026-04-29, P0-03)

- Card: `P0-03 Auth/Config Runtime Unification`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/commands/auth/__init__.py`
- Test scripts landed:
  - `tests/test_commands_auth_runtime.py`
  - `tests/test_main_runtime.py` (auth key precedence coverage extension)
- Not executed locally per release policy:
  - Auth/config unit/component/integration checks will run in Linux unified validation stage.

## 16. Execution Log (2026-04-29, P0-04)

- Card: `P0-04 Feature Flag Runtime Repair`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/features.py`
- Test scripts landed:
  - `tests/test_features_runtime.py`
- Not executed locally per release policy:
  - Feature flag unit/component checks will run in Linux unified validation stage.

## 17. Execution Log (2026-04-29, P0-05)

- Card: `P0-05 Review Command Productization`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/commands/review/__init__.py`
  - `claude_code/services/review_service.py`
- Test scripts landed:
  - `tests/test_review_command_runtime.py`
- Not executed locally per release policy:
  - Review command unit/component/integration checks will run in Linux unified validation stage.

## 18. Execution Log (2026-04-29, P0-06)

- Card: `P0-06 Session/History/Memory Boundary Convergence`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/engine/query.py`
  - `claude_code/engine/session.py`
  - `claude_code/services/history_manager.py`
  - `claude_code/services/memory_service.py`
  - `claude_code/main.py`
- Test scripts landed:
  - `tests/test_session_history_memory_runtime.py`
  - `tests/test_context_builder_runtime.py` (boundary assertions extension)
  - `tests/test_main_runtime.py` (runtime service wiring extension)
- Not executed locally per release policy:
  - Session/history/memory unit/component/integration checks will run in Linux unified validation stage.

## 19. Execution Log (2026-04-29, P0-07)

- Card: `P0-07 Hooks Runtime Integration`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/services/hooks_manager.py`
  - `claude_code/commands/hooks/__init__.py`
  - `claude_code/engine/query.py`
  - `claude_code/repl/__init__.py`
  - `claude_code/main.py`
- Test scripts landed:
  - `tests/test_hooks_runtime.py`
  - `tests/test_main_runtime.py` (hooks manager runtime bootstrap wiring update)
- Not executed locally per release policy:
  - Hooks runtime unit/component/integration checks will run in Linux unified validation stage.

## 20. Execution Log (2026-04-29, P0-09)

- Card: `P0-09 Temp Artifact Hygiene`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `tests/test_plugins_runtime.py`
  - `.gitignore`
- Test scripts landed:
  - `tests/test_plugins_runtime.py` (fixture teardown cleanup assertion + idempotent cleanup coverage)
- Not executed locally per release policy:
  - Plugin runtime cleanup and residue-isolation checks will run in Linux unified validation stage.

## 21. Execution Log (2026-04-29, P0-08)

- Card: `P0-08 Windows Bootstrap & Interpreter Probe Stabilization`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/main.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_doctor_runtime.py`
- Not executed locally per release policy:
  - Doctor interpreter-detection unit/component checks and Windows stub regression cases will run in Linux unified validation stage.

## 22. Execution Log (2026-04-29, P0-10)

- Card: `P0-10 Phase 0 Regression Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `pytest.ini`
  - `scripts/run_phase0_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_phase0_regression_contract.py`
- Not executed locally per release policy:
  - Phase 0 gate contract and curated regression-entry checks will run in Linux unified validation stage.

## 23. Execution Log (2026-04-29, P1-01)

- Card: `P1-01 Daemon/API Control Plane`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/server/control_plane.py`
  - `claude_code/server/__init__.py`
  - `claude_code/main.py`
  - `scripts/run_p1_control_plane_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_server_runtime.py` (`T1` schema validation, `T2` service behavior, `T3` client->server->runtime chain, `T4` daemon down/timeout/session-not-found)
  - `tests/test_main_runtime.py` (daemon CLI bootstrap wiring coverage)
- Not executed locally per release policy:
  - Daemon/API unit/component/integration/regression checks will run in Linux unified validation stage.

## 24. Execution Log (2026-04-29, P1-02)

- Card: `P1-02 Event Journal`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/services/event_journal.py`
  - `claude_code/services/__init__.py`
  - `claude_code/tasks/manager.py`
  - `claude_code/tasks/factory.py`
  - `claude_code/tasks/__init__.py`
  - `claude_code/engine/query.py`
  - `claude_code/server/control_plane.py`
  - `claude_code/main.py`
  - `scripts/run_p1_event_journal_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_event_journal_runtime.py` (`T1` schema/versioning, `T2` writer/reader correctness, `T3` query->tool->task event chain, `T4` partial write/corruption recovery)
  - `tests/test_server_runtime.py` (event list/replay daemon API coverage)
  - `tests/test_main_runtime.py` (runtime bootstrap wiring includes event journal)
- Not executed locally per release policy:
  - Event journal unit/component/integration/regression checks will run in Linux unified validation stage.

## 25. Execution Log (2026-04-29, P1-03)

- Card: `P1-03 SQLite Runtime State Backend`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/tasks/repository.py` (SQLite runtime repository + schema version/migration guard)
  - `claude_code/tasks/factory.py` (runtime backend default switched to `sqlite`)
  - `claude_code/tasks/__init__.py` (SQLite repository exports)
  - `claude_code/engine/session.py` (SQLite session store + manager constructor hook)
  - `claude_code/services/event_journal.py` (SQLite event journal + schema version/migration guard)
  - `claude_code/services/__init__.py` (SQLite event journal exports)
  - `claude_code/engine/query.py` (event journal duck-typing for backend-agnostic write path)
  - `claude_code/main.py` (runtime bootstrap switched to unified `.claude/runtime_state.db`)
  - `scripts/run_p1_sqlite_state_backend_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_sqlite_runtime_state_backend.py` (`T1` schema init/version guard, `T2` repository/session/event correctness, `T3` runtime chain wiring)
  - `tests/test_tasks_backend_contract.py` (SQLite repository contract + schema guard extension)
  - `tests/test_tasks_factory_runtime.py` (default runtime backend contract update to `sqlite`)
  - `tests/test_tasks_manager_runtime.py` (SQLite lifecycle persistence/recovery extension)
  - `tests/test_event_journal_runtime.py` (SQLite event journal schema/query/replay guard extension)
  - `tests/test_main_runtime.py` (runtime bootstrap mocks updated for SQLite state wiring)
- Not executed locally per release policy:
  - SQLite runtime state backend unit/component/integration/regression checks will run in Linux unified validation stage.
