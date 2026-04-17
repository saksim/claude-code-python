# Docs Index

`docs/` 目录现在按“当前主文档”和“历史文档”两层拆分：

- `current/`：当前仍应优先阅读、可代表现状的文档
- `history/`：历史评审、修复方案、阶段性计划和过程记录

## current

- `current/architecture/ARCHITECTURE_EVALUATION_2026-04-16.md`
  当前架构状态与综合评测结论
- `current/middleware/MIDDLEWARE_EVOLUTION_ASSESSMENT_2026-04-16.md`
  当前任务/中间件演进判断与决策依据
- `current/middleware/MIDDLEWARE_EVOLUTION_EXECUTION_2026-04-16.md`
  当前任务/中间件落地进展
- `current/performance/PERFORMANCE_ONE_PAGER.md`
  当前性能状态的一页纸摘要
- `current/performance/BASELINE_V1.md`
  当前性能基线摘要
- `current/performance/baseline_v1.json`
  当前性能原始基线数据
- `current/reference/AGENT.MD`
  Agent 系统完整手册
- `current/reference/MCP.md`
  MCP 使用手册

## history

- `history/architecture/ARCHITECTURE_REVIEW.md`
  首轮架构问题盘点
- `history/architecture/FIX_PROPOSALS.md`
  历史修复方案与备选实现
- `history/performance/PERFORMANCE_TOP_TIER_EVALUATION_PLAN.md`
  性能阶段计划
- `history/performance/PERFORMANCE_OPTIMIZATION_REPORT.md`
  性能优化细节报告
- `history/performance/OPTIMIZATION_PROGRESS.md`
  性能阶段进度记录

## 维护规则

1. 新文档默认先判断是 `current` 还是 `history`，不要直接平铺到 `docs/` 根目录。
2. 同一主题优先更新现有主文档，而不是新建平行文档。
3. 带日期的评估/执行文档如果已被新文档取代，应降级到 `history/`。
