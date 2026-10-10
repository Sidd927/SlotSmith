# SlotSmith: final evidence-based audit (10 Oct 2026, 12:15–12:40 IST)

Nothing was committed, published, uploaded or sent.

## 0. Artifacts audited (final state)
| File | Size | SHA-256 | Opens? |
|---|---|---|---|
| `deliverables/round1/SlotSmith_Round1.pptx` | 1,818,678 B | `f56d59c0…f9e2b9` | python-pptx: 8 slides, 13.33 × 7.46 in; `validate.py` PASSED |
| `deliverables/round1/SlotSmith_Round1.pdf` | 2,764,985 B | `6b18380c…c99231` | PyMuPDF: 8 pages, not encrypted; every number in the PPTX text also appears in the PDF text |
| `artifacts/benchmarks.json` (canonical = clean run 1) | — | `6dd076cc…78043` | The pre-audit version is kept as `artifacts/benchmarks_pre_audit.json` |

The deck numbers are generated from `artifacts/benchmarks.json` plus `artifacts/repro/*.json` and `artifacts/audit/revision_status.json` by `scripts/build_deck.py`. No figure is typed by hand.

## 1. Data provenance

**Every SlotSmith result in the deck and the docs is on SYNTHETIC data** from `src/slotsmith/generator.py`. **No result has been verified against official organiser data**, because none has been released (section 6). The synthetic data was built from the same published rulebook the engine implements, so passing on it is a consistency check, not external validation.

## 2. Slide-by-slide claim register
Status: ✅ verified · ✏️ corrected in this audit · ⚠️ caveated/interpretation · ⛔ removed.

