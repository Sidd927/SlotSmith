# Benchmark audit: final pitch deck (11 Oct 2026)

All numbers are on **synthetic data** produced by `src/slotsmith/generator.py` (seeded). They are consistency checks against the rulebook the engine itself implements, not evidence about the organiser's hidden test or any customer project. Hardware: Apple M5, 10 cores, 16 GB, macOS 27.0, Python 3.12.13 (`artifacts/repro/environment.txt`; the 11 Oct re-run used the same machine and the repository `.venv`).

## 1. What was re-run on 11 Oct 2026
| Item | Command | Output | Result |
|---|---|---|---|
| Full test suite | `.venv/bin/python -m pytest -q tests/` | `artifacts/pitch_deck_repro/pytest_rerun.log` | **122 passed** (38 s) |
| Benchmark (scale + TQ recall + 10 revisions) | `SLOTSMITH_BENCH_DIR=/tmp/... SLOTSMITH_BENCH_JSON=artifacts/pitch_deck_repro/benchmarks_rerun.json .venv/bin/python scripts/benchmark.py` | `benchmarks_rerun.json`, `benchmark_rerun.log` | deterministic results identical; timings and revision moves differ (see §3, §4) |
| Exhaustive allocator vs exact CP-SAT | `scripts/audit_ffd_exact.py` (run in a temporary copy so tracked files were not overwritten) | `ffd_exact_rerun.json` | **identical** to `artifacts/audit/ffd_exact.json` except wall time (186.8 s vs 180.2 s) |
| Instances vs exact per-group minimum | `scripts/audit_lb_gap.py` (temporary copy) | `lb_gap_rerun.json` | **identical** to `artifacts/audit/lb_gap.json` |

The benchmark re-run overlapped with browser screenshot capture on the same laptop, so its timings are slightly pessimistic (one 20k run: 8.68 s).

## 2. Evidence base
| Batch | File | Generated | 20k median wall | Revision moves (10 cases) |
|---|---|---|---|---|
| Clean run 1 (canonical) | `artifacts/benchmarks.json` = `artifacts/repro/benchmarks_clean_run1.json` | 10 Oct 12:25 | 5.99 s | 429 |
| Status audit | `artifacts/audit/revision_status.json` | 10 Oct | n/a | 446 |
| Clean run 2 | `artifacts/repro/benchmarks_clean_run2.json` | 10 Oct 12:29 | 6.03 s | 470 |
| Re-run | `artifacts/pitch_deck_repro/benchmarks_rerun.json` | 11 Oct 22:35 | 6.31 s | 575 |
| (pre-audit, before fixes; not used for charts) | `artifacts/benchmarks_pre_audit.json` | 10 Oct 11:35 | 5.93 s | 470 |

