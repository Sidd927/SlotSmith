# Claim-to-slide matrix: final pitch deck

Built after the evidence audit (`fact_audit.md`, `benchmark_audit.md`) and before the final slide text was fixed. State: **I** implemented · **T** implemented and tested · **P** planned · **U** unvalidated · **Prf** proved · **Ill** illustrative (derived from real engine output, not user data). "Visual?" = whether the point is carried by a diagram/chart/screenshot rather than prose. Duplicates are intentional only where noted.

| Slide | Element | Communicates | Source | Verification | State | Importance | Duplicates | Visual? |
|---|---|---|---|---|---|---|---|---|
| 1 | Team, leader, PS | identity | registration form | ✅ | – | required | slide 8 team line (intended) | text (template) |
| 1 | "rule-driven, independently checked, revision-aware" + one-line plain description | what SlotSmith is in 10 s | content lock; slides 3–4 | ✅ | T | high | – | text |
| 2 | Who is affected | audience | PS p.4 | ✅ | – | high | – | text |
| 2 | 10,000+ signals by hand; revisions mean rework | the problem | PS p.4 | ✅ sponsor claim | – | high | slide 7 (scale card) | text |
| 2 | DeltaV automates auto-sense, late binding, Bulk Edit; no public tool found | gap, with limits | EM PDS, WPs, R-1 | ⚠️ | – | high | slide 7 (fits) | text |
| 2 | Cabinet → CIOC → baseplate → CHARM chips | hierarchy | PS p.5; EM PDS | ✅ | – | high | – | ✅ diagram |
| 2 | A/B interaction example | why rules interact | PS rules 2 and 4; allocator | ✅ | Ill | high | – | ✅ diagram |
| 2 | Six rules → 11 verifier families | how rules relate to checks | `verifier.py` CHECKS | ✅ code | T | high | slide 3 (11 checks) | ✅ chips |
| 3 | Five-step workflow | core workflow | `pipeline.py`, `docs/architecture.md` | ✅ | T | high | slide 4 diagram (same flow, deeper) | ✅ diagram |
| 3 | Baseline = FFD, no solver | accurate algorithm role | `allocator.py` | ✅ | T | high | slide 4 | text + diagram |
| 3 | Independent verifier re-reads exported file, imports only rules | independence | `verifier.py`, `pipeline.py` | ✅ | T | high | slides 2, 4, 5 | text |
| 3 | CP-SAT only for revision repair, 10 s, proven exact / best found | CP-SAT scope | `repair_cpsat.py`, audit | ✅ | T | high | slides 4, 6 | text |
| 3 | PROVED / TESTED / NOT CLAIMED | proof vs evidence | `architecture.md` §4; `ffd_exact.json`; `lb_gap.json` | ✅ reproduced | Prf / T | high | – | ✅ three-state cards |
| 3 | AI helpers planned, none runs today | AI honesty | README; no LLM code | ✅ | P | medium | slides 4, 6 | text |
| 3 | 122 tests; ~6 s for 20,033 signals | feasibility | pytest; benchmarks | ✅ | T | medium | slide 7 chart | text |
| 4 | Stack boxes (template categories) | technology | `pyproject.toml`, imports | ✅ | I | high | – | text + logos |
| 4 | Lane diagram: inputs, ingest, validate, allocate, export, workbook; Rev B → revision engine → export; verify re-reads file | architecture | `src/slotsmith/*` | ✅ | T | high | slide 3 | ✅ diagram |
| 4 | Surfaces/tests/storage lane; planned dashed (LLM helper, Docker) | status separation | `technology_decisions.md` | ✅ | I / P | high | – | ✅ |
| 4 | No database; files only | storage truth | repository | ✅ | I | medium | – | text |
| 5 | Seven workbench stages | UI scope | `app/ui/shell.py` | ✅ | T | high | – | ✅ chips |
| 5 | Cabinet inspector screenshot (dominant) | genuine product proof | live capture 11 Oct | ✅ | I | high | – | ✅ screenshot |
| 5 | Results screenshot + annotation (0 violations, 29 held, 6 TQs) | verification proof | live capture | ✅ | I | high | slide 6 card (scoped) | ✅ screenshot |
| 5 | Revise screenshot + annotation (46 moved …) | revision proof | live capture | ✅ | I | high | slide 6 chart (aggregate) | ✅ screenshot |
| 5 | "Synthetic" disclosure | data honesty | – | ✅ | – | required | slides 1, 6, 7 | text |
| 6 | Milestone timeline (built / Round 2 / Finale / beyond) | roadmap and status | handbook dates; task ledger | ⚠️ intentions, not commitments | I / P / U | high | – | ✅ timeline |
| 6 | Revision-cost chart, per case, log scale, 4 runs | revision benefit and variance | 4 benchmark runs | ✅ | T (measured) | high | – | ✅ chart |
| 6 | 429–575 vs 49,805 | headline revision metric | `benchmark_audit.md` §4 | ✏️ corrected | T | high | chart title only | ✅ |
| 6 | 0 violations / 81 of 81 TQs / 0 over exact minimum / 7 of 11 proven | selected evidence | benchmark batches | ✅ | T | high | slide 3 TESTED (different metric) | ✅ cards |
| 6 | Synthetic + hardware qualifier | scope | `benchmarks.json` machine | ✅ | – | required | – | text |
| 7 | Runtime scatter and medians | observed scaling | 3 batches | ✅ | T | high | slide 3 "~6 s" | ✅ chart |
| 7 | Expected benefits (not measured) | users | – | ✅ labelled | U | medium | – | text |
| 7 | 10,000+ and ≤ 28,800 | scale context | PS; EM PDS | ✅ | – | medium | slide 2 (10,000+) | text |
| 7 | DeltaV tools ↔ SlotSmith | complement not replace | R-1 | ⚠️ positioning | – | medium | – | ✅ mini-diagram |
| 7 | Limits and next validation dependency | honesty; next step | known_limitations; audit | ⚠️ re-check template release | U | high | – | ✅ card |
| 8 | Closing statement | central value | slides 3–4 | ✅ | – | medium | – | text |
| 8 | GitHub URL (private repo!) | resource | `git remote`, `gh repo view` | ⚠️ not publicly reachable | – | high | – | text link |
| 8 | YouTube and documentation placeholders | resources to add | – | ✅ placeholders | P | high | – | text |

## Items deliberately excluded
- SQLite run log, React migration as part of the stack, "near-linear" wording, AI-column-mapping as a built feature, any time or cost saving, any official-template compatibility, any customer, adoption or market-size statement.
- QR code: not added (no verified public destination).
