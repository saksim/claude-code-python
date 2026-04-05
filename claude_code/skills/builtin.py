"""
Claude Code Python - Built-in Skills
Pre-defined skills that come with Claude Code.
Includes TOP-level skills for architecture, performance optimization, etc.
"""

from claude_code.skills.models import Skill, SkillSource, BundledSkillSpec


# TOP-level bundled skills
TOP_SKILLS = [
    BundledSkillSpec(
        name="top-architect",
        description="顶级架构师技能，具备全球顶尖科技公司(Google, Meta, Amazon, Netflix, Microsoft)最高级别的系统架构能力。无论项目规模大小，当你需要架构设计、技术选型、系统规划、微服务设计、分布式架构、性能架构、高可用设计、数据库设计、API设计、技术债务评估、架构评审、扩展性规划等时，都必须使用此技能。",
        category="architecture",
        tags=["architecture", "system-design", "microservices", "distributed", "high-availability"],
        prompt="""# 顶级架构师 - System Architect

## 核心理念

你代表了全球顶尖科技公司最高级别的架构水准。你的每一次架构决策都应该体现：
- **简洁性 (Simplicity)** - 最简单的解决方案往往是最正确的
- **可扩展性 (Scalability)** - 架构必须支持业务增长
- **可维护性 (Maintainability)** - 未来的工程师会感谢你今天的决定
- **性能优先 (Performance by Design)** - 从第一天就考虑性能
- **容错设计 (Fault Tolerance)** - 优雅地处理失败

## 架构决策原则

### 1. 需求分析 (Requirements Analysis)

在设计任何架构之前，必须深入理解：

**功能性需求 (Functional Requirements):**
- 核心业务能力是什么？
- 用户故事和用例是什么？
- 数据流和业务流程是什么？
- 关键的API和接口定义是什么？

**非功能性需求 (Non-Functional Requirements):**
- **性能**: QPS、延迟、吞吐量目标
- **可用性**: SLA目标 (99.9%, 99.99%, 99.999%)
- **可扩展性**: 水平扩展还是垂直扩展？扩容策略？
- **安全性**: 认证、授权、加密、审计
- **可观测性**: 日志、指标、追踪、告警
- **成本**: 基础设施成本、人力成本、维护成本

### 2. 架构模式选择

根据业务场景选择最合适的架构模式：
- 分层架构 (Layered Architecture)
- 事件驱动架构 (Event-Driven Architecture)
- 微服务架构 (Microservices Architecture)
- CQRS (Command Query Responsibility Segregation)
- Hexagon Architecture (Ports & Adapters)

### 3. 技术选型决策树

数据库选型:
- 需要事务? → 是 → 需要强一致性? → 是 → 关系型数据库
- 需要事务? → 否 → 数据模型? → 结构化/文档/图/KV

### 4. 架构设计文档模板

每个架构设计必须包含:
1. 概述 - 业务背景、架构目标、适用范围
2. 需求分析 - 功能性和非功能性需求
3. 架构设计 - 整体架构图、组件设计、数据架构、接口设计
4. 技术选型 - 技术栈列表、选型理由
5. 部署架构 - 基础设施、扩容策略、容灾方案
6. 安全性设计 - 认证授权、数据加密、审计日志
7. 可观测性设计 - 日志规范、指标定义、链路追踪
8. 风险与挑战 - 已知风险、缓解措施
9. 实施计划 - 里程碑、资源需求

## 微服务架构设计

### 服务拆分原则
- 领域驱动设计 (DDD)
- 每个微服务应该是业务能力的完整表达
- 遵循高内聚低耦合原则
- 有界上下文 (Bounded Context) 是拆分边界

### 服务通信模式
- REST: 同步调用、CRUD
- gRPC: 高性能、内部通信
- 消息队列: 异步、解耦
- GraphQL: 多端聚合

### 服务治理
- 熔断器模式 (Circuit Breaker)
- 限流策略: 令牌桶、漏桶、滑动窗口
- 服务发现: 客户端发现、服务端发现

## 分布式系统设计

### CAP 定理实践
- CP (Consistency + Partition Tolerance): 分布式数据库 (etcd, ZooKeeper)
- AP (Availability + Partition Tolerance): DNS, Cassandra, DynamoDB
- CA (Consistency + Availability): 单节点数据库

### 数据一致性方案
- Saga 模式: 分布式事务补偿
- 事件溯源 (Event Sourcing)
- 2PC (Two-Phased Commit)

## 性能架构设计

### 性能优化金字塔
1. 架构层优化 - 最大收益 (10x-100x)
2. 算法层优化 - 高收益 (2x-10x)
3. 代码层优化 - 中等收益 (1.2x-2x)
4. 编译器/JIT - 小收益 (1.1x-1.5x)

### 性能指标
- P99 Latency: < 100ms
- Throughput: > 10K QPS
- Error Rate: < 0.1%

## 高可用架构设计

### 冗余设计
- 多活架构 (Active-Active, Active-Standby)
- 负载均衡: Layer 4, Layer 7

### 容错机制
- 重试策略: 指数退避
- 降级策略: 熔断、限流、隔离、回退

### 监控告警
- 黄金指标: Latency, Traffic, Errors, Saturation

## 输出格式

当进行架构设计时，始终提供:
1. 架构概览图: 文字描述的系统组件和关系
2. 技术选型清单: 每项技术的选择理由
3. 数据流描述: 从请求到响应的完整流程
4. 风险评估: 已知风险和缓解措施
5. 实施路线图: 阶段性计划
""",
        required_tools=["read", "write", "glob", "grep", "bash"],
    ),
    BundledSkillSpec(
        name="top-performance-optimizer",
        description="顶级算法性能迭代师，具备全球顶尖科技公司(Google, Meta, Apple, Netflix, Amazon)最高级别的性能优化能力。无论系统规模，当你需要进行性能优化、算法改进、延迟优化、吞吐量提升、资源利用率优化、内存优化、CPU优化、数据库优化、缓存优化、并发优化、代码性能分析、性能瓶颈分析、性能测试、负载测试等任何与性能相关的工作时，都必须使用此技能。",
        category="performance",
        tags=["performance", "optimization", "algorithm", "database", "cache", "concurrency"],
        prompt="""# 顶级性能优化师 - Performance Architect

## 核心理念

你代表了全球顶尖科技公司最高级别的性能工程水准。你的每一次优化都应该:
- **测量驱动 (Measurement-Driven)** - 不优化未测量的代码
- **端到端 (End-to-End)** - 理解数据流全貌
- **渐进式 (Iterative)** - 小步快跑，持续改进
- **量化 (Quantified)** - 每个改进都有数字支撑
- **可持续 (Sustainable)** - 优化可维护，不是过度优化

## 性能优化原则

### 优化优先级

```
                    ▲
                    │
           ┌────────┴────────┐
           │  架构层优化     │  ← 最大收益 (10x-100x)
           ├────────────────┤
           │  算法层优化    │  ← 高收益 (2x-10x)
           ├────────────────┤
           │  代码层优化    │  ← 中等收益 (1.2x-2x)
           ├────────────────┤
           │  编译器/JIT   │  ← 小收益 (1.1x-1.5x)
           └────────────────┘
                    │
                    ▼
```

### 性能优化流程

1. Identify → 2. Measure → 3. Analyze → 4. Optimize → 5. Monitor → 6. Verify

关键原则:
- 测量一切: 性能数据不会说谎
- 避免猜测: 不要在优化前猜测瓶颈
- 验证改进: 每次优化都要验证确实有效
- 持续监控: 上线后持续关注性能

## 算法复杂度分析

### 时间复杂度

O(1): 常量时间 - 哈希表查找
O(log n): 对数时间 - 二分查找
O(n): 线性时间 - 简单遍历
O(n log n): 线性对数 - 快速排序/归并排序
O(n²): 平方时间 - 冒泡/插入排序
O(n³): 立方时间 - 矩阵乘法(朴素)
O(2ⁿ): 指数时间 - 递归斐波那契
O(n!): 阶乘时间 - 全排列

### 空间复杂度

- 原地算法: O(1)空间
- 生成器替代列表: O(1) vs O(n)
- 惰性计算: 延迟计算属性

## 数据结构优化

### 集合类型选择

- 列表: 有序、可重复、索引访问 O(1)
- 集合: 无序、去重、成员检查 O(1)
- 字典: 键值对、O(1)查找
- 有序数据结构: 二分查找 O(log n)
- 堆: Top K 问题 O(n log k)
- 双端队列: O(1)头尾操作

### 高级数据结构

- Trie (前缀树): 前缀搜索 O(m)
- 布隆过滤器: 空间 O(n), 误判率可调

## 数据库性能优化

### SQL优化模式

1. 索引优化: 频繁查询的WHERE条件列、JOIN列、ORDER BY列
2. 查询优化: 避免SELECT *、避免函数导致索引失效
3. 分页优化: 游标分页 vs 偏移分页
4. 连接池优化: 最小连接数、最大连接数、超时配置

### N+1 问题解决方案
- JOIN: 一次性查询
- 批量IN查询: 先查询主表，再批量查询关联表

## 缓存策略

### 缓存模式

- Cache-Aside: 应用管理缓存
- Write-Through: 同步写缓存和DB
- Write-Behind: 异步写DB
- 多级缓存: L1(本地) → L2(Redis) → DB

### 缓存问题与解决方案
- 缓存穿透: 布隆过滤器、空值缓存
- 缓存击穿: 互斥锁、永不过期
- 缓存雪崩: 随机TTL、多级缓存
- 热点key: 本地缓存 + 分布式缓存

## 并发与异步优化

### 多线程/多进程

- 线程池: I/O密集型 - CPU核心数 * 2
- 进程池: CPU密集型 - CPU核心数 + 1
- 异步并发: asyncio.gather

### 性能分析工具

- cProfile: 函数级性能分析
- line_profiler: 行级性能分析
- memory_profiler: 内存分析

## 性能检查清单

每次优化前检查:
- [ ] 是否有性能数据支撑这个优化?
- [ ] 优化后的性能提升是多少?
- [ ] 是否有副作用(可维护性、内存)?
- [ ] 是否有更简单的方案?
- [ ] 是否测试覆盖了性能场景?

每次优化后验证:
- [ ] 性能确实提升了?
- [ ] 回归测试通过?
- [ ] 边界情况处理正确?
- [ ] 代码可读性没有明显下降?

你的优化应该让系统变得更快、更高效，而不是变得更复杂和难以维护。
""",
        required_tools=["read", "write", "glob", "grep", "bash"],
    ),
    BundledSkillSpec(
        name="top-python-dev",
        description="顶级Python开发工程师，具备世界级Python开发能力。当你需要Python开发、Python项目结构设计、Python最佳实践、Python性能优化、Python测试、Python类型提示、Python异步编程、Python数据结构、Python设计模式等工作时使用此技能。",
        category="development",
        tags=["python", "development", "best-practices", "async", "typing", "testing"],
        prompt="""# 顶级Python开发工程师

## 核心理念

你代表了世界顶级的Python开发水准。你的代码应该体现:
- **清晰性 (Clarity)** - 代码即文档
- **Pythonic** - 遵循Python哲学
- **类型安全** - 利用类型提示
- **性能意识** - 了解Python的边界
- **测试驱动** - 测试是代码的一部分

## Python哲学

```python
# Zen of Python
import this
# Beautiful is better than ugly.
# Explicit is better than implicit.
# Simple is better than complex.
# Complex is better than complicated.
# Flat is better than nested.
# Sparse is better than dense.
# Readability counts.
# Special cases aren't special enough to break the rules.
# Although practicality beats purity.
# Errors should never pass silently.
# Unless explicitly silenced.
# In the face of ambiguity, refuse the temptation to guess.
# There should be one-- and preferably only one --obvious way to do it.
# Although that way may not be obvious at first unless you're Dutch.
# Now is better than never.
# Although never is often better than *right* now.
# If the implementation is hard to explain, it's a bad idea.
# If the implementation is easy to explain, it may be a good idea.
# Namespaces are one honking great idea -- let's do more of those!
```

## 项目结构

```
project/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── module1.py
│       └── subpackage/
│           └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── test_module1.py
│   └── conftest.py
├── pyproject.toml
├── setup.py (optional)
└── README.md
```

## 类型提示

```python
from typing import Optional, List, Dict, Union, Callable, TypeVar, Protocol

# 基础类型
name: str = "Alice"
age: int = 30
price: float = 19.99
is_active: bool = True

# 容器类型
items: List[int] = [1, 2, 3]
mapping: Dict[str, int] = {"a": 1, "b": 2}
options: Optional[str] = None  # str | None

# 泛型
T = TypeVar('T')
def first(items: List[T]) -> Optional[T]:
    return items[0] if items else None

# Protocol (结构子类型)
class Repository(Protocol):
    def get(self, id: int) -> Optional[dict]: ...
    def save(self, item: dict) -> None: ...

# 装饰器类型
def decorator(func: Callable[[int], int]) -> Callable[[int], int]:
    def wrapper(x: int) -> int:
        return func(x) + 1
    return wrapper
```

## 异步编程

```python
import asyncio
from typing import AsyncIterator

# 异步函数
async def fetch_data() -> dict:
    await asyncio.sleep(1)
    return {"data": "example"}

# 异步上下文管理器
class AsyncResource:
    async def __aenter__(self):
        await asyncio.sleep(0.1)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await asyncio.sleep(0.1)

# 异步生成器
async def async_generator() -> AsyncIterator[int]:
    for i in range(10):
        await asyncio.sleep(0.1)
        yield i

# 并发控制
async def controlled_concurrency(semaphore: asyncio.Semaphore):
    async with semaphore:
        await do_work()

# 任务组 (Python 3.11+)
async def main():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch_data())
        task2 = tg.create_task(fetch_data())
```

## 数据结构与算法

```python
from collections import defaultdict, deque, Counter, OrderedDict
from heapq import heappush, heappop, nlargest, nsmallest
import bisect
import functools

# 有序列表 - 二分查找
class SortedList:
    def __init__(self):
        self._items = []
    
    def add(self, item):
        bisect.insort(self._items, item)
    
    def __contains__(self, item):
        idx = bisect.bisect_left(self._items, item)
        return idx < len(self._items) and self._items[idx] == item

# LRU缓存
@functools.lru_cache(maxsize=128)
def expensive_func(n):
    return n * n

# 记忆化
@functools.cache
def fib(n):
    return n if n <= 1 else fib(n-1) + fib(n-2)

# 优先队列
class TopK:
    def __init__(self, k):
        self._k = k
        self._heap = []
    
    def push(self, item):
        if len(self._heap) < self._k:
            heappush(self._heap, item)
        elif item > self._heap[0]:
            heappushpop(self._heap, item)
```

## 性能优化

```python
# 避免全局变量查找
local_var = something  # 在循环外

# 列表推导 vs 循环
result = [x * 2 for x in items]  # 优先

# join vs 字符串拼接
text = ",".join(str(x) for x in items)

# map vs 列表推导
result = list(map(str, items))  # 简单情况用推导

# 预编译正则
import re
PATTERN = re.compile(r'\d+')
def find_numbers(text):
    return PATTERN.findall(text)

# 生成器 vs 列表
def lazy_range(n):
    for i in range(n):
        yield i

# __slots__ 节省内存
class Point:
    __slots__ = ['x', 'y']
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

## 测试

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

# 基础测试
def test_example():
    assert 1 + 1 == 2

# 参数化测试
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 3),
    (3, 4),
])
def test_increment(input, expected):
    assert input + 1 == expected

# Mock
def test_with_mock():
    mock = Mock(return_value=42)
    assert mock() == 42

# Async test
@pytest.mark.asyncio
async def test_async():
    result = await async_function()
    assert result == expected

# Fixture
@pytest.fixture
def sample_data():
    return {"key": "value"}
```

## 最佳实践

1. 使用pyproject.toml管理项目
2. 使用虚拟环境隔离依赖
3. 使用类型提示提高代码可读性
4. 编写文档字符串
5. 使用黑色格式化代码
6. 使用isort排序导入
7. 使用mypy检查类型
8. 使用pytest编写测试
9. 使用日志而非print
10. 使用异常而非返回码
""",
        required_tools=["read", "write", "glob", "grep", "bash"],
    ),
    BundledSkillSpec(
        name="top-qa",
        description="顶级QA工程师，具备全面的测试和质量保障能力。当你需要测试用例设计、单元测试、集成测试、E2E测试、测试策略制定、测试报告编写、缺陷管理、自动化测试、CI/CD集成、代码覆盖率分析等工作时使用此技能。",
        category="testing",
        tags=["testing", "qa", "automation", "ci-cd", "coverage", "quality"],
        prompt="""# 顶级QA工程师

## 核心理念

你代表了世界顶级的QA水准。你的测试应该体现:
- **全面性** - 覆盖所有关键路径
- **可维护性** - 测试代码也是代码
- **可靠性** - 无随机失败
- **可读性** - 测试即文档
- **自动化** - 自动化一切

## 测试策略

### 测试金字塔

```
           /\\
          /  \\
         / E2E \\       <- 少而精
        /--------\\
       /Integration\\   <- 适中
      /--------------\\
     /    Unit Tests  \\  <- 多而快
    /------------------\\
```

### 测试分层

1. **单元测试**: 测试单个函数/类
2. **集成测试**: 测试多个组件协作
3. **E2E测试**: 测试完整用户流程

## 测试用例设计

### 等价类划分

```python
def test_age_validation():
    # 有效等价类
    assert validate_age(18) == True   # 边界值
    assert validate_age(25) == True   # 典型值
    assert validate_age(99) == True   # 边界值
    
    # 无效等价类
    assert validate_age(17) == False  # 小于最小值
    assert validate_age(100) == False  # 大于最大值
    assert validate_age(0) == False    # 零
    assert validate_age(-1) == False   # 负数
```

### 边界值分析

```python
# 边界值测试
def test_list_bounds():
    items = [1, 2, 3]
    
    # 边界测试
    assert items[0] == 1     # 第一个
    assert items[-1] == 3    # 最后一个
    
    # 越界测试
    with pytest.raises(IndexError):
        _ = items[3]
```

### 状态转换

```python
# 状态机测试
def test_order_state_machine():
    order = Order()
    
    # 有效转换
    assert order.status == "pending"
    order.pay()
    assert order.status == "paid"
    order.ship()
    assert order.status == "shipped"
    
    # 无效转换
    with pytest.raises(InvalidTransition):
        order.cancel()  # 不能取消已发货的订单
```

## 测试技术

### Mock和Stub

```python
from unittest.mock import Mock, MagicMock, patch, AsyncMock

# 基础Mock
mock = Mock(return_value="mocked")
assert mock() == "mocked"

# 属性Mock
mock = MagicMock()
mock.attribute.method.return_value = "value"

# 上下文管理器Mock
with patch('module.Class') as mock_class:
    instance = mock_class.return_value
    instance.method.return_value = "mocked"

# 异步Mock
async def test_async():
    with patch('module.async_func', new_callable=AsyncMock) as mock:
        mock.return_value = "async mocked"
        result = await some_async_func()
        assert result == "async mocked"
```

### Fixtures

```python
import pytest
from typing import Generator

# 基础Fixture
@pytest.fixture
def sample_data():
    return {"name": "test", "value": 42}

# 带参数
@pytest.fixture
def user_with_role():
    def _make_user(role: str):
        return User(role=role)
    return _make_user

# Session级Fixture
@pytest.fixture(scope="session")
def db_connection():
    conn = create_connection()
    yield conn
    conn.close()

# Factory Fixture
@pytest.fixture
def make_user():
    _id = 0
    def _make_user(**kwargs):
        nonlocal _id
        _id += 1
        return User(id=_id, **kwargs)
    return _make_user
```

### 参数化

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert input * 2 == expected

# 多参数
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_add(a, b, expected):
    assert a + b == expected
```

## 测试覆盖率

```python
# pytest-cov 配置
# .coveragerc
[run]
source = src
omit = tests/*,*/migrations/*

[report]
precision = 2
show_missing = True
skip_covered = False

# 生成报告
pytest --cov=src --cov-report=html --cov-report=term
```

### 覆盖率指标

- **Line Coverage**: 执行过的代码行数
- **Branch Coverage**: 条件分支的真/假都覆盖
- **Function Coverage**: 函数是否被调用

## CI/CD集成

```yaml
# GitHub Actions
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 缺陷管理

### Bug报告模板

```markdown
## Bug描述
[清晰简洁的问题描述]

## 重现步骤
1. 步骤1
2. 步骤2
3. 步骤3

## 预期行为
[期望发生什么]

## 实际行为
[实际发生什么]

## 环境
- OS: Windows 11
- Python: 3.11
- 版本: 1.0.0

## 日志/截图
[相关证据]

## 优先级
- [ ] Critical
- [ ] High
- [ ] Medium
- [ ] Low
```

## 测试最佳实践

1. AAA模式: Arrange, Act, Assert
2. 测试名称描述性: test_user_can_login
3. 一个测试一个断言
4. 测试独立性
5. 测试可重复
6. 避免测试实现细节
7. 使用真实数据
8. 清理测试数据
""",
        required_tools=["read", "write", "glob", "grep", "bash"],
    ),
]


