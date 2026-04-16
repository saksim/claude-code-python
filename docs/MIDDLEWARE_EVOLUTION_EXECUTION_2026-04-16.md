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