| Slide | Claim (as it now reads) | Evidence | Status |
|---|---|---|---|
| 1 | Team Mac_Enthu; leader Aayush Aade; Track 1 (Emerson) PS 1.2 IO Signal Sudoku | `reference/team/registration_form_draft.pdf` (form shows PS number 1.2, title IO Signal Sudoku) | ✅ |
| 2 | Engineers must give every signal a home cabinet → CIOC → baseplate → CHARM | PS #02 p.4 (S-01) | ✅ |
| 2 | "10,000+ signals are allocated by hand in Excel … each revision means reworking it and tracing the impact again" | PS #02 p.4, near-verbatim | ✅ sponsor statement, not our measurement |
| 2 | DeltaV automates auto-sense, late binding, Bulk Edit | S-03 p.2 (auto-sense, drag-drop), S-06 p.5 (late binding; non-HART manual or bulk edit), S-04 (Bulk Edit) | ✅ |
| 2 | "We found no public tool that places signals from project rules (internal tools may exist)" | docs/emerson_product_analysis.md §4–5 | ⚠️ absence of public evidence only; worded as such |
| 2 | "without lifting a wire" | S-03 p.1 | ✅ |
| 2 | Cabinet ≤ 4 CIOCs; CIOC 8 baseplates; baseplate 12 CHARMs; CHARM 1 signal | PS p.5 rule 3; S-03 pp.2–3, p.10 (96 ch/CIOC) | ✅ (4/cabinet is a PS project rule, not a hardware limit) |
| 2 | 24-pair = 2 full baseplates (22 signals + 2 wired spares) | PS p.5 | ✅ |
| 2 | Six rules | PS p.5 rules 1–6 | ✅ |
| 3 | Independent verifier re-checks the exported workbook (11 rule families) | `verifier.py:19` CHECKS (11); imports only `.rules` (`verifier.py:17`); pipeline re-reads the file (`pipeline.py:93`); **CLI revise now re-reads too** (`cli.py:77`) | ✏️ revise path previously verified in-memory rows |
| 3 | "unchanged cables stay put; CP-SAT seeks the fewest moves locally" | `revision.py:95` pinning; `repair_cpsat.py` window model | ✏️ was "CP-SAT minimises it". Now local, with optimality not always proven (§4) |
| 3 | "Rules are data … no code to re-tune" | `rules.py` RuleSet; `test_rule_change_without_code_change` | ✏️ was "No code change". New rule *types* need code (slide 7 limits) |
| 3 | Every TQ cites rule ID and MDB file/row | `validate.py` TQ fields; `test_row_level_tqs`; capacity TQs have sources | ✅ |
| 3 | FFD provably minimises baseplates within a side class; group totals matched an exact solver in 19,682 exhaustive cases and 12/12 benchmark runs | Proof `architecture.md §4`; `scripts/audit_ffd_exact.py` → `artifacts/audit/ffd_exact.json` (342 + 19,682 cases, all CP-SAT OPTIMAL, 0 mismatches); `scripts/audit_lb_gap.py` → `lb_gap.json` (12/12 equal; 150 random larger: 0 worse, 148 OPTIMAL / 2 FEASIBLE) | ✏️ was "minimum … in each class (proof)". The proof does not cover the neutral top-up |
| 3 | 20,033 synthetic signals allocated + verified in 6.0 s | `artifacts/benchmarks.json` scale, 20k median 5.99 s (clean runs 5.99 / 6.03; pre-audit 5.93) | ✅ synthetic, Apple M5 |
| 3 | From-scratch re-run moved 9,070 of ~10k | benchmarks.json revisions[5] `moved_from_scratch` (identical in all runs) | ✅ |
| 3 | AI helpers "planned for Round 2+" | No LLM code in `src/` | ✅ |
| 3 | "Solver + independent verifier" box | — | ✏️ was "Deterministic, provable". Revision CP-SAT is not deterministic |
| 4 | Stack: Streamlit prototype, Python 3.12, pandas, openpyxl, pydantic, OR-Tools CP-SAT (Apache-2.0); SQLite and Docker planned | `pyproject.toml`, `requirements.lock.txt`, `app/streamlit_app.py` | ✅ |
| 4 | Verifier "shares no code with 4" | `verifier.py:17` | ✅ (revision imports the verifier's regex helper; not the reverse) |
| 4 | Row provenance travels with every signal | `ingest.py` src_file/sheet/row → `Signal.src` → rows "Source" | ✅ |
| 5 | Features 1–5 "Built"; set rules = "Built (prototype panel)" | CLI `cli.py`; UI `app/streamlit_app.py` (toggles, parameters, save/load JSON). The UI cannot add new rule types | ✅ (prototype) |
| 5 | Cabinet map is engine output on a 900-signal synthetic MDB | `build_deck.py` slide5 → `run()` | ✅ regenerated with post-audit code |
| 5 | UI screenshots (1,981 allocated, 29 TQ, 0 violations, 199 (199); Rev B 46/111/58/28/1,849/0) | `artifacts/screenshots/*.png`, captured 10 Oct before the audit fixes. The fixes do not affect that run (no capacity failures). The label "(LB)" there is the old bound | ⚠️ pre-audit screenshots, still accurate for that input |
| 6 | 31 automated tests | `pytest --co`: 31 (27 functions, parametrised); clean env: 31 passed (`artifacts/repro/pytest.log`) | ✏️ was 25 |
| 6 | 0 violations in 12 runs; 100%; 81/81 | benchmarks.json + both clean runs + pre-audit run: identical | ✅ synthetic |
| 6 | "0 baseplates above the exact per-group minimum (12 runs)" | `baseplates_over_exact_max` = 0 (all runs) | ✏️ was "+2 above the lower bound": a weak bound, not waste |
| 6 | 5.99 s for 20,033 signals | benchmarks.json | ✅ |
| 6 | "429–470 vs 49,805 moved, 10 Rev B cases, 3 runs; CP-SAT proven exact in 7/11 window repairs" | clean run 1 = 429, clean run 2 = 470, status-audit run = 446 (`artifacts/audit/revision_status.json`); scratch 49,805 in all runs | ✏️ was the single figure "470". The range shows non-determinism; 10k seed 3 gave 115 and 156 for the same input, so 156 was not minimal |
| 7 | Impact cards | Expected, not measured | ✏️ "Faster" removed (unmeasured) |
| 7 | 300 CIOCs/system → 28,800 channels | S-03 p.10; 300 × 96 | ✅ |
| 7 | "could be adapted to other EM I/O families (untested)" | S-10 lists other vendors | ✏️ was "fits" |
| 7 | Near-linear runtime 0.6/3.0/6.0 s at 2k/10k/20k | benchmarks.json medians | ✅ synthetic |
| 7 | Limits: synthetic only; no official-template compatibility; new rule types need code; CP-SAT window-local | this audit | ✏️ strengthened |
| 8 | Team names | registration form | ✅ |

## 3. Allocator capacity-model audit
| Aspect | Finding | Status |
|---|---|---|
| Pair → slot | 1 pair = 1 slot; cable block width = cable size, wired spares included (`export.build_rows`) | ✅ |
| Baseplate capacity 12 / CIOC 8 / cabinet 4 | Enforced in `Placer._cioc_ok/_cab_ok`; verifier C-1 | ✅ |
| Cable splitting | ≤12-pair never straddles; >12-pair starts at slot 1 and spans ⌈size/12⌉ baseplates in one CIOC. Non-multiples of 12 (e.g. 16) waste the tail of the last baseplate | ✅ / ⚠️ inefficiency documented |
| `allow_cable_straddle=true` | **Not honoured by the allocator.** It only relaxes the verifier | ⚠️ documented (rule register K-3, known_limitations) |
| Oversized cable (> what one CIOC/cabinet allows) | **Bug found:** the whole group was marked unplaced while some of its cables were placed (duplicate allocated + not-allocated rows), and an empty cabinet could be left behind. **Fixed** (`allocator.py:276` per-unit check; `fits_empty` before touching the layout); regression test `test_oversized_cable_does_not_unplace_its_group` | ✏️ fixed |
| Grouping | Groups contiguous; one group per CIOC (default); look-ahead avoids needless splits | ✅ |
| Spare reservation | ⌈spare% × 32⌉ empty baseplates per cabinet (counting unopened CIOC positions as empty). Rounding/basis is an interpretation | ⚠️ ASM P-1 |
| Optimality | See slide 3 row: proof per side class; exact match at group level in every tested case; CIOC/cabinet optimality **not claimed** | ✏️ claim narrowed |

## 4. Verifier and revision-solver audit
| Aspect | Finding | Status |
|---|---|---|
| Verifier independence | Imports only `rules`; positions re-parsed from names | ✅ |
| Verifier blind spot | Q-1 accepted a tag that was both "Allocated" and "Not allocated". **Fixed**; regression test added | ✏️ fixed |
| Mutation detection | Double-booked slot, wrong TB, A/B mix, missing signal, cable split, spare budget, bad names: all detected (`tests/test_core.py`) | ✅ |
| Not checked by the verifier | "In sequence" ordering of groups; minimality of a group's cabinet span | ⚠️ documented |
| CP-SAT limits | 10 s wall clock per window, `relative_gap_limit` 0.05, 8 workers, ≤ 6 window widenings; existing cables may move ≤ 1 cabinet | ⚠️ window-local, non-deterministic |
| Optimality status | 11 accepted windows (status audit): 7 proven exact (objective = bound), 4 FEASIBLE at the time limit | ✏️ now reported, not "minimum" |
| Infeasible windows | Correctly widened; INFEASIBLE/UNKNOWN windows are logged in `metrics["cpsat_repairs"]` | ✅ |
| Fallback path | Full re-allocation; **previously produced no TQ**. Now raises a warning TQ (R-2) and capacity TQs; test `test_revision_fallback_raises_warning_tq`. Fallback occurred in 0 of 10 benchmark cases | ✏️ fixed |
| Oversized new cable in Rev B | Previously forced the fallback. Now a capacity TQ, no fallback, 0 moves (test) | ✏️ fixed |
| Cabinet-level segregation/isolation in revision | Greedy and CP-SAT enforced CIOC-level only. **Now enforced at cabinet level when configured**; edge-case audit 0 violations | ✏️ fixed |
| Failures → traceable TQs | Every "Not allocated" row now references a real TQ ID (allocation and revision) | ✅ after fix |

## 5. Reproduction from a clean environment
- Command: `zsh scripts/repro_clean.sh`. It makes a fresh copy in `/tmp/slotsmith_clean_20261010_122423`, a new venv from `requirements.lock.txt`, then runs pytest and the benchmark twice.
- Environment: `artifacts/repro/environment.txt` (macOS 27.0, Apple M5, 10 cores, Python 3.12.13, full pip freeze).
- Tests: **31 passed** (`artifacts/repro/pytest.log`).
- Benchmark: `artifacts/repro/benchmarks_clean_run{1,2}.json` and logs.
  - The deterministic outputs (12 scale runs, 81/81 TQs) are identical across the pre-audit run and both clean runs.
  - Timing differs by < 2%.
  - Revision move totals: 470 (pre-audit), 429, 470, 446 (status audit). They are not reproducible exactly.
- Audit scripts and logs: `scripts/audit_ffd_exact.py`, `audit_lb_gap.py`, `audit_edge_cases.py`, `audit_revision_status.py` → `artifacts/audit/`.

## 6. Official data and template availability (checked 12:24 IST)
- Unstop record 1751374 (`artifacts/audit/unstop_competition_20261010_1224.json`, `updated_at` 2026-10-09 20:26 IST) lists five attachments: PPT template, Track 1/2/4 PS PDFs, handbook. **There is no IO MDB sample and no IO allocation template.**
- The official PDFs contain no links or embedded files pointing to sample data.
- The AISF website (handbook's official channel) has no Code Apex 3.0 content.
- The Instagram, LinkedIn and Verzii community were **not checked** (they need logins).
- **Conclusion: no official-template compatibility is claimed anywhere.** The exporter layout is our own reading of the PS.

## 7. Deadline and format (same source, 12:24 IST)
- Round 1 submission round: **11 Oct 2026 21:00 → 12 Oct 2026 10:00 IST**. PDF or PPTX, max 50 MB, multiple submissions allowed, "Participants must use the provided PPT Template". The submission type was configured 9 Oct 22:45 IST.
- The same record's "important dates" list shows **Round 1 (PPT Screening) 10 Oct 2026 23:59 IST**. The handbook says 10–11 Oct.
- **Unresolved conflict.** It was not changed by the organisers as of 12:24 IST. The safe action is to have the final file ready before 10 Oct 23:59 IST and upload when the round accepts files. Confirm in the Verzii community.

## 8. Addendum: content-lock revision (10 Oct 2026, 13:15 IST)
The final files supersede §0:
- `SlotSmith_Round1.pptx`: 1,816,838 B, SHA-256 `3368d6b6…7a607a`.
- `SlotSmith_Round1.pdf`: 2,778,833 B, SHA-256 `cdabfc67…72f2a8`.

| Slide | Previous wording | Final wording | Evidence |
|---|---|---|---|
| 1 | "… with minimum-move revisions" | "rule-driven, independently checked, revision-aware DeltaV I/O allocation" | Revision optimality not guaranteed (§4) |
| 2 | "the allocation paperwork is now the bottleneck" | "allocation planning and revision tracking remain a manual workflow burden (per the PS)" | PS #02 p.4 |
| 3 | "Proven, not claimed" | "Independently checked" | `verifier.py` |
| 3 | "FFD provably minimises baseplates within a side class; group totals matched …" | "**Proved:** one A/B side, sizes 2/6/12 (24 = two full baseplates). **Tested, not proved:** whole-group totals matched an exact CP-SAT solver in 19,682 exhaustive small cases and 12/12 benchmark runs" | `architecture.md §4`; `artifacts/audit/ffd_exact.json`, `lb_gap.json` |
| 3 | "Why look-alike approaches fail …" (incl. 9,070 figure) | "Design principles" (4 positive statements, no comparative numbers) | — |
| 3 | "Rules are data … no code to re-tune" | "Configurable: existing rule parameters live in JSON; new rule types may need code" | `known_limitations.md` |
| 3 | "Solver + independent verifier"; "Placement is not probabilistic" | "No AI in placement" | No LLM in `src/` |
| 4 | diagonal arrow, separate Rev A store | straight flow; Rev A folded into the Revision engine; built/planned unchanged | `docs/architecture.md` |
| 5 | screenshot with "Baseplates (LB) 199 (199)" | re-captured post-audit: "Baseplates used 199"; dataset labelled SYNTHETIC | `artifacts/screenshots/*.png` (10 Oct, 13:0x IST) |
| 5 | "fewest moves, impact report" | "unchanged stay put; impact report" | — |
| 6 | "CP-SAT min-move repair"; "Faster CP-SAT repair" | "CP-SAT window repair"; "Cut CP-SAT repair time and run-to-run variance" | §4 |
| 6 | figures | unchanged: 0 / 12 runs · 100% allocated-or-TQ · 81/81 · 0 above exact · 5.99 s / 20,033 · 429–470 vs 49,805 · 7/11 · 31 tests | scripted cross-check, all match |
| 7 | "300 CIOCs per system → up to 28,800" | "≤ 300 … (spec maximum) → at most 28,800" | S-03 p.10 "Number of CIOCs per System: 300" |
| 7 | "Every customer revision restarts the rework" | "… means rework and impact tracing" | PS #02 p.4 |
