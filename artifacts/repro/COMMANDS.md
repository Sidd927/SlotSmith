# Reproduction commands (audit, 10 Oct 2026)

```bash
zsh scripts/repro_clean.sh                       # clean copy + fresh venv: pytest + benchmark x2
.venv/bin/python scripts/audit_ffd_exact.py      # exhaustive allocator vs exact CP-SAT (≈3 min)
.venv/bin/python scripts/audit_lb_gap.py         # benchmark instances vs exact per-group minimum
.venv/bin/python scripts/audit_edge_cases.py     # capacity / failure-path edge cases
```
Outputs: `artifacts/repro/{environment.txt,pytest.log,benchmark_clean_run{1,2}.log,benchmarks_clean_run{1,2}.json}`,
`artifacts/audit/*.log|json`.