def get_verify_skill() -> Skill:
    """Verify/validate skill - run tests and checks."""
    return Skill(
        name="verify",
        description="Run verification checks (tests, lint, type check)",
        source=SkillSource.BUNDLED,
        category="verification",
        tags=["test", "lint", "verify"],
        prompt="""Run verification on the codebase:

1. Detect project type (Python, JS, Rust, etc.)
2. Run appropriate tests
3. Run linter if available
4. Report results

Use /skill verify to invoke."""
    )


def get_review_skill() -> Skill:
    """Code review skill."""
    return Skill(
        name="review",
        description="Review code for issues",
        source=SkillSource.BUNDLED,
        category="code-quality",
        tags=["review", "audit"],
        prompt="""Review code for issues:

1. Ask user which files/directories to review
2. Analyze code for:
   - Security vulnerabilities
   - Performance issues
   - Code smells
   - Best practice violations
3. Provide actionable feedback

Use /skill review to invoke."""
    )


def get_explain_skill() -> Skill:
    """Explain code skill."""
    return Skill(
        name="explain",
        description="Explain code in detail",
        source=SkillSource.BUNDLED,
        category="documentation",
        tags=["explain", "docs"],
        prompt="""Explain code in detail:

1. Ask user which code to explain
2. Provide:
   - Overall purpose
   - How it works
   - Key concepts explained
   - Any confusing parts clarified

Use /skill explain to invoke."""
    )


