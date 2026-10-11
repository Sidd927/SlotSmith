# SlotSmith — UX Redesign Implementation Plan

**Project:** SlotSmith (VIT Code Apex 3.0 · Track 1 Emerson · PS 1.2: Project IO Signal Sudoku)  
**Team:** Mac_Enthu  
**Document Status:** Phase 1 Deliverable — Implementation Plan for Frontend Redesign  
**Backend Constraint:** Complete Freeze on `src/slotsmith/` and Core Algorithms  

---

## 1. Safety Boundaries & Frozen Components

To ensure that the mathematical guarantees, verification independence, and CLI contracts remain 100% intact, the redesign is strictly constrained to the presentation layer.

### 1.1 Components & Files Frozen (Must NOT Be Modified)
- **All Core Business Logic:**
  - `src/slotsmith/allocator.py` (FFD divisible-packing logic, `Placer`, `build_units`, capacity math)
  - `src/slotsmith/rules.py` (RuleSet schema, Pydantic models, default parameters)
  - `src/slotsmith/validate.py` (validation checks, TQ generation, held slot reservation)
  - `src/slotsmith/verifier.py` (independent 11-family verifier, pattern regexes)
  - `src/slotsmith/export.py` (data contracts, sheet definitions, openpyxl output)
  - `src/slotsmith/revision.py` (pinning, greedy fill, revision heuristics)
  - `src/slotsmith/repair_cpsat.py` (OR-Tools CP-SAT window model and constraints)
  - `src/slotsmith/pipeline.py` (end-to-end execution flow, timing capture)
  - `src/slotsmith/generator.py` (synthetic benchmark generation and error injection)
- **CLI & Integration Boundaries:**
  - `src/slotsmith/cli.py` (all CLI command arguments, JSON outputs, exit codes)
  - `tests/test_core.py` and `tests/test_audit_regressions.py` (must pass 31/31 without edits)
- **Core Dependencies:**
  - `pyproject.toml` and `requirements.lock.txt` (no framework migration, no new dependencies)

### 1.2 Permitted Scope of Modification
- `app/streamlit_app.py` (or cleanly modularized components under `app/` that import directly into Streamlit)
- `docs/ux/` documentation and design specifications
- New UI-specific helper tests under `tests/test_ui.py` (validating UI data transformations without mutating core tests)

---

## 2. Reviewable Implementation Milestones

The redesign is decomposed into six reviewable, incremental milestones. Each milestone can be tested and reviewed independently.

