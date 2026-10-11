# SlotSmith — Project Understanding & Frontend UX Audit

**Project:** SlotSmith (VIT Code Apex 3.0 · Track 1 Emerson · PS 1.2: Project IO Signal Sudoku)  
**Team:** Mac_Enthu (Aayush Aade, Siddhant Patil, Gaurang Bagwe)  
**Document Status:** Phase 1 Investigation & Engineering Audit (Pre-Redesign Baseline)  
**Audit Scope:** Deep Architecture Analysis, Backend Contract Verification, and Streamlit UX Audit  
**Author Role:** Senior Software Architect, Industrial Engineering Product Designer, UX Researcher & Test Engineer  

---

## 1. Product Purpose & Target Users

### 1.1 Engineering Problem & Operational Context
In process automation and distributed control system (DCS) engineering (specifically Emerson DeltaV Electronic Marshalling with CHARMs), industrial projects frequently encompass 10,000 to over 28,000 I/O signals across chemical plants, refineries, and offshore platforms. 

Historically, assigning field I/O signals to marshalling hardware was a manual, spreadsheet-bound workflow:
1. Systems engineering teams receive customer Instrument Master Databases (MDBs) in heterogeneous, non-standard Excel/CSV formats.
2. Engineers manually allocate signal pairs into marshalling cabinets, I/O carriers, baseplates, and individual CHARM terminal slots while juggling competing physical and electrical constraints (redundancy A/B segregation, logical grouping, multi-pair cable integrity, spare margins, and hardware matching).
3. Whenever a customer submits a revision (e.g., Rev B), engineers face hours of manual rework: re-checking assignments, identifying additions/deletions, and manually tracing the impact on panel construction while attempting to minimize costly wiring disruptions.

SlotSmith automates this end-to-end process using deterministic, constraint-based optimization (First-Fit-Decreasing divisible bin packing) combined with local minimal-perturbation repair (Google OR-Tools CP-SAT). It ingests MDBs, automatically maps schema headers, enforces rulebooks, produces traceable Technical Queries (TQs) for all unplaceable rows, executes allocation in seconds, certifies the results with an isolated verifier, and carries out revision-aware re-allocation.

### 1.2 Target User Personas
1. **DeltaV Lead I/O & Systems Engineer:**
   - *Needs:* Rapid ingestion of messy customer MDBs; configurable project rules without code edits; auditable 100% signal coverage (every signal either placed or covered by an actionable TQ); automated export to handover workbooks.
   - *Pain points:* Ambiguous header naming; conflicting engineering rules; untraceable errors in customer data; fear of black-box placement decisions.
2. **Cabinet Panel Designer & Packager:**
   - *Needs:* Clear visibility of physical hardware layout (Marshalling Cabinet → CIOC → Baseplate → CHARM); understanding exact spare capacity (empty baseplates, free terminal slots, wired spares); verifying that redundant A/B channels never share carriers.
   - *Pain points:* Dense, unreadable spreadsheets; accidental cable splitting across distant carriers; lack of visual spatial confirmation.
3. **Site Commissioning & Operations Lead (Downstream):**
   - *Needs:* Traceable impact reports between revisions; guarantee that wired Rev A signals remain in place during Rev B changes; zero unexplained signal movements.
   - *Pain points:* Physical rewiring costs; inconsistent controller numbering; untracked channel modifications.
4. **Hackathon Evaluator / Emerson Domain Judge:**
   - *Needs:* Immediate visual clarity on synthetic benchmark data; transparent verification of all 11 rule families; evidence-based performance claims; rapid interactive demonstration within a 5-minute presentation window.

---

## 2. Verified Architecture & Actual Data Flow

The architecture implements a rigorous certifying pipeline (`docs/architecture.md`, `src/slotsmith/pipeline.py`). Below is the verified end-to-end data flow:

```
Customer MDB(s) (Excel/CSV)
       │
       ▼
[ 1. Ingest & Auto-Map ] (src/slotsmith/ingest.py)
       │ • Auto-detects header row in top 15 rows
       │ • Fuzzy synonym matching (threshold >= 0.8)
       │ • Attaches row-level provenance (file:sheet:row)
       ▼
   MDB Object (Canonical DataFrame + Mapping Metadata)
       │
       ▼
[ 2. Data Validation & TQs ] (src/slotsmith/validate.py)
       │ • Row-level checks: missing tags, bad pairs, unknown IO, duplicate tags
       │ • Cable-level checks: size mismatches, pair collisions, A/B mix, group mix
       │ • Reserves held slots for blocked signals (Rule K-4)
       ▼
ValidationResult (Valid CableBlocks + Structured TQ List + Held Slots)
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
[ 3. RuleSet Configuration ]     [ 4. Constructive Allocator ] (src/slotsmith/allocator.py)
   (src/slotsmith/rules.py)              │ • Per-class First-Fit-Decreasing (sizes 2, 6, 12, 24)
   • Capacity & Spare %                  │ • Divisible-size optimal baseplate packing
   • Segregation & Isolation             │ • Group contiguity & look-ahead cabinet placer
   • Hardware table & Naming             ▼
                                 AllocationResult (Placements + Layout + Unplaced)
                                         │
                                         ▼
                                 [ 5. Flat Row Assembly & Exporter ] (src/slotsmith/export.py)
                                         │ • Emits 1 row per pair (Signal, Spare, Held)
                                         │ • Appends unplaced capacity & validation rows
                                         │ • Formats openpyxl 7-sheet deliverable
                                         ▼
                                  SlotSmith_allocation.xlsx
                                         │
       ┌─────────────────────────────────┴─────────────────────────────────┐
       ▼                                                                   ▼
[ 6. Independent Verifier ] (src/slotsmith/verifier.py)        [ 7. Revision Engine ] (src/slotsmith/revision.py)
   • Re-reads exported file                                       • Inputs: Rev A Rows + Rev B MDB
   • Zero code shared with allocator                              • Step 1: Pin identical cables (0 moves)
   • Checks 11 rule families from text names                      • Step 2: Greedy fill into spare holes
   • Emits PASS/FAIL & violation tallies                          • Step 3: CP-SAT window repair (repair_cpsat.py)
                                                                  • Step 4: Fallback full re-allocation if needed
                                                                  • Emits: Impact Report & Rev B Deliverable
```

### Verified Module Responsibilities & Key Decisions:
- **`src/slotsmith/ingest.py` (`read_mdb`, `auto_map`):** Maps input headers to canonical names (`tag`, `io_type`, `cable`, `pair`, `group`, `seg`, `cable_size`). Preserves exact Excel source row numbers (`src_row`). Supports multi-file and multi-sheet consolidation.
- **`src/slotsmith/validate.py` (`validate`):** Partitions raw rows into valid `CableBlock` structures and generates structured `TQ` objects citing rule-register IDs (`D-1` through `D-5`, `S-2`, `G-3`, `H-*`). A critical architectural decision: when a signal on a cable has an error, its slot is marked *held* (`held_slots`), ensuring other signals in the multi-pair cable retain their physical pair offsets (`Rule K-4`).
- **`src/slotsmith/allocator.py` (`allocate`, `Placer`, `ffd_pack`):**
  - Uses First-Fit-Decreasing (FFD) to pack cable blocks into 12-slot baseplates. For standard divisible sizes $S \in \{2, 6, 12\}$ and bin capacity $C = 12$, FFD provably achieves the theoretical minimum number of baseplates $\lceil \sum \text{sizes} / C \rceil$ (Coffman et al. 1987).
  - Segregates cables into side A, neutral, and side B. Neutral cables top up remaining capacity on A/B baseplates before opening dedicated baseplates.
  - Places baseplates into CIOCs (8 max) and Marshalling Cabinets (4 CIOCs max), keeping logical groups contiguous using a simulation look-ahead (`_touched`).
  - Enforces spare percentage by leaving $\lceil \text{spare\%} \times 32 \rceil$ baseplates empty in every cabinet.
- **`src/slotsmith/verifier.py` (`verify`):** Formulates an isolated certifying checker. It re-parses locations directly from exported hierarchical strings (e.g., `001-CBP-1-01` into CIOC 1, BP 1, Slot 1) and verifies 11 distinct rule families. It does not import the allocator or exporter.
- **`src/slotsmith/revision.py` & `repair_cpsat.py` (`revise`, `repair_window`):**
  - Pinning: Rev B cables matching Rev A in size, group, and segregation retain their exact physical slots. Additions on existing spare pairs incur 0 moves.
  - Greedy fill: New cables fill available holes in compatible CIOCs.
  - CP-SAT Window Repair: When greedy fill fails (e.g., spare limit reached), CP-SAT optimizes a sliding cabinet window with objective $\min(1000 \times \text{moved signals} + \text{baseplates})$.
  - Fallback: If CP-SAT cannot find a feasible repair within limits, the system falls back to full re-allocation and logs an explicit warning TQ (`R-2`).