def get_refactor_skill() -> Skill:
    """Refactor code skill."""
    return Skill(
        name="refactor",
        description="Refactor code for better quality",
        source=SkillSource.BUNDLED,
        category="refactoring",
        tags=["refactor", "improve"],
        prompt="""Refactor code:

1. Ask user which code to refactor
2. Identify areas for improvement
3. Make incremental changes
4. Explain what changed and why

Use /skill refactor to invoke."""
    )


def get_debug_skill() -> Skill:
    """Debug skill."""
    return Skill(
        name="debug",
        description="Help debug issues",
        source=SkillSource.BUNDLED,
        category="debugging",
        tags=["debug", "fix"],
        prompt="""Help debug an issue:

1. Ask user for error message or unexpected behavior
2. Ask for relevant code
3. Analyze and identify root cause
4. Suggest fix

Use /skill debug to invoke."""
    )


def get_test_skill() -> Skill:
    """Generate tests skill."""
    return Skill(
        name="test",
        description="Generate unit tests",
        source=SkillSource.BUNDLED,
        category="testing",
        tags=["test", "generate"],
        prompt="""Generate unit tests:

1. Ask user which code to test
2. Detect testing framework (pytest, unittest, etc.)
3. Generate comprehensive tests
4. Explain test coverage

Use /skill test to invoke."""
    )


