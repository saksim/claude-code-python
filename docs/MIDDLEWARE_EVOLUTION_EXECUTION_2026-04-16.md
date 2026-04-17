# 中间件演进落地执行记录（持续迭代）

- 关联评估报告：`docs/MIDDLEWARE_EVOLUTION_ASSESSMENT_2026-04-16.md`
- 执行日期：2026-04-16
- 当前状态：Phase 0 全量完成 + Phase 1（仓储抽象）首步完成

---

## 本轮已落地

### 1) 修复 TaskControl 链路可用性（P0）

- `TaskStopTool` / `TaskOutputTool` / `TaskControlListTool` 统一改为 `get_task_manager()`，不再错误创建新 `TaskManager()` 实例。
- `TaskOutputTool` 改为调用 `task.get_output()`，移除对不存在字段 `task.output` 的访问。
- `TaskControlListTool` 改为展示通用字段 `task.description`，移除对非通用字段 `task.command` 的依赖。

对应文件：
- `claude_code/tools/control/__init__.py`

### 2) 统一 tasks.json schema + 向后兼容迁移（P1）

- 新增 `task_store` 层，支持三种输入格式并统一写回 canonical schema：
  - legacy dict：`{"<id>": {...}}`
  - legacy list：`[{...}]`
  - canonical wrapper：`{"schema_version": 2, "tasks": [...]}`
- workflow tools 与 `/tasks` command 全部切换到统一存储逻辑，避免 list/dict 双写冲突。

对应文件：
- `claude_code/utils/task_store.py`（新增）
- `claude_code/tools/workflow/task_create.py`
- `claude_code/tools/workflow/task_get.py`
- `claude_code/tools/workflow/task_list.py`
- `claude_code/tools/workflow/task_update.py`
- `claude_code/commands/tasks/__init__.py`

### 3) 文件锁 + 安全写入机制（P1）

- 新增跨平台文件锁 `TaskFileLock`（Windows: `msvcrt.locking`; POSIX: `fcntl.flock`）。
- 保留原子写优先策略（temp + replace），并在受限文件系统下自动降级为直接写，保证功能可用性。

对应文件：
- `claude_code/utils/task_store.py`

### 4) 修复 cron durable 语义（P2）

- `durable=false`：只保存到内存，不落盘。
- `durable=true`：写入 `.claude/scheduled_tasks.json`。
- 同步修复持久化写入策略（受限环境降级路径）。

对应文件：
- `claude_code/tools/cron/create.py`

### 5) 任务状态完成事件完善（可靠性增强）

- 任务完成/失败/超时/取消时，补齐 `task.set_completed()`，避免等待方挂起。
- 修复 `create_bash_task` 中 `description` 参数冲突。

对应文件：
- `claude_code/tasks/manager.py`

### 6) Phase 1 首步：引入仓储抽象（可演进）

- 新增 `TaskRepository` 与默认 `create_file_task_repository()`。
- workflow tools 与 `/tasks` command 已通过仓储层访问任务存储。
- 为未来替换 Redis/MySQL backend 提供稳定边界。

对应文件：
- `claude_code/tasks/repository.py`（新增）
- `claude_code/tasks/__init__.py`
- `claude_code/tools/workflow/task_create.py`
- `claude_code/tools/workflow/task_get.py`
- `claude_code/tools/workflow/task_list.py`
- `claude_code/tools/workflow/task_update.py`
- `claude_code/commands/tasks/__init__.py`

---

## 回归验证

新增测试：
- `tests/test_tasks_middleware_runtime.py`
  - `TaskControl` 工具链单例与输出行为验证
  - legacy schema 自动迁移验证
  - 并发写场景下无丢更新验证
  - `cron_create durable` 语义验证
  - `/tasks` command 统一 schema 验证

测试结果：
- `python -m pytest tests -q`
- 结果：`73 passed`

---

## 下一迭代（继续执行）