---

## 3. Implemented vs. Planned Feature Matrix

To maintain strict scientific and engineering integrity, capabilities in the repository are catalogued below as **Implemented**, **Partially Implemented**, or **Planned / Conceptual**:

| Feature / Capability | Status in Codebase | Verification Source in Repo | Notes & Boundaries |
|---|---|---|---|
| Multi-file Excel/CSV Ingestion | **Implemented** | `src/slotsmith/ingest.py:79` | Multi-file and multi-sheet reading verified. |
| Header Detection & Auto-Mapping | **Implemented** | `src/slotsmith/ingest.py:42`, `test_core.py:52` | Deterministic synonym list + fuzzy match ($\ge 0.8$). |
| AI-Assisted Column Mapping | **Planned** | `docs/architecture.md:76`, `README.md:52` | **Not implemented.** No LLM is executed at runtime. |
| Source-Row Provenance Tracking | **Implemented** | `src/slotsmith/ingest.py:102`, `model.py:17` | `file:sheet:row` tracked for every signal. |
| Rule-Driven Validation & TQs | **Implemented** | `src/slotsmith/validate.py:54`, `test_core.py:100` | 9 error kinds raised as structured TQs with rule citations. |
| Natural-Language Rule Authoring | **Planned** | `docs/architecture.md:79` | **Not implemented.** Mentioned only as roadmap item. |
| Typed Configurable Rule Set | **Implemented** | `src/slotsmith/rules.py:44`, `test_core.py:226` | Pydantic model (`RuleSet`) serialized to/from JSON. |
| Interactive Rule Configuration UI | **Partially Implemented** | `app/streamlit_app.py:38` | Sidebar toggles and sliders exist; cannot edit hardware table or aliases. |
| Optimal Baseplate Packing (FFD) | **Implemented** | `src/slotsmith/allocator.py:81`, `test_core.py:201` | Divisible bin-packing proved for $\{2, 6, 12\}$. |
| Hierarchy Allocation Placer | **Implemented** | `src/slotsmith/allocator.py:139` | Cabinet $\to$ CIOC $\to$ Baseplate $\to$ Slot. |
| Independent Rule Verifier | **Implemented** | `src/slotsmith/verifier.py:58`, `test_core.py:158` | 11 rule families re-checked on exported strings. |
| Official Organiser Template Export | **Planned / Incomplete** | `docs/known_limitations.md:4`, `export.py:21` | Template not released by organizers; custom schema used. |
| Multi-Sheet Excel Exporter | **Implemented** | `src/slotsmith/export.py:151`, `test_core.py:290` | openpyxl export with 7 structured sheets. |
| Rev B Pinning & Greedy Fill | **Implemented** | `src/slotsmith/revision.py:96`, `test_core.py:254` | Unchanged cables pinned; spare pair additions = 0 moves. |
| CP-SAT Window-Local Repair | **Implemented** | `src/slotsmith/repair_cpsat.py:23` | OR-Tools CP-SAT window model (10s wall-clock limit). |
| Revision Impact Reporting | **Implemented** | `src/slotsmith/revision.py:289`, `test_core.py:263` | Tracks Added, Deleted, Moved, Modified in place, Cabinets hit. |
| Streamlit Prototype UI | **Partially Implemented** | `app/streamlit_app.py` | 191-line prototype; lacks error handling and UX polish. |
| React / Web Framework UI | **Not Implemented** | Out of scope / Frozen | Explicitly forbidden in hackathon scope; Streamlit frozen. |
| SQLite Run / Audit Logging | **Planned** | `docs/architecture.md:22` | **Not implemented.** Stack shows as planned. |
| Docker Containerization | **Planned** | `docs/requirements.md:22` | **Not implemented.** Local venv execution only. |
| Synthetic Data Generator | **Implemented** | `src/slotsmith/generator.py:37`, `cli.py:52` | Generates MDBs (100–30,000 signals) with injected errors. |

---

