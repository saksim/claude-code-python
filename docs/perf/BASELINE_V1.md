# Performance Baseline V1

Date (UTC): `2026-04-16T07:49:59.935167+00:00`  
Interpreter: `D:/code_environment/anaconda_all_css/py311/python.exe`  
Source: [baseline_v1.json](/D:/download/gaming/new_program/claude-code-python/docs/perf/baseline_v1.json)

## Scope

1. Read-only syntax health scan (`claude_code/**/*.py`)
2. Startup import benchmark (`import claude_code.main`)
3. Stubbed QueryEngine single-turn benchmark (no external API)
4. File tool micro-benchmarks (`read`, `grep`, `glob`) on generated dataset

## Key Metrics

1. Syntax errors: `0 / 204` files
2. Startup wall time: `1109.38 ms`
3. `QueryEngine` single turn (`p95`): `0.071 ms`
4. `ReadTool` (`p95`): `0.595 ms`
5. `GrepTool` (`p95`): `27.663 ms`
6. `GlobTool` (`p95`): `13.003 ms`

## Interpretation

1. `P0` runnable baseline is restored (syntax + import + tests all green).
2. Startup import remains the highest coarse-grain latency bucket, but this run is already faster than the pre-lazy-load baseline.
3. Tool-level baseline indicates `grep` and `glob` are the main local hot paths for next optimization rounds.

## Reproduce

```powershell
# syntax guardrail
& 'D:\code_environment\anaconda_all_css\py311\python.exe' scripts/check_syntax.py --root claude_code

# full baseline snapshot
& 'D:\code_environment\anaconda_all_css\py311\python.exe' scripts/perf/run_baseline.py `
  --project-root . `
  --iterations 20 `
  --output docs/perf/baseline_v1.json
```
