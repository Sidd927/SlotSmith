# SlotSmith

SlotSmith automates DeltaV field signal allocation using constraint-based optimisation. It validates IO data, enforces capacity, CHARM and redundancy rules, flags conflicts, verifies placements, and minimises signal moves across revisions. AI assists with ambiguous data mapping, while deterministic rules ensure correctness and auditability.

**VIT Code Apex 3.0 · Track 1 (Emerson) · PS 1.2 Project IO SIGNAL SUDOKU · Team Mac_Enthu**

> Prototype status: works end-to-end on **synthetic** MDBs generated from the published rulebook. The organiser's sample MDB and allocation template have not been released, so nothing here demonstrates hidden-test compatibility.

## What it does
1. **Ingest:** reads one or many Excel/CSV IO MDBs, detects the header row, auto-maps columns and keeps `file:sheet:row` provenance.
2. **Validate:** raises traceable TQs for missing or invalid data, duplicates, pairs beyond the cable size, A+B on one cable, mixed groups, and unknown IO types.
3. **Allocate:** places each cable as a block into cabinet → CIOC → baseplate → CHARM slot, following user-editable rules: grouping, A/B segregation, 12/8/4 capacity, pair order, spare %, CHARM + terminal block, and naming patterns.
4. **Verify:** an independent checker re-reads the exported workbook and re-checks 11 rule families.
5. **Revise:** for Rev B it pins unchanged cables, fills holes, and uses an OR-Tools CP-SAT window repair to minimise moved signals. It also produces an impact report.

## Quick start
```bash
/opt/homebrew/bin/python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev,ui]"
.venv/bin/slotsmith generate --signals 2000 --errors 6 --out data/synthetic/mdb.xlsx --rev-b data/synthetic/mdb_revB.xlsx
.venv/bin/slotsmith allocate data/synthetic/mdb.xlsx --out artifacts/alloc.xlsx
.venv/bin/slotsmith verify artifacts/alloc.xlsx --mdb data/synthetic/mdb.xlsx
.venv/bin/slotsmith revise --prev artifacts/alloc.xlsx --mdb data/synthetic/mdb_revB.xlsx --out artifacts/alloc_revB.xlsx
.venv/bin/streamlit run app/streamlit_app.py      # landing page + workbench (light/dark follow the system or Streamlit Settings)
.venv/bin/python -m pytest -q                     # 31 tests
.venv/bin/python scripts/benchmark.py             # artifacts/benchmarks.json
.venv/bin/python scripts/build_deck.py            # Round 1 deck
```

## Measured on synthetic data (`artifacts/benchmarks.json`, Apple M5 laptop)
- 0 verifier violations in 12 runs (500–20,000 signals).
- 100% of rows allocated or covered by a TQ.
- 81 of 81 injected errors raised as TQs.
- Baseplates equal the exact per-group minimum in 12/12 runs (`artifacts/audit/`).
- 20,033 signals end-to-end in 6.0 s (median).
- Revisions (10 cases): 429–470 signals moved across 3 runs (CP-SAT is multi-threaded under a time limit, so results vary) vs 49,805 for from-scratch re-runs; 0 violations; 7 of 11 CP-SAT window repairs proven exact; worst case ≈ 58 s.
- Audit (10 Oct): see `docs/audit/final_audit.md`. Clean-environment reproduction: `zsh scripts/repro_clean.sh`.

## Repository map
| Path | Contents |
|---|---|
| `src/slotsmith/` | engine (ingest, validate, rules, allocator, verifier, export, revision, repair_cpsat, generator, cli) |
| `app/` | Streamlit UI: `views/` (pages), `ui/` (theme, components, shell), `core/` (session and display logic). Design: [design.md](design.md) |
| `tests/` | pytest + Hypothesis |
| `scripts/` | benchmark, deck builder |
| `docs/` | requirements, rule register, Emerson analysis, literature, sources, architecture, decisions, validation, limitations, ledger |
| `deliverables/round1/` | `SlotSmith_Round1.pptx/.pdf`, presentation QA, source register |
| `reference/` | official files (git-ignored, hackathon use only), Emerson public documents |

## Declared tools
Python, pandas, openpyxl, pydantic, Google OR-Tools CP-SAT (Apache-2.0), pytest, Hypothesis, Streamlit, python-pptx, PyMuPDF, LibreOffice (deck PDF).

AI coding assistance: Claude Code (Anthropic) was used during development. **No LLM is used at runtime yet**; planned uses are limited to suggestions that a user reviews.