## 4. Existing UI Page & Interaction Inventory

The existing UI is a single-file Streamlit script (`app/streamlit_app.py`, 191 lines). An exhaustive component inventory reveals the current interaction surface:

### 4.1 Global Layout & Sidebar
- **`st.set_page_config` (`streamlit_app.py:26`):** Sets `page_title="SlotSmith"` and `layout="wide"`.
- **Global Header (`streamlit_app.py:30-31`):** `st.title` and `st.caption` declaring prototype status and synthetic labelling.
- **Sidebar: Rule Panel (`streamlit_app.py:38-58`):**
  - Iterates `rules.toggles`: `st.toggle(t.description, value=t.enabled, key=f"tg_{t.id}")` which directly mutates `RuleToggle.enabled` in session memory.
  - Spare Capacity: `st.slider("Spare per cabinet (%)", 0.0, 40.0, 10.0, 1.0)`. Displays caption calculating reserved baseplates.
  - Dropdowns: `st.selectbox` for `group_isolation_level` (`cioc`, `cabinet`, `none`) and `segregation_level` (`cioc`, `cabinet`).
  - Text inputs: `rules.naming.area` (default "AR1") and `rules.naming.unit` (default "100").
  - Expander: Read-only `st.dataframe` showing the CHARM / terminal-block lookup table.
  - Actions: `st.download_button` downloading `ruleset.json` and `st.file_uploader` for loading JSON rule sets.

### 4.2 Tab 1: "1 · Upload + allocate" (`streamlit_app.py:73-119`)
- **Top Inputs (Split 2:1):**
  - Left column: `st.file_uploader` accepting multiple `.xlsx`, `.xls`, `.csv` customer files.
  - Right column: Synthetic generator controls: number inputs for signals (100–30,000), seed (0–9999), and injected errors (0–50). Button: "Generate synthetic MDB" which invokes `generate()`, saves to a tempdir, and stores paths in session state.
- **Mapping Preview (`streamlit_app.py:91-92`):**
  - Displays `st.dataframe` of `mdb.mapping` once files are present.
- **Action Button (`streamlit_app.py:93`):**
  - "Allocate" (`type="primary"`). Invokes `slotsmith.pipeline.run()`, writes to a temporary Excel file, and stores `res` in `st.session_state`.
- **Results Display (`streamlit_app.py:98-119`):**
  - Metric row (6 columns): Signals allocated, Covered by TQ, Verifier violations, Cabinets, CIOCs, Baseplates used.
  - Data displays: Rule-check report dataframe and TQ list dataframe side-by-side.
  - Cabinet summary dataframe.
  - Workbook download button.

### 4.3 Tab 2: "2 · Cabinet map" (`streamlit_app.py:150-160`)
- **State Gate:** Displays `st.info("Allocate first.")` if `st.session_state.res` is absent.
- **Cabinet Selector:** `st.selectbox("Marshalling cabinet", cabs)`.
- **Custom HTML Renderer (`cabinet_html`, lines 121–147):**
  - Generates raw HTML flexbox divs displaying each CIOC as a vertical column with 8 horizontal rows (baseplates), each containing 12 tiny boxes (CHARM slots, 12px × 22px).
  - Colors slots according to a static color dictionary (`COL`): AI blue (`#4FA3FF`), AO violet (`#B98CFF`), DI green (`#7BD88F`), DO yellow (`#FFD54F`), DO_ISO orange (`#FF8A50`), DO_RELAY pink (`#FF6FA8`), SPARE grey (`#5B6B5F`), FREE dark green (`#16241A`).
  - Native browser tooltip (`title`) displays tag name on hover.

### 4.4 Tab 3: "3 · Revise (Rev B)" (`streamlit_app.py:161-191`)
- **State Gate:** Displays `st.info("Allocate Rev A first.")` if `st.session_state.res` is absent.
- **Inputs:** `st.file_uploader` for Rev B MDB and a checkbox "Use the synthetic Rev B generated with Rev A".
- **Action Button:** "Compare + re-allocate (keep unchanged in place)" (`type="primary"`). Executes `slotsmith.revision.revise()` under `st.spinner`.
- **Results Display:**
  - Metric row (6 columns): Moved, Added, Deleted, Modified in place, Unchanged, Violations.
  - Caption: Cabinets hit, CP-SAT repairs, fallback full re-allocation indicator.
  - Impact table: `st.dataframe` of `rr.impact`.