```
┌────────────────────────────────────────────────────────────────────────┐
│ MILESTONE 1: Architecture Decoupling, State Hygiene & Test Harness     │
├────────────────────────────────────────────────────────────────────────┤
│ MILESTONE 2: Defensive Ingestion, Override Mapping & Pre-Flight Audit   │
├────────────────────────────────────────────────────────────────────────┤
│ MILESTONE 3: Executive KPI Dashboard, Certifier Ledger & TQ Console     │
├────────────────────────────────────────────────────────────────────────┤
│ MILESTONE 4: Interactive Digital Marshalling Cabinet Inspector          │
├────────────────────────────────────────────────────────────────────────┤
│ MILESTONE 5: Revision Impact Control Center & Solver Transparency      │
├────────────────────────────────────────────────────────────────────────┤
│ MILESTONE 6: Industrial Styling, Laptop Responsiveness & QA Sign-Off   │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Milestone 1: Architecture Decoupling, State Hygiene & Test Harness

**Objective:** Establish robust session-state management, eliminate stale data hazards, and set up a UI helper test harness.

- **Files Expected to Change:**
  - `app/streamlit_app.py`
  - `tests/test_ui.py` (new test file)
- **Key Enhancements:**
  1. Define a centralized `SessionStateManager` in the UI to manage workflow phases (`IDLE`, `MAPPED`, `ALLOCATED`, `REVISED`).
  2. Implement an active rule hashing mechanism (`hashlib.md5(rules.model_dump_json())`) to detect when sidebar parameters change after an allocation has been run.
  3. Render a visual "Stale Results" warning banner when active rules do not match the displayed allocation.
  4. Create `tests/test_ui.py` verifying that state transitions, rule hash tracking, and data formatters work correctly.
- **Acceptance Criteria:**
  - Modifying a slider or toggle in the sidebar after allocating triggers a clear staleness warning rather than silently showing mismatched data.
  - State does not crash or lose data when switching between tabs.
  - All 31 existing backend tests in `tests/test_core.py` pass cleanly.

---

### Milestone 2: Defensive Ingestion, Override Mapping & Pre-Flight Audit

**Objective:** Eliminate unhandled upload crashes, present transparent column mapping review, and provide data-backed pre-flight audit before allocation.

- **Files Changed:**
  - `app/streamlit_app.py`
  - `tests/test_ui.py`
- **Key Enhancements (Completed):**
  1. Implemented `safe_read_mdb` with defensive exception handling for `ValueError` (missing IO columns), corrupted archives, empty files, and missing paths, rendering concise actionable alerts with technical diagnostic expanders.
  2. Implemented `build_mapping_review_rows` providing complete transparency into auto-mapping confidence (High, Fuzzy, Missing Required, Unmapped Optional) and listing unused source headers. Documented that manual overrides are not supported end-to-end without altering frozen backend pipeline contracts.
  3. Implemented data-backed `compute_preflight_audit` powered by `validate(mdb.df, rules)`, calculating exact row/cable counts, categorizing blocking/warning/info TQs based on backend semantics, and displaying readiness status before allocation.
  4. Cached ingested `MDB` in session state keyed by composite input hash to prevent redundant Excel parsing on UI reruns.
  5. Implemented failure preservation: failed uploads or allocations preserve previous results and fingerprints.
- **Acceptance Criteria (Verified - 74/74 tests passing):**
  - Uploading corrupted or column-deficient files produces clean user alerts and preserves existing allocations without tracebacks.
  - Pre-flight audit accurately reflects data validation issues and readiness without executing allocation.
  - Mapping review clearly distinguishes required vs optional fields and shows confidence scores.

---

### Milestone 3: Executive KPI Dashboard, Certifier Ledger & TQ Console

**Objective:** Transform raw data tables into a high-impact engineering summary, transparent certification checklist, and filterable TQ console.

- **Files Expected to Change:**
  - `app/streamlit_app.py`
- **Key Enhancements:**
  1. Build an Executive KPI strip with industrial badges:
     - Signals Allocated (with percentage)
     - Signals with TQs (severity breakdown)
     - Verifier Status (Prominent green "PASS · 0 Violations" badge)
     - Hardware Footprint: Cabinets, CIOCs, Baseplates (compared to exact theoretical lower bound `lb_baseplates`)
     - Pipeline Timing breakdown (`ingest_s`, `validate_s`, `allocate_s`, `verify_s`)
  2. Implement the Rule Certification Ledger:
     - Render all 11 verified rule families (`Q-1`, `D-2`, `C-1`, `K-1`, `S-1`, `G-1`, `P-1`, `H-1..6`, `N-1..6`, `C-2`, `M-1`) as an auditable checklist with PASS icons.
  3. Implement an Actionable TQ Console:
     - Severity filter chips: All, Blocking, Warning, Info.
     - Tag/Cable text search filter.
     - Direct display of `suggested_action` and source rows (`file:sheet:row`).
  4. Provide clean workbook export triggers with summary metrics.
- **Acceptance Criteria:**
  - Evaluators can verify zero rule violations across all 11 checks in one glance.
  - Engineers can filter TQs to see only the 6 blocking errors in the synthetic benchmark and immediately read the suggested action and offending source rows.

---

### Milestone 4: Interactive Digital Marshalling Cabinet Inspector

**Objective:** Upgrade the cabinet visualization from static HTML div blocks into an accessible, searchable, and interactive spatial inspector.

- **Files Expected to Change:**
  - `app/streamlit_app.py`
- **Key Enhancements:**
  1. Redesign CIOC cards:
     - Clear headers displaying CIOC name, controller assignment, logical group, and A/B segregation tags.
     - Clean rendering of 8 baseplates per CIOC with 12 CHARM slots each.
  2. Standardize Emerson-aligned color tokens with clear borders:
     - AI (Blue), AO (Violet), DI (Green), DO (Gold), DO-ISO (Orange), DO-RELAY (Pink), Spare Pair (Steel Slate), Free Slot (Grid Void).
  3. Add Signal Finder / Search Bar:
     - Typing a Tag or Cable ID instantly highlights matching CHARM slots with a glowing border and auto-navigates to the containing cabinet.
  4. Implement an interactive CHARM Detail Card:
     - Hover or selection reveals complete engineering metadata: Tag, Cable, Pair, IO Type, Terminal Block, Controller, Baseplate, and Excel source provenance.
  5. Include a spatial toggle to inspect Rev A or Rev B layouts.
- **Acceptance Criteria:**
  - Searching for `10-PT-1001A` highlights its exact slot in `001-CBP-1` and displays its terminal block and CIOC metadata.
  - Colors are distinct and readable in both dark and light presentation environments.
  - Empty baseplates reserved for the spare budget ($\lceil \text{spare\%} \times 32 \rceil$) are clearly labelled as "Reserved Cabinet Spare".

---

### Milestone 5: Revision Impact Control Center & Solver Transparency

**Objective:** Provide full transparency into the revision engine, minimal-move optimization, and CP-SAT solver behavior.

- **Files Expected to Change:**
  - `app/streamlit_app.py`
- **Key Enhancements:**
  1. Rev B Execution Center:
     - Choice between uploading a customer Rev B file or using the synchronized synthetic Rev B benchmark.
     - Single-click revision execution with progress tracking.
  2. Revision Impact Metric Cards:
     - Moved Signals (with comparison note against full re-allocation moves)
     - Added Signals (distinguishing zero-move additions on spare pairs from new cables)
     - Deleted Signals
     - Modified in Place (same slot CHARM/TB updates)
     - Unchanged Signals
     - Rev B Rule Verifier Status
  3. Solver Transparency Badge:
     - Displays CP-SAT solve status (`OPTIMAL` vs `FEASIBLE`), wall-clock solve time, window scope, and accepted lower bound.
  4. Interactive Move Audit Table:
     - Filterable by change type (`Moved`, `Added`, `Deleted`, `Modified in place`).
     - Clear "From" $\to$ "To" location columns with monospace formatting.
- **Acceptance Criteria:**
  - On the 2,000-signal benchmark with Rev B, the UI clearly displays 46 moved signals (vs. thousands in a full re-run), 111 additions, 58 deletions, 28 in-place mods, and 1,849 unchanged signals with 0 verifier violations.
  - Solver status (`OPTIMAL` or `FEASIBLE`) and affected cabinets are transparently stated without unsupported claims of "global optimality".

---

### Milestone 6: Industrial Styling, Laptop Responsiveness & QA Sign-Off

**Objective:** Inject professional industrial design, verify responsiveness on presentation laptops, and perform complete regression validation.

- **Files Expected to Change:**
  - `app/streamlit_app.py`
  - `docs/ux/design_system.css` (or embedded CSS in `app/streamlit_app.py`)
- **Key Enhancements:**
  1. Professional Industrial CSS Injection:
     - Deep slate and high-contrast typography styling.
     - Monospace styling for engineering tags.
     - Elevated card containers and subtle micro-borders.
  2. Viewport Responsiveness:
     - Optimize layout for standard 13" laptop resolutions (1280×800 to 1440×900).
     - Ensure dataframes and cabinet flexboxes scroll horizontally without breaking container boundaries.
  3. Full End-to-End Test Suite Execution:
     - Run `pytest` across all existing tests and new UI helper tests.
  4. Live Demo Walkthrough Rehearsal:
     - Validate that the complete pitch journey (Ingest → Allocate → Verify → Cabinet Map → Revise) can be demonstrated smoothly in under 60 seconds.
- **Acceptance Criteria:**
  - 100% of automated tests pass (31 backend tests + all UI tests).
  - Clean visual appearance with zero clipped cards or awkward overflows on 1280px viewports.
  - Zero warnings or errors in the Streamlit runtime console.

---

## 3. Test & Verification Strategy

### 3.1 Backend Regression Suite (Unchanged)
The existing test suite must be executed before and after every milestone:
```bash
.venv/bin/python -m pytest -q
```
- **Target:** 31 passed in ~37 seconds.
- **Coverage Areas:** Auto-mapping, divisible bin packing optimality, row-level TQs, cable blocking, corruption detection in verifier, rule parameter changes, revision pinning, and audit regression edge cases.

### 3.2 UI Helper Tests (`tests/test_ui.py`)
New test cases will cover:
1. `test_staleness_detection`: Verifies that altering rule parameters flags `is_stale=True`.
2. `test_override_mapping_integration`: Verifies that user-supplied overrides update `ColumnMapping` and successfully pass to `read_mdb`.
3. `test_tq_filtering_logic`: Verifies severity and text search filtering on TQ lists.
4. `test_cabinet_html_data_contract`: Verifies that the cabinet renderer correctly maps all signal types, spare pairs, and free slots without missing slots.

---

## 4. Rollback Strategy

Because all work is strictly confined to `app/` and new UI test files:

1. **Git Isolation:**
   - All redesign work can be committed to a dedicated feature branch or staged cleanly against `main`.
2. **Instant Rollback:**
   - If an unexpected Streamlit regression occurs, `app/streamlit_app.py` can be restored immediately using Git:
     ```bash
     git checkout main -- app/streamlit_app.py
     ```
3. **No Database or Migration Hazards:**
   - The application does not use a persistent database or schema migrations; state is entirely ephemeral in `st.session_state`.
   - Rollback requires zero database rollbacks or cleanup scripts.

---

## 5. Milestone Execution Status

| Milestone | Scope | Status | Verification Result |
| :--- | :--- | :--- | :--- |
| **Milestone 1** | Session-State Hygiene & Staleness Tracking | ✅ Complete | 54 tests passing; strict rule and input fingerprinting |
| **Review Corrections** | Effective Input & Revision Staleness | ✅ Complete | 63 tests passing; composite hashes, upload preservation |
| **Milestone 2** | Defensive Ingestion, Mapping Review & Pre-flight Audit | ✅ Complete | 74 tests passing; `safe_read_mdb`, pre-flight audit cards |
| **Milestone 3A** | Full UI Transformation & Industrial Workstation | ✅ Complete | 81 tests passing; dark industrial UI, KPI grid, certification ledger, TQ filter console, cabinet map styling |
| **Milestone 3B** | UX Architecture Redesign (5-Stage Workflow) | ✅ Complete | 85 tests passing; 5-stage workflow, reduced sidebar footprint, progressive disclosure, verifier guard |
| **Milestone 4** | Product-Level UI Redesign & Dedicated Screens | 🔄 In Progress | Comprehensive product overhaul: Home landing page, dedicated setup/review/allocate/results screens, cabinet map, revision hub, export center |

---

## 6. Milestone 4: Product-Level UI Architecture & Screen Specification

### 6.1 Purpose & Design Philosophy
Transform SlotSmith from a technical single-page dashboard into a serious, modern industrial engineering application. First-time engineers can immediately understand the product purpose, navigate focused screens without scrolling through long uninterrupted tables, and operate complex allocation and revision workflows with confidence.

### 6.2 Application Shell & Navigation Structure
- **Persistent Header:** Compact SlotSmith brand identity, concise value proposition ("Turn I/O workbooks into rule-checked electronic marshalling allocations"), and live session lifecycle indicator badge (`NO_INPUT`, `INPUT_LOADED`, `ALLOCATED`, `STALE`, `REVISED`).
- **Global Navigation Bar:**
  1. `🏠 Home` (Screen A: Genuine product landing page)
  2. `⚡ Allocation Journey` (Guided 5-stage engineering workflow: `1. Input` → `2. Review` → `3. Allocate` → `4. Results` → `5. Export`)
  3. `🗄️ Cabinet Map` (Dedicated interactive rack inspector)
  4. `🔄 Revision Repair (Rev B)` (Dedicated CP-SAT revision repair workspace)
- **State Hygiene:** All navigation changes occur via `st.session_state["active_nav"]` and `st.session_state["workflow_stage"]`. Navigation never clears or mutates loaded datasets, allocation results, rule parameters, or revision states.

### 6.3 Screen Specifications & Backend Mapping

| Screen | Core Purpose | Primary Action | Primary Details | Advanced Details (Progressive Disclosure) | State / Staleness Behavior | Backend Mapping |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Screen A: Home / Landing** | Product orientation & quick start | "Start New Allocation" (or "Explore Benchmark Demo") | Purpose statement, 5-stage visual how-it-works stepper, active session resume banner | Technical rule configuration and verification ledgers omitted | Displays live session lifecycle badge; offers 1-click resume if data exists | `generate(2000, seed=7, inject_errors=6)` for benchmark preset |
| **Screen B: Input Setup** | Customer workbook ingestion | Upload files / load benchmark $\to$ "Proceed to Review Input →" | Drag-and-drop file uploader, nominal vs actual row distinction, benchmark preset | Synthetic generator sliders (signals, seed, injected errors) in collapsed expander | Defensive ingestion with `safe_read_mdb`; corrupt files produce clear alerts without crashes | `safe_read_mdb`, `_save_uploads` |
| **Screen C: Review Input** | Pre-flight schema & grouping audit | "Proceed to Allocation Setup →" | 4 KPI cards (Actual Rows, Valid Signals, Blocking Issues, Warnings/Info), readiness alert, partial allocation explanation | Expandable Pre-Flight Validation Queries with suggested actions; expandable Column Mapping Review | Green "Ready", Yellow "Partial Allocation", Red "Blocked" based on valid cable blocks | `compute_preflight_audit` powered by `validate()` |
| **Screen D: Allocation Setup** | Deterministic channel allocation | "Allocate IO Channels" (or "Allocate Eligible Signals") | Plain-language constraint summary (spares, isolation, segregation, adjacency, hardware) | Full RuleSet parameter editor in collapsed expander (all controls/defaults preserved) | Disabled if 0 valid cables; spinner feedback; transitions to Results on success | `run(paths, rules, out)` using FFD solver |
| **Screen E: Results Workspace** | Outcome analysis & verification | Review outcomes $\to$ Navigate to Cabinet Map or Export | Concise outcome banner, 6 KPI cards (Allocated, Unplaced TQs, Verifier Violations, Cabinets, CIOCs, Utilization), Verifier Certification Banner | 3 sub-tabs: 1. Rule Verification Ledger, 2. Technical Queries (with severity/search filters), 3. Cabinet Summary table | Displays prominent stale warning when rules/inputs change; guards verifier certification | `RunResult.metrics`, `res.check`, `res.tqs`, `res.summary` |
| **Screen F: Cabinet Map** | Physical rack & slot inspection | Cabinet selector $\to$ Inspect slot tooltips | Cabinet selector, CIOC/baseplate metrics, Emerson high-contrast CHARM color key | Interactive slot grid rendered with hover tag tooltips and free/spare slot distinctions | Displays stale warning if layout reflects prior run | `cabinet_html(res.rows, cab)` |
| **Screen G: Revision Repair** | Rev B minimal-move re-allocation | "Compare + re-allocate (keep unchanged in place)" | Baseline Rev A context, Rev B upload/demo toggle, delta comparison metrics, CP-SAT solver status | Monospace impact ledger table showing moved, added, deleted, in-place, and unchanged signals | Guarded: disabled when Rev A is missing or stale; staleness tracking for Rev B dataset | `revise(res.rows, mdb_b, rules)` using CP-SAT solver |
| **Screen H: Export Center** | Authoritative deliverables download | "Download allocation workbook" | Clear description of all 4 generated sheets (Allocation, Summary, TQ List, Rule-Check Report) | Technical file metadata and checksum | Download disabled when results are stale; clear guidance on re-running | Streams `write_workbook` Excel payload |