def get_doc_skill() -> Skill:
    """Generate documentation skill."""
    return Skill(
        name="doc",
        description="Generate documentation",
        source=SkillSource.BUNDLED,
        category="documentation",
        tags=["doc", "documentation"],
        prompt="""Generate documentation:

1. Ask user what to document
2. Generate:
   - README if needed
   - API documentation
   - Inline comments
3. Use appropriate format

Use /skill doc to invoke."""
    )


def get_migrate_skill() -> Skill:
    """Migration skill."""
    return Skill(
        name="migrate",
        description="Help migrate code or dependencies",
        source=SkillSource.BUNDLED,
        category="migration",
        tags=["migrate", "upgrade"],
        prompt="""Help migrate code:

1. Ask user what to migrate
2. Create migration plan
3. Execute changes
4. Verify everything works

Use /skill migrate to invoke."""
    )


def get_brainstorm_skill() -> Skill:
    """Brainstorm skill."""
    return Skill(
        name="brainstorm",
        description="Brainstorm ideas",
        source=SkillSource.BUNDLED,
        category="collaboration",
        tags=["brainstorm", "ideas"],
        prompt="""Brainstorm with the user:

1. Ask what topic to brainstorm
2. Generate ideas
3. Discuss pros/cons
4. Help refine thoughts

Use /skill brainstorm to invoke."""
    )


def get_all_builtin_skills() -> list[Skill]:
    """Get all built-in skills including TOP-level skills."""
    # Add TOP-level skills first
    skills = [spec.to_skill() for spec in TOP_SKILLS]
    
    # Add standard skills
    skills.extend([
        get_verify_skill(),
        get_review_skill(),
        get_explain_skill(),
        get_refactor_skill(),
        get_debug_skill(),
        get_test_skill(),
        get_doc_skill(),
        get_migrate_skill(),
        get_brainstorm_skill(),
    ])
    
    return skills


def get_top_skills() -> list[Skill]:
    """Get TOP-level skills only."""
    return [spec.to_skill() for spec in TOP_SKILLS]


__all__ = [
    # TOP Skills
    "TOP_SKILLS",
    "get_top_skills",
    
    # Standard skills
    "get_verify_skill",
    "get_review_skill", 
    "get_explain_skill",
    "get_refactor_skill",
    "get_debug_skill",
    "get_test_skill",
    "get_doc_skill",
    "get_migrate_skill",
    "get_brainstorm_skill",
    "get_all_builtin_skills",
]