---

## 5. Frontend-to-Backend Integration Points & Data Contracts

The frontend interacts with the backend strictly through six discrete entry points. These define the frozen backend boundary:

```
[ app/streamlit_app.py ]
        │
        ├── (1) rules.default_ruleset() / RuleSet.model_validate()
        │       Contract: returns RuleSet model with toggles, hardware, naming, spare_percent
        │
        ├── (2) ingest.read_mdb(paths, mapping_override=None) -> MDB
        │       Contract: paths: list[Path|str]
        │       Returns: MDB(df=pd.DataFrame, mapping=dict[str, ColumnMapping])
        │       Raises: ValueError if no valid IO sheet found
        │
        ├── (3) generator.generate(n, seed, inject_errors) -> GenResult
        │       Contract: returns GenResult(df=pd.DataFrame, injected=list[dict])
        │
        ├── (4) generator.make_revision(rev_a_df, seed) -> pd.DataFrame
        │       Contract: returns pd.DataFrame of Rev B signals
        │
        ├── (5) pipeline.run(paths, rules, out_path, df=None, verify_from_file=True) -> RunResult
        │       Contract: returns RunResult with .rows, .summary, .tqs, .check, .metrics, .timings
        │
        └── (6) revision.revise(prev_rows, rev_b_df, rules) -> RevisionResult
                Contract: prev_rows: list[dict], rev_b_df: pd.DataFrame, rules: RuleSet
                Returns: RevisionResult with .rows, .summary, .impact, .check, .metrics, .tqs
```

### Critical Data Structures & Fields Utilized by the UI:
1. **`RunResult.metrics` (`dict`):**
   - `signals_allocated` (int), `signals_with_tq` (int), `violations` (int), `cabinets` (int), `ciocs` (int), `baseplates` (int), `lb_baseplates` (int), `coverage_pct` (float).
2. **`RunResult.rows` (`list[dict]`):**
   - Keys: `"Tag"`, `"IO Type"`, `"Cable"`, `"Cable Size"`, `"Pair"`, `"IO Group"`, `"Segregation"`, `"Row Kind"`, `"Controller"`, `"System Cabinet"`, `"Marshalling Cabinet"`, `"CIOC"`, `"Baseplate"`, `"Slot"`, `"CHARM Address"`, `"CHARM Type"`, `"Terminal Block"`, `"Status"`, `"TQ Ref"`, `"Source"`, plus internal coordinates `"_cab"`, `"_cioc"`, `"_bp"`.
3. **`RunResult.tqs` (`list[TQ]`):**
   - Attributes: `id` (str), `severity` ("blocking"|"warning"|"info"), `category` ("data"|"rule-conflict"|"capacity"|"hardware"), `rule_ref` (str), `message` (str), `tags` (list[str]), `cables` (list[str]), `sources` (list[str]), `suggested_action` (str).
4. **`RunResult.check` (`list[dict]`):**
   - Keys: `"Rule"` (str), `"Check"` (str), `"Result"` ("PASS"|"FAIL"), `"Violations"` (int), `"Examples"` (str).
5. **`RevisionResult.metrics` (`dict`):**
   - `moved`, `added`, `deleted`, `modified_in_place`, `unchanged`, `violations`, `cabinets_hit` (list[str]), `cpsat_repairs` (list[dict]), `fallback_full_reallocation` (bool).
6. **`RevisionResult.impact` (`list[dict]`):**
   - Keys: `"Change"` (str), `"Tag"` (str), `"Cable"` (str), `"From"` (str), `"To"` (str), `"IO Type (A→B)"` (str).

---

## 6. UX Friction Points Ranked by Severity & User Impact

Each evaluated finding is explicitly categorized as an **Observed Defect** (reproducible bug in code), a **Usability Concern** (inferred from interaction analysis), or an **Improvement Opportunity** (enhancement within frozen boundaries):

