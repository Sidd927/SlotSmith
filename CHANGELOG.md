# Changelog

## Unreleased — UI redesign (11 Oct 2026)
- New landing page and seven-stage workbench (Input, Review, Allocate, Results, Cabinets, Revise, Deliverables) on real URL routes; design in `design.md`, research in `docs/ux_research.md`, feature truth in `docs/feature_capability_matrix.md`, review in `docs/ux_review_log.md`.
- Native light and dark themes with no reruns on switch; cabinet map with type codes; revision workbook download; start-over confirmation; computed (not hard-coded) rule summary.
- Fixed: duplicate-widget-key crash on Allocate, uploads not reflected until the next click, `.xls` advertised without support, removed disabled CORS/XSRF flags from the worktree config.
- Performance: landing HTML 2.37 MB to 55 KB (base64 images removed).
- Tests: 122 (31 backend/audit unchanged, 91 UI). `src/slotsmith/` unchanged.

## 0.1.0 — 10 Oct 2026
- Research: Emerson ecosystem analysis, literature review (23 verified refs), source and rule registers.
- Engine: ingestion + auto-map, validation/TQs, per-class FFD allocator, independent verifier, Excel exporter,
  revision engine with CP-SAT minimum-move window repair, CLI, Streamlit prototype UI.
- Tests: 25 (unit, mutation, property-based). Benchmark on synthetic data (`artifacts/benchmarks.json`).
- Round 1 deck v1 on the official template (PPTX + PDF) with QA log.