1. 引入 `TaskQueue` 抽象（`InMemoryTaskQueue` 默认实现）。
2. 将后台任务调度从 `TaskManager` 内部结构逐步转向 `TaskQueue + TaskRepository` 协作。
3. 增加状态机约束与幂等键（为 Redis/MySQL 双后端做准备）。
4. 增加观察指标埋点（队列积压、重试、失败率、超时率）。

---

## 增量迭代（本轮追加）

### 7) TaskQueue 抽象接入 TaskManager（Phase 1 持续）

- 新增 `TaskQueue` 接口与默认 `InMemoryTaskQueue`。
- 新增 `QueueItem` 队列项模型。
- `TaskManager` 启动任务改为经 `TaskQueue` 分发（当前仍为进程内实现）。

对应文件：
- `claude_code/tasks/queue.py`（新增）
- `claude_code/tasks/manager.py`
- `claude_code/tasks/__init__.py`

### 8) 任务状态机约束与统计（Phase 1 持续）

- 新增 `TaskStateTransitionError`。
- 增加状态流转校验，禁止非法流转（如非 `PENDING` 状态再次 `start`）。
- `start_task` 强制要求 `executor`，避免任务进入 `RUNNING` 后悬挂。
- 增加 `get_stats()`，输出创建、入队、启动、完成、失败、取消、超时、队列长度等统计。
- `cancel_task` 对已终态任务返回 `False`，避免状态污染。

对应文件：
- `claude_code/tasks/manager.py`

### 9) 追加回归测试

- 新增 `tests/test_tasks_manager_runtime.py`：
  - `start_task` 无 executor 拒绝
  - 非法状态流转拒绝
  - 已完成任务取消行为
  - 生命周期统计计数

测试结果更新：
- `python -m pytest tests -q`
- 结果：`77 passed`

---

## 增量迭代（继续追加）

### 10) Queue + RuntimeRepository 协同（Phase 1 关键里程碑）

- `TaskManager` 增加可插拔 `runtime_repository`（`RuntimeTaskRepository`）。
- 任务创建/启动/完成/失败/超时/取消均同步持久化运行态快照。
- `clear_completed()` 同步清理持久化运行态记录。
- 新增文件实现 `FileRuntimeTaskRepository`，默认存储：`.claude/runtime_tasks.json`。

对应文件：
- `claude_code/tasks/repository.py`
- `claude_code/tasks/manager.py`
- `claude_code/tasks/__init__.py`

### 11) 幂等能力（Idempotency）初版

- `create_bash_task` / `create_agent_task` 支持 `idempotency_key`。
- 相同 key 重复创建返回同一任务，避免重复入队与重复执行。
- 增加 manager 侧幂等索引清理逻辑（任务清理后自动回收 key）。

对应文件：
- `claude_code/tasks/manager.py`

### 12) 调度解耦优化

- 启动流程改为：`enqueue -> dispatch`，引入 `_pending_executors`，队列项只保留 `task_id`。
- 该结构为未来“远端 Queue 仅传递任务标识，执行逻辑由 worker 侧解析”做准备。

对应文件：
- `claude_code/tasks/manager.py`

### 13) 回归测试补强

- 在原有 `test_tasks_manager_runtime.py` 基础上新增覆盖：
  - 幂等 key 复用行为
  - runtime repository 生命周期持久化行为

测试结果更新：
- `python -m pytest tests -q`
- 结果：`79 passed`

---

## 增量迭代（继续追加 2）

### 14) 运行态恢复（Recovery）能力接入

- `TaskManager` 启动时可从 `RuntimeTaskRepository` 自动恢复任务快照。
- 重启时处于 `PENDING/RUNNING` 的任务，统一标记为 `FAILED` 并写回仓储，避免悬挂状态。
- 运行态统计新增 `recovered` 计数，便于观测重启恢复规模。

对应文件：
- `claude_code/tasks/manager.py`

### 15) 反序列化兼容修复

