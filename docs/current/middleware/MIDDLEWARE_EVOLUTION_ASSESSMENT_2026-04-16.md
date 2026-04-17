# 中间件架构评估报告（任务队列方向）

- 项目：`claude-code-python`
- 评估日期：2026-04-16
- 评估视角：平台化中间件演进（任务队列 / 调度 / 状态存储）
- 评估结论先行：当前实现不是“数据库队列模型”，而是“进程内队列 + 文件持久化模型”。在单机 CLI 场景可用；在平台化、多实例、可恢复场景下风险较高。

---

## 1. 执行摘要

### 1.1 关键结论

1. 当前并未使用 Redis / MySQL / Kafka 作为任务队列中间件。
2. 现有任务模型分裂为两套：
   - 进程内任务：`TaskManager`（内存字典）。
   - 工作流任务：`.claude/tasks.json`（文件）。
3. 你担心的“数据库队列风险”本质上是“缺少专业队列中间件 + 文件并发一致性风险”。
4. 是否需要“完全使用 Redis+MySQL”：
   - **现在立即全量切换：不建议**（对当前仓库定位可能过度工程）。
   - **按平台化目标分阶段切换：建议**（先修一致性，再抽象，再替换 backend）。

### 1.2 当前风险评级

- P0（高）：控制工具与任务管理器实例不一致、字段访问不安全，导致控制面功能可失效。
- P1（中高）：`tasks.json` 数据结构在不同入口不一致，存在互相破坏风险。
- P1（中高）：文件读写无锁、非原子事务，不具备并发安全。
- P1（中高）：进程重启后运行中任务丢失，无法恢复。
- P2（中）：`durable` 语义与实现不一致（文档说不落盘，实际落盘）。
- P2（中）：任务/调度关键链路缺少测试覆盖。

---

## 2. 证据链（代码审计）

### 2.1 进程内任务队列（非数据库）

- `claude_code/tasks/manager.py:45`
  - `_tasks: dict[str, Task] = {}`（内存存储）
- `claude_code/tasks/manager.py:49`
  - `_running_tasks: dict[str, asyncio.Task] = {}`（内存运行态）
- `claude_code/tasks/manager.py:85`
  - `create_agent_task(...)` 仅创建对象并放入内存
- `claude_code/tasks/manager.py:107`
  - `start_task(...)` 依赖进程内 `asyncio.create_task`
- `claude_code/tasks/manager.py:305`
  - 通过 `get_instance()` 暴露单例

### 2.2 文件任务存储（workflow/command）

- `claude_code/tools/workflow/task_create.py:93`
  - 从 `tasks.json` 读取 list
- `claude_code/tools/workflow/task_create.py:106`
  - `tasks.append(task)`（list 结构）
- `claude_code/commands/tasks/__init__.py:95`
  - `for task_id, task in tasks.items()`（dict 结构）
- `claude_code/commands/tasks/__init__.py:123`
  - `tasks[task_id] = {...}`（dict 写入）

> 同一文件 `.claude/tasks.json` 在不同入口采用不同 schema（list vs dict）。

### 2.3 控制面工具风险

- `claude_code/tools/control/__init__.py:94`
  - `manager = TaskManager()`（未使用单例）
- `claude_code/tools/control/__init__.py:178`
  - `manager = TaskManager()`（再次新建实例）
- `claude_code/tools/control/__init__.py:184`
  - `output = task.output`（`Task` 并无该字段）
- `claude_code/tools/control/__init__.py:279`
  - `task.command`（并非所有任务类型具备）

### 2.4 调度 durable 语义不一致

- `claude_code/tools/cron/create.py:146`
  - 文档描述：`durable=false` 时“session-only，不写盘”
- `claude_code/tools/cron/create.py:189`
  - 实际总是读写 `.claude/scheduled_tasks.json`
- `claude_code/tools/cron/create.py:210`
  - 返回文案区分 durable，但实现未区分

### 2.5 中间件依赖现状

- `requirements.txt` 无 `redis` / `aioredis` / `mysqlclient` / `SQLAlchemy` 等队列/数据库运行依赖。

---

## 3. 当前模型的中间件合理性判断

## 3.1 适用场景（合理）

- 本地单机 CLI。
- 低并发、短生命周期任务。
- 容忍进程重启后丢失运行态。
- 对“至少一次投递/重试/死信”没有强约束。

## 3.2 非适用场景（不合理）

- 多实例部署（API 层和 worker 分离）。
- 需要任务可恢复（crash recovery）。
- 需要可观测队列语义（lag、DLQ、重试队列）。
- 需要任务幂等和严格状态机（防重、补偿）。

---

## 4. 风险分级与影响

## 4.1 P0：控制面可用性风险

- 现象：`task_stop/task_output/task_control_list` 可能拿不到真实任务状态或直接抛错。
- 根因：控制工具使用 `TaskManager()` 新实例，不是全局单例；并访问不稳定字段（`task.output` / `task.command`）。
- 影响：运维与控制链路失效，任务可观测性和可控性下降。

## 4.2 P1：任务数据模型分裂风险

- 现象：同一 `tasks.json` 文件被两套 schema 写入。
- 根因：workflow tools 采用 list，commands 采用 dict。
- 影响：互相读写时结构不兼容，可能触发运行时异常或数据破坏。

## 4.3 P1：文件并发一致性风险

- 现象：`read -> modify -> write` 无锁。
- 根因：未使用文件锁/原子写入/版本校验。
- 影响：并发操作下可能丢更新、写坏 JSON、状态回退。

