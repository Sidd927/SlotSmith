# Validation plan and current results

All current results are on **synthetic** data (`src/slotsmith/generator.py`). They show the engine follows the published rules at scale. They do **not** show compatibility with the organiser's unseen MDB, template or hidden test.

| Acceptance criterion (PS #02 Definition of Done) | Metric | Target | Current result | How measured |
|---|---|---|---|---|
| 100% allocated or TQ'd | (allocated + TQ rows) / MDB rows | 100% | **100%** in 12 scale runs + 3 error runs | `scripts/benchmark.py` |
| Zero violations of user rules | Independent verifier violations | 0 | **0** in 12 runs (500–20k), 0 in 10 revisions | verifier on the re-read workbook |
| Verifier actually catches errors | Mutation tests detected | 100% | Double-booked slot, wrong TB, A/B mix, missing signal, cable split, spare budget, bad names: **all caught** | `tests/test_core.py` |
| TQs for data problems | Injected errors raised as blocking TQs | 100% | **81/81** (9 error kinds × 9) | benchmark `tq_recall` |
| Right hardware and names | H-1..6 and N-1..6 checks | 0 violations | 0 | verifier |
| Revision-friendly | Moved signals vs a from-scratch re-run | ≪ re-run | **429–470 vs 49,805** (10 cases, 3 runs; not deterministic) | benchmark `revisions`, `artifacts/repro` |
| Revision correctness | Verifier violations on Rev B | 0 | 0 | benchmark |
| No code change for new rules/MDBs | Change parameters via JSON; renamed headers | Pass | Pass (`test_rule_change_without_code_change`, `test_auto_map_variant_headers`) | pytest |
| Efficiency | Baseplates − exact per-group minimum | 0 | **0** in 12/12 runs (exhaustive small cases vs CP-SAT: 0 mismatches in 19,682) | benchmark + `scripts/audit_*` |
| Scale | End-to-end time at 20k signals (laptop) | < 60 s | **6.0 s** median (allocation 0.01 s) | benchmark |
| Revision runtime | Worst case | < 60 s | ≈ 58 s (CP-SAT window); 4 of 11 windows stop at the 10 s limit unproven | benchmark, `artifacts/audit/revision_status.json` |

## Still to validate

1. The organiser's sample MDB and template: ingestion, mapping and export layout.
2. Mentor answers on the open interpretations (rule register ASM items), re-run with the resulting rule-set variants.
3. Unseen-schema robustness: generate MDB variants with renamed, merged and missing columns and extra sheets.
4. Revisions with larger change rates (10–30%) and group splits.
5. Hand-checked small cases reviewed by a domain expert (an Emerson mentor, if possible).