| ID | Category | Severity | Description & Root Cause | Affected File & Line | Expected User / Evaluator Impact |
|---|---|---|---|---|---|
| **UX-01** | Observed Defect | **CRITICAL** | **Unhandled crash on unmappable / corrupted upload.** `read_mdb(paths)` is called directly in tab 1 without exception handling. If a user uploads an invalid file, Streamlit crashes with a raw Python traceback (`ValueError`). | `app/streamlit_app.py:90` | First-time users are blocked immediately; fatal during live judging. |
| **UX-02** | Usability Concern | **HIGH** | **Stale results upon rule modification.** If a user tweaks a sidebar rule (e.g., changes spare % or toggles segregation), the page re-renders, but `st.session_state.res` retains results from the *old* rule set. The screen displays out-of-sync KPIs with zero staleness warning. | `app/streamlit_app.py:38-58`, `98` | Engineers make incorrect capacity assumptions; creates confusion when rules don't match reports. |
| **UX-03** | Usability Concern | **HIGH** | **Cluttered, confusing first-run experience.** In Tab 1, synthetic demo parameters (`signals`, `seed`, `injected errors`) are placed side-by-side with real file uploaders in a 2:1 column split, confusing users about which action to perform first. | `app/streamlit_app.py:74-85` | High cognitive friction; first-time engineers cannot tell demo mode from production mode. |
| **UX-04** | Usability Concern | **HIGH** | **Read-only column mapping with no manual override.** `read_mdb` supports a `mapping_override` dict, but the UI only renders auto-mapped headers in a read-only table. If a column is misidentified, users cannot fix it in the UI. | `app/streamlit_app.py:91-92`, `src/slotsmith/ingest.py:92` | Forces user to edit source Excel files externally if auto-mapping fails on custom headers. |
| **UX-05** | Usability Concern | **HIGH** | **Inaccessible, non-interactive cabinet visualization.** The cabinet map in Tab 2 uses raw HTML strings with tiny 12px × 22px colored boxes. Clicking a slot does nothing; tooltips rely on delayed browser `title` tags; dark `#16241A` free slots look unstyled; no slot search. | `app/streamlit_app.py:121-147` | Impossible to inspect signals rapidly or locate specific tags across hundreds of slots during a demo. |
| **UX-06** | Usability Concern | **MEDIUM** | **Disjointed TQ remediation.** TQs are presented in a flat, unfilterable dataframe. Users cannot filter by severity (Blocking vs Warning), search by tag, or view complete source rows without horizontal scrolling. | `app/streamlit_app.py:111-114` | Slows down data cleaning; engineers cannot prioritize fatal errors over informational warnings. |
| **UX-07** | Usability Concern | **MEDIUM** | **Asymmetric revision workflow.** Rev B allocation is hidden in Tab 3. After running Rev B, the cabinet map in Tab 2 *still shows Rev A*. Users have no visual representation of Rev B cabinets or moved signals. | `app/streamlit_app.py:150`, `161` | Users cannot visually inspect where moved signals landed in the physical cabinet. |
| **UX-08** | Usability Concern | **MEDIUM** | **Lack of execution progress & stage timings.** Allocation and revision display a basic `st.spinner` without showing pipeline phase breakdown (ingest, validate, allocate, verify). Metrics omit timing data even though `res.timings` is computed by the backend. | `app/streamlit_app.py:95`, `177`, `src/slotsmith/pipeline.py:71` | For large 20k runs taking 6s, user experiences a frozen screen without feedback on which step is running. |
| **UX-09** | Improvement Opportunity | **MEDIUM** | **Missing industrial aesthetic & hierarchy.** Standard Streamlit styling (bright red primary button, generic font, raw table borders) looks like an informal script rather than an enterprise DCS engineering platform. | `app/streamlit_app.py:26-31` | Reduces credibility and polish during competition presentations. |
| **UX-10** | Usability Concern | **LOW** | **Silent halt on missing Rev B input.** If user clicks "Compare + re-allocate" without uploading a file and with synthetic box unchecked, `st.stop()` executes silently, leaving a blank area without guidance. | `app/streamlit_app.py:176` | Confuses users who expect an error banner indicating missing inputs. |

---

## 7. Recommended Information Architecture & User Journey