- 修复 `create_task_from_dict()` 在 bash/agent 场景下 `description` 参数冲突风险。
- 同步增强 `error/is_backgrounded/metadata/tags/parent_id` 字段恢复能力。

对应文件：
- `claude_code/tasks/types.py`

### 16) 持久化管理器工厂

- 新增 `create_persistent_task_manager(working_directory)` 工厂，快速创建“带运行态文件仓储”的管理器实例。

对应文件：
- `claude_code/tasks/manager.py`
- `claude_code/tasks/__init__.py`

### 17) 回归测试追加

- `test_create_task_from_dict_handles_bash_description`
- `test_manager_recovers_inflight_task_as_failed`

对应文件：
- `tests/test_tasks_manager_runtime.py`

测试结果更新：
- `python -m pytest tests -q`
- 结果：`81 passed`

---

## 增量迭代（继续追加 3）

### 18) Backend 契约测试基线（为 Redis/MySQL 接入做准备）

- 新增 `TaskQueue` 契约测试：
  - FIFO 顺序保证
  - timeout 语义（超时返回 `None`）
- 新增 `RuntimeTaskRepository` 契约测试：
  - upsert/get/delete 的最小行为闭环

对应文件：
- `tests/test_tasks_backend_contract.py`

测试结果更新：
- `python -m pytest tests -q`
- 结果：`84 passed`

---

## 增量迭代（继续追加 4）

### 19) Backend Factory（后端选择入口）

- 新增 `tasks/factory.py`，集中管理中间件后端构建：
  - `create_task_queue()`：当前支持 `memory`，预留 `redis`（未接入时明确报错）
  - `create_runtime_repository()`：支持 `file/none`
  - `create_task_manager(TaskBackendConfig)`：统一构建 manager
- 该入口用于后续灰度切换 backend（memory/file -> redis/mysql）时减少改动面。

对应文件：
- `claude_code/tasks/factory.py`
- `claude_code/tasks/__init__.py`

### 20) Factory 回归测试

- 新增工厂测试，覆盖：
  - memory queue 创建
  - redis backend 未接入提示
  - manager + runtime repo 构建

对应文件：
- `tests/test_tasks_factory_runtime.py`

测试结果更新：
- `python -m pytest tests -q`
- 结果：`87 passed`

---

## 增量迭代（继续追加 5）

### 21) 任务可观测埋点补齐（队列积压/重试率/失败率/超时率）

- `TaskManager.start_task()` 新增可选重试参数：
  - `max_retries`（默认 `0`）
  - `retry_delay`（默认 `0.0`）
- 失败/超时场景支持自动重试回队列（受状态机约束，`RUNNING -> PENDING` 仅用于内部重试）。
- `get_stats()` 增强输出：
  - `queue_backlog`（`queue_size + pending_executors`）
  - `failure_rate` / `timeout_rate` / `retry_rate`
  - `queue_lag_avg_ms` / `queue_lag_p95_ms`
  - `task_exec_avg_ms` / `task_exec_p95_ms`
- 增加重试生命周期事件 `retrying`，补齐执行过程可观测性。

对应文件：
- `claude_code/tasks/manager.py`

### 22) 队列超时语义修复（避免派发饥饿）

- 修复 `InMemoryTaskQueue.dequeue(timeout=0)` 行为：
  - 改为非阻塞 `get_nowait()` 语义
  - 避免 `TaskManager` 在“可派发轮询”时误判超时，导致任务不启动

对应文件：
- `claude_code/tasks/queue.py`

### 23) 回归测试补强

- 新增管理器运行时测试覆盖：
  - 重试策略生效与成功重试路径
  - 失败率/超时率观测指标输出
- 新增队列契约测试覆盖：
  - `dequeue(timeout=0)` 非阻塞语义（空队列返回 `None`，有数据时立即返回）

对应文件：
- `tests/test_tasks_manager_runtime.py`

测试结果更新：
- `python -m pytest -c pytest.ini tests -q`
- 结果：`90 passed`