## 3. Metric-by-metric
| Metric (as on the slides) | Dataset / size | Count | Definition and baseline | Kind | Limits |
|---|---|---|---|---|---|
| **0 verifier violations** | 12 allocation runs (500, 2,000, 10,000, ~20,000 signals × 3 seeds) + 10 revisions | 3 batches, all 0 | violations reported by the independent verifier (11 check families) on the exported workbook | measured | "no violation detected by implemented checks", not universal correctness; same engine author wrote the rulebook reading |
| **100% of rows allocated or covered by a TQ** | same 12 runs | 3 batches, all 100 | rows with Status Allocated or a TQ ÷ rows | measured | not "100% allocated" (29 of 2,010 rows are held under TQs in the UI demo) |
| **81/81 injected errors raised as TQs** | 3 synthetic MDBs with 27 injected errors each | 3 × 27 | each injected defect has a TQ naming its row | measured | recall on our own injected error types |
| **0 baseplates above the exact per-group minimum** | same 12 runs | 3 batches, all 0 | `baseplates − exact_group_baseplates`; the minimum is a closed form for item sizes 2/6/12 (+ multiples of 12) | measured against a proved formula | says nothing about CIOC or cabinet counts; the formula is validated against CP-SAT in the exhaustive audit |
| **19,682 exhaustive small cases + 150 larger groups** | generated groups with 0–2 cables per (side, size); 150 random larger groups | 19,682 OPTIMAL, 0 worse; 148 OPTIMAL + 2 FEASIBLE, 0 worse | allocator's baseplate count per group vs CP-SAT bin-packing minimum under the same A/B and group-isolation rules | measured (exact solver), reproduced 11 Oct | per-group baseplates only; non-standard sizes outside the proof |
| **FFD optimal for one A/B side, sizes 2/6/12** | n/a | proof | `docs/architecture.md` §4 | mathematically proved (+ `test_ffd_divisible_sizes_is_optimal`, 200 random instances) | does not cover the neutral top-up step |
| **~6 s for 20,033 signals** | 3 seeds per batch (20,033 / 20,003 / 20,003 rows) | batch medians 5.99, 6.03, 6.31 (+5.93 pre-audit) | wall time of ingest → validate → allocate → export → verify, one process, one laptop | measured | outlier 8.68 s under other load; no complexity claim; allocation alone 0.012 s median |
| **Runtime chart** | 12 points × 3 batches | 36 | each allocation run (rows, wall s) | measured | observed on one machine |
| **429–575 moved (4 runs) vs 49,805** | 10 revision cases: 2,000 signals × 5 seeds, 10,000 × 5 | 4 independent runs for SlotSmith; 1 deterministic total for the re-run | "moved" = a tag in both revisions whose cabinet/CIOC/baseplate/slot differs (`revision.impact_report`), same on both sides; SlotSmith = `revise()` (pin → greedy → CP-SAT window → fallback); baseline = `run()` on Rev B alone, ignoring Rev A | measured | baseline is naive by design; the minimum possible is unknown; SlotSmith moves vary by run |
| **7 of 11 repair windows proven exact** | the 7 of 10 cases that needed CP-SAT | 11 accepted windows | CP-SAT status OPTIMAL (objective = bound) vs FEASIBLE at the 10 s limit; windows that came back INFEASIBLE/UNKNOWN were rejected and widened | measured | identical 7/4 split in all four runs |
| **122 tests pass** | `tests/` | 122 | pytest collection: 31 engine (25 + 6 audit regressions, incl. Hypothesis property tests) + 91 UI | measured | tests exercise synthetic fixtures |

## 4. Revision moves in detail (the number that changed)
Moves per case over the four runs (clean run 1 / status audit / clean run 2 / re-run):

| Case | 2k·1 | 2k·2 | 2k·3 | 2k·4 | 2k·5 | 10k·1 | 10k·2 | 10k·3 | 10k·4 | 10k·5 | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Full re-run (every run) | 1,287 | 883 | 1,728 | 1,157 | 1,095 | 9,070 | 8,535 | 7,252 | 9,166 | 9,632 | 49,805 |
| SlotSmith, run 1 | 53 | 11 | 4 | 50 | 66 | 50 | 9 | 115 | 44 | 27 | 429 |
| SlotSmith, status audit | 53 | 11 | 4 | 50 | 66 | 50 | 9 | 132 | 44 | 27 | 446 |
| SlotSmith, run 2 | 53 | 11 | 4 | 50 | 66 | 50 | 9 | 156 | 44 | 27 | 470 |
| SlotSmith, re-run | 53 | 11 | 4 | **218** | 66 | 50 | 9 | 93 | 44 | 27 | **575** |

- Eight of ten cases are identical in every run. The variance comes from the two cases where CP-SAT returns a best-found (FEASIBLE) solution at the 10 s limit with 8 workers.
- The Round 1 deck said "429–470". That range is **no longer supportable**: the re-run gave 575. The final deck states "429–575 over 4 runs" and plots the per-case range.
- All compared outputs satisfied the constraints (0 violations in both methods, 0 fallbacks to full re-allocation in 10 cases).
- Same inputs and rules: `make_revision(g.df, seed=300+seed)` with the default rule set; the two methods share inputs. Same-seed generation makes the 49,805 total identical in every run.
- Possible cause of the 218 (CPU contention while other work ran) was **not** isolated; reported as unexplained variance.

## 5. Not retained / not shown
- "Near-linear runtime": not shown; only the observed points are plotted.
- Pre-audit figures ("+2 baseplates over the lower bound"): superseded by the exact per-group minimum (explained in `docs/architecture.md` §4).
- Single-number revision claims ("470 moved"): removed.
- Any speed or time-saving statement relative to manual work: none was measured, none is made.