## 4.4 P1：可靠性语义不足

- 现象：任务运行态仅在内存，重启即丢。
- 根因：无持久队列、无 lease/ack/retry。
- 影响：平台化后会出现“幽灵任务”“任务丢失”“状态不一致”。

## 4.5 P2：调度语义偏差

- 现象：`durable=false` 仍写磁盘。
- 影响：行为与用户预期不一致，增加排障成本。

## 4.6 P2：测试缺口

- 现象：`tests/` 中几乎无任务存储/控制链路测试。
- 影响：重构时高回归风险。

---

## 5. 需不需要“完全使用 Redis + MySQL”？

## 5.1 结论

- **不是“必须立刻完全切换”**，但如果目标是平台化（多实例 + 可恢复 + 可扩展），**最终建议采用 Redis + MySQL 的混合模型**。

## 5.2 决策矩阵

| 场景 | 推荐方案 | 结论 |
|---|---|---|
| 单机 CLI、低并发 | 内存 + 文件（先修一致性） | 可接受 |
| 单实例服务化、需基本可靠性 | MySQL 任务表 + 应用轮询（短期） | 可过渡 |
| 多实例平台、需恢复/重试/观测 | Redis 队列 + MySQL 状态/审计 | 推荐 |
| 超高吞吐（>10万QPS） | Kafka/Pulsar + MySQL | 长期演进 |

## 5.3 为什么不是“只用 MySQL 队列”

- MySQL 可做队列（`SELECT ... FOR UPDATE SKIP LOCKED`），但在高并发下会遭遇热点行竞争、轮询低效、延迟抖动。
- Redis 在短任务调度、延迟队列、消费组方面更适合承担“热路径队列”。
- MySQL 适合作为任务状态事实源（state store）和审计存储。

---

## 6. 推荐目标架构（平台向）

```text
API/Orchestrator
   |  (create task)
   v
MySQL(task_metadata, task_state, audit)
   |  (enqueue task_id)
   v
Redis(Stream/List/ZSet)
   |
Worker Pool (N instances)
   |-- claim + lease + heartbeat
   |-- idempotent execute
   |-- retry with backoff
   v
MySQL(state transition + result + error)
```

核心原则：

1. Redis 负责任务分发与短期调度。
2. MySQL 负责强一致状态、审计、查询。
3. 任务执行必须幂等（基于 `task_id` / `idempotency_key`）。
4. 状态机统一：`PENDING -> RUNNING -> SUCCEEDED/FAILED/DEAD_LETTER`。

---

## 7. 分阶段落地计划（建议）

## Phase 0（1-3 天）：先止血，不引入新中间件

目标：修复当前高风险缺陷，确保现有模型可用。

1. 控制工具统一使用 `TaskManager.get_instance()`。
2. `TaskOutputTool` 改为调用 `task.get_output()`。
3. `TaskControlListTool` 展示字段改为 `task.description`（兼容全部任务类型）。
4. 统一 `tasks.json` schema（建议 dict + `schema_version`）。
5. 文件写入改为原子写（临时文件 + replace）并加文件锁。
6. 修复 `cron_create durable` 语义与实现一致。
7. 增加最小测试：
   - schema 兼容测试
   - 并发写安全测试
   - task_control 工具链测试

## Phase 1（3-5 天）：抽象任务存储/队列接口

目标：为中间件替换做“低风险可逆”准备。

1. 抽象 `TaskRepository`（状态存储）与 `TaskQueue`（分发）。
2. 保留 `FileTaskRepository + InMemoryTaskQueue` 作为默认实现。
3. 完成接口契约测试（同一测试集跑不同 backend）。

## Phase 2（1-2 周）：引入 Redis + MySQL（可开关）

目标：平台化能力上线，但可回退。

1. 新增 `RedisTaskQueue`（ack/retry/delay/dead-letter）。
2. 新增 `MySQLTaskRepository`（状态机、结果、审计）。
3. feature flag 切换 backend（灰度发布）。
4. 增加观测指标：queue lag、retry rate、DLQ count、task SLA。

## Phase 3（持续）：稳定性与成本优化

1. 加入任务幂等键、去重窗口。
2. 增加 worker 自动扩缩容策略。
3. 增加高优先级队列与租户隔离。

---

## 8. 验收指标（上线门槛）

- 功能：任务状态转换正确率 = 100%。
- 可靠性：进程重启后任务恢复成功率 >= 99.9%。
- 性能：任务入队 P99 < 20ms；任务拉取 P99 < 50ms。
- 稳定性：重试风暴场景下无级联失败。
- 观测：必须可查看 backlog、consumer lag、DLQ。

---

## 9. 最终建议（给本项目）

1. 不建议“今天直接全量改成 Redis+MySQL”。
2. 建议先做 Phase 0/1，把模型收敛与接口抽象做好。
3. 若你们近期明确要做平台化（多实例/高可用/可恢复），再推进 Phase 2，上 Redis+MySQL 是合理且必要的。

---

## 10. 待你确认后可立即执行的改造清单

1. 修复 TaskControl 三个工具与 TaskManager 单例/字段兼容问题。
2. 统一 `.claude/tasks.json` schema 并提供一次性迁移逻辑。
3. 增加文件锁 + 原子写，避免并发损坏。
4. 修复 `cron_create durable` 行为。
5. 补齐回归测试。

> 以上 5 项可在不引入 Redis/MySQL 的前提下先完成，风险收益比最高。