To solve the friction points without changing backend behavior, we propose restructuring the Streamlit interface into a cohesive 4-stage engineering workflow:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ HEADER: SlotSmith Industrial Marshalling Platform · VIT Code Apex 3.0 (PS 1.2 Emerson)          │
│ System Status: Ready | Engine: Certifying FFD + CP-SAT | Verifier: 11 Rule Families Active      │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ STAGE 1: INGEST & AUDIT ──► STAGE 2: ALLOCATE & VERIFY ──► STAGE 3: CABINET MAP ──► STAGE 4: REVISION │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 7.1 Stage 1: Ingest & Data Pre-Check ("Ingest & Audit")
- **Dual-Path Onboarding:**
  - *Mode A: Production Upload:* Dropzone supporting multi-file customer MDBs (`.xlsx`, `.csv`).
  - *Mode B: Benchmark / Synthetic Preset:* Prominent one-click load button ("Quick Load Synthetic 2,000-Signal Benchmark (6 Injected Errors)") for instant evaluation.
- **Interactive Schema Alignment:**
  - Displays detected headers alongside canonical fields (`Tag`, `IO Type`, `Cable`, `Pair`, `Group`, `Segregation`, `Cable Size`).
  - Provides dropdown overrides for each required field if confidence is below 100%.
  - Emits pre-flight data health summary (total rows, detected sheets, null counts) before allocation.

### 7.2 Stage 2: Allocation & Verification Engine ("Allocate & Verify")
- **Primary Execution Bar:**
  - Clear "Run Complete Allocation" action with progress stages (Ingesting → Validating → Packing → Verifying).
  - Displays pipeline benchmark timing breakdown (`ingest_s`, `validate_s`, `allocate_s`, `verify_s`).
- **Executive Metric Cards (KPI Strip):**
  - Signals Allocated (count + fill %)
  - Signals Covered by TQ (severity breakdown)
  - Independent Verifier Status (Bold Green "0 Violations · PASS" badge)
  - Hardware Footprint: Cabinets, CIOCs, Baseplates (with exact theoretical lower bound comparison)
- **Deep-Dive Diagnostic Tabs:**
  - *Rule Certification Ledger:* 11-row verification checklist with PASS badges and rule citations.
  - *Actionable TQ Console:* Interactive table with search, severity filter chips (Blocking, Warning, Info), and rule-register reference links.
  - *Cabinet Capacity Breakdown:* Interactive summary of signals, spares, and fill % per cabinet.
  - *Deliverable Handover:* One-click download of the complete 7-sheet openpyxl Excel deliverable.

### 7.3 Stage 3: Digital Marshalling Cabinet Inspector ("Cabinet Map")
- **Spatial Hardware Navigator:**
  - Selector for Marshalling Cabinet (e.g., `AR1-DCM-100-01`).
  - Toggle between Rev A layout and Rev B layout (when revision exists).
  - Signal finder / search bar: typing a Tag or Cable instantly highlights its physical CHARM location.
- **Card-Based Spatial Visualization:**
  - Renders CIOCs as physical carrier cards with group and segregation headers.
  - Displays 8 Baseplates per CIOC with slot strips.
  - Uses high-contrast, Emerson-aligned color tokens with clear borders.
  - Clickable slots that populate a "CHARM Details Drawer" showing Tag, Cable, Pair, IO Type, Terminal Block, Controller, and Source Provenance.

### 7.4 Stage 4: Revision & Minimal-Move Impact Engine ("Revise (Rev B)")
- **Revision Control Center:**
  - Load Rev B MDB or use synthetic revision.
  - Single-click "Execute Minimal-Move Re-allocation".
- **Comparative Impact KPI Cards:**
  - Moved Signals (highlighting CP-SAT move minimization vs. from-scratch re-run)
  - Added Signals (distinguishing zero-move spare-pair additions from new cables)
  - Deleted Signals
  - Modified in Place (CHARM / Terminal Block swaps)
  - Unchanged Signals (pinned count)
  - Independent Verifier Check on Rev B
- **Interactive Move Audit Table:**
  - Filter by change type (e.g., view only Moved or only Modified).
  - Displays exact "From" and "To" physical addresses.
  - Lists affected cabinets and CP-SAT solver status (Optimal vs. Feasible).

---

## 8. Visual Design Direction for Industrial Engineering Software

The visual presentation must reflect mission-critical DCS engineering software rather than a generic consumer prototype:

### 8.1 Design Tokens & Theming
- **Background & Canvas:**
  - Base canvas: Deep industrial slate (`#0B0F19` or clean neutral light `#F8FAFC`).
  - Card surfaces: Elevated container gray (`#1E2638` in dark, `#FFFFFF` with `#E2E8F0` border in light).
