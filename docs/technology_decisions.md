# Technology decisions

| Decision | Choice | Alternatives considered | Why | Licence | Evidence / experiment |
|---|---|---|---|---|---|
| Language | Python 3.12 | TypeScript, Java | PS says "Python preferred"; strong data and solver ecosystem | PSF | — |
| Initial allocation | Constructive per-class **FFD** on cable blocks + sequential CIOC/cabinet fill | Pure CP-SAT model; MILP; LLM placement | Optimal baseplate count per class (proof, architecture §4); ~10 ms for 20k signals; deterministic and explainable | — | `artifacts/benchmarks.json`: 12 runs, 0 violations, ≤ +2 baseplates vs lower bound |
| Revision repair | Pin + greedy fill + **OR-Tools CP-SAT** window MPP | Full re-solve; MILP (HiGHS/CBC); local search | CP-SAT handles Boolean exact-slot models with hints; free; fast enough on 1–5 cabinet windows | Apache-2.0 | 10 Rev B cases: 470 vs 49,805 moved; CP-SAT used in 7; max 55 s |
| Rule representation | pydantic v2 models saved as JSON | YAML DSL; Python plug-ins; free-text | Typed validation, easy diff/preview, no code change for new parameters | MIT | `test_rule_change_without_code_change` |
| Excel I/O | openpyxl + pandas | xlsxwriter (write-only); LibreOffice UNO | Read and write; styling; formula-free output | MIT / BSD-3 | Round-trip test |
| Verification | Independent Python verifier that reads the exported workbook | Re-use allocator invariants; solver-side checks only | Certifying-algorithm principle (L-11); catches exporter bugs too | — | Mutation tests: every injected corruption caught |
| Testing | pytest + Hypothesis | unittest only | Property-based tests for "0 violations / 100% coverage" on random MDBs | MIT / MPL-2.0 | 25 tests passing |
| UI (planned) | Streamlit for Round 2; React optional later | React from day one; desktop Qt | Fastest route to a working rule panel and cabinet map in Python | Apache-2.0 | — |
| Deck | python-pptx on rendered template pages; LibreOffice for PDF | pptxgenjs (needed npm install); Canva by hand | The template is published only as PDF; generating from code keeps numbers in sync with benchmarks | MIT / MPL-2.0 | `scripts/build_deck.py` |
| LLM (planned) | Optional, for header-mapping suggestions and rule drafting; the model will be declared | None | PS allows any AI; kept out of the placement path | — | — |

## Rejected or deferred

- **LLM-driven placement.** It cannot guarantee zero violations, and outputs are not reproducible.
- **MILP for the initial allocation.** It is unnecessary given the per-class FFD optimality proof; it would be slower and less explainable.
- **Allowing cable straddling by default.** The PS diagram shows no straddling; it is kept as a parameter (`allow_cable_straddle`).
- **Docker now.** Deferred; the venv plus lockfile is enough for Round 1.
