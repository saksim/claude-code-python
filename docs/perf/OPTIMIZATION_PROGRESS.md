# Performance Optimization Progress

更新时间：2026-04-16

## 已完成（当前迭代）

1. `P0` 可运行性恢复：
   - 修复 8 个语法级阻塞文件。
   - 修复工具导入链阻塞问题。
   - `import claude_code.main` 验证通过。
2. 测试基线稳定：
   - `BashTool` 增加受限环境兼容回退。
   - 测试状态：`48 passed`。
3. 测量体系落地：
   - 新增 `scripts/check_syntax.py`（只读语法门禁）。
   - 新增 `scripts/perf/run_baseline.py`（统一基线采样）。
   - 新增 `tests/perf/test_perf_smoke.py`（性能 smoke）。
4. 启动性能优化：
   - `claude_code/__init__.py` 懒加载导出。
   - `claude_code/tools/__init__.py` 懒加载导出。
   - 本地基线启动时延从约 `1259 ms` 收敛到约 `1109 ms`。
5. 工具热路径优化：
   - `grep`：include 匹配改为 `fnmatch`，减少错误过滤开销。
   - `glob`：改为 `iglob` 流式遍历，避免大仓库一次性物化全量结果。

## 当前基线

1. 数据文件：`docs/perf/baseline_v1.json`
2. 摘要文档：`docs/perf/BASELINE_V1.md`

关键指标：

1. Startup wall time：`1109.38 ms`
2. QueryEngine p95：`0.071 ms`
3. ReadTool p95：`0.595 ms`
4. GrepTool p95：`27.663 ms`
5. GlobTool p95：`13.003 ms`

## 风险与处理

1. 部分受限环境对删除临时文件权限严格，导致历史 `.claude/perf_tmp` 无法自动清理。
2. 已将 `.claude/perf_tmp/` 加入 `.gitignore`，并将基线脚本默认临时目录切换到系统 temp + 失败回退策略，避免继续污染仓库。

## 下一步（高 ROI）

1. 扩展端到端场景压测（长会话/并发任务/大仓库）。
2. 增加 baseline diff 与回归阈值报警。
3. 将语法门禁、perf smoke、baseline 融入 CI。
4. 继续下探启动链路重依赖，进一步压缩 cold-start。