- **Typography:**
  - Headings & Body: Clean system sans-serif (`Inter`, `system-ui`, `-apple-system`).
  - Engineering Identifiers: Monospace typography (`ui-monospace`, `SFMono-Regular`, `Menlo`) for all Tags (`10-PT-1001A`), Cables (`CBL-0014`), and CHARM Addresses (`001-CBP-1-01`).
- **Signal Type Color Coding (Emerson DeltaV Standards):**
  - **AI (Analog Input):** Tech Azure Blue (`#2563EB` / `#38BDF8`)
  - **AO (Analog Output):** Control Violet (`#7C3AED` / `#A855F7`)
  - **DI (Digital Input):** Emerald Green (`#059669` / `#34D399`)
  - **DO Standard:** Industrial Gold (`#D97706` / `#FBBF24`)
  - **DO Isolated / Fused:** Safety Orange (`#EA580C` / `#FB923C`)
  - **DO Relay Output:** Magenta / Rose (`#E11D48` / `#F43F5E`)
  - **Wired Spare Pair:** Steel Slate (`#64748B`)
  - **Free Unused Slot:** Dark Void Grid (`#1E293B` with `#334155` border)
- **Status & Certification Badges:**
  - Certified PASS: Emerald badge (`#065F46` bg, `#34D399` text) with checkmark icon.
  - Warning TQ: Amber badge (`#78350F` bg, `#FBBF24` text).
  - Blocking TQ: Crimson badge (`#7F1D1D` bg, `#F87171` text).

---

## 9. Accessibility, Error Handling, Session State, & Demo Reliability

### 9.1 Session-State Architecture & Staleness Protection
Streamlit scripts execute from top to bottom on every user input. To eliminate data loss and stale state:
1. **Explicit State Schema:** Maintain dedicated session keys:
   - `st.session_state.app_state`: `"IDLE"` | `"MAPPED"` | `"ALLOCATED"` | `"REVISED"`
   - `st.session_state.active_rules_hash`: MD5 hash of active RuleSet.
   - `st.session_state.last_allocated_rules_hash`: Hash of rules used during the last allocation.
   - `st.session_state.is_stale`: Boolean flag indicating if rules were altered after allocation.
2. **Visual Staleness Warning:** If `is_stale` is true, render a prominent warning banner: *"Active rules have changed since last allocation. Re-run allocation to update results."*

### 9.2 Robust Exception Trapping & Defensive Input Validation
- Wrap all invocations of `read_mdb()` in comprehensive `try ... except ValueError as e` blocks.
- If ingestion fails, display an informative, dismissible error card explaining the required columns (`tag`, `io_type`, `cable`, `pair`) instead of allowing an unhandled crash.
- Validate that Rev A allocation exists before enabling Rev B buttons.

### 9.3 Demo Reliability & Laptop Viewport Optimization
- **Laptop Responsiveness:** Ensure wide tables have container width constraints and horizontal scrolling enabled for 13" laptop screens (1280px width) commonly used by judges and presenters.
- **One-Click Benchmark Mode:** Provide pre-packaged synthetic demo buttons in the UI header. Evaluators can experience the full pipeline (Ingestion → Allocation → Verification → Spatial Map → Revision) in 3 clicks within 30 seconds.

---

## 10. Technical Risks, Unresolved Questions, & Assumptions

The audit confirms the following boundary conditions that must be respected during Phase 2:

1. **Unreleased Official Datasets:** The official organizer sample MDB and allocation template have not been released (`docs/known_limitations.md:4`). The UI must clearly label synthetic demo data and remain schema-flexible via `export.COLUMNS`.
2. **CP-SAT Non-Determinism:** The revision repair engine uses multi-threaded OR-Tools CP-SAT under a wall-clock limit (10s). Move counts vary between runs (429–470 moves across runs). The UI must report actual solver status (`OPTIMAL` vs. `FEASIBLE`) transparently without claiming "globally proven minimum moves".
3. **Optimality Scope:** FFD is provably optimal for divisible sizes $\{2, 6, 12\}$ within a single segregation class. Group-level optimality is tested and verified, but CIOC and cabinet minimization is heuristic. The UI must avoid misleading claims of "universal mathematical optimality".
4. **Backend Freeze Integrity:** All business logic in `src/slotsmith/` is frozen. The frontend redesign must interface exclusively via public module contracts and must not duplicate allocation or verifier checks in UI code.
